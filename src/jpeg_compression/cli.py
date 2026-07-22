"""Command-line interface for encoding and decoding images."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from .decoder import decode_image
from .encoder import encode_image


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="jpeg-compression",
        description="Explore JPEG-style compression with a readable Python implementation.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    encode_parser = subparsers.add_parser("encode", help="encode an image to a .jpc bitstream")
    encode_parser.add_argument("input", help="path to any Pillow-supported image")
    encode_parser.add_argument("output", help="path for the encoded .jpc file")

    decode_parser = subparsers.add_parser("decode", help="decode a .jpc bitstream")
    decode_parser.add_argument("input", help="path to a .jpc file")
    decode_parser.add_argument("output", help="path for the reconstructed image")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "encode":
        encode_image(args.input, args.output)
    else:
        decode_image(args.input, args.output)
