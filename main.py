"""Carry the bundled picture to the runner's output folder.

The picture sits next to this file under the name ``entry.png`` even
though its actual encoding may be JPEG.  Before copying, we peek at
the header ourselves, confirm the file is not oversized, and make
sure both sides fit inside the allowed square.
"""

import os
import struct
import sys
from pathlib import Path

BYTE_LIMIT = 1_048_576
SIDE_LIMIT = 1024

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8"


def abort(reason: str) -> None:
    print(f"entry check failed: {reason}", file=sys.stderr)
    raise SystemExit(1)


def png_dimensions(blob: bytes) -> tuple[int, int]:
    # Layout: 8 byte signature, then the IHDR chunk header, then W/H.
    if len(blob) < 24:
        abort("PNG data is too short to contain an IHDR header")
    if blob[12:16] != b"IHDR":
        abort("PNG data is missing its IHDR chunk")
    wide, tall = struct.unpack(">II", blob[16:24])
    return wide, tall


def jpeg_dimensions(blob: bytes) -> tuple[int, int]:
    # Walk marker segments until a start-of-frame segment turns up.
    cursor = 2
    total = len(blob)
    while cursor + 1 < total:
        if blob[cursor] != 0xFF:
            abort("JPEG segment does not begin with a marker prefix")
        marker = blob[cursor + 1]
        # Padding bytes show up as repeated 0xFF values.
        if marker == 0xFF:
            cursor += 1
            continue
        # Standalone markers carry no length field at all.
        if marker in (0x01, 0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            cursor += 2
            continue
        if cursor + 3 >= total:
            abort("JPEG segment header is truncated")
        seg_len = struct.unpack(">H", blob[cursor + 2 : cursor + 4])[0]
        if seg_len < 2:
            abort("JPEG segment declares an impossible length")
        if marker in (0xC0, 0xC2):
            if cursor + 8 >= total:
                abort("JPEG frame header is truncated")
            tall = struct.unpack(">H", blob[cursor + 5 : cursor + 7])[0]
            wide = struct.unpack(">H", blob[cursor + 7 : cursor + 9])[0]
            return wide, tall
        if marker == 0xDA:
            break
        cursor += 2 + seg_len
    abort("JPEG data has no readable frame header")
    return 0, 0  # unreachable; keeps type checkers quiet


def measure(blob: bytes) -> tuple[int, int]:
    if blob.startswith(PNG_MAGIC):
        return png_dimensions(blob)
    if blob.startswith(JPEG_MAGIC):
        return jpeg_dimensions(blob)
    abort("bundled file is neither PNG nor JPEG")
    return 0, 0  # unreachable


def main() -> None:
    here = Path(__file__).resolve().parent
    source = here / "entry.png"
    if not source.is_file():
        abort(f"bundled image not found beside script: {source}")

    payload = source.read_bytes()
    if len(payload) > BYTE_LIMIT:
        abort(f"image weighs {len(payload)} bytes, over the {BYTE_LIMIT} limit")
    if not payload:
        abort("bundled image is empty")

    wide, tall = measure(payload)
    for label, value in (("width", wide), ("height", tall)):
        if value < 1 or value > SIDE_LIMIT:
            abort(f"image {label} is {value}, outside 1..{SIDE_LIMIT}")

    target_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        abort(f"cannot create output directory {target_dir}: {exc}")

    destination = target_dir / "entry.png"
    destination.write_bytes(payload)
    print(f"Delivered entry.png: {len(payload)} bytes, {wide}x{tall} -> {destination}")


if __name__ == "__main__":
    main()

# --- Usage and behaviour notes -------------------------------------------
# Run with the standard library only; no third-party packages are needed.
# Output location is controlled by the MAKEFUN_OUTPUT_DIR environment
# variable. When it is unset or empty the entrypoint defaults to /output.
# Validation is performed before any copy happens: the bundled picture
# must be at most 1 MiB in size and at most 1024 px on each side.
# Format is checked from magic bytes rather than the file name, and
# PNG/JPEG dimensions are parsed from the headers to enforce the cap.
# Determinism guarantee: once validation passes, the source bytes are
# copied to the destination unchanged, with no re-encoding, resizing,
# or metadata rewriting, so repeated runs produce identical output.
