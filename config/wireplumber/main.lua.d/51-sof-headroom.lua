-- Give SOF playback room for the DSP's burst reads to prevent xrun loops.
-- https://github.com/thesofproject/linux/issues/5284
table.insert(alsa_monitor.rules, {
  matches = {
    {
      { "node.name", "matches", "alsa_output.*" },
      { "api.alsa.card.name", "matches", "sof-*" },
    },
  },
  apply_properties = {
    ["api.alsa.headroom"] = 1024,
  },
})
