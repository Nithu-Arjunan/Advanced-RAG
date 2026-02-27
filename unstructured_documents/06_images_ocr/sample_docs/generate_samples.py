"""
Generate sample images with text for OCR extraction demos.

Creates three PNG images that simulate different scan qualities:
1. simple_text.png     - Clean black text on white background
2. multi_paragraph.png - Multi-paragraph letter/document layout
3. noisy_text.png      - Simulated low-quality scan with random noise

Uses Pillow's default font so it works on any system without external font files.
"""

import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SAMPLE_DIR = Path(__file__).parent


def get_font(size: int = 16) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font, falling back to Pillow's built-in default if needed."""
    # Try a few common system fonts first (better text rendering if available)
    font_candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSText.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]
    for font_path in font_candidates:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError):
            continue

    # Fall back to Pillow's built-in default
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        # Older Pillow versions don't accept size for load_default
        return ImageFont.load_default()


def wrap_text(text: str, font: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Word-wrap text to fit within a pixel width."""
    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=font)
        if bbox[2] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    return lines


def generate_simple_text() -> Path:
    """
    Generate a clean image with a paragraph of text.
    Simulates a well-scanned document page.
    """
    width, height = 800, 600
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = get_font(18)

    text = (
        "Artificial Intelligence (AI) is the simulation of human intelligence "
        "processes by computer systems. These processes include learning, "
        "reasoning, and self-correction. AI applications include expert systems, "
        "natural language processing, speech recognition, and machine vision."
    )

    margin = 60
    max_width = width - 2 * margin
    lines = wrap_text(text, font, max_width, draw)

    y = 80
    for line in lines:
        draw.text((margin, y), line, fill="black", font=font)
        y += 30

    path = SAMPLE_DIR / "simple_text.png"
    img.save(path)
    print(f"  Created: {path.name} ({width}x{height})")
    return path


def generate_multi_paragraph() -> Path:
    """
    Generate a multi-paragraph document image.
    Simulates a scanned letter with sender, recipient, subject, and body.
    """
    width, height = 800, 1000
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = get_font(16)
    bold_font = get_font(18)

    margin = 60
    max_width = width - 2 * margin
    y = 60

    # Header fields
    headers = [
        "From: Dr. Sarah Chen, AI Research Division",
        "To: Department of Computer Science Faculty",
        "Subject: Annual Review of Machine Learning Progress",
        "Date: January 15, 2025",
    ]
    for header in headers:
        draw.text((margin, y), header, fill="black", font=bold_font)
        y += 32

    y += 30  # Extra space after headers

    # Paragraph 1
    para1 = (
        "Dear Colleagues, I am writing to share the findings from our annual review "
        "of machine learning research progress. Over the past year, our department has "
        "made significant strides in several key areas including natural language "
        "understanding, computer vision, and reinforcement learning. The results have "
        "been published in top-tier conferences and journals."
    )
    lines = wrap_text(para1, font, max_width, draw)
    for line in lines:
        draw.text((margin, y), line, fill="black", font=font)
        y += 26

    y += 26  # Paragraph spacing

    # Paragraph 2
    para2 = (
        "Looking ahead to the next fiscal year, we plan to expand our research into "
        "multimodal learning systems that combine text, image, and audio processing. "
        "We have secured additional funding from three industry partners and expect "
        "to hire four new postdoctoral researchers. The budget allocation for computing "
        "resources has been increased by forty percent to support large-scale experiments "
        "with foundation models."
    )
    lines = wrap_text(para2, font, max_width, draw)
    for line in lines:
        draw.text((margin, y), line, fill="black", font=font)
        y += 26

    y += 26

    # Closing
    draw.text((margin, y), "Best regards,", fill="black", font=font)
    y += 30
    draw.text((margin, y), "Dr. Sarah Chen", fill="black", font=font)

    path = SAMPLE_DIR / "multi_paragraph.png"
    img.save(path)
    print(f"  Created: {path.name} ({width}x{height})")
    return path


def generate_noisy_text() -> Path:
    """
    Generate a noisy version of the simple text image.
    Simulates a low-quality scan with random pixel noise.
    """
    width, height = 800, 600
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = get_font(18)

    text = (
        "Artificial Intelligence (AI) is the simulation of human intelligence "
        "processes by computer systems. These processes include learning, "
        "reasoning, and self-correction. AI applications include expert systems, "
        "natural language processing, speech recognition, and machine vision."
    )

    margin = 60
    max_width = width - 2 * margin
    lines = wrap_text(text, font, max_width, draw)

    y = 80
    for line in lines:
        draw.text((margin, y), line, fill="black", font=font)
        y += 30

    # Add random noise to simulate a low-quality scan
    pixels = img.load()
    random.seed(42)  # Reproducible noise
    num_noise_pixels = int(width * height * 0.03)  # 3% noise coverage

    for _ in range(num_noise_pixels):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        # Random gray/dark noise
        gray = random.randint(0, 180)
        pixels[x, y] = (gray, gray, gray)

    # Add some larger blotches to simulate scan artifacts
    for _ in range(20):
        cx = random.randint(0, width - 1)
        cy = random.randint(0, height - 1)
        radius = random.randint(1, 3)
        gray = random.randint(100, 200)
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < width and 0 <= ny < height:
                    pixels[nx, ny] = (gray, gray, gray)

    path = SAMPLE_DIR / "noisy_text.png"
    img.save(path)
    print(f"  Created: {path.name} ({width}x{height}, with noise)")
    return path


if __name__ == "__main__":
    print("Generating sample images for OCR demos...")
    print()
    generate_simple_text()
    generate_multi_paragraph()
    generate_noisy_text()
    print()
    print("Done! All sample images are in:", SAMPLE_DIR)
