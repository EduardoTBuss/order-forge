"""
Color parsing utilities for Excalidraw elements.
"""

from typing import Tuple

# Excalidraw's default color palette
EXCALIDRAW_COLORS = {
    "#1e1e1e": "black",
    "#e03131": "red",
    "#2f9e44": "green",
    "#1971c2": "blue",
    "#f08c00": "orange",
    "#fab005": "yellow",
    "#9c36b5": "violet",
    "#a5d8ff": "light-blue",
    "#ffc9c9": "light-red",
    "#b2f2bb": "light-green",
    "#ffec99": "light-yellow",
    "#eebefa": "light-violet",
    "#ffffff": "white",
    "#868e96": "gray",
}


def parse_color(color_str: str, opacity: int = 100) -> Tuple[float, float, float, float]:
    """
    Convert color string to RGBA tuple (0-1 range).

    Args:
        color_str: Hex color like "#1e1e1e" or "transparent"
        opacity: Opacity 0-100

    Returns:
        Tuple of (r, g, b, a) in 0-1 range
    """
    if color_str == "transparent" or not color_str:
        return (0.0, 0.0, 0.0, 0.0)

    if color_str.startswith("#"):
        hex_color = color_str.lstrip("#")
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16) / 255.0
            g = int(hex_color[2:4], 16) / 255.0
            b = int(hex_color[4:6], 16) / 255.0
        elif len(hex_color) == 3:
            r = int(hex_color[0] * 2, 16) / 255.0
            g = int(hex_color[1] * 2, 16) / 255.0
            b = int(hex_color[2] * 2, 16) / 255.0
        else:
            return (0.0, 0.0, 0.0, 1.0)

        a = opacity / 100.0
        return (r, g, b, a)

    # Default to black
    return (0.0, 0.0, 0.0, 1.0)


def to_pil_color(color_str: str, opacity: int = 100) -> Tuple[int, int, int, int]:
    """
    Convert color string to PIL RGBA tuple (0-255 range).
    """
    r, g, b, a = parse_color(color_str, opacity)
    return (int(r * 255), int(g * 255), int(b * 255), int(a * 255))
