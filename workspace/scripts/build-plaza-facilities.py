"""Build the retro vending machine and fountain plaza benches as separate GLBs.

Run with Blender: blender --background --factory-startup --python this_file.py -- output_directory
The public-facing side is local -Y in Blender and +Z in the exported GLB.
"""

from pathlib import Path
import runpy
import sys


toolkit = runpy.run_path(str(Path(__file__).resolve().with_name("build-civic-structures.py")))
box = toolkit["box"]
round_piece = toolkit["round_piece"]
export_model = toolkit["export_model"]

toolkit["MATERIALS"].update({
    "Powder blue enamel": ("A2CED8", 0.66),
    "Blush enamel": ("E5AEA9", 0.70),
    "Display interior": ("62637A", 0.81),
    "Display trim": ("D8E3DA", 0.67),
    "Soft mint": ("A5D9B7", 0.84),
    "Berry drink": ("DA8686", 0.68),
    "Lemon drink": ("E7C970", 0.69),
    "Lilac drink": ("B8A5CC", 0.72),
    "Limestone": ("E7D6BE", 0.91),
    "Dark soil": ("80634E", 0.88),
    "Rosé petals": ("DB9694", 0.76),
})


def make_vending_machine():
    box("Limestone service pad", (0, 0, 0.045), (2.30, 1.78, 0.09), "Limestone", 0.04)
    box("Rounded rear cabinet", (0, 0.16, 1.24), (1.62, 0.91, 2.30), "Blush enamel", 0.115)
    box("Powder-blue front casing", (0, -0.30, 1.28), (1.66, 0.35, 2.25), "Powder blue enamel", 0.09)
    for x in (-0.57, 0.57):
        box("Raised machine foot", (x, -0.26, 0.16), (0.26, 0.33, 0.17), "Warm slate", 0.025)

    display_x = -0.17
    box("Cream display frame", (display_x, -0.499, 1.64), (1.12, 0.11, 1.21), "Painted cream", 0.048)
    box("Display case recess", (display_x, -0.560, 1.64), (1.02, 0.060, 1.10), "Display interior", 0.035)
    for z in (1.24, 1.62, 2.00):
        box("Illuminated drink shelf", (display_x, -0.626, z), (0.98, 0.235, 0.059), "Display trim", 0.015)

    bottles = ("Lemon drink", "Soft mint", "Berry drink", "Lilac drink", "Sea glass")
    for row in range(2):
        for column in range(5):
            x = -0.557 + column * 0.194
            y = -0.64
            shelf = 1.269 + row * 0.38
            color = bottles[(column + row * 2) % len(bottles)]
            round_piece("Drink bottle", (x, y, shelf + 0.109), 0.058, 0.054, 0.218, color)
            round_piece("Bottle collar", (x, y, shelf + 0.23), 0.046, 0.037, 0.044, color)
            round_piece("Bottle cap", (x, y, shelf + 0.267), 0.042, 0.040, 0.025, "Painted cream")
            box("Bottle label", (x, -0.697, shelf + 0.107), (0.070, 0.018, 0.050), "Painted cream", 0.006)

    box("Coin panel", (0.54, -0.509, 1.57), (0.31, 0.10, 0.73), "Painted cream", 0.03)
    box("Price window", (0.54, -0.569, 1.79), (0.21, 0.043, 0.126), "Sea glass", 0.016)
    box("Coin slot", (0.54, -0.571, 1.59), (0.156, 0.040, 0.035), "Warm slate", 0.007)
    for x, color in ((0.48, "Blush enamel"), (0.60, "Soft mint")):
        box("Selection button", (x, -0.572, 1.40), (0.085, 0.061, 0.073), color, 0.015)

    box("Product return panel", (-0.02, -0.514, 0.74), (1.35, 0.108, 0.50), "Blush enamel", 0.045)
    box("Product door recess", (-0.10, -0.585, 0.72), (0.98, 0.064, 0.235), "Warm slate", 0.031)
    box("Product door grip", (-0.10, -0.629, 0.756), (0.47, 0.057, 0.055), "Display trim", 0.012)


def bench(center_x):
    for x in (center_x - 0.75, center_x + 0.75):
        for y in (-0.51, 0.03):
            box("Bench feet", (x, y, 0.22), (0.14, 0.16, 0.44), "Toasted timber", 0.022)
        box("Armrest support", (x, -0.51, 0.56), (0.09, 0.10, 0.28), "Toasted timber", 0.016)
        box("Bench back support", (x, 0.072, 0.52), (0.11, 0.123, 1.02), "Toasted timber", 0.022)
        box("Rounded armrest", (x, -0.27, 0.704), (0.18, 0.63, 0.081), "Pale timber", 0.024)
    for index in range(4):
        box("Seat slat", (center_x, -0.52 + 0.165 * index, 0.45), (1.92, 0.152, 0.08),
            "Pale timber" if index % 2 == 0 else "Honey timber", 0.019)
    for index in range(2):
        box("Back slat", (center_x, 0.015 + 0.023 * index, 0.77 + 0.185 * index), (1.92, 0.09, 0.163),
            "Honey timber" if index == 0 else "Pale timber", 0.026)


def planter(x, y):
    round_piece("Low terracotta flowerpot", (x, y, 0.22), 0.22, 0.29, 0.44, "Terracotta enamel", 12)
    round_piece("Planter lip", (x, y, 0.449), 0.303, 0.303, 0.065, "Terracotta enamel", 12)
    round_piece("Soil", (x, y, 0.486), 0.262, 0.262, 0.021, "Dark soil", 12)
    for dx, dy, z, color in ((-0.105, -0.06, 0.66, "Rosé petals"), (0.10, -0.04, 0.73, "Painted cream"),
                              (0.04, 0.10, 0.80, "Rosé petals")):
        round_piece("Short leaf stem", (x + dx, y + dy, (z + 0.50) / 2), 0.034, 0.025,
                    z - 0.50, "Leaf green", 7)
        round_piece("Petal mass", (x + dx, y + dy, z), 0.076, 0.092, 0.091, color, 8)


def make_plaza_benches():
    for x in (-1.26, 1.26):
        bench(x)
    for x in (-2.08, 2.08):
        planter(x, 0.66)


if __name__ == "__main__":
    if "--" not in sys.argv:
        raise SystemExit("Pass the GLB output directory after Blender's -- separator.")
    output = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    output.mkdir(parents=True, exist_ok=True)
    export_model("vending.glb", make_vending_machine, output)
    export_model("plaza-benches.glb", make_plaza_benches, output)
