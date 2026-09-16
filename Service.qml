import QtQuick
import Quickshell

// Window management runs inside Hyprland Lua (auto-pip.lua), loaded from
// ~/.config/hypr/hyprland.lua. This service exists so the plugin is a valid
// Omarchy service and stays enabled across shell rescans.
Item {
  id: root
  property var shell: null
  property var manifest: null
}
