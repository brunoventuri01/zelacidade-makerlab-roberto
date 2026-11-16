import json
from pathlib import Path

base = Path(__file__).resolve().parent
part = next(
    p
    for p in json.loads((base / "pecas.json").read_text(encoding="utf-8"))
    if p["id"] == "C_FRENTE_MAKER"
)


def points(loop):
    return " ".join(f"{x},{146 - y}" for x, y in loop)


items = []
for index, loop in enumerate(part["loops"]):
    fill = "#d7b98a" if index == 0 else "#eef3f1"
    items.append(
        f'<polygon points="{points(loop)}" fill="{fill}" '
        'stroke="#173f49" stroke-width="1.5"/>'
    )

for x, y, radius in part["circles"]:
    items.append(
        f'<circle cx="{x}" cy="{146 - y}" r="{radius}" fill="#eef3f1" '
        'stroke="#173f49" stroke-width="1.5"/>'
    )

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="940" viewBox="-14 -20 168 180">
<rect x="-14" y="-20" width="168" height="180" fill="#eef3f1"/>
<text x="70" y="-8" text-anchor="middle" font-family="Segoe UI,Arial" font-size="5" font-weight="700" fill="#173f49">TAMPA FRONTAL MAKER — ROBERTO</text>
{''.join(items)}
<!-- Contornos tracejados representam os componentes atrás do MDF, não são linhas de corte. -->
<rect x="30" y="23.75" width="80" height="36.5" fill="none" stroke="#1976a3" stroke-width="1" stroke-dasharray="3 2"/>
<rect x="47.5" y="78" width="45" height="20" fill="none" stroke="#378b61" stroke-width="1" stroke-dasharray="3 2"/>
<text x="70" y="19" text-anchor="middle" font-family="Segoe UI,Arial" font-size="3.5" font-weight="700" fill="#1976a3">LCD 16×2</text>
<text x="70" y="104" text-anchor="middle" font-family="Segoe UI,Arial" font-size="3.5" font-weight="700" fill="#378b61">HC-SR04</text>
<path d="M 91 119 L 74 119" stroke="#b23b32" stroke-width="1"/>
<path d="M 74 119 l4 -2 l0 4 z" fill="#b23b32"/>
<text x="93" y="121" font-family="Segoe UI,Arial" font-size="3.5" font-weight="700" fill="#b23b32">LED 5 mm</text>
<text x="70" y="155" text-anchor="middle" font-family="Segoe UI,Arial" font-size="3.3" fill="#526b72">140 × 146 mm · MDF 3 mm · orientação frontal</text>
</svg>'''

(base.parent / "PREVIA_TAMPA_FRONTAL_MAKER.svg").write_text(svg, encoding="utf-8")
