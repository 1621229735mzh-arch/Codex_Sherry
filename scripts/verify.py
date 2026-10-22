"""Verify the published asset's checksum, dimensions and occupied frame layout."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
COUNTS = [6, 8, 8, 4, 5, 8, 6, 6, 6, 8, 8]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", type=Path, default=ROOT / "assets/sherry.png")
    parser.add_argument("--manifest", type=Path, default=ROOT / "validation/manifest.json")
    args = parser.parse_args()
    expected = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = []
    digest = hashlib.sha256(args.image.read_bytes()).hexdigest()
    if digest != expected["sha256"]:
        errors.append("File checksum differs from the published manifest")
    with Image.open(args.image) as opened:
        if opened.size != (1536, 2288):
            errors.append(f"Expected 1536x2288, got {opened.size}")
        if "A" not in opened.getbands():
            errors.append("An alpha channel is required")
        image = opened.convert("RGBA")
    if image.size == (1536, 2288):
        for row, count in enumerate(COUNTS):
            for col in range(8):
                alpha = image.crop((col * 192, row * 208, (col + 1) * 192, (row + 1) * 208)).getchannel("A")
                if (alpha.getbbox() is not None) != (col < count):
                    errors.append(f"Unexpected occupancy at row {row}, column {col}")
    print(json.dumps({"ok": not errors, "sha256": digest, "frames": sum(COUNTS), "errors": errors}, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
