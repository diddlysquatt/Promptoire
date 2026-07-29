"""Build Product Hunt images from Promptoire's real documentation screenshots."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "assets" / "product-hunt"
FONT_REGULAR = Path(r"C:\Windows\Fonts\segoeui.ttf")
FONT_SEMIBOLD = Path(r"C:\Windows\Fonts\seguisb.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\segoeuib.ttf")


def font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def gradient_canvas() -> Image.Image:
    base = Image.new("RGBA", (1270, 760), "#0d0c18")
    glow = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(glow)
    draw.ellipse((690, -260, 1450, 520), fill=(0, 229, 199, 70))
    draw.ellipse((-340, 350, 570, 1160), fill=(213, 45, 120, 70))
    draw.ellipse((250, -380, 1080, 410), fill=(112, 41, 215, 45))
    glow = glow.filter(ImageFilter.GaussianBlur(125))
    return Image.alpha_composite(base, glow)


def paste_window(
    canvas: Image.Image,
    image_path: Path,
    box: tuple[int, int, int, int],
    accent: str,
) -> None:
    image = Image.open(image_path).convert("RGBA")
    left, top, max_width, max_height = box
    scale = min(max_width / image.width, max_height / image.height)
    size = (round(image.width * scale), round(image.height * scale))
    image = image.resize(size, Image.Resampling.LANCZOS)
    x = left + (max_width - size[0]) // 2
    y = top + (max_height - size[1]) // 2

    shadow = Image.new("RGBA", (size[0] + 80, size[1] + 80), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle(
        (40, 35, 40 + size[0], 35 + size[1]),
        radius=24,
        fill=(0, 0, 0, 215),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(24))
    canvas.alpha_composite(shadow, (x - 40, y - 35))

    border = Image.new("RGBA", (size[0] + 6, size[1] + 6), (0, 0, 0, 0))
    border_draw = ImageDraw.Draw(border)
    border_draw.rounded_rectangle(
        (0, 0, size[0] + 5, size[1] + 5),
        radius=16,
        fill=accent,
    )
    border.alpha_composite(image, (3, 3))
    canvas.alpha_composite(border, (x - 3, y - 3))


def build_thumbnail() -> None:
    icon_path = (
        ROOT
        / "icons"
        / "replicate-prediction-2j5y20xssnrmc0crx40tp1mzjc.ico"
    )
    icon = Image.open(icon_path).convert("RGBA")
    icon.thumbnail((190, 190), Image.Resampling.LANCZOS)

    thumbnail = Image.new("RGBA", (240, 240), "#11101e")
    glow = Image.new("RGBA", thumbnail.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse((18, 18, 222, 222), fill=(46, 232, 193, 100))
    glow = glow.filter(ImageFilter.GaussianBlur(34))
    thumbnail = Image.alpha_composite(thumbnail, glow)

    draw = ImageDraw.Draw(thumbnail)
    draw.rounded_rectangle(
        (16, 16, 224, 224),
        radius=48,
        fill="#171527",
        outline="#39e5c1",
        width=3,
    )
    thumbnail.alpha_composite(
        icon,
        ((240 - icon.width) // 2, (240 - icon.height) // 2),
    )
    thumbnail.convert("RGB").save(
        OUTPUT / "promptoire-thumbnail-240.png",
        quality=95,
    )


def build_launcher_gallery() -> None:
    image = gradient_canvas()
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (68, 64, 335, 112),
        radius=24,
        fill="#1a1830",
        outline="#3ae4c0",
        width=2,
    )
    draw.text(
        (91, 76),
        "PROMPTOIRE  •  WINDOWS",
        font=font(FONT_SEMIBOLD, 18),
        fill="#eafdf8",
    )
    draw.text(
        (68, 165),
        "Your prompt library,",
        font=font(FONT_BOLD, 48),
        fill="#ffffff",
    )
    draw.text(
        (68, 222),
        "one hotkey away.",
        font=font(FONT_BOLD, 54),
        fill="#43ebc6",
    )
    draw.text(
        (72, 330),
        "Search  •  Fill  •  Copy",
        font=font(FONT_SEMIBOLD, 27),
        fill="#f4f2fb",
    )
    y = 405
    for item in (
        "Text and image prompts together",
        "Local-first with no telemetry",
        "Free and open source",
    ):
        draw.ellipse((74, y + 9, 88, y + 23), fill="#f54c91")
        draw.text(
            (106, y),
            item,
            font=font(FONT_REGULAR, 24),
            fill="#d9d6e7",
        )
        y += 58

    paste_window(
        image,
        ROOT / "docs" / "assets" / "promptoire-launcher.png",
        (690, 75, 500, 620),
        "#39e5c1",
    )
    draw.text(
        (70, 682),
        "Promptoire 2.3.0",
        font=font(FONT_SEMIBOLD, 19),
        fill="#8f8aa5",
    )
    image.convert("RGB").save(
        OUTPUT / "promptoire-gallery-01-launcher.png",
        quality=95,
    )


def build_workflow_gallery() -> None:
    image = gradient_canvas()
    draw = ImageDraw.Draw(image)
    draw.text(
        (62, 44),
        "Organize locally. Improve with any LLM.",
        font=font(FONT_BOLD, 42),
        fill="#ffffff",
    )
    draw.text(
        (64, 102),
        "Drag, filter, export, preview, and safely merge — your library stays yours.",
        font=font(FONT_REGULAR, 23),
        fill="#c9c5d8",
    )
    paste_window(
        image,
        ROOT / "docs" / "assets" / "promptoire-edit-library.png",
        (80, 175, 470, 500),
        "#f24e93",
    )
    paste_window(
        image,
        ROOT / "docs" / "assets" / "promptoire-improve-library.png",
        (720, 175, 470, 500),
        "#39e5c1",
    )

    draw.rounded_rectangle((143, 678, 487, 728), radius=25, fill="#1a1830")
    draw.text(
        (213, 690),
        "Edit Library",
        font=font(FONT_SEMIBOLD, 21),
        fill="#f7f4fb",
    )
    draw.rounded_rectangle((783, 678, 1127, 728), radius=25, fill="#1a1830")
    draw.text(
        (846, 690),
        "Improve Library",
        font=font(FONT_SEMIBOLD, 21),
        fill="#f7f4fb",
    )
    image.convert("RGB").save(
        OUTPUT / "promptoire-gallery-02-workflow.png",
        quality=95,
    )


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    build_thumbnail()
    build_launcher_gallery()
    build_workflow_gallery()
    for path in sorted(OUTPUT.glob("*.png")):
        with Image.open(path) as image:
            print(f"{path.name}: {image.width}x{image.height}, {path.stat().st_size} bytes")


if __name__ == "__main__":
    main()
