#!/usr/bin/env python3
"""
Nano Banana Background Generator

Generate tiling presentation backgrounds that form one continuous panorama.
Each slide is a segment of a larger image with:
- Conway's Game of Data (small 0s and 1s)
- Flowing lines with cross-slide continuity

Usage:
    python nano-banana-backgrounds.py --slides 8 --output-dir ./backgrounds
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

from dotenv import load_dotenv
load_dotenv(Path.home() / "Data/.datacore/env/.env")

import google.generativeai as genai
from PIL import Image
from io import BytesIO
from reportlab.pdfgen import canvas


def generate_background_tile(model, tile_number: int, total_tiles: int) -> bytes:
    """Generate a single background tile that connects vertically with adjacent tiles."""

    # Fixed line positions for EXACT continuity across all slides
    # 5 lines creating an intricate but coherent pattern
    # Each line has fixed x-positions at top and bottom of each slide

    # Line paths (x-position as % from left edge)
    # Format: (top_x, bottom_x) - lines curve between these points
    line_paths = [
        # Line 1: Far left, gentle rightward drift
        [(8, 10), (10, 12), (12, 14), (14, 12), (12, 10), (10, 8), (8, 10), (10, 12)],
        # Line 2: Left-center, sinuous wave
        [(20, 25), (25, 22), (22, 28), (28, 24), (24, 26), (26, 22), (22, 25), (25, 20)],
        # Line 3: Center, dramatic S-curve
        [(45, 55), (55, 48), (48, 52), (52, 45), (45, 55), (55, 48), (48, 52), (52, 45)],
        # Line 4: Right-center, opposite wave
        [(72, 78), (78, 74), (74, 80), (80, 75), (75, 78), (78, 73), (73, 77), (77, 72)],
        # Line 5: Far right, gentle leftward drift
        [(90, 88), (88, 92), (92, 89), (89, 91), (91, 88), (88, 90), (90, 92), (92, 90)],
    ]

    # Get positions for this specific tile
    tile_idx = tile_number - 1
    line_specs = []
    for line_num, path in enumerate(line_paths, 1):
        top_x = path[tile_idx % len(path)][0]
        bottom_x = path[tile_idx % len(path)][1]
        line_specs.append(f"Line {line_num}: enters at {top_x}% from left (TOP), exits at {bottom_x}% from left (BOTTOM)")

    line_instruction = "\n".join(line_specs)

    # Previous and next slide connections
    if tile_number > 1:
        prev_connections = []
        for line_num, path in enumerate(line_paths, 1):
            prev_bottom = path[(tile_idx - 1) % len(path)][1]
            prev_connections.append(f"Line {line_num} must enter at EXACTLY {prev_bottom}% (connecting from slide {tile_number-1})")
        continuity_top = "\n".join(prev_connections)
    else:
        continuity_top = "Lines originate at top of this slide (first slide)"

    if tile_number < total_tiles:
        next_connections = []
        for line_num, path in enumerate(line_paths, 1):
            this_bottom = path[tile_idx % len(path)][1]
            next_connections.append(f"Line {line_num} must exit at EXACTLY {this_bottom}% (connecting to slide {tile_number+1})")
        continuity_bottom = "\n".join(next_connections)
    else:
        continuity_bottom = "Lines terminate at bottom of this slide (last slide)"

    prompt = f"""Generate a PURE BACKGROUND IMAGE for a presentation slide.

CRITICAL REQUIREMENTS:
1. EXACTLY 16:9 LANDSCAPE aspect ratio (like 1920x1080) - NOT square
2. NO TEXT - no numbers, letters, labels, words anywhere except Conway pattern
3. This is slide {tile_number} of {total_tiles} in a VERTICAL scroll

INTRICATE LINE PATTERN (5 flowing lines):
These lines create an elegant, interconnected pattern across all slides.
Lines are hair-thin (0.3-0.5px), pale mint green (#4ADE80) at 8-12% opacity.

EXACT LINE POSITIONS FOR THIS SLIDE ({tile_number}/{total_tiles}):
{line_instruction}

TOP EDGE CONTINUITY (must match previous slide's bottom):
{continuity_top}

BOTTOM EDGE CONTINUITY (must match next slide's top):
{continuity_bottom}

LINE STYLE:
- Hair-thin lines (0.3-0.5px stroke)
- Smooth bezier curves between entry and exit points
- Lines may cross each other gracefully
- Some lines curve dramatically, others are gentler
- Creates organic, flowing, interconnected pattern
- Like data streams or neural pathways

CONWAY'S GAME OF DATA (margins only):
- Small 0s and 1s in very light gray (#F0F0F0), ~5% opacity
- LEFT margin only: 0-12% of slide width
- RIGHT margin only: 88-100% of slide width
- {"Dense clusters on left, sparse on right" if tile_number % 2 == 0 else "Sparse on left, dense clusters on right"}
- Tiny characters (5-7pt), some clustered, some isolated
- Leave center 70% of slide completely clear

BACKGROUND: Pure white (#FFFFFF)

FORBIDDEN:
- Text/numbers anywhere except Conway margins
- Lines thicker than 0.5px
- Lines with opacity above 15%
- Square aspect ratio
- Conway pattern in center area

This slide MUST connect seamlessly to slides {tile_number-1 if tile_number > 1 else 'N/A'} (above) and {tile_number+1 if tile_number < total_tiles else 'N/A'} (below)."""

    try:
        response = model.generate_content(
            contents=[prompt],
            generation_config={
                "response_modalities": ["IMAGE"],
            }
        )

        for part in response.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                return part.inline_data.data

        print(f"  Warning: No image in response for tile {tile_number}")
        return None

    except Exception as e:
        print(f"  Error generating tile {tile_number}: {e}")
        return None


def save_image(image_data: bytes, output_path: str) -> tuple:
    """Save image, return (success, original_size)."""
    try:
        image = Image.open(BytesIO(image_data))
        orig_size = image.size
        aspect = orig_size[0] / orig_size[1]
        print(f"  Output: {orig_size[0]}x{orig_size[1]} (aspect {aspect:.2f})")

        # Save at native resolution - no scaling
        image.save(output_path, 'PNG', optimize=False)
        return True, orig_size

    except Exception as e:
        print(f"  Error saving: {e}")
        return False, (0, 0)


def create_panorama(image_paths: list, output_path: str):
    """Stitch all tiles into one VERTICAL panorama image (top to bottom)."""
    if not image_paths:
        return

    images = [Image.open(p) for p in image_paths]

    # Calculate total height (vertical stack)
    max_width = max(img.width for img in images)
    total_height = sum(img.height for img in images)

    # Create vertical panorama canvas
    panorama = Image.new('RGB', (max_width, total_height), (255, 255, 255))

    # Paste images top to bottom
    y_offset = 0
    for img in images:
        # Center horizontally if widths differ
        x_offset = (max_width - img.width) // 2
        panorama.paste(img, (x_offset, y_offset))
        y_offset += img.height

    panorama.save(output_path, 'PNG', optimize=False)
    print(f"Vertical panorama created: {output_path} ({max_width}x{total_height})")


def create_pdf(image_paths: list, output_path: str):
    """Compile tiles into PDF."""
    if not image_paths:
        return

    first_img = Image.open(image_paths[0])
    width, height = first_img.size

    c = canvas.Canvas(output_path, pagesize=(width, height))

    for img_path in image_paths:
        c.drawImage(img_path, 0, 0, width, height)
        c.showPage()

    c.save()
    print(f"PDF created: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate tiling presentation backgrounds')
    parser.add_argument('--slides', '-n', type=int, default=8,
                        help='Number of background tiles to generate')
    parser.add_argument('--output-dir', '-o', default='./backgrounds',
                        help='Output directory')
    parser.add_argument('--model', '-m', default='gemini-3-pro-image-preview',
                        help='Gemini model')
    args = parser.parse_args()

    # Check API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY not found")
        sys.exit(1)

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(args.model)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.slides} background tiles...")
    print("These will form one continuous panorama when placed side by side.\n")

    image_paths = []
    log = {
        'type': 'background_tiles',
        'total_tiles': args.slides,
        'model': args.model,
        'generated_at': datetime.now().isoformat(),
        'tiles': []
    }

    for i in range(1, args.slides + 1):
        print(f"Generating tile {i}/{args.slides}...")

        image_data = generate_background_tile(model, i, args.slides)

        if image_data:
            filename = f"bg-tile-{i:02d}.png"
            output_path = output_dir / filename

            success, orig_size = save_image(image_data, str(output_path))
            if success:
                image_paths.append(str(output_path))
                log['tiles'].append({
                    'number': i,
                    'file': filename,
                    'size': f"{orig_size[0]}x{orig_size[1]}",
                    'status': 'success'
                })
            else:
                log['tiles'].append({'number': i, 'status': 'save_failed'})
        else:
            log['tiles'].append({'number': i, 'status': 'generation_failed'})

    # Create outputs
    if image_paths:
        # Individual PDF
        pdf_path = output_dir / "all-backgrounds.pdf"
        create_pdf(image_paths, str(pdf_path))

        # Panorama (all tiles stitched)
        panorama_path = output_dir / "panorama.png"
        create_panorama(image_paths, str(panorama_path))

    # Save log
    log_path = output_dir / "generation-log.json"
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)

    successful = len([t for t in log['tiles'] if t.get('status') == 'success'])
    print(f"\nDone! {successful}/{args.slides} tiles generated")
    print(f"Output: {output_dir}")
    print(f"Panorama: {output_dir}/panorama.png")


if __name__ == '__main__':
    main()
