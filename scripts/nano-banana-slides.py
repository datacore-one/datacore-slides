#!/usr/bin/env python3
"""
Nano Banana Slide Generator

Generate presentation slides as images using Google's Gemini (Nano Banana) API.
Saves images locally and compiles into PDF.

Usage:
    python nano-banana-slides.py <markdown_file> [--output-dir <dir>] [--test <n>]
    python nano-banana-slides.py --rebuild-pdf <slides_dir> [--add-logo <logo>] [--pdf-name <name>]

Example:
    python nano-banana-slides.py presentation.md --output-dir ./slides --test 3
    python nano-banana-slides.py --rebuild-pdf ./slides --add-logo logo.svg --pdf-name my-deck
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
- Split content into two clear columns based on the actual content provided
- Use subtle visual divider between columns
- Both columns should have equal visual weight
- Do NOT invent column headings - only use headings from the actual content
- Do NOT add content that is not in the source material"""

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
- SMALL font size for bullet text (body text should be noticeably smaller than title)
- Generous spacing between items - use whitespace liberally
- At least 40% of the slide area should be empty white space
- Group related items visually
- Section headers should be slightly emphasized but not oversized"""

    else:
        return """LAYOUT TYPE: STANDARD
- Title prominent at top
- Content balanced and readable
- Key callouts or highlights styled consistently
- Clean visual hierarchy"""


def generate_slide_image(slide: dict, model, total_slides: int = 7, reference_images: list = None, logo_image = None, portrait: bool = False) -> bytes:
    """Generate a slide image using Gemini API."""

    slide_type = slide.get('type', 'standard')
    slide_type_instructions = get_slide_type_instructions(slide_type)

    # System style description (consistent across all slides)
    if portrait:
        orientation_instruction = """ASPECT RATIO CRITICAL: Output image must be taller than wide — portrait orientation (height:width ratio approximately 1.41:1, like 768x1087 or 864x1232). NOT landscape. NOT square. This is a printed document page, NOT a presentation slide. Do NOT add any format labels, watermarks, orientation text, or instruction text as visible content on the image.

PORTRAIT DOCUMENT COLOR RULES (override system color defaults):
- Section headings / section labels: dark charcoal #2a2a2a — small uppercase, letter-spaced
- Body text: dark charcoal #2a2a2a
- Title: dark charcoal #1a1a1a
- Background: soft and airy — gentle pastel gradient orbs in corners (pale blue, soft peach, light lavender), mostly white in the center so text is fully readable. Subtle, not busy.
- Accent lines (hairlines, rules): light gray #d0d0d0
- Follow the slide's design notes for any color overrides"""
        layout_instruction = "Portrait document format (taller than wide). Full-page document layout — use the full height. Content flows top to bottom. No format labels or watermarks on the image."
    else:
        orientation_instruction = """Generate a WIDE presentation slide image. CRITICAL: Output must be 16:9 LANDSCAPE aspect ratio (width much greater than height, like 1920x1080 or 1456x816). NOT square. NOT portrait."""
        layout_instruction = "WIDE 16:9 landscape format (NOT square)\n- Generous margins (100px+)\n- Content left-aligned\n- Simple diagram or icon on right if needed\n- Fine delicate lines for any connections\n- 80%+ empty space"

    system_style = f"""{orientation_instruction}

BRAND: Organization - data tokenization company.

LOGO: DO NOT draw any logo, brand mark, or icon in the corner. Leave the bottom-right corner completely empty - the real logo will be added in post-processing.

DESIGN PHILOSOPHY:
- Ultra-minimal, refined, premium (like Apple keynotes)
- MASSIVE negative space (80%+ of slide should be empty white/light space)
- ONE simple visual element per slide maximum
- Text should be sparse and elegant - let whitespace communicate
- Soft, calming, refined aesthetic

COLORS (CRITICAL - SOFT AND MUTED ONLY):
- Background: Pure white (#FFFFFF) with SOFT GRADIENT ORBS
- Background orbs: Pale blue (#E8F0FE), soft cyan (#B8E0E8), soft peach (#FFF0E8), soft lavender
- Orbs should be very subtle, semi-transparent, floating gently
- Text: Black (#000000) - Regular weight only, NOT bold
- NO intense or saturated colors anywhere
- NO mint green, NO bright colors

TYPOGRAPHY:
- Sans-serif (Inter/Helvetica style)
- Title: Medium size, Regular weight (NOT bold), top-left aligned
- Body: SMALL elegant font size, Regular weight only
- 3-5 bullet points MAX or one short paragraph
- NO bold text anywhere - everything Regular weight
- Prioritize readability through whitespace, not large fonts

BACKGROUND STYLE - "Soft Gradient Orbs":
- Gentle, soft gradient orbs floating in background
- Colors: pale blue, soft peach, light lavender, soft cyan
- Orbs should be semi-transparent, blurred edges, dreamy quality
- Some larger, some smaller - organic arrangement
- Must NOT interfere with readability - very subtle
- Creates refined, calming, premium atmosphere

LAYOUT:
- {layout_instruction}

VISUAL STYLE:
- Fine, delicate line work
- Soft, muted colors only
- Simple circle diagrams with thin lines
- NO complex infographics
- NO stock photo style imagery
- Refined and elegant, not tech-heavy

FORBIDDEN:
- Square aspect ratio
- Bold text anywhere
- Intense/saturated colors (no mint green, bright blue, etc.)
- Dense text blocks
- Complex multi-element diagrams
- Drawing ANY logo, brand mark, or icon
- Busy or cluttered layouts
- Large/oversized fonts
- Heavy line weights"""

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
        '8k': (7680, 4320),
        'portrait-a4': (2160, 3054),   # A4 portrait at ~4K height (ratio 1:1.414)
        'portrait-hq': (3508, 4961),   # A4 portrait at 300 DPI (true print quality)
    }
    return resolutions.get(resolution, (3840, 2160))


def detect_canvas_bg(image: "Image") -> tuple:
    """Detect canvas background color by averaging the four corners of the image."""
    img = image.convert('RGB')
    w, h = img.size
    sample = 10
    corners = [
        img.crop((0, 0, sample, sample)),
        img.crop((w - sample, 0, w, sample)),
        img.crop((0, h - sample, sample, h)),
        img.crop((w - sample, h - sample, w, h)),
    ]
    pixels = []
    for corner in corners:
        pixels.extend(list(corner.getdata()))
    avg_r = sum(p[0] for p in pixels) // len(pixels)
    avg_g = sum(p[1] for p in pixels) // len(pixels)
    avg_b = sum(p[2] for p in pixels) // len(pixels)
    return (avg_r, avg_g, avg_b)


def save_image(image_data: bytes, output_path: str, target_size: tuple = (3840, 2160), canvas_bg: tuple = None) -> tuple:
    """Save image data to file, fitting into target dimensions with padding.
    canvas_bg: RGB tuple for padding. If None, auto-detected from image corners.
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

        # Auto-detect canvas background from image corners if not specified
        if canvas_bg is None:
            canvas_bg = detect_canvas_bg(image)
            print(f"  Canvas bg: auto-detected {canvas_bg}")

        # Create background canvas at target size
        canvas = Image.new('RGB', target_size, canvas_bg)

        # Center the image on canvas
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        canvas.paste(image, (x_offset, y_offset))

        canvas.save(output_path, 'PNG', optimize=False)
        return True, orig_size
    except Exception as e:
        print(f"  Error saving image: {e}")
        return False, (0, 0)


def create_pdf(image_paths: list[str], output_path: str, page_width: float = None):
    """Compile images into a PDF.

    Args:
        page_width: PDF page width in points (1 pt = 1/72 inch).
                    Default None uses A4 landscape width (842 pt).
    """
    if not image_paths:
        print("No images to compile into PDF")
        return

    # A4 landscape width = 297mm = 842 points
    if page_width is None:
        page_width = 842.0

    # Get first image to determine aspect ratio
    first_img = Image.open(image_paths[0])
    img_w, img_h = first_img.size
    aspect = img_w / img_h

    # Scale page to target width, maintaining aspect ratio
    page_height = page_width / aspect

    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))

    for img_path in image_paths:
        c.drawImage(img_path, 0, 0, page_width, page_height)
        c.showPage()

    c.save()
    print(f"PDF created: {output_path} ({page_width:.0f}x{page_height:.0f} pt)")


def add_logo_to_image(image_path: str, logo_path: str, logo_height: int = 160, margin_pct: float = 0.03):
    """Overlay logo on an image in the bottom-right corner with transparency.

    Args:
        image_path: Path to the slide image (PNG)
        logo_path: Path to logo file (SVG or PNG)
        logo_height: Logo height in pixels (width auto-calculated from aspect ratio)
        margin_pct: Margin as percentage of image dimensions (default 3%)
    """
    # Load the slide image
    slide = Image.open(image_path).convert('RGBA')
    slide_w, slide_h = slide.size

    # Load logo - handle SVG via cairosvg
    if logo_path.lower().endswith('.svg'):
        try:
            import cairosvg
            # Render SVG to PNG at target height
            png_data = cairosvg.svg2png(url=logo_path, output_height=logo_height)
            logo = Image.open(BytesIO(png_data)).convert('RGBA')
        except ImportError:
            print("  Warning: cairosvg not installed for SVG support. Run: pip install cairosvg")
            return False
    else:
        logo = Image.open(logo_path).convert('RGBA')
        # Resize to target height maintaining aspect ratio
        logo_w, logo_h = logo.size
        scale = logo_height / logo_h
        logo = logo.resize((int(logo_w * scale), logo_height), Image.Resampling.LANCZOS)

    # Calculate position: bottom-right with margin
    margin_x = int(slide_w * margin_pct)
    margin_y = int(slide_h * margin_pct)
    logo_w, logo_h = logo.size
    x = slide_w - logo_w - margin_x
    y = slide_h - logo_h - margin_y

    # Composite with alpha transparency
    slide.paste(logo, (x, y), logo)

    # Save back as RGB PNG
    slide.convert('RGB').save(image_path, 'PNG', optimize=False)
    return True


def rebuild_pdf_from_directory(slides_dir: str, pdf_name: str, logo_path: str = None, logo_height: int = 160):
    """Rebuild PDF from existing PNGs in a directory.

    Args:
        slides_dir: Directory containing slide PNGs (sorted alphabetically)
        pdf_name: PDF filename without extension
        logo_path: Optional logo to overlay on each slide before PDF compilation
        logo_height: Logo height in pixels
    """
    slides_path = Path(slides_dir)
    if not slides_path.is_dir():
        print(f"Error: {slides_dir} is not a directory")
        return

    # Find all PNGs, sorted by name
    png_files = sorted(slides_path.glob("*.png"))
    if not png_files:
        print(f"Error: No PNG files found in {slides_dir}")
        return

    print(f"Found {len(png_files)} slides in {slides_dir}")

    # Add logo to each slide if requested
    if logo_path:
        print(f"Adding logo: {logo_path} (height: {logo_height}px)")
        for png in png_files:
            success = add_logo_to_image(str(png), logo_path, logo_height)
            if success:
                print(f"  Logo added: {png.name}")
            else:
                print(f"  Logo failed: {png.name}")

    # Build PDF
    image_paths = [str(p) for p in png_files]
    pdf_path = slides_path / f"{pdf_name}.pdf"
    create_pdf(image_paths, str(pdf_path))
    print(f"PDF rebuilt: {pdf_path}")


def main():
    parser = argparse.ArgumentParser(description='Generate slides using Nano Banana (Gemini)')
    parser.add_argument('markdown_file', nargs='?', default=None,
                        help='Path to markdown presentation file')
    parser.add_argument('--output-dir', '-o', default='./nano-banana-output',
                        help='Output directory for images')
    parser.add_argument('--test', '-t', type=int, default=0,
                        help='Only generate first N slides for testing')
    parser.add_argument('--model', '-m', default='gemini-3.1-flash-image-preview',
                        choices=['gemini-2.5-flash-image', 'gemini-2.5-flash-image-preview', 'gemini-3-pro-image-preview', 'gemini-3.1-flash-image-preview'],
                        help='Gemini model to use (default: gemini-3.1-flash-image-preview = Nano Banana 2)')
    parser.add_argument('--reference', '-r', default=None,
                        help='Path to reference PDF for style matching')
    parser.add_argument('--logo', '-l', default=None,
                        help='Path to logo image for Gemini reference (unreliable - logo is passed to '
                             'Gemini but the system prompt says "don\'t draw logos"). '
                             'Use --add-logo for reliable post-processing logo placement.')
    parser.add_argument('--add-logo', default=None,
                        help='Path to logo file (SVG or PNG) to overlay in post-processing. '
                             'Placed bottom-right with transparency. Recommended over --logo.')
    parser.add_argument('--logo-height', type=int, default=160,
                        help='Logo height in pixels for --add-logo (default: 160, good for 4K)')
    parser.add_argument('--resolution', default='4k',
                        choices=['1080p', '4k', '8k', 'portrait-a4', 'portrait-hq'],
                        help='Output resolution (default: 4k for highest quality). Use portrait-a4 or portrait-hq for A4 portrait one-pagers.')
    parser.add_argument('--portrait', action='store_true',
                        help='Generate in portrait orientation (A4 format). Automatically sets resolution to portrait-a4.')
    parser.add_argument('--pdf-name', '-p', default=None,
                        help='PDF filename (without extension). Defaults to markdown filename.')
    parser.add_argument('--rebuild-pdf', default=None, metavar='SLIDES_DIR',
                        help='Skip generation, rebuild PDF from existing PNGs in directory. '
                             'Combine with --add-logo to add logos before compilation.')
    args = parser.parse_args()

    # Handle --rebuild-pdf mode (no generation, just recompile)
    if args.rebuild_pdf:
        pdf_name = args.pdf_name or 'all-slides'
        rebuild_pdf_from_directory(args.rebuild_pdf, pdf_name, args.add_logo, args.logo_height)
        return

    # Normal generation mode requires markdown file
    if not args.markdown_file:
        parser.error("markdown_file is required (unless using --rebuild-pdf)")

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

    # Load logo if provided (for Gemini reference - unreliable)
    logo_image = None
    if args.logo:
        print(f"Loading logo for Gemini reference: {args.logo}")
        logo_image = load_logo_image(args.logo)

    # Portrait mode: auto-set resolution
    portrait_mode = args.portrait or args.resolution in ('portrait-a4', 'portrait-hq')
    if portrait_mode and args.resolution == '4k':
        args.resolution = 'portrait-hq'

    # Get target resolution
    target_resolution = get_resolution(args.resolution)
    print(f"Target resolution: {target_resolution[0]}x{target_resolution[1]} ({args.resolution})")
    if portrait_mode:
        print("Portrait mode: ON (A4 format)")

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

        image_data = generate_slide_image(slide, model, total_slides, reference_images, logo_image, portrait=portrait_mode)

        # Auto-retry if portrait mode but Gemini generated landscape
        if image_data and portrait_mode:
            from io import BytesIO as _BytesIO
            from PIL import Image as _Image
            _chk = _Image.open(_BytesIO(image_data))
            _w, _h = _chk.size
            if _w > _h:
                print(f"  Wrong orientation ({_w}x{_h} is landscape) — retrying for portrait...")
                image_data = generate_slide_image(slide, model, total_slides, reference_images, logo_image, portrait=portrait_mode)

        if image_data:
            # Create safe filename
            safe_title = re.sub(r'[^\w\s-]', '', slide['title'])[:30].strip().replace(' ', '-').lower()
            filename = f"slide-{slide['number']:02d}-{safe_title}.png"
            output_path = output_dir / filename

            # Auto-detect canvas background from image corners (handles both dark and light slides)
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

    # Post-processing: add logo overlay if requested
    if args.add_logo and image_paths:
        print(f"\nPost-processing: adding logo from {args.add_logo}")
        for img_path in image_paths:
            success = add_logo_to_image(img_path, args.add_logo, args.logo_height)
            if success:
                print(f"  Logo added: {Path(img_path).name}")
            else:
                print(f"  Logo failed: {Path(img_path).name}")

    # Create PDF
    if image_paths:
        if args.pdf_name:
            pdf_name = args.pdf_name
        else:
            pdf_name = Path(args.markdown_file).stem
        pdf_path = output_dir / f"{pdf_name}.pdf"
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
