"""
Main renderer orchestrating cairo shapes and PIL text.
"""

import io
from pathlib import Path
from typing import List, Optional, Tuple

import cairo

from .colors import parse_color
from .parser import Bounds, ExcalidrawElement, calculate_bounds, parse_excalidraw


class ExcalidrawRenderer:
    """
    Renders Excalidraw elements to PNG/SVG.

    Uses cairo for shapes, PIL for text overlay.
    """

    def __init__(self, scale: float = 2.0, padding: float = 32.0):
        self.scale = scale
        self.padding = padding
        self.elements: List[ExcalidrawElement] = []
        self.bounds: Optional[Bounds] = None
        self.width: int = 0
        self.height: int = 0

    def load(self, file_path: Path) -> "ExcalidrawRenderer":
        """Load elements from an .excalidraw file."""
        self.elements, _ = parse_excalidraw(file_path)
        self.bounds = calculate_bounds(self.elements, padding=self.padding / self.scale)
        self.width = int(self.bounds.width * self.scale + 2 * self.padding)
        self.height = int(self.bounds.height * self.scale + 2 * self.padding)
        return self

    def transform(self, x: float, y: float) -> Tuple[float, float]:
        """Transform element coordinates to canvas coordinates."""
        if self.bounds is None:
            return x, y
        tx = (x - self.bounds.min_x) * self.scale + self.padding
        ty = (y - self.bounds.min_y) * self.scale + self.padding
        return tx, ty

    def render_to_png(self, output_path: Path) -> Path:
        """Render elements to PNG file."""
        from .shapes import render_shapes
        from .text import render_text_overlay

        # Create cairo surface
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, self.width, self.height)
        ctx = cairo.Context(surface)

        # White background
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.paint()

        # Render shapes (non-text elements)
        shape_elements = [e for e in self.elements if e.type != "text"]
        render_shapes(ctx, shape_elements, self)

        # Write cairo surface to bytes
        png_buffer = io.BytesIO()
        surface.write_to_png(png_buffer)
        png_buffer.seek(0)

        # Apply text overlay with PIL
        text_elements = [e for e in self.elements if e.type == "text"]
        final_image = render_text_overlay(png_buffer, text_elements, self)

        # Save final image
        final_image.save(str(output_path), "PNG")
        return output_path

    def render_to_svg(self, output_path: Path) -> Path:
        """Render elements to SVG file."""
        from .shapes import render_shapes

        # Create SVG surface
        surface = cairo.SVGSurface(str(output_path), self.width, self.height)
        ctx = cairo.Context(surface)

        # White background
        ctx.set_source_rgb(1.0, 1.0, 1.0)
        ctx.paint()

        # Render shapes
        shape_elements = [e for e in self.elements if e.type != "text"]
        render_shapes(ctx, shape_elements, self)

        # Render text elements as SVG text
        text_elements = [e for e in self.elements if e.type == "text"]
        self._render_svg_text(ctx, text_elements)

        surface.finish()
        return output_path

    def _render_svg_text(
        self, ctx: cairo.Context, text_elements: List[ExcalidrawElement]
    ):
        """Render text elements using cairo (for SVG output)."""
        ctx.select_font_face("Virgil", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

        for elem in text_elements:
            if not elem.text:
                continue

            tx, ty = self.transform(elem.x, elem.y)
            font_size = elem.font_size * self.scale

            ctx.set_font_size(font_size)
            r, g, b, a = parse_color(elem.stroke_color, elem.opacity)
            ctx.set_source_rgba(r, g, b, a)

            # Split text into lines and render each
            lines = elem.text.split("\n")
            line_height = font_size * elem.line_height

            for i, line in enumerate(lines):
                ctx.move_to(tx, ty + font_size + i * line_height)
                ctx.show_text(line)
