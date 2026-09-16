-- Default Auto PiP settings.
-- Override any of these in ~/.config/omarchy/auto-pip.lua by returning a table
-- with the keys you want to change.

return {
  enabled = true,

  -- Logical pixels. 16:9, similar in spirit to Omarchy's native PiP overlay.
  width = 480,
  height = 270,
  margin = 40,
  -- bottom-right | bottom-left | top-right | top-left
  anchor = "bottom-right",

  -- Keep the last place you dragged (and resized) the PiP window to.
  remember_position = true,

  -- Only PiP while MPRIS reports PlaybackStatus=Playing (YouTube, mpv, VLC, …).
  -- Paused/stopped windows stay on their home workspace.
  only_when_playing = true,

  -- Lua patterns (not PCRE). A window matches if ANY rule matches.
  -- A rule matches when every provided field matches.
  matches = {
    { class = "youtube%.com__" },
    { class = "^mpv$" },
    { class = "^vlc$" },
    { class = "^celluloid$" },
    { class = "^io%.github%.celluloid_player%.Celluloid$" },
    { class = "^org%.gnome%.Totem$" },
    { class = "^com%.github%.rafostar%.Clapper$" },
  },

  debug = false,
}
