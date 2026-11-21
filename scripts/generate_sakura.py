#!/usr/bin/env python3
"""Generate a daily pixel-art Sakura Journal GIF.

The scene is deterministic for each UTC date: rerunning it on the same day
produces the same artwork, while the composition changes on a new day.
"""
from datetime import datetime, timezone
from pathlib import Path
import random

from PIL import Image, ImageDraw

# Work at a small resolution, then enlarge with nearest-neighbour scaling
# to preserve crisp pixel-art edges.
W, H = 160, 100
SCALE = 3
FRAMES = 8
OUT = Path("sakura/sakura.gif")

BG_TOP = (12, 18, 43)
BG_BOTTOM = (27, 29, 62)
BRANCH = (91, 55, 57)
BRANCH_LIGHT = (143, 82, 83)
PINKS = [
    (255, 177, 207),
    (246, 139, 184),
    (255, 207, 221),
    (222, 112, 166),
]
LEAF = (93, 126, 111)
GOLD = (255, 226, 166)


def rect(draw, xy, fill):
    draw.rectangle(xy, fill=fill)


def make_background(draw, rng, day_number):
    # Pixelated vertical night gradient.
    for y in range(H):
        t = y / max(1, H - 1)
        color = tuple(
            int(BG_TOP[i] * (1 - t) + BG_BOTTOM[i] * t)
            for i in range(3)
        )
        draw.line((0, y, W, y), fill=color)

    # Moon position and phase vary daily.
    moon_x = 123 + (day_number % 5 - 2) * 3
    moon_y = 22 + (day_number % 3) * 2
    rect(draw, (moon_x - 7, moon_y - 7, moon_x + 7, moon_y + 7), (247, 230, 190))
    rect(draw, (moon_x - 5, moon_y - 7, moon_x + 7, moon_y + 5), BG_TOP)

    # Tiny pixel stars, fixed for the date.
    for _ in range(34):
        x = rng.randrange(4, W - 4)
        y = rng.randrange(4, 72)
        if abs(x - moon_x) < 12 and abs(y - moon_y) < 12:
            continue
        size = rng.choice([0, 0, 1])
        color = rng.choice([(255, 239, 205), (164, 185, 222), (211, 196, 225)])
        rect(draw, (x, y, x + size, y + size), color)

    # Distant rooftops / quiet horizon silhouettes.
    rect(draw, (0, 83, W, 99), (17, 24, 48))
    for x, width, height in [(8, 27, 9), (43, 23, 13), (83, 30, 8), (126, 25, 12)]:
        rect(draw, (x, 83 - height, x + width, 83), (21, 29, 54))
        rect(draw, (x + width // 2 - 2, 83 - height - 4, x + width // 2 + 2, 83 - height), (21, 29, 54))


def draw_branch(draw, day_number):
    # Main branch: stepped pixel-art diagonal rising toward the right.
    points = [
        (8, 86), (22, 78), (35, 69), (49, 61), (63, 52),
        (78, 43), (94, 35), (111, 27), (130, 19), (151, 12)
    ]
    for a, b in zip(points, points[1:]):
        draw.line((a, b), fill=BRANCH, width=5)
        draw.line((a[0], a[1] - 1, b[0], b[1] - 1), fill=BRANCH_LIGHT, width=1)

    # Small offshoots.
    offshoots = [
        ((36, 69), (30, 53), (23, 44)),
        ((60, 54), (58, 37), (52, 29)),
        ((83, 41), (91, 28), (102, 22)),
        ((108, 29), (112, 43), (121, 49)),
        ((128, 20), (139, 29), (148, 34)),
    ]
    for p1, p2, p3 in offshoots:
        draw.line((p1, p2, p3), fill=BRANCH, width=3)
        draw.point(p2, fill=BRANCH_LIGHT)

    # Blossom clusters. Their placement shifts subtly each day.
    shift = day_number % 4 - 1
    clusters = [
        (22 + shift, 42), (48, 27 + shift), (62, 42),
        (99 + shift, 19), (119, 47 - shift), (145, 32),
        (79, 57),
    ]
    for cx, cy in clusters:
        # Five chunky petals around a darker center.
        petal_color = PINKS[(day_number + cx + cy) % len(PINKS)]
        for dx, dy in [(0, -5), (5, -1), (3, 5), (-4, 4), (-5, -1)]:
            rect(draw, (cx + dx - 2, cy + dy - 2, cx + dx + 2, cy + dy + 2), petal_color)
        rect(draw, (cx - 1, cy - 1, cx + 1, cy + 1), (171, 91, 126))
        # A few pale pixel highlights.
        draw.point((cx - 1, cy - 5), fill=(255, 225, 235))
        draw.point((cx + 4, cy - 2), fill=(255, 225, 235))

    # A few tiny leaves for contrast.
    for x, y in [(33, 61), (72, 48), (115, 33), (137, 24)]:
        rect(draw, (x, y, x + 2, y + 4), LEAF)


def make_frame(seed, frame_index, day_number):
    rng = random.Random(seed)
    image = Image.new("RGB", (W, H), BG_TOP)
    draw = ImageDraw.Draw(image)
    make_background(draw, rng, day_number)
    draw_branch(draw, day_number)

    # Petals drift downward; their paths are stable for the day's GIF.
    petal_rng = random.Random(seed + 900)
    for i in range(9):
        start_x = petal_rng.randrange(12, 155)
        start_y = petal_rng.randrange(15, 75)
        drift = (frame_index * (1 if i % 2 else -1) + i * 2) % 13
        x = max(2, min(W - 4, start_x + drift - 6))
        y = min(H - 8, start_y + frame_index * (1 + (i % 3)))
        color = PINKS[(i + day_number) % len(PINKS)]
        rect(draw, (x, y, x + 2, y + 1), color)
        if i % 3 == 0:
            draw.point((x + 1, y + 2), fill=(255, 218, 230))

    # Subtle lantern glow near the lower edge.
    rect(draw, (18, 76, 23, 81), (87, 65, 76))
    rect(draw, (19, 77, 22, 80), GOLD)
    rect(draw, (20, 82, 21, 86), (112, 77, 72))

    return image.resize((W * SCALE, H * SCALE), Image.Resampling.NEAREST)


def main():
    today = datetime.now(timezone.utc).date()
    date_text = today.isoformat()
    seed = int(today.strftime("%Y%m%d"))
    day_number = today.timetuple().tm_yday

    frames = [make_frame(seed, i, day_number) for i in range(FRAMES)]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(
        OUT,
        save_all=True,
        append_images=frames[1:],
        duration=180,
        loop=0,
        optimize=False,
        disposal=2,
    )
    print(f"Generated {OUT} for {date_text} ({W*SCALE}x{H*SCALE}, {FRAMES} frames)")


if __name__ == "__main__":
    main()
