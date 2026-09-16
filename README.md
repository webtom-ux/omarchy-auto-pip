# omarchy-auto-pip

Automatically picture-in-picture a playing video when you leave its Hyprland
workspace, and put it back when you return.

On YouTube that is Chromium's real Picture-in-Picture window (video only, no
toolbar). mpv, VLC and similar players still pop out as the whole window.

## Behavior

1. YouTube is playing on workspace 3.
2. Switch to workspace 1 → a small floating PiP appears (bottom-right by
   default, or wherever you last dragged it). Paused videos stay put.
3. Drag the PiP wherever you like; the position is remembered.
4. Pause → PiP closes. Play on another workspace → PiP comes back.
5. Return to workspace 3 → PiP closes and the video is back in the app.

You can switch workspaces as often as you want while the video is playing.

## Install

```bash
omarchy plugin add https://github.com/webtom-ux/omarchy-auto-pip.git --enable
~/.config/omarchy/plugins/webtom.auto-pip/install.sh
```

Then restart Chromium/YouTube and run `hyprctl reload`.

`install.sh` is idempotent. It:

- registers the Chromium native messaging host
- loads the Auto PiP extension and a localhost DevTools port (needed so PiP
  can re-enter after every workspace switch)
- hooks the Hyprland Lua engine from `~/.config/hypr/hyprland.lua`

## Configuration

Override any defaults in `~/.config/omarchy/auto-pip.lua`:

```lua
return {
  enabled = true,
  width = 480,
  height = 270,
  margin = 40,
  anchor = "bottom-right", -- bottom-left, top-right, top-left
  remember_position = true,
  only_when_playing = true,
  matches = {
    { class = "youtube%.com__" },
    { class = "^mpv$" },
    { class = "^vlc$" },
  },
}
```

`class` and `title` are Lua patterns. A window matches if **any** rule matches
completely. Apply with `hyprctl reload`.

## Disable

```lua
-- ~/.config/omarchy/auto-pip.lua
return { enabled = false }
```

Then `hyprctl reload`. Or `omarchy plugin disable webtom.auto-pip` and comment
out the Auto PiP block in `~/.config/hypr/hyprland.lua`.

## Uninstall

`omarchy plugin remove` only deletes the plugin folder. Also undo what
`install.sh` added:

```bash
omarchy plugin remove webtom.auto-pip
```

1. Remove the Auto PiP block from `~/.config/hypr/hyprland.lua` (the
   `dofile` of `webtom.auto-pip/auto-pip.lua`).
2. Delete `~/.config/chromium/NativeMessagingHosts/com.webtom.auto_pip.json`.
3. In `~/.config/chromium-flags.conf`, drop this plugin's path from
   `--load-extension=...` (keep Omarchy's other extensions). Remove these
   lines if Auto PiP added them and you do not need them otherwise:
   `--remote-debugging-address=127.0.0.1`,
   `--remote-debugging-port=19222`,
   `--remote-allow-origins=*`.
4. Restart Chromium/YouTube and run `hyprctl reload`.

Optional leftovers:

```bash
rm -f ~/.config/omarchy/auto-pip.lua
rm -rf ~/.local/state/omarchy/auto-pip
```
