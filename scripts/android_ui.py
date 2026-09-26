"""
Tiny adb/uiautomator helper for the emulator smoke test
(scripts/android_emulator_smoke.sh).

    python3 scripts/android_ui.py tap <label> [--prefix]   tap the node whose text or
                                                            content-desc matches <label>
    python3 scripts/android_ui.py tab <index>               tap bottom-nav slot 0..4 by
                                                            geometry (fallback)
    python3 scripts/android_ui.py has <label>               exit 0 if <label> is on screen

Flutter exposes its semantics tree to UiAutomator, so NavigationBar
destinations and buttons show up with their labels as content-desc.
"""

import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

BOUNDS = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def adb(*args: str) -> str:
    return subprocess.run(["adb", *args], capture_output=True, text=True, check=False).stdout


def dump() -> ET.Element:
    # The first dump after a screen change can come back before Flutter has
    # published its semantics; take the richer of two.
    best = None
    for _ in range(2):
        adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
        xml = adb("exec-out", "cat", "/sdcard/ui.xml")
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            time.sleep(1)
            continue
        if best is None or len(list(root.iter())) > len(list(best.iter())):
            best = root
        time.sleep(1)
    return best if best is not None else ET.Element("hierarchy")


def labels(node: ET.Element) -> list:
    out = []
    for attr in ("text", "content-desc"):
        value = (node.get(attr) or "").strip()
        if value:
            out.append(value)
            out.append(value.splitlines()[0].strip())  # "Болжам\nTab 2 of 5"
    return out


def find(label: str, prefix: bool):
    for node in dump().iter("node"):
        for value in labels(node):
            if value == label or (prefix and value.startswith(label)):
                match = BOUNDS.match(node.get("bounds") or "")
                if match:
                    x1, y1, x2, y2 = map(int, match.groups())
                    return (x1 + x2) // 2, (y1 + y2) // 2
    return None


def screen():
    w, h = map(int, re.search(r"(\d+)x(\d+)", adb("shell", "wm", "size")).groups())
    density = int(re.search(r"(\d+)", adb("shell", "wm", "density")).group(1))
    return w, h, density / 160.0


def main() -> int:
    cmd, arg = sys.argv[1], sys.argv[2]
    prefix = "--prefix" in sys.argv
    if cmd in ("tap", "has"):
        pos = find(arg, prefix)
        if pos is None:
            print(f"not found: {arg}")
            return 1
        if cmd == "tap":
            adb("shell", "input", "tap", str(pos[0]), str(pos[1]))
            print(f"tapped {arg} at {pos}")
        return 0
    if cmd == "tab":
        # Material NavigationBar is 80 dp tall above a 24–48 dp system bar;
        # 88 dp from the bottom lands inside it either way.
        w, h, dp = screen()
        x = int((int(arg) + 0.5) * w / 5)
        y = int(h - 88 * dp)
        adb("shell", "input", "tap", str(x), str(y))
        print(f"tapped tab {arg} at ({x}, {y})")
        return 0
    print(f"unknown command {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
