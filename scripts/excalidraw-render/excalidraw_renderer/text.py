"""
Text rendering for Excalidraw elements using PIL with Excalifont.
"""

import io
import re
from pathlib import Path
from typing import TYPE_CHECKING, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

from .colors import to_pil_color

if TYPE_CHECKING:
    from .parser import ExcalidrawElement
    from .renderer import ExcalidrawRenderer


# Paths to fonts - inside this package
FONT_DIR = Path(__file__).parent / "fonts"
DISPLAY_FONT = FONT_DIR / "Excalifont-Regular.woff2"
EMOJI_FONT = FONT_DIR / "NotoColorEmoji.ttf"

# NotoColorEmoji is a bitmap font with fixed size (109px is standard)
EMOJI_NATIVE_SIZE = 109

# Font cache for display font (scalable)
_display_font_cache: dict[int, ImageFont.FreeTypeFont] = {}

# Emoji font loaded once at native size
_emoji_font: Optional[ImageFont.FreeTypeFont] = None

# Regex pattern to match emoji characters
# Covers most common emoji ranges including emoticons, symbols, flags, etc.
EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols & pictographs
    "\U0001f680-\U0001f6ff"  # transport & map symbols
    "\U0001f700-\U0001f77f"  # alchemical symbols
    "\U0001f780-\U0001f7ff"  # geometric shapes extended
    "\U0001f800-\U0001f8ff"  # supplemental arrows-c
    "\U0001f900-\U0001f9ff"  # supplemental symbols and pictographs
    "\U0001fa00-\U0001fa6f"  # chess symbols
    "\U0001fa70-\U0001faff"  # symbols and pictographs extended-a
    "\U00002702-\U000027b0"  # dingbats
    "\U000024c2-\U0001f251"  # enclosed characters
    "\U0001f1e0-\U0001f1ff"  # flags (iOS)
    "]+",
    flags=re.UNICODE,
)


def is_emoji(char: str) -> bool:
    """Check if a character is an emoji."""
    return bool(EMOJI_PATTERN.match(char))


def segment_text(text: str) -> List[Tuple[str, bool]]:
    """
    Segment text into runs of emoji and non-emoji characters.

    Returns:
        List of (text_segment, is_emoji) tuples
    """
    if not text:
        return []

    segments = []
    current_segment = ""
    current_is_emoji = None

    for char in text:
        char_is_emoji = is_emoji(char)

        if current_is_emoji is None:
            current_is_emoji = char_is_emoji
            current_segment = char
        elif char_is_emoji == current_is_emoji:
            current_segment += char
        else:
            segments.append((current_segment, current_is_emoji))
            current_segment = char
            current_is_emoji = char_is_emoji

    if current_segment:
        segments.append((current_segment, current_is_emoji))

    return segments


def get_display_font(size: int) -> ImageFont.FreeTypeFont:
    """Get display font at specified size, with caching."""
    if size not in _display_font_cache:
        if not DISPLAY_FONT.exists():
            raise FileNotFoundError(f"Excalifont font not found at {DISPLAY_FONT}")
        _display_font_cache[size] = ImageFont.truetype(str(DISPLAY_FONT), size)
    return _display_font_cache[size]


def get_emoji_font() -> ImageFont.FreeTypeFont:
    """Get emoji font at native size (bitmap font, fixed size)."""
    global _emoji_font
    if _emoji_font is None:
        if not EMOJI_FONT.exists():
            raise FileNotFoundError(f"Noto Color Emoji font not found at {EMOJI_FONT}")
        _emoji_font = ImageFont.truetype(str(EMOJI_FONT), EMOJI_NATIVE_SIZE)
    return _emoji_font


def get_text_width(
    text: str, display_font: ImageFont.FreeTypeFont, target_size: int
) -> float:
    """
    Calculate the total width of text, accounting for mixed emoji/text.

    For emojis, width is estimated based on target size since the emoji font
    is a fixed-size bitmap font.
    """
    segments = segment_text(text)
    total_width = 0.0

    for segment, is_emoji_segment in segments:
        if is_emoji_segment:
            # Estimate emoji width: each emoji is roughly square at the target size
            # Count actual emoji characters (some emojis are multi-codepoint)
            emoji_count = len(segment)
            total_width += emoji_count * target_size
        else:
            bbox = display_font.getbbox(segment)
            if bbox:
                total_width += bbox[2] - bbox[0]

    return total_width


def draw_text_with_emojis(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    x: float,
    y: float,
    text: str,
    display_font: ImageFont.FreeTypeFont,
    target_size: int,
    color: tuple,
):
    """
    Draw text with proper emoji font handling.

    Regular text is drawn directly. Emojis are rendered at native size
    and then scaled/composited onto the image.
    """
    segments = segment_text(text)
    current_x = x
    emoji_font = get_emoji_font()
    scale_factor = target_size / EMOJI_NATIVE_SIZE

    for segment, is_emoji_segment in segments:
        if is_emoji_segment:
            # Render each emoji and composite it
            for emoji_char in segment:
                # Create a temporary image for the emoji
                # Use larger canvas to ensure emoji fits
                temp_size = EMOJI_NATIVE_SIZE + 20
                temp_img = Image.new("RGBA", (temp_size, temp_size), (0, 0, 0, 0))
                temp_draw = ImageDraw.Draw(temp_img)

                # Draw emoji at native size with embedded colors
                temp_draw.text((10, 0), emoji_char, font=emoji_font, embedded_color=True)

                # Find the actual emoji bounds
                bbox = temp_img.getbbox()
                if bbox:
                    # Crop to content
                    emoji_img = temp_img.crop(bbox)

                    # Scale to target size
                    new_width = int(emoji_img.width * scale_factor)
                    new_height = int(emoji_img.height * scale_factor)
                    if new_width > 0 and new_height > 0:
                        emoji_img = emoji_img.resize(
                            (new_width, new_height), Image.Resampling.LANCZOS
                        )

                        # Composite onto main image
                        paste_x = int(current_x)
                        paste_y = int(y)
                        img.paste(emoji_img, (paste_x, paste_y), emoji_img)

                current_x += target_size
        else:
            # Draw regular text directly
            draw.text((current_x, y), segment, font=display_font, fill=color)
            bbox = display_font.getbbox(segment)
            if bbox:
                current_x += bbox[2] - bbox[0]


def render_text_overlay(
    png_buffer: io.BytesIO,
    text_elements: List["ExcalidrawElement"],
    renderer: "ExcalidrawRenderer",
) -> Image.Image:
    """
    Overlay text elements on a PNG image using PIL.

    Args:
        png_buffer: BytesIO containing PNG data from cairo
        text_elements: List of text elements to render
        renderer: ExcalidrawRenderer for coordinate transformation

    Returns:
        PIL Image with text overlaid
    """
    # Load the cairo-rendered shapes
    img = Image.open(png_buffer).convert("RGBA")
    draw = ImageDraw.Draw(img)

    for elem in text_elements:
        if not elem.text:
            continue

        # Transform coordinates
        tx, ty = renderer.transform(elem.x, elem.y)

        # Scale font size
        font_size = int(elem.font_size * renderer.scale)
        display_font = get_display_font(font_size)

        # Get color
        color = to_pil_color(elem.stroke_color, elem.opacity)

        # Handle multiline text
        lines = elem.text.split("\n")
        line_height = font_size * elem.line_height

        for i, line in enumerate(lines):
            y_offset = ty + i * line_height

            # Handle text alignment - calculate width with emoji support
            text_width = get_text_width(line, display_font, font_size)

            if elem.text_align == "center":
                x_pos = tx + (elem.width * renderer.scale - text_width) / 2
            elif elem.text_align == "right":
                x_pos = tx + elem.width * renderer.scale - text_width
            else:
                x_pos = tx

            # Draw text with emoji support
            draw_text_with_emojis(
                img, draw, x_pos, y_offset, line, display_font, font_size, color
            )

    return img


def render_bound_text(
    img: Image.Image,
    draw: ImageDraw.ImageDraw,
    elem: "ExcalidrawElement",
    container_x: float,
    container_y: float,
    container_width: float,
    container_height: float,
    renderer: "ExcalidrawRenderer",
):
    """
    Render text bound to a container shape.

    For text elements with containerId set, the text should be
    centered within the container bounds.
    """
    if not elem.text:
        return

    font_size = int(elem.font_size * renderer.scale)
    display_font = get_display_font(font_size)
    color = to_pil_color(elem.stroke_color, elem.opacity)

    lines = elem.text.split("\n")
    line_height = font_size * elem.line_height

    # Calculate total text height
    total_height = len(lines) * line_height

    # Center vertically in container
    start_y = container_y + (container_height - total_height) / 2

    for i, line in enumerate(lines):
        y_pos = start_y + i * line_height

        # Center horizontally - calculate width with emoji support
        text_width = get_text_width(line, display_font, font_size)
        x_pos = container_x + (container_width - text_width) / 2

        # Draw text with emoji support
        draw_text_with_emojis(
            img, draw, x_pos, y_pos, line, display_font, font_size, color
        )
