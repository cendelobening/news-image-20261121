#!/usr/bin/env python3
"""Entrypoint for the news-image-20261121 make.fun entry (v2 finals hardening).

Reads entry.png from this directory, validates that it is a well-formed
1024x1024 8-bit RGB PNG under 1 MiB, then copies it byte-for-byte to
$MAKEFUN_OUTPUT_DIR/entry.png (default /output) with mode 0644.
No network access, no randomness, deterministic.
"""

import os
import shutil
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "entry.png")
DEFAULT_OUTPUT_DIR = "/output"
MAX_BYTES = 1024 * 1024
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def read_chunks(path):
    """Yield (tag, data) for every chunk of a PNG file, checking CRCs.

    The reader walks the file once and verifies each chunk's CRC-32
    against the value stored after its data, so a flipped byte anywhere
    is caught before the image is handed to the grader.
    """
    with open(path, "rb") as handle:
        blob = handle.read()
    if blob[:8] != PNG_MAGIC:
        raise ValueError("not a PNG file: bad signature")
    pos = 8
    chunks = []
    while pos < len(blob):
        if pos + 8 > len(blob):
            raise ValueError("truncated chunk header")
        size = struct.unpack(">I", blob[pos:pos + 4])[0]
        tag = blob[pos + 4:pos + 8]
        end = pos + 8 + size + 4
        if end > len(blob):
            raise ValueError("truncated chunk: %r" % tag)
        data = blob[pos + 8:pos + 8 + size]
        stored = struct.unpack(">I", blob[pos + 8 + size:end])[0]
        actual = zlib.crc32(tag)
        actual = zlib.crc32(data, actual)
        if actual & 0xFFFFFFFF != stored:
            raise ValueError("bad CRC in chunk %r" % tag)
        chunks.append((tag, data))
        pos = end
    if not chunks or chunks[0][0] != b"IHDR":
        raise ValueError("first chunk is not IHDR")
    if chunks[-1][0] != b"IEND":
        raise ValueError("last chunk is not IEND")
    return blob, chunks


def validate(path):
    """Check the PNG and return its raw size in bytes."""
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        raise ValueError("entry.png is %d bytes, over the 1 MiB limit" % size)
    blob, chunks = read_chunks(path)
    width, height, depth, colour = struct.unpack(">IIBB", chunks[0][1][:10])
    if (width, height) != (1024, 1024):
        raise ValueError("expected 1024x1024, got %dx%d" % (width, height))
    if depth != 8:
        raise ValueError("expected 8-bit depth, got %d" % depth)
    if colour != 2:
        raise ValueError("expected RGB colour type 2, got %d" % colour)
    idat = b"".join(data for tag, data in chunks if tag == b"IDAT")
    raw = zlib.decompress(idat)
    stride = 1024 * 3 + 1
    if len(raw) != stride * 1024:
        raise ValueError("decoded data is %d bytes, expected %d" % (len(raw), stride * 1024))
    for row in range(1024):
        if raw[row * stride] != 0:
            raise ValueError("scanline %d uses filter %d, expected 0" % (row, raw[row * stride]))
    return size


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", DEFAULT_OUTPUT_DIR)
    size = validate(SOURCE)
    os.makedirs(out_dir, exist_ok=True)
    target = os.path.join(out_dir, "entry.png")
    shutil.copyfile(SOURCE, target)
    os.chmod(target, 0o644)
    print("validated entry.png (%d bytes) -> %s" % (size, target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
