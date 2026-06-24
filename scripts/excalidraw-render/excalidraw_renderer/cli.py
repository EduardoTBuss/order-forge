"""
Command-line interface for Excalidraw renderer.
"""

import argparse
import sys
from pathlib import Path
from typing import List

from .renderer import ExcalidrawRenderer


def render_file(input_path: Path, output_path: Path, format: str, scale: float = 2.0):
    """Render a single .excalidraw file."""
    renderer = ExcalidrawRenderer(scale=scale)
    renderer.load(input_path)

    if format == "png":
        renderer.render_to_png(output_path)
    elif format == "svg":
        renderer.render_to_svg(output_path)

    print(f"Rendered: {input_path} -> {output_path}")


def batch_render(
    input_files: List[Path], output_dir: Path, format: str, scale: float = 2.0
):
    """Render multiple .excalidraw files."""
    output_dir.mkdir(parents=True, exist_ok=True)

    for input_path in input_files:
        output_name = input_path.stem + f".{format}"
        output_path = output_dir / output_name
        try:
            render_file(input_path, output_path, format, scale)
        except Exception as e:
            print(f"Error rendering {input_path}: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Render .excalidraw files to PNG or SVG"
    )
    parser.add_argument("input", type=Path, nargs="?", help="Input .excalidraw file")
    parser.add_argument("-o", "--output", type=Path, help="Output file path")
    parser.add_argument(
        "-f",
        "--format",
        choices=["png", "svg"],
        default="png",
        help="Output format (default: png)",
    )
    parser.add_argument(
        "-s", "--scale", type=float, default=2.0, help="Scale factor (default: 2.0)"
    )
    parser.add_argument(
        "--batch", type=Path, nargs="+", help="Batch render multiple files"
    )
    parser.add_argument(
        "--outdir", type=Path, help="Output directory for batch rendering"
    )

    args = parser.parse_args()

    # Batch mode
    if args.batch:
        if not args.outdir:
            print("Error: --outdir required for batch mode", file=sys.stderr)
            sys.exit(1)
        batch_render(args.batch, args.outdir, args.format, args.scale)
        return

    # Single file mode
    if not args.input:
        parser.print_help()
        sys.exit(1)

    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    output_path = args.output
    if not output_path:
        output_path = args.input.with_suffix(f".{args.format}")

    render_file(args.input, output_path, args.format, args.scale)


if __name__ == "__main__":
    main()
