import argparse
import base64
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("response", type=Path)
    parser.add_argument("image", type=Path)
    args = parser.parse_args()

    response = json.loads(args.response.read_text(encoding="utf-8"))
    if response.get("status") != "COMPLETED":
        raise SystemExit(response.get("error") or "The job has not completed.")

    output = response.get("output") or {}
    if "error" in output:
        raise SystemExit(output["error"])

    image = base64.b64decode(output["image_base64"], validate=True)
    if not image.startswith(b"\x89PNG\r\n\x1a\n"):
        raise SystemExit("The response does not contain a PNG image.")

    args.image.write_bytes(image)
    print(f"Saved {args.image}")


if __name__ == "__main__":
    main()
