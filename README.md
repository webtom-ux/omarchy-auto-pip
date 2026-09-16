# Auto PiP

Wechselt ein passendes App-Fenster (z. B. YouTube) automatisch in ein kleines,
verschiebbares Picture-in-Picture-Fenster, sobald du den Workspace verlässt.
Kommst du zurück, landet es wieder als normales App-Fenster auf seinem
ursprünglichen Workspace.

## Verhalten

1. YouTube (oder mpv, VLC, …) spielt ein Video auf Workspace 3.
2. Du wechselst auf Workspace 1 → nur wenn das Video **läuft**, wird das
   Fenster klein, floating, gepinnt und erscheint unten rechts (oder dort,
   wohin du es zuletzt geschoben hast). Ist es pausiert, bleibt es auf 3.
3. Du schiebst das PiP-Fenster irgendwohin — die Position wird merkt.
4. Pause im PiP → es geht zurück auf seinen Workspace. Play auf einem
   anderen Workspace → es kommt wieder als PiP.
5. Du gehst zurück auf Workspace 3 → Pin weg, Originalgröße, wieder gekachelt.

Native Browser-PiP-Fenster (`Picture-in-Picture`) und manuell mit Super+O
herausgelöste Fenster (`pop`) werden nicht angefasst.

## Konfiguration

Eigene Werte in `~/.config/omarchy/auto-pip.lua` (nur die Keys, die du ändern willst):

```lua
return {
  enabled = true,
  width = 480,
  height = 270,
  margin = 40,
  anchor = "bottom-right", -- bottom-left, top-right, top-left
  remember_position = true,
  only_when_playing = true, -- false = immer PiP, sobald die App offen ist
  matches = {
    { class = "youtube%.com__" },
    { class = "^mpv$" },
    { class = "^vlc$" },
  },
}
```

`class` und `title` sind Lua-Patterns. Ein Fenster matcht, wenn **eine** Regel
vollständig passt.

Nach einer Config-Änderung: Hyprland lädt beim Speichern von
`~/.config/hypr/*.lua` neu. Für `~/.config/omarchy/auto-pip.lua` reicht
`hyprctl reload`.

## Sichern

Das Plugin ist ein Git-Repo. Lokal reicht:

```bash
cd ~/.config/omarchy/plugins/webtom.auto-pip
git status
git add -A && git commit -m "…"
```

Für ein Backup außer Haus (GitHub), nach `gh auth login`:

```bash
cd ~/.config/omarchy/plugins/webtom.auto-pip
gh repo create webtom.auto-pip --private --source . --remote origin --push
```

Danach ist es auch per `omarchy plugin add <git-url> --enable` auf einem anderen Rechner installierbar.

Zusätzlich außerhalb des Repos (nicht vergessen):

- `~/.config/omarchy/auto-pip.lua` — deine Einstellungen
- die Auto-PiP-Zeilen in `~/.config/hypr/hyprland.lua`

## Deaktivieren

In `~/.config/omarchy/auto-pip.lua`:

```lua
return { enabled = false }
```

Danach `hyprctl reload`. Oder das Plugin mit `omarchy plugin disable webtom.auto-pip`
ausschalten und die Zeile in `~/.config/hypr/hyprland.lua` auskommentieren.
