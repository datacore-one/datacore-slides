#!/usr/bin/env python3
"""
Nano Banana Slide Generator

Generate presentation slides as images using Google's Gemini (Nano Banana) API.
Saves images locally and compiles into PDF.

Usage:
    python nano-banana-slides.py <markdown_file> [--output-dir <dir>] [--test <n>]

Example:
    python nano-banana-slides.py presentation.md --output-dir ./slides --test 3
"""

import os
import sys
import json
import re
import argparse
import base64
from pathlib import Path
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv
load_dotenv(Path.home() / "Data/.datacore/env/.env")

import google.generativeai as genai
from PIL import Image
from io import BytesIO
from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas


def strip_markdown(text: str) -> str:
    """Remove markdown formatting from text."""
    # Remove bold (**text** or __text__)
    text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
    text = re.sub(r'__(.+?)__', r'\1', text)
    # Remove italic (*text* or _text_)
    text = re.sub(r'\*(.+?)\*', r'\1', text)
    text = re.sub(r'_(.+?)_', r'\1', text)
    return text


def detect_slide_type(slide_content: str) -> str:
    """Detect slide type for layout optimization."""
    content_lower = slide_content.lower()

    # Count tables
    table_count = slide_content.count('|---|')

    # Check for comparison patterns
    has_vs = 'vs' in content_lower or 'versus' in content_lower
    has_traditional_new = 'traditional' in content_lower and 'new' in content_lower
    has_comparison_table = table_count > 0 and ('|' in slide_content)

    if has_traditional_new or has_vs:
        return 'comparison'
    elif table_count > 0:
        return 'table'
    elif content_lower.count('-') > 5:
        return 'bullets'
    else:
        return 'standard'


def parse_markdown_slides(markdown_path: str) -> list[dict]:
    """Parse markdown file into slide content."""
    with open(markdown_path, 'r') as f:
        content = f.read()

    # Remove frontmatter if present
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            content = parts[2]

    # Split by slide separators (---)
    raw_slides = re.split(r'\n---\n', content)

    slides = []
    for i, slide_content in enumerate(raw_slides):
        slide_content = slide_content.strip()
        if not slide_content:
            continue

        # Extract title (first # heading)
        title_match = re.search(r'^#\s+(.+)$', slide_content, re.MULTILINE)
        title = title_match.group(1) if title_match else f"Slide {i+1}"
        title = strip_markdown(title)

        # Extract subtitle (first ## heading or **bold** line after title)
        subtitle_match = re.search(r'^##\s+(.+)$', slide_content, re.MULTILINE)
        if not subtitle_match:
            subtitle_match = re.search(r'^\*\*(.+)\*\*$', slide_content, re.MULTILINE)
        subtitle = subtitle_match.group(1) if subtitle_match else ""
        subtitle = strip_markdown(subtitle)

        # Get body content (everything after title/subtitle)
        body = slide_content
        if title_match:
            body = body.replace(title_match.group(0), '', 1)
        if subtitle_match:
            body = body.replace(subtitle_match.group(0), '', 1)
        body = body.strip()

        # Detect slide type
        slide_type = detect_slide_type(slide_content)

        slides.append({
            'number': len(slides) + 1,
            'title': title,
            'subtitle': subtitle,
            'body': body,
            'raw': slide_content,
            'type': slide_type
        })

    return slides


def load_reference_images(reference_path: str, max_pages: int = 3) -> list:
    """Load reference images from a PDF file."""
    try:
        from pdf2image import convert_from_path
        images = convert_from_path(reference_path, first_page=1, last_page=max_pages, dpi=150)
        print(f"  Loaded {len(images)} reference images from {reference_path}")
        return images
    except ImportError:
        print("  Warning: pdf2image not installed. Run: pip install pdf2image")
        return []
    except Exception as e:
        print(f"  Warning: Could not load reference PDF: {e}")
        return []


def load_logo_image(logo_path: str):
    """Load logo image for brand consistency."""
    try:
        logo = Image.open(logo_path)
        # Convert to RGB if necessary
        if logo.mode in ('RGBA', 'P'):
            logo = logo.convert('RGB')
        print(f"  Loaded logo: {logo_path} ({logo.size[0]}x{logo.size[1]})")
        return logo
    except Exception as e:
        print(f"  Warning: Could not load logo: {e}")
        return None


def get_slide_type_instructions(slide_type: str) -> str:
    """Get layout instructions based on slide type."""
    if slide_type == 'comparison':
        return """LAYOUT TYPE: TWO-COLUMN COMPARISON
- Split content into two clear columns
- Left column: "Traditional/Old approach"
- Right column: "New approach/Data Tokenization"
- Use subtle visual divider between columns
- Highlight labels (like "THE RESULT") should be styled consistently
- Both columns should have equal visual weight"""

    elif slide_type == 'table':
        return """LAYOUT TYPE: DATA TABLE
- Table should be the primary visual element
- Clean hairline borders, no heavy lines
- Header row slightly darker or bold
- Alternating row colors (very subtle)
- Numbers right-aligned, text left-aligned
- Highlight row (like DMCC = $0) should stand out
- Table should be centered and well-spaced"""

    elif slide_type == 'bullets':
        return """LAYOUT TYPE: BULLET LIST
- Use small, elegant icons instead of dashes or dots
- Clean left alignment with consistent indentation
- Generous spacing between items
- Group related items visually
- Section headers (like "Scope:", "Structure:") should be bold/highlighted"""

    else:
        return """LAYOUT TYPE: STANDARD
- Title prominent at top
- Content balanced and readable
- Key callouts or highlights styled consistently
- Clean visual hierarchy"""


def generate_slide_image(slide: dict, model, total_slides: int = 7, reference_images: list = None, logo_image = None) -> bytes:
    """Generate a slide image using Gemini API."""

    slide_type = slide.get('type', 'standard')
    slide_type_instructions = get_slide_type_instructions(slide_type)

    # System style description (consistent across all slides)
    system_style = """Generate a WIDE presentation slide image. CRITICAL: Output must be 16:9 LANDSCAPE aspect ratio (width much greater than height, like 1920x1080 or 1456x816). NOT square. NOT portrait.

BRAND: Datafund - data tokenization fintech company.

LOGO PLACEMENT:
- Copy the provided logo EXACTLY to bottom-right corner (small, ~80px)
- NEVER redraw or modify the logo - pixel-perfect copy only

DESIGN PHILOSOPHY:
- Ultra-minimal, clean, premium (like Apple keynotes)
- Maximum whitespace, minimum elements
- ONE simple visual per slide - no complex diagrams
- Text should be sparse - let visuals communicate

COLORS:
- Background: Pure white (#FFFFFF)
- Text: Black (#000000)
- Accent: Mint green (#4ADE80) - sparingly
- NO gradients, NO colored backgrounds

TYPOGRAPHY:
- Sans-serif (Inter/Helvetica)
- Title: Bold, large, top-left
- Body: Minimal - 3-5 bullet points MAX or one short paragraph
- NO walls of text

BACKGROUND PATTERN - "Conway's Game of Data":
- Subtle grid of 0s and 1s (binary digits) in very light gray (#E5E7EB, 10% opacity)
- Scattered across background like a cellular automaton pattern
- Some 0s and 1s clustered, some isolated - suggesting data emergence
- Must NOT interfere with readability - barely visible
- Creates subtle "digital/data" texture across all slides

LAYOUT:
- WIDE 16:9 landscape format (NOT square)
- Generous margins (100px)
- Content left-aligned
- Simple icons or single illustration on right if needed
- Logo bottom-right corner

VISUAL STYLE:
- Simple line icons (not detailed illustrations)
- Clean geometric shapes
- Minimal diagrams - circles, arrows, simple flows
- NO complex infographics
- NO stock photo style imagery

FORBIDDEN:
- Square aspect ratio
- Dense text blocks
- Complex multi-element diagrams
- Recreating/modifying the logo
- Busy or cluttered layouts
- Centered body text"""

    # Slide-specific prompt
    slide_prompt = f"""Generate slide {slide['number']} of {total_slides}.

{slide_type_instructions}

CONTENT TO RENDER:
Title: {slide['title']}
{f"Subtitle: {slide['subtitle']}" if slide['subtitle'] else ""}

Body:
{slide['body'][:1500]}

SLIDE POSITION:
- This is slide {slide['number']} of {total_slides}
- Decorative lines should flow naturally from previous slide
- {"Lines entering from left edge" if slide['number'] == 1 else ""}
- {"Lines culminating/converging" if slide['number'] == total_slides else ""}

CRITICAL REQUIREMENTS:
1. All text MUST be sharp, legible, and properly rendered
2. Layout MUST be clean and professional
3. Style MUST match the reference images exactly
4. NO placeholder text or "Lorem ipsum"
5. Render the ACTUAL content provided above
6. If logo reference provided, use it EXACTLY - do not modify or recreate
7. Make the slide VISUALLY ENGAGING - minimize text, maximize visual communication
8. Include subtle Conway's Game of Life pattern in background"""

    prompt = f"{system_style}\n\n---\n\n{slide_prompt}"

    try:
        # Build content list with optional reference images
        contents = []

        # Add logo reference first if provided
        if logo_image:
            contents.append("BRAND LOGO - Use this EXACT logo without modification (place in bottom-right corner):")
            contents.append(logo_image)
            contents.append("\n")

        if reference_images and len(reference_images) > 0:
            # Add reference images first
            contents.append("REFERENCE IMAGES - Match this exact visual style:")
            for i, ref_img in enumerate(reference_images[:2]):  # Max 2 reference images
                contents.append(ref_img)
            contents.append("\nNow generate a new slide matching this style:\n")

        contents.append(prompt)

        response = model.generate_content(
            contents=contents,
            generation_config={
                "response_modalities": ["IMAGE"],
            }
        )

        # Extract image from response
        for part in response.parts:
            if hasattr(part, 'inline_data') and part.inline_data:
                return part.inline_data.data

        print(f"  Warning: No image in response for slide {slide['number']}")
        return None

    except Exception as e:
        print(f"  Error generating slide {slide['number']}: {e}")
        return None


def get_resolution(resolution: str) -> tuple:
    """Get target dimensions for resolution."""
    resolutions = {
        '1080p': (1920, 1080),
        '4k': (3840, 2160),
    }
    return resolutions.get(resolution, (3840, 2160))


def save_image(image_data: bytes, output_path: str, target_size: tuple = (3840, 2160)) -> tuple:
    """Save image data to file, fitting into target dimensions with padding.
    Returns (success, original_size) tuple."""
    try:
        # Decode image
        image = Image.open(BytesIO(image_data))

        # Get current dimensions
        orig_width, orig_height = image.size
        orig_size = (orig_width, orig_height)

        # Log actual Gemini output
        aspect = orig_width / orig_height
        print(f"  Gemini output: {orig_width}x{orig_height} (aspect {aspect:.2f})")

        # Target dimensions
        target_width, target_height = target_size

        # If image is already close to target aspect ratio, just resize
        target_aspect = target_width / target_height
        if abs(aspect - target_aspect) < 0.1:
            # Good aspect ratio - resize directly
            image = image.resize(target_size, Image.Resampling.LANCZOS)
            image.save(output_path, 'PNG', optimize=False)
            return True, orig_size

        # Otherwise, fit into target with padding
        scale_w = target_width / orig_width
        scale_h = target_height / orig_height
        scale = min(scale_w, scale_h)

        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)

        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Create white background canvas at target size
        canvas = Image.new('RGB', target_size, (255, 255, 255))

        # Center the image on canvas
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        canvas.paste(image, (x_offset, y_offset))

        canvas.save(output_path, 'PNG', optimize=False)
        return True, orig_size
    except Exception as e:
        print(f"  Error saving image: {e}")
        return False, (0, 0)


def create_pdf(image_paths: list[str], output_path: str):
    """Compile images into a PDF."""
    if not image_paths:
        print("No images to compile into PDF")
        return

    # Get first image to determine size
    first_img = Image.open(image_paths[0])
    width, height = first_img.size

    # Create PDF with custom page size matching image aspect ratio
    c = canvas.Canvas(output_path, pagesize=(width, height))

    for img_path in image_paths:
        c.drawImage(img_path, 0, 0, width, height)
        c.showPage()

    c.save()
    print(f"PDF created: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate slides using Nano Banana (Gemini)')
    parser.add_argument('markdown_file', help='Path to markdown presentation file')
    parser.add_argument('--output-dir', '-o', default='./nano-banana-output',
                        help='Output directory for images')
    parser.add_argument('--test', '-t', type=int, default=0,
                        help='Only generate first N slides for testing')
    parser.add_argument('--model', '-m', default='gemini-3-pro-image-preview',
                        choices=['gemini-2.5-flash-image', 'gemini-2.5-flash-image-preview', 'gemini-3-pro-image-preview'],
                        help='Gemini model to use for image generation (Pro recommended for quality)')
    parser.add_argument('--reference', '-r', default=None,
                        help='Path to reference PDF for style matching')
    parser.add_argument('--logo', '-l', default=None,
                        help='Path to logo image file (PNG/SVG) for brand consistency')
    parser.add_argument('--resolution', default='4k',
                        choices=['1080p', '4k'],
                        help='Output resolution (default: 4k for highest quality)')
    args = parser.parse_args()

    # Check API key
    api_key = os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment")
        sys.exit(1)

    # Configure Gemini
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(args.model)

    # Load reference images if provided
    reference_images = []
    if args.reference:
        print(f"Loading reference: {args.reference}")
        reference_images = load_reference_images(args.reference)

    # Load logo if provided
    logo_image = None
    if args.logo:
        print(f"Loading logo: {args.logo}")
        logo_image = load_logo_image(args.logo)

    # Get target resolution
    target_resolution = get_resolution(args.resolution)
    print(f"Target resolution: {target_resolution[0]}x{target_resolution[1]} ({args.resolution})")

    # Parse markdown
    print(f"Parsing: {args.markdown_file}")
    slides = parse_markdown_slides(args.markdown_file)
    total_slides = len(slides)
    print(f"Found {total_slides} slides")

    # Show slide types detected
    for s in slides:
        print(f"  Slide {s['number']}: {s['type']} - {s['title'][:40]}...")

    # Limit slides if testing
    if args.test > 0:
        slides = slides[:args.test]
        print(f"Testing mode: generating {len(slides)} slides")

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate slides
    image_paths = []
    log = {
        'source': args.markdown_file,
        'model': args.model,
        'reference': args.reference,
        'logo': args.logo,
        'resolution': args.resolution,
        'generated_at': datetime.now().isoformat(),
        'slides': []
    }

    for slide in slides:
        print(f"Generating slide {slide['number']}: {slide['title'][:50]}...")

        image_data = generate_slide_image(slide, model, total_slides, reference_images, logo_image)

        if image_data:
            # Create safe filename
            safe_title = re.sub(r'[^\w\s-]', '', slide['title'])[:30].strip().replace(' ', '-').lower()
            filename = f"slide-{slide['number']:02d}-{safe_title}.png"
            output_path = output_dir / filename

            success, orig_size = save_image(image_data, str(output_path), target_resolution)
            if success:
                image_paths.append(str(output_path))
                print(f"  Saved: {filename}")
                log['slides'].append({
                    'number': slide['number'],
                    'title': slide['title'],
                    'file': filename,
                    'original_size': f"{orig_size[0]}x{orig_size[1]}",
                    'status': 'success'
                })
            else:
                log['slides'].append({
                    'number': slide['number'],
                    'title': slide['title'],
                    'status': 'save_failed'
                })
        else:
            log['slides'].append({
                'number': slide['number'],
                'title': slide['title'],
                'status': 'generation_failed'
            })

    # Create PDF
    if image_paths:
        pdf_path = output_dir / "all-slides.pdf"
        create_pdf(image_paths, str(pdf_path))

    # Save log
    log_path = output_dir / "generation-log.json"
    with open(log_path, 'w') as f:
        json.dump(log, f, indent=2)
    print(f"Log saved: {log_path}")

    # Summary
    successful = len([s for s in log['slides'] if s['status'] == 'success'])
    print(f"\nDone! {successful}/{len(slides)} slides generated successfully")
    print(f"Output: {output_dir}")


if __name__ == '__main__':
    main()
