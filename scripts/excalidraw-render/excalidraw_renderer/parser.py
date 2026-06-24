"""
Parser for Excalidraw JSON files.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ExcalidrawElement:
    """Represents a single Excalidraw element."""

    id: str
    type: str
    x: float
    y: float
    width: float = 0.0
    height: float = 0.0
    angle: float = 0.0
    stroke_color: str = "#1e1e1e"
    background_color: str = "transparent"
    fill_style: str = "solid"
    stroke_width: int = 2
    stroke_style: str = "solid"
    roughness: int = 1
    opacity: int = 100
    index: str = ""

    # Text-specific
    text: str = ""
    font_size: int = 20
    font_family: int = 1
    text_align: str = "left"
    vertical_align: str = "top"
    line_height: float = 1.25

    # Line/arrow-specific
    points: List[List[float]] = field(default_factory=list)
    start_arrowhead: Optional[str] = None
    end_arrowhead: Optional[str] = None

    # Container reference (for text bound to shapes)
    container_id: Optional[str] = None


def parse_excalidraw(file_path: Path) -> Tuple[List[ExcalidrawElement], Dict[str, Any]]:
    """
    Parse an .excalidraw JSON file.

    Args:
        file_path: Path to the .excalidraw file

    Returns:
        Tuple of (elements list, app_state dict)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    elements = []
    raw_elements = data.get("elements", [])

    for raw in raw_elements:
        # Skip deleted elements
        if raw.get("isDeleted", False):
            continue

        elem = ExcalidrawElement(
            id=raw.get("id", ""),
            type=raw.get("type", ""),
            x=raw.get("x", 0.0),
            y=raw.get("y", 0.0),
            width=raw.get("width", 0.0),
            height=raw.get("height", 0.0),
            angle=raw.get("angle", 0.0),
            stroke_color=raw.get("strokeColor", "#1e1e1e"),
            background_color=raw.get("backgroundColor", "transparent"),
            fill_style=raw.get("fillStyle", "solid"),
            stroke_width=raw.get("strokeWidth", 2),
            stroke_style=raw.get("strokeStyle", "solid"),
            roughness=raw.get("roughness", 1),
            opacity=raw.get("opacity", 100),
            index=raw.get("index", ""),
            # Text fields
            text=raw.get("text", ""),
            font_size=raw.get("fontSize", 20),
            font_family=raw.get("fontFamily", 1),
            text_align=raw.get("textAlign", "left"),
            vertical_align=raw.get("verticalAlign", "top"),
            line_height=raw.get("lineHeight", 1.25),
            # Line/arrow fields
            points=raw.get("points", []),
            start_arrowhead=raw.get("startArrowhead"),
            end_arrowhead=raw.get("endArrowhead"),
            # Container
            container_id=raw.get("containerId"),
        )
        elements.append(elem)

    # Sort by index for proper z-order
    elements.sort(key=lambda e: e.index)

    app_state = data.get("appState", {})

    return elements, app_state


@dataclass
class Bounds:
    """Bounding box for elements."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y


def calculate_bounds(elements: List[ExcalidrawElement], padding: float = 20.0) -> Bounds:
    """
    Calculate the bounding box of all elements.

    Args:
        elements: List of elements
        padding: Extra padding around the bounds

    Returns:
        Bounds object
    """
    if not elements:
        return Bounds(0, 0, 100, 100)

    min_x = float("inf")
    min_y = float("inf")
    max_x = float("-inf")
    max_y = float("-inf")

    for elem in elements:
        # For lines/arrows, consider all points
        if elem.type in ("line", "arrow") and elem.points:
            for pt in elem.points:
                px = elem.x + pt[0]
                py = elem.y + pt[1]
                min_x = min(min_x, px)
                min_y = min(min_y, py)
                max_x = max(max_x, px)
                max_y = max(max_y, py)
        else:
            # For shapes, use x, y, width, height
            min_x = min(min_x, elem.x)
            min_y = min(min_y, elem.y)
            max_x = max(max_x, elem.x + elem.width)
            max_y = max(max_y, elem.y + elem.height)

    return Bounds(
        min_x=min_x - padding,
        min_y=min_y - padding,
        max_x=max_x + padding,
        max_y=max_y + padding,
    )
