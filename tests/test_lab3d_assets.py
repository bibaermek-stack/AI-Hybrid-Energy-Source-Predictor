"""The 3D inverter lab's static files (static/lab3d/) are complete and up to date."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from src.education.inverter_lab import (
    CONTROLS,
    SCENARIOS,
    grade_wiring,
    initial_state,
    status,
    viewer_config,
)

LAB3D = Path(__file__).resolve().parents[1] / "static" / "lab3d"


class TestLab3dAssets(unittest.TestCase):
    def setUp(self):
        self.assembly = json.loads((LAB3D / "assembly.json").read_text(encoding="utf-8"))

    def test_lab_state_is_generated_from_inverter_lab(self):
        on_disk = json.loads((LAB3D / "lab_state.json").read_text(encoding="utf-8"))
        self.assertEqual(
            on_disk,
            json.loads(json.dumps(viewer_config())),
            "static/lab3d/lab_state.json is stale: run python scripts/build_lab3d_assets.py",
        )

    def test_every_mesh_and_texture_exists(self):
        for m in self.assembly["meshes"]:
            self.assertTrue((LAB3D / "models" / m["file"]).is_file(), m["file"])
            if m.get("texture"):
                self.assertTrue((LAB3D / "models" / m["texture"]).is_file(), m["texture"])

    def test_parts_are_named_in_both_languages(self):
        parts = self.assembly["parts"]
        for m in self.assembly["meshes"]:
            self.assertIn(m["part"], parts)
        for c in CONTROLS.values():
            self.assertIn(c["part"], parts)
        for pid, p in parts.items():
            for field in ("name", "info"):
                self.assertTrue(p[field]["en"] and p[field]["kk"], f"{pid}.{field}")

    def test_viewer_uses_only_bundled_scripts(self):
        # The old viewer imported three.js from unpkg.com: no 3D where that host is blocked.
        for name in ("index.html", "lab3d.js"):
            text = (LAB3D / name).read_text(encoding="utf-8")
            self.assertIsNone(
                re.search(r"https?://(?!127\.0\.0\.1)", text), f"{name} loads from the internet"
            )
        self.assertTrue((LAB3D / "vendor" / "three-lab.min.js").is_file())

    def test_viewer_animates_the_roles_the_assembly_declares(self):
        js = (LAB3D / "lab3d.js").read_text(encoding="utf-8")
        for m in self.assembly["meshes"]:
            if m.get("role"):
                self.assertTrue(
                    m["role"] in js, f"{m['role']} is declared but the viewer never uses it"
                )


class TestInverterBoard(unittest.TestCase):
    def test_every_fault_scenario_starts_broken_and_can_be_fixed(self):
        for sid, sc in SCENARIOS.items():
            board = initial_state(sid)
            self.assertEqual(grade_wiring(board)["ok"], not sc["faults"], sid)
            fixed = {**board, **{k: CONTROLS[k]["states"][0]["id"] for k in CONTROLS}}
            self.assertTrue(grade_wiring(fixed)["ok"])

    def test_display_reports_the_first_fault_an_inverter_checks(self):
        healthy = initial_state("healthy")
        self.assertEqual(status(healthy)["code"], "OK")
        self.assertTrue(status(healthy)["meter_running"])
        self.assertEqual(status({**healthy, "dc_isolator": "off"})["code"], "NO_PV")
        self.assertEqual(
            status({**healthy, "dc_polarity": "reversed", "ac_isolator": "off"})["code"],
            "DC_POLARITY",
        )
        self.assertEqual(status({**healthy, "pe": "open"})["code"], "EARTH_FAULT")
        self.assertEqual(status({**healthy, "ac_isolator": "off"})["code"], "GRID_LOST")
        self.assertEqual(status({**healthy, "ac_ln": "swapped"})["code"], "GRID_LN")
        loose = status({**healthy, "logger": "loose"})
        self.assertTrue(loose["meter_running"])
        self.assertFalse(loose["cloud_online"])
