"""
Build the assets of the 3D inverter lab (static/lab3d/) from the CAD export.

    python scripts/build_lab3d_assets.py

Source: static/models/solar_inverter_subsystem/ — the «Solar Inverter Subsystem»
CAD assembly exported as 13 OBJ meshes plus basecolor PNGs, with no usable
materials. This script

  * rewrites each mesh compactly (coordinates to 0.01 mm, normals to 1e-3,
    UVs to 1e-4, degenerate triangles dropped): 6 MB → about 2.5 MB;
  * copies the four distinct textures under names that say what they are;
  * writes assembly.json: which mesh belongs to which part, its texture or
    colour, and the part names and descriptions (kk/en) shown by the viewer
    and used by the lab test;
  * writes lab_state.json from src/education/inverter_lab.py: controls,
    scenarios and the status of every board state.

The mesh-to-part mapping was established by rendering each mesh on its own
(the earlier viewer had guessed it: the DC cables were labelled
"generation meter", the inverter "structure"). Texture assignment follows the
label printed on each texture («PV Array DC Isolator», «Single Phase Watt Hour
Meter», the inverter front and the isolator face).

tests/test_lab3d_assets.py checks the outputs are up to date.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.education.inverter_lab import viewer_config  # noqa: E402

SRC = ROOT / "static" / "models" / "solar_inverter_subsystem"
OUT = ROOT / "static" / "lab3d"


def _L(en: str, kk: str) -> dict[str, str]:
    return {"en": en, "kk": kk}


TEXTURES = {
    "dc_isolator_label.png": "Material__733basecolortexture_3.png.png",
    "isolator_face.png": "PV_AC_isolatorbasecolortexture_0.png.png",
    "inverter.png": "adskMatPV_inverterbasecolortexture_2.png.png",
    "meter.png": "adskMatPV_generation_meterbasecolortexture_4.png.png",
}

# mesh file -> part, look, and the role the viewer animates (if any)
MESHES = [
    {"file": "model_4.obj", "part": "dc_isolator", "texture": "dc_isolator_label.png"},
    {"file": "model_7.obj", "part": "dc_isolator", "texture": "isolator_face.png"},
    {"file": "model_6.obj", "part": "dc_isolator", "color": "#4b5563", "role": "dc_handle"},
    {"file": "model_5.obj", "part": "dc_isolator", "color": "#6b7280"},
    {"file": "model_1.obj", "part": "dc_cables", "color": "#2f343c"},
    {"file": "model_3.obj", "part": "dc_inputs", "color": "#2563eb", "role": "dc_neg_tag"},
    {"file": "model_2.obj", "part": "dc_inputs", "color": "#dc2626", "role": "dc_pos_tag"},
    {"file": "model_11.obj", "part": "inverter", "texture": "inverter.png"},
    {"file": "model_12.obj", "part": "ac_cable", "color": "#8a919c"},
    {"file": "model_0.obj", "part": "ac_isolator", "texture": "isolator_face.png"},
    {"file": "model_8.obj", "part": "generation_meter", "texture": "meter.png"},
    {
        "file": "model_9.obj",
        "part": "generation_meter",
        "color": "#9ec7a8",
        "role": "meter_display",
    },
    {"file": "model_10.obj", "part": "generation_meter", "color": "#f59e0b", "role": "meter_led"},
]

PARTS = {
    "dc_isolator": {
        "name": _L("PV array DC isolator", "PV массивінің DC ажыратқышы"),
        "info": _L(
            "A load-break switch between the PV string and the inverter. Turned to 0 (OFF) it "
            "disconnects the array so the inverter can be worked on. Its label warns that it "
            "contains live parts during daylight: the cables from the panels are live whenever "
            "the sun shines.",
            "PV тізбегі мен инвертор арасындағы жүктемемен ажырататын ажыратқыш. 0 (OFF) "
            "күйіне бұрағанда массив ажыратылады, инверторда жұмыс істеуге болады. Жапсырмасы "
            "күндіз ішінде кернеу бар екенін ескертеді: күн түсіп тұрса, панельдерден келетін "
            "кабельдерде кернеу болады.",
        ),
    },
    "dc_cables": {
        "name": _L("DC cables PV+ / PV−", "DC кабельдер PV+ / PV−"),
        "info": _L(
            "Two single-core cables from the isolator to the inverter, ending in MC4 plugs. "
            "Never pull the plugs under load: the inverter's own label says to switch the AC "
            "supply off first.",
            "Ажыратқыштан инверторға баратын екі бір талсымды кабель, ұштарында MC4 ашалары. "
            "Ашаларды жүктеме астында суыруға болмайды: инвертордың жапсырмасы алдымен AC "
            "қоректі ажыратуды талап етеді.",
        ),
    },
    "dc_inputs": {
        "name": _L("Inverter DC inputs (DC− / DC+)", "Инвертордың DC кірістері (DC− / DC+)"),
        "info": _L(
            "Where the PV cables plug into the inverter: DC− (blue tag) and DC+ (red tag). "
            "PV+ must land on DC+. With the cables reversed the inverter's reverse-polarity "
            "protection keeps it off.",
            "PV кабельдері инверторға қосылатын орын: DC− (көк белгі) және DC+ (қызыл белгі). "
            "PV+ DC+-ке қосылуы тиіс. Кабельдер кері қосылса, инвертордың кері полярлықтан "
            "қорғанысы оны іске қоспайды.",
        ),
    },
    "inverter": {
        "name": _L("Grid-tied inverter", "Желілік инвертор"),
        "info": _L(
            "Converts the direct current from the panels into 230 V alternating current in step "
            "with the grid. The display shows the output power (Pac) or the fault that stops it. "
            "Its label warns of a dual supply: isolate both AC and DC before work.",
            "Панельдердің тұрақты тогын желімен үйлескен 230 В айнымалы токқа түрлендіреді. "
            "Экраны шығыс қуатын (Pac) немесе оны тоқтатқан ақауды көрсетеді. Жапсырмасы қос "
            "қорек туралы ескертеді: жұмыс алдында AC мен DC екеуін де ажырату керек.",
        ),
    },
    "ac_cable": {
        "name": _L("AC cable and mounting rail", "AC кабель және бекіту рельсі"),
        "info": _L(
            "Carries the inverter's output (line L, neutral N and protective earth PE) to the AC "
            "isolator and the meter on the rail.",
            "Инвертордың шығысын (фаза L, нөл N және қорғаныстық жер PE) рельстегі AC "
            "ажыратқыш пен есептегішке жеткізеді.",
        ),
    },
    "ac_isolator": {
        "name": _L("AC isolator", "AC ажыратқыш"),
        "info": _L(
            "Disconnects the inverter from the grid. Inside are the L, N and PE terminals of the "
            "AC cable. Switched OFF, the inverter sees no grid and will not export.",
            "Инверторды желіден ажыратады. Ішінде AC кабелінің L, N және PE клеммалары бар. "
            "Ажыратулы тұрса, инвертор желіні көрмейді және қуат бермейді.",
        ),
    },
    "generation_meter": {
        "name": _L("Generation meter (kWh)", "Генерация есептегіші (кВт·сағ)"),
        "info": _L(
            "A single-phase watt-hour meter counting the energy the inverter delivers. The LED "
            "flashes 1000 times per kWh, so it blinks only while the plant exports.",
            "Инвертор берген энергияны санайтын бір фазалы ватт-сағат есептегіші. Жарық диоды "
            "әр кВт·сағ сайын 1000 рет жыпылықтайды, яғни станция қуат бергенде ғана жанады.",
        ),
    },
    "logger": {
        "name": _L("Wi-Fi data logger", "Wi-Fi деректер логгері"),
        "info": _L(
            "Plugs into the inverter's COM port and sends its data to Solarman / EcoPredict. "
            "Not part of the CAD model: added for this lab. Pulled out, the plant still produces "
            "but the app goes offline.",
            "Инвертордың COM портына қосылып, деректерді Solarman / EcoPredict-ке жібереді. CAD "
            "моделінде жоқ: осы зертханаға қосылған. Суырылса, станция өндіре береді, бірақ "
            "қосымша офлайн болады.",
        ),
    },
}


def _fmt(values: list[str], digits: int) -> str:
    out = []
    for v in values:
        s = f"{float(v):.{digits}f}".rstrip("0").rstrip(".")
        out.append("0" if s in ("-0", "") else s)
    return " ".join(out)


def compact_obj(src: Path, dst: Path) -> dict[str, int]:
    lines_out: list[str] = []
    n_v = n_f = dropped = 0
    for raw in src.read_text(encoding="utf-8-sig").splitlines():
        parts = raw.split()
        if not parts:
            continue
        tag = parts[0]
        if tag == "v":
            lines_out.append("v " + _fmt(parts[1:4], 5))
            n_v += 1
        elif tag == "vn":
            lines_out.append("vn " + _fmt(parts[1:4], 3))
        elif tag == "vt":
            lines_out.append("vt " + _fmt(parts[1:3], 4))
        elif tag == "f":
            corners = parts[1:]
            if len({c.split("/")[0] for c in corners}) < 3:
                dropped += 1  # degenerate triangle from the strip export
                continue
            lines_out.append("f " + " ".join(corners))
            n_f += 1
        elif tag == "o":
            lines_out.append(raw.strip())
        # mtllib / usemtl dropped: the viewer assigns materials from assembly.json
    dst.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
    return {"vertices": n_v, "faces": n_f, "dropped": dropped}


def build() -> None:
    models = OUT / "models"
    models.mkdir(parents=True, exist_ok=True)
    for m in MESHES:
        stats = compact_obj(SRC / m["file"], models / m["file"])
        print(f"{m['file']:<13} {stats}")
    for name, src_name in TEXTURES.items():
        shutil.copyfile(SRC / src_name, models / name)

    assembly = {
        "source": "Solar Inverter Subsystem — CAD assembly (OBJ export); materials re-assigned for the lab",
        "units": "m",
        "meshes": MESHES,
        "parts": PARTS,
        "added_parts": ["logger"],
    }
    (OUT / "assembly.json").write_text(
        json.dumps(assembly, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (OUT / "lab_state.json").write_text(
        json.dumps(viewer_config(), ensure_ascii=False, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print("wrote", OUT / "assembly.json", "and", OUT / "lab_state.json")


if __name__ == "__main__":
    build()
