"""
Shape renderers for Excalidraw elements using rough.js port for hand-drawn style.
"""

import math
from typing import TYPE_CHECKING, List

import cairo
from rough import Options, RoughGenerator

from .colors import parse_color

if TYPE_CHECKING:
    from .parser import ExcalidrawElement
    from .renderer import ExcalidrawRenderer


def render_shapes(
    ctx: cairo.Context,
    elements: List["ExcalidrawElement"],
    renderer: "ExcalidrawRenderer",
):
    """Render all shape elements to the cairo context."""
    for elem in elements:
        if elem.type == "rectangle":
            render_rectangle(ctx, elem, renderer)
        elif elem.type == "ellipse":
            render_ellipse(ctx, elem, renderer)
        elif elem.type == "diamond":
            render_diamond(ctx, elem, renderer)
        elif elem.type == "line":
            render_line(ctx, elem, renderer)
        elif elem.type == "arrow":
            render_arrow(ctx, elem, renderer)


def _get_rough_options(
    elem: "ExcalidrawElement", renderer: "ExcalidrawRenderer"
) -> Options:
    """Create rough.js options from element properties.

    Uses fixed wobbliness settings - not adjustable per element.
    """
    return Options(
        roughness=0.5,  # Fixed low wobbliness
        strokeWidth=elem.stroke_width * renderer.scale,
        bowing=0.5,  # Fixed low bowing
        curveStepCount=12,
        disableMultiStroke=False,  # Enable double-stroke sketchy effect
        maxRandomnessOffset=0.5 * renderer.scale,  # Fixed low randomness
    )


def _render_rough_ops(
    ctx: cairo.Context, drawable, offset_x: float = 0, offset_y: float = 0
):
    """Render rough.js drawable operations to cairo context."""
    for opset in drawable.sets:
        if opset.type == "path":
            for op in opset.ops:
                if op.op == "move":
                    ctx.move_to(op.data[0] + offset_x, op.data[1] + offset_y)
                elif op.op == "lineTo":
                    ctx.line_to(op.data[0] + offset_x, op.data[1] + offset_y)
                elif op.op == "bcurveTo":
                    # bcurveTo has 6 values: cp1x, cp1y, cp2x, cp2y, x, y
                    ctx.curve_to(
                        op.data[0] + offset_x,
                        op.data[1] + offset_y,
                        op.data[2] + offset_x,
                        op.data[3] + offset_y,
                        op.data[4] + offset_x,
                        op.data[5] + offset_y,
                    )
        elif opset.type == "fillPath":
            # Handle fill paths similarly
            for op in opset.ops:
                if op.op == "move":
                    ctx.move_to(op.data[0] + offset_x, op.data[1] + offset_y)
                elif op.op == "lineTo":
                    ctx.line_to(op.data[0] + offset_x, op.data[1] + offset_y)
                elif op.op == "bcurveTo":
                    ctx.curve_to(
                        op.data[0] + offset_x,
                        op.data[1] + offset_y,
                        op.data[2] + offset_x,
                        op.data[3] + offset_y,
                        op.data[4] + offset_x,
                        op.data[5] + offset_y,
                    )


def _set_stroke_style(
    ctx: cairo.Context, elem: "ExcalidrawElement", renderer: "ExcalidrawRenderer"
):
    """Set stroke color and width."""
    r, g, b, a = parse_color(elem.stroke_color, elem.opacity)
    ctx.set_source_rgba(r, g, b, a)
    ctx.set_line_width(elem.stroke_width * renderer.scale)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)

    # Handle stroke style
    if elem.stroke_style == "dashed":
        dash_length = 8 * renderer.scale
        ctx.set_dash([dash_length, dash_length])
    elif elem.stroke_style == "dotted":
        dot_length = 2 * renderer.scale
        ctx.set_dash([dot_length, dot_length * 2])
    else:
        ctx.set_dash([])


def _fill_shape(ctx: cairo.Context, elem: "ExcalidrawElement"):
    """Fill shape with background color if not transparent."""
    if elem.background_color != "transparent":
        r, g, b, a = parse_color(elem.background_color, elem.opacity)
        ctx.set_source_rgba(r, g, b, a)
        ctx.fill_preserve()


def render_rectangle(
    ctx: cairo.Context, elem: "ExcalidrawElement", renderer: "ExcalidrawRenderer"
):
    """Render a rectangle element with hand-drawn style."""
    x, y = renderer.transform(elem.x, elem.y)
    w = elem.width * renderer.scale
    h = elem.height * renderer.scale

    ctx.save()

    # Apply rotation around center
    if elem.angle != 0:
        cx, cy = x + w / 2, y + h / 2
        ctx.translate(cx, cy)
        ctx.rotate(elem.angle)
        ctx.translate(-cx, -cy)

    if elem.roughness > 0:
        # Use rough.js for hand-drawn style
        gen = RoughGenerator()
        opts = _get_rough_options(elem, renderer)
        drawable = gen.rectangle(0, 0, w, h, opts)

        # Fill first if needed
        if elem.background_color != "transparent":
            ctx.rectangle(x, y, w, h)
            _fill_shape(ctx, elem)
            ctx.new_path()

        # Draw rough stroke
        _render_rough_ops(ctx, drawable, x, y)
        _set_stroke_style(ctx, elem, renderer)
        ctx.stroke()
    else:
        # Clean rectangle for roughness=0
        ctx.rectangle(x, y, w, h)
        _fill_shape(ctx, elem)
        _set_stroke_style(ctx, elem, renderer)
        ctx.stroke()

    ctx.restore()


def render_ellipse(
    ctx: cairo.Context, elem: "ExcalidrawElement", renderer: "ExcalidrawRenderer"
):
    """Render an ellipse element with hand-drawn style."""
    x, y = renderer.transform(elem.x, elem.y)
    w = elem.width * renderer.scale
    h = elem.height * renderer.scale
    cx, cy = x + w / 2, y + h / 2

    ctx.save()

    # Apply rotation around center
    if elem.angle != 0:
        ctx.translate(cx, cy)
        ctx.rotate(elem.angle)
        ctx.translate(-cx, -cy)

    if elem.roughness > 0:
        # Use rough.js for hand-drawn style
        gen = RoughGenerator()
        opts = _get_rough_options(elem, renderer)
        drawable = gen.ellipse(cx, cy, w, h, opts)

        # Fill first if needed
        if elem.background_color != "transparent":
            ctx.save()
            ctx.translate(cx, cy)
            ctx.scale(w / 2, h / 2)
            ctx.arc(0, 0, 1, 0, 2 * math.pi)
            ctx.restore()
            _fill_shape(ctx, elem)
            ctx.new_path()

        # Draw rough stroke
        _render_rough_ops(ctx, drawable)
        _set_stroke_style(ctx, elem, renderer)
        ctx.stroke()
    else:
        # Clean ellipse
        ctx.translate(cx, cy)
        ctx.scale(w / 2, h / 2)
        ctx.arc(0, 0, 1, 0, 2 * math.pi)
        ctx.restore()
        ctx.save()
        _fill_shape(ctx, elem)
        _set_stroke_style(ctx, elem, renderer)
        ctx.stroke()

    ctx.restore()


def render_diamond(
    ctx: cairo.Context, elem: "ExcalidrawElement", renderer: "ExcalidrawRenderer"
):
    """Render a diamond element with hand-drawn style."""
    x, y = renderer.transform(elem.x, elem.y)
    w = elem.width * renderer.scale
    h = elem.height * renderer.scale

    ctx.save()

    # Apply rotation around center
    cx, cy = x + w / 2, y + h / 2
    if elem.angle != 0:
        ctx.translate(cx, cy)
        ctx.rotate(elem.angle)
        ctx.translate(-cx, -cy)

    # Diamond points: top, right, bottom, left
    points = [
        (x + w / 2, y),
        (x + w, y + h / 2),
        (x + w / 2, y + h),
        (x, y + h / 2),
    ]

    if elem.roughness > 0:
        gen = RoughGenerator()
        opts = _get_rough_options(elem, renderer)
        drawable = gen.polygon(points, opts)

        # Fill first
        if elem.background_color != "transparent":
            ctx.move_to(*points[0])
            for pt in points[1:]:
                ctx.line_to(*pt)
            ctx.close_path()
            _fill_shape(ctx, elem)
            ctx.new_path()

        _render_rough_ops(ctx, drawable)
        _set_stroke_style(ctx, elem, renderer)
        ctx.stroke()
    else:
        ctx.move_to(*points[0])
        for pt in points[1:]:
            ctx.line_to(*pt)
        ctx.close_path()
        _fill_shape(ctx, elem)
        _set_stroke_style(ctx, elem, renderer)
        ctx.stroke()

    ctx.restore()


def render_line(
    ctx: cairo.Context, elem: "ExcalidrawElement", renderer: "ExcalidrawRenderer"
):
    """Render a line element with hand-drawn style."""
    if not elem.points or len(elem.points) < 2:
        return

    ctx.save()

    base_x, base_y = renderer.transform(elem.x, elem.y)
    scaled_points = [
        (base_x + pt[0] * renderer.scale, base_y + pt[1] * renderer.scale)
        for pt in elem.points
    ]

    gen = RoughGenerator()
    opts = _get_rough_options(elem, renderer)

    if len(scaled_points) == 2:
        # Straight line - use linearPath
        drawable = gen.linearPath(scaled_points, opts)
    else:
        # Multi-point line - use curve for smooth interpolation
        drawable = gen.curve(scaled_points, opts)

    _render_rough_ops(ctx, drawable)
    _set_stroke_style(ctx, elem, renderer)
    ctx.stroke()

    ctx.restore()


def render_arrow(
    ctx: cairo.Context, elem: "ExcalidrawElement", renderer: "ExcalidrawRenderer"
):
    """Render an arrow element with hand-drawn style."""
    if not elem.points or len(elem.points) < 2:
        return

    ctx.save()

    base_x, base_y = renderer.transform(elem.x, elem.y)
    scaled_points = [
        (base_x + pt[0] * renderer.scale, base_y + pt[1] * renderer.scale)
        for pt in elem.points
    ]

    gen = RoughGenerator()
    opts = _get_rough_options(elem, renderer)

    if len(scaled_points) == 2:
        # Straight arrow - use linearPath
        drawable = gen.linearPath(scaled_points, opts)
    else:
        # Multi-point arrow - use curve for smooth interpolation
        drawable = gen.curve(scaled_points, opts)

    _render_rough_ops(ctx, drawable)
    _set_stroke_style(ctx, elem, renderer)
    ctx.stroke()

    # Draw arrowheads
    arrow_size = 10 * renderer.scale

    # For curved arrows, calculate tangent direction at endpoints
    if len(scaled_points) > 2:
        # Use the curve tangent direction for arrowhead orientation
        if elem.start_arrowhead == "arrow":
            # Tangent at start: direction from first to second point
            _draw_arrowhead(
                ctx, scaled_points[1], scaled_points[0], arrow_size, elem, renderer
            )
        if elem.end_arrowhead == "arrow":
            # Tangent at end: direction from second-to-last to last point
            _draw_arrowhead(
                ctx, scaled_points[-2], scaled_points[-1], arrow_size, elem, renderer
            )
    else:
        if elem.start_arrowhead == "arrow":
            _draw_arrowhead(
                ctx, scaled_points[1], scaled_points[0], arrow_size, elem, renderer
            )
        if elem.end_arrowhead == "arrow":
            _draw_arrowhead(
                ctx, scaled_points[-2], scaled_points[-1], arrow_size, elem, renderer
            )

    ctx.restore()


def _draw_arrowhead(
    ctx: cairo.Context,
    from_pt: tuple,
    to_pt: tuple,
    size: float,
    elem: "ExcalidrawElement",
    renderer: "ExcalidrawRenderer",
):
    """Draw an arrowhead at to_pt pointing from from_pt."""
    dx = to_pt[0] - from_pt[0]
    dy = to_pt[1] - from_pt[1]
    length = math.sqrt(dx * dx + dy * dy)

    if length < 0.001:
        return

    dx /= length
    dy /= length

    angle = math.pi / 6

    ax1 = to_pt[0] - size * (dx * math.cos(angle) - dy * math.sin(angle))
    ay1 = to_pt[1] - size * (dy * math.cos(angle) + dx * math.sin(angle))
    ax2 = to_pt[0] - size * (dx * math.cos(angle) + dy * math.sin(angle))
    ay2 = to_pt[1] - size * (dy * math.cos(angle) - dx * math.sin(angle))

    if elem.roughness > 0:
        gen = RoughGenerator()
        opts = _get_rough_options(elem, renderer)

        line1 = gen.line(to_pt[0], to_pt[1], ax1, ay1, opts)
        _render_rough_ops(ctx, line1)
        _set_stroke_style(ctx, elem, renderer)
        ctx.stroke()

        line2 = gen.line(to_pt[0], to_pt[1], ax2, ay2, opts)
        _render_rough_ops(ctx, line2)
        _set_stroke_style(ctx, elem, renderer)
        ctx.stroke()
    else:
        ctx.move_to(*to_pt)
        ctx.line_to(ax1, ay1)
        ctx.move_to(*to_pt)
        ctx.line_to(ax2, ay2)
        _set_stroke_style(ctx, elem, renderer)
        ctx.stroke()
