"""Render the original shield mark and multi-resolution Windows icon."""
from pathlib import Path
from PIL import Image, ImageDraw

output = Path(__file__).resolve().parents[1] / "assets" / "icons"
canvas = Image.new("RGBA", (1024, 1024))
draw = ImageDraw.Draw(canvas)
shield = [(512, 65), (893, 198), (893, 502), (867, 643), (802, 758),
          (703, 852), (512, 965), (321, 852), (222, 758), (157, 643),
          (131, 502), (131, 198)]
draw.polygon(shield, fill="#53D9F0")
draw.polygon([(512, 113), (850, 231), (850, 498), (826, 626),
              (766, 730), (678, 817), (512, 916), (346, 817),
              (258, 730), (198, 626), (174, 498), (174, 231)], fill="#102B4C")
draw.polygon([(512, 113), (850, 231), (850, 498), (826, 626),
              (766, 730), (678, 817), (512, 916)], fill="#15395C")


def bezier(start, control1, control2, end):
    for step in range(1, 41):
        t = step / 40
        u = 1 - t
        yield tuple(u**3 * a + 3*u*u*t*b + 3*u*t*t*c + t**3*d
                    for a, b, c, d in zip(start, control1, control2, end))


start = (653, 350)
points = [start]
for controls in [
    ((611, 315), (553, 297), (497, 303)),
    ((414, 312), (369, 354), (385, 416)),
    ((403, 473), (505, 483), (563, 501)),
    ((633, 521), (666, 555), (650, 615)),
    ((625, 714), (457, 734), (365, 658)),
]:
    points.extend(bezier(points[-1], *controls))
width = 93
draw.line(points, fill="#E0FBFF", width=width, joint="curve")
for x, y in (points[0], points[-1]):
    radius = width / 2
    draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill="#E0FBFF")

canvas.save(output / "ip-sentinel.png")
canvas.save(output / "ip-sentinel.ico", sizes=[(n, n) for n in (16, 24, 32, 48, 64, 128, 256)])
