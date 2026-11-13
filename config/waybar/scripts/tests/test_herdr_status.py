import importlib.util
import json
import os
import select
import signal
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).parent.parent / "herdr-status.py"
SPEC = importlib.util.spec_from_file_location("herdr_status", SCRIPT)
herdr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(herdr)


def terminal(address, status, state="live", turn=0, seen=None):
    return {
        "address": address,
        "status": {"state": status, "app": "codex"} if status is not None else None,
        "state": state,
        "turn": turn,
        "labels": {} if seen is None else {"herdr.seen": seen},
    }


class HerdrStatusTest(unittest.TestCase):
    def test_done_counts_only_unseen_completed_turns(self):
        agents = [
            terminal("t12", "done", turn=23, seen="23"),
            terminal("box/t4", "done", turn=2, seen="2"),
            terminal("box/t1", "idle", turn=2, seen="2"),
            terminal("t17", "working", turn=9, seen="9"),
        ]
        snapshot = {
            "machines": [{"name": "box", "state": "connected"}],
            "terminals": agents,
        }
        result = herdr.render(snapshot, set())
        self.assertIn("Herdr: 1 working, 3 idle", result["tooltip"])
        self.assertNotIn(herdr.STATUS_ICONS["done"], result["text"])
        agents[0]["turn"] = 24
        self.assertEqual("done", herdr.agent_status(agents[0]))
        agents[0]["status"]["state"] = "idle"
        self.assertEqual("done", herdr.agent_status(agents[0]))
        agents[0]["labels"]["herdr.seen"] = "24"
        self.assertEqual("idle", herdr.agent_status(agents[0]))
        for raw in ("done", "idle", "working", "blocked", "error"):
            self.assertEqual(raw, herdr.agent_status(terminal("t1", raw)))
        self.assertEqual("done", herdr.agent_status(terminal("t1", "done", seen="invalid")))

    def test_counts_live_agents_and_excludes_disconnected_machines(self):
        # hc omits machines entirely when no remote connections are configured.
        self.assertEqual("idle", herdr.render({"terminals": []}, set())["class"])
        snapshot = {
            "machines": [
                {"name": "box", "state": "connected"},
                {"name": "offline<&", "state": "needs_login"},
            ],
            "terminals": [
                terminal("t1", "working"),
                terminal("t2", None),
                terminal("t3", "done", "finished"),
                terminal("box/t1", "error"),
                terminal("box/t2", "idle"),
                terminal("box/t3", "new-status"),
                terminal("offline<&/t1", "done"),
            ],
        }
        rendered = herdr.render(snapshot, set())
        self.assertEqual(["error", "partial"], rendered["class"])
        self.assertIn("Herdr: 1 working, 1 idle, 1 error, 1 unknown", rendered["tooltip"])
        self.assertIn("offline&lt;&amp;: needs_login", rendered["tooltip"])
        self.assertNotIn("done", rendered["tooltip"])
        excluded = herdr.render(snapshot, {"machine:box", "machine:offline<&"})
        self.assertEqual("working", excluded["class"])
        self.assertIn("box: excluded", excluded["tooltip"])

    def test_menu_updates_exclusions_without_removing_other_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "settings.json"
            state.write_text(json.dumps({"disabled": ["local", "old-machine-id"]}))
            snapshot = {"machines": [{"name": "local", "state": "connected"}]}
            choose = lambda entries: entries[1]
            self.assertTrue(herdr.machine_menu(state, lambda *_: snapshot, choose))
            self.assertEqual(
                {"local", "old-machine-id", "machine:local"}, herdr.read_disabled(state)
            )
            herdr.machine_menu(state, lambda *_: snapshot, choose)
            self.assertEqual({"local", "old-machine-id"}, herdr.read_disabled(state))
            before = state.read_bytes()
            self.assertFalse(herdr.machine_menu(state, lambda *_: snapshot, lambda _: None))
            self.assertEqual(before, state.read_bytes())

    def test_stream_coalesces_status_events_and_reacts_to_menu_and_heartbeat(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "settings.json"
            read_fd, write_fd = os.pipe()
            stream = os.fdopen(read_fd, "rb", buffering=0)
            snapshot = {"machines": [], "terminals": [terminal("t1", "working")]}
            outputs, calls, errors = [], [], []
            changed = threading.Condition()

            def emit(value):
                with changed:
                    outputs.append(value)
                    changed.notify_all()

            def fetch(*args):
                calls.append(args)
                return snapshot

            def run():
                try:
                    herdr.follow(stream, emit, state, fetch)
                except (EOFError, ValueError) as error:
                    errors.append(error)

            def wait_for_count(count):
                with changed:
                    self.assertTrue(changed.wait_for(lambda: len(outputs) >= count, timeout=2))

            def send(message):
                os.write(write_fd, (json.dumps(message) + "\n").encode())

            with (
                patch.object(herdr, "DEBOUNCE", 0.03),
                patch.object(herdr, "STATE_INTERVAL", 0.03),
            ):
                worker = threading.Thread(target=run, daemon=True)
                worker.start()
                try:
                    # The stream starts with a snapshot; split JSON across reads.
                    os.write(write_fd, b'{"terminals":')
                    os.write(write_fd, b'[]}\n')
                    wait_for_count(1)
                    snapshot["terminals"][0]["status"]["state"] = "blocked"
                    for _ in range(8):
                        send({"method": "event", "params": {"type": "status"}})
                    wait_for_count(2)
                    self.assertEqual("blocked", outputs[-1]["class"])
                    self.assertEqual(2, len(calls))
                    send({"method": "event", "params": {"type": "title"}})
                    with changed:
                        self.assertFalse(changed.wait_for(lambda: len(outputs) > 2, timeout=0.12))
                    self.assertEqual(2, len(calls))
                    state.write_text('{"disabled":["local"]}')
                    wait_for_count(3)
                    self.assertIn("local: excluded", outputs[-1]["tooltip"])
                    snapshot["machines"] = [{"name": "box", "state": "needs_login"}]
                    send({"method": "heartbeat", "params": {}})
                    wait_for_count(4)
                    self.assertIn("box: needs_login", outputs[-1]["tooltip"])
                    send({"method": "missed", "params": {"terminals": []}})
                    wait_for_count(5)
                    # Connection health must still refresh when title chatter
                    # prevents idle heartbeats from arriving.
                    snapshot["machines"][0]["state"] = "connected"
                    with patch.object(herdr, "HEALTH_INTERVAL", 0.06):
                        send({"method": "event", "params": {"type": "title"}})
                        wait_for_count(6)
                    self.assertEqual("idle", outputs[-1]["class"])
                    snapshot["terminals"][0].update(
                        status={"state": "done"}, turn=1, labels={"herdr.seen": "0"}
                    )
                    state.write_text('{"disabled":[]}')
                    send({"method": "event", "params": {"type": "turn"}})
                    wait_for_count(7)
                    self.assertEqual("done", outputs[-1]["class"])
                    snapshot["terminals"][0]["labels"]["herdr.seen"] = "1"
                    send({"method": "event", "params": {"type": "labels"}})
                    wait_for_count(8)
                    self.assertEqual("idle", outputs[-1]["class"])
                finally:
                    os.close(write_fd)
                    worker.join(timeout=2)
                    stream.close()
                self.assertFalse(worker.is_alive())
                self.assertIsInstance(errors[-1], EOFError)

    def test_subscriber_reconnects_and_cleans_up_its_child_on_sigterm(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fake = root / "hc"
            fake.write_text(
                f"#!{sys.executable}\n"
                "import json, os, sys, time\n"
                "from pathlib import Path\n"
                "root = Path(__file__).parent\n"
                "if sys.argv[1] == 'connect':\n"
                "    request = json.loads(sys.stdin.readline())\n"
                "    assert request['method'] == 'terminal.list'\n"
                "    snapshot = json.loads((root / 'snapshot.json').read_text())\n"
                "    print(json.dumps({'id': request['id'], 'result': snapshot}))\n"
                "else:\n"
                "    count = root / 'connections'\n"
                "    n = int(count.read_text()) + 1 if count.exists() else 1\n"
                "    count.write_text(str(n))\n"
                "    (root / 'child.pid').write_text(str(os.getpid()))\n"
                "    state = 'working' if n == 1 else 'blocked'\n"
                "    snapshot = {'terminals': [dict(address='t1', state='live', status={'state': state})]}\n"
                "    (root / 'snapshot.json').write_text(json.dumps(snapshot))\n"
                "    print(json.dumps({'terminals': []}), flush=True)\n"
                "    time.sleep(0.3 if n == 1 else 30)\n"
            )
            fake.chmod(0o755)
            env = {
                **os.environ,
                "PATH": f"{root}:{os.environ['PATH']}",
                "XDG_STATE_HOME": str(root / "state"),
            }
            process = subprocess.Popen(
                [sys.executable, str(SCRIPT)], env=env, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, bufsize=0,
            )
            try:
                outputs = []
                for _ in range(3):
                    self.assertTrue(select.select([process.stdout], [], [], 5)[0])
                    outputs.append(json.loads(process.stdout.readline()))
                self.assertEqual(
                    ["working", "unavailable", "blocked"], [v["class"] for v in outputs]
                )
                child_pid = int((root / "child.pid").read_text())
                process.terminate()
                self.assertEqual(0, process.wait(timeout=3))
                with self.assertRaises(ProcessLookupError):
                    os.kill(child_pid, 0)
                self.assertEqual(b"", process.stderr.read())
            finally:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=3)
                process.stdout.close()
                process.stderr.close()

    def test_snapshot_failure_clears_counts_instead_of_reusing_them(self):
        with tempfile.TemporaryDirectory() as directory:
            read_fd, write_fd = os.pipe()
            stream = os.fdopen(read_fd, "rb", buffering=0)
            outputs = []
            os.write(write_fd, b'{"terminals":[]}\n')

            def unavailable_snapshot(*_):
                raise subprocess.TimeoutExpired("hc ls", 5)

            try:
                with self.assertRaises(subprocess.TimeoutExpired):
                    herdr.follow(
                        stream, outputs.append, Path(directory) / "settings.json",
                        unavailable_snapshot,
                    )
                self.assertEqual([], outputs)
                self.assertNotIn("no agents", herdr.unavailable()["tooltip"])
            finally:
                os.close(write_fd)
                stream.close()


if __name__ == "__main__":
    unittest.main()
