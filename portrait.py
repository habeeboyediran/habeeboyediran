from pathlib import Path
import json

import numpy as np
from PIL import Image

INPUT = Path("assets/portrait.jpg")
OUTPUT = Path("dots.json")

IMAGE_SIZE = 180
MAX_DOTS = 2200


def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Portrait not found: {INPUT}")

    image = Image.open(INPUT).convert("RGB")

    # Crop the image to a centered square.
    width, height = image.size
    side = min(width, height)

    left = (width - side) // 2
    top = (height - side) // 2

    image = image.crop(
        (left, top, left + side, top + side)
    )

    # Resize for dot sampling.
    image = image.resize(
        (IMAGE_SIZE, IMAGE_SIZE),
        Image.Resampling.LANCZOS
    )

    pixels = np.asarray(image).astype(np.float32)

    # Convert RGB to grayscale.
    grayscale = (
        0.299 * pixels[:, :, 0]
        + 0.587 * pixels[:, :, 1]
        + 0.114 * pixels[:, :, 2]
    )

    # Estimate the background brightness using image edges.
    edge_brightness = np.concatenate([
        grayscale[:10, :].ravel(),
        grayscale[-10:, :].ravel(),
        grayscale[:, :10].ravel(),
        grayscale[:, -10:].ravel(),
    ])

    background = float(np.median(edge_brightness))

    # Darker parts of the portrait receive more dots.
    darkness = np.clip(
        (background - grayscale) / max(background, 1),
        0,
        1
    )

    weights = darkness ** 1.7

    ys, xs = np.where(weights > 0.06)

    if len(xs) == 0:
        raise RuntimeError(
            "Could not detect enough portrait detail."
        )

    probabilities = weights[ys, xs]
    probabilities = probabilities / probabilities.sum()

    dot_count = min(MAX_DOTS, len(xs))

    rng = np.random.default_rng(42)

    selected = rng.choice(
        len(xs),
        size=dot_count,
        replace=False,
        p=probabilities
    )

    dots = []

    for index in selected:
        x = float(xs[index]) / (IMAGE_SIZE - 1)
        y = float(ys[index]) / (IMAGE_SIZE - 1)
        intensity = float(weights[ys[index], xs[index]])

        dots.append({
            "x": round(x, 5),
            "y": round(y, 5),
            "w": round(intensity, 5)
        })

    data = {
        "count": len(dots),
        "points": dots
    }

    OUTPUT.write_text(
        json.dumps(data, indent=2),
        encoding="utf-8"
    )

    print(f"Saved {len(dots)} portrait dots to {OUTPUT}")


if __name__ == "__main__":
    main()
