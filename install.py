#!/usr/bin/env python3
"""Apply the Shibumi music visibility and TIDAL click fixes."""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


HOME = Path.home()
CONFIG = Path(os.environ.get("XDG_CONFIG_HOME", HOME / ".config")) / "omarchy"
TIDAL = CONFIG / "plugins/quickshell.tidal/qml/BarWidget.qml"
RESPONSIVE = CONFIG / "plugins/hancore.shibumi.bar/core/ResponsiveLayout.js"
TIDAL_MANIFEST = CONFIG / "plugins/quickshell.tidal/manifest.json"
YTM_MANIFEST = CONFIG / "plugins/damir.ytmusic/manifest.json"
SHELL_CONFIG = CONFIG / "shell.json"

OLD_TIDAL_HANDLER = '''    onClicked: function(mouse) {
      if (!root.svc) return
      if (mouse.button === Qt.LeftButton) root.toggle()
      else if (mouse.button === Qt.RightButton) root.svc.openView("nowPlaying")
      else if (mouse.button === Qt.MiddleButton) root.svc.playPause()
    }
'''

NEW_TIDAL_HANDLER = '''    onClicked: function(mouse) {
      if (mouse.button === Qt.LeftButton) {
        if (root.svc) root.toggle()
        else if (root.bar && root.bar.shell
            && typeof root.bar.shell.summon === "function")
          root.bar.shell.summon("quickshell.tidal", JSON.stringify({view: "search"}))
      } else if (mouse.button === Qt.RightButton) {
        if (root.svc) root.svc.openView("nowPlaying")
        else if (root.bar && root.bar.shell
            && typeof root.bar.shell.summon === "function")
          root.bar.shell.summon("quickshell.tidal", JSON.stringify({view: "nowPlaying"}))
      } else if (mouse.button === Qt.MiddleButton && root.svc) {
        root.svc.playPause()
      }
    }
'''

OLD_VISIBILITY = '  return ["G1", "G2", "G6", "G8", "G11", "G14"].indexOf(id) >= 0'
NEW_VISIBILITY = '''  return ["G1", "G2", "G6", "G8", "G11", "G14",
    "G:quickshell.tidal", "G:damir.ytmusic"].indexOf(id) >= 0'''


def backup(path: Path) -> Path:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    target = path.with_name(path.name + ".bak." + stamp)
    shutil.copy2(path, target)
    return target


def replace_once(path: Path, old: str, new: str, label: str) -> bool:
    source = path.read_text()
    if new in source:
        print(f"Already patched: {label}")
        return False
    if source.count(old) != 1:
        raise RuntimeError(f"Unsupported {label} version at {path}; no changes made")
    backup(path)
    path.write_text(source.replace(old, new))
    print(f"Patched {label}: {path}")
    return True


def locate_state(config: dict) -> dict:
    for item in config.get("plugins", []):
        if isinstance(item, dict) and item.get("id") == "hancore.shibumi.state":
            state = item.get("shibumi")
            if isinstance(state, dict):
                return state
    raise RuntimeError("Shibumi state config not found in shell.json")


def ensure_entry(layout: dict, plugin_id: str) -> dict:
    for section in ("left", "centerBegin", "center", "centerEnd", "right", "tray"):
        rows = layout.setdefault(section, [])
        for entry in rows:
            if entry == plugin_id:
                entry = {"id": plugin_id}
                rows[rows.index(plugin_id)] = entry
            if isinstance(entry, dict) and entry.get("id") == plugin_id:
                entry["shibumiModule"] = True
                return entry
    layout.setdefault("right", []).append({"id": plugin_id, "shibumiModule": True})
    return layout["right"][-1]


def update_shell_config() -> None:
    config = json.loads(SHELL_CONFIG.read_text())
    state = locate_state(config)
    order = state.get("order")
    if not isinstance(order, dict) or not isinstance(order.get("right"), list):
        raise RuntimeError("Unsupported Shibumi right-side layout in shell.json")

    ids = ("quickshell.tidal", "damir.ytmusic")
    right = order["right"]
    missing = ["G:" + plugin_id for plugin_id in ids if "G:" + plugin_id not in right]
    if len(right) + len(missing) > 9:
        raise RuntimeError("Shibumi right side has no free extension slots; move a widget first")
    right.extend(missing)

    roles = state.setdefault("v1SlotRoles", {})
    roles_right = roles.setdefault("right", [])
    roles["right"] = [roles_right[i] if i < len(roles_right) else ("base" if i < 7 else "extra")
                       for i in range(len(right))]
    splits = state.setdefault("splits", {})
    split_right = splits.setdefault("right", [])
    splits["right"] = [split_right[i] if i < len(split_right) else False
                        for i in range(max(0, len(right) - 1))]

    layout = config.setdefault("bar", {}).setdefault("layout", {})
    for plugin_id in ids:
        ensure_entry(layout, plugin_id)
    tidal_entry = ensure_entry(layout, "quickshell.tidal")
    tidal_entry["showLabel"] = False

    backup(SHELL_CONFIG)
    SHELL_CONFIG.write_text(json.dumps(config, indent=2) + "\n")
    print(f"Updated Shibumi widget placement: {SHELL_CONFIG}")


def main() -> int:
    required = (TIDAL_MANIFEST, YTM_MANIFEST, TIDAL, RESPONSIVE, SHELL_CONFIG)
    missing = [path for path in required if not path.is_file()]
    if missing:
        print("Install Shibumi, TIDAL, and YouTube Music before applying these fixes:", file=sys.stderr)
        for path in missing:
            print(f"  {path}", file=sys.stderr)
        return 1

    try:
        replace_once(TIDAL, OLD_TIDAL_HANDLER, NEW_TIDAL_HANDLER, "TIDAL click fallback")
        replace_once(RESPONSIVE, OLD_VISIBILITY, NEW_VISIBILITY, "Shibumi narrow-stage visibility")
        update_shell_config()
    except (OSError, ValueError, RuntimeError) as error:
        print(f"Install stopped: {error}", file=sys.stderr)
        return 1

    print("Done. Restart with: omarchy restart shell")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
