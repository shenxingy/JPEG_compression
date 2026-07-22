"""Educational JPEG-style image compression package."""

from .decoder import decode_image
from .encoder import encode_image

__all__ = ["decode_image", "encode_image"]
__version__ = "1.0.0"
