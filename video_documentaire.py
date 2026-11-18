"""Rend un documentaire éditorial en vidéo MP4 originale, sans images externes."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1280, 720
BACKGROUND = (245, 243, 235)
INK = (35, 49, 40)
MUTED = (91, 105, 94)
GREEN = (48, 83, 61)
GOLD = (166, 126, 78)


def _font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold
        else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).is_file():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def _wrap(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    lines = []
    for paragraph in str(text).splitlines() or [""]:
        words = paragraph.split()
        current = ""
        for word in words:
            candidate = f"{current} {word}".strip()
            if current and draw.textlength(candidate, font=font) > max_width:
                lines.append(current)
                current = word
            else:
                current = candidate
        if current:
            lines.append(current)
        elif not words:
            lines.append("")
    return lines


def creer_diapositive(label: str, title: str, body: str, destination: Path) -> Path:
    """Crée une diapositive 16:9 avec une identité graphique propre au projet."""
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)
    # Cadre et motif circulaire dessinés localement : aucune ressource distante.
    draw.rectangle((0, 0, 18, HEIGHT), fill=GREEN)
    for radius in (90, 145, 200):
        draw.ellipse((WIDTH - radius - 55, 65, WIDTH + radius - 55, 65 + 2 * radius),
                     outline=(218, 224, 211), width=3)
    draw.text((92, 78), "OBSERVATOIRE", font=_font(22, True), fill=GREEN)
    draw.text((92, 145), label.upper()[:70], font=_font(17, True), fill=GOLD)
    title_font = _font(43, True)
    title_lines = _wrap(draw, title, title_font, 1040)
    y = 205
    for line in title_lines[:3]:
        draw.text((92, y), line, font=title_font, fill=INK)
        y += 58
    y += 28
    body_font = _font(25)
    for line in _wrap(draw, body, body_font, 1050)[:9]:
        draw.text((96, y), line, font=body_font, fill=MUTED)
        y += 39
    draw.line((92, 635, 1188, 635), fill=(211, 217, 207), width=2)
    draw.text((92, 657), "TECHNOLOGIE  ·  INTELLIGENCE ARTIFICIELLE  ·  JEUX VIDÉO",
              font=_font(14, True), fill=GREEN)
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, format="PNG", optimize=True)
    return destination


def generer_video(audio_path: Path, slides: list[tuple[str, str, str]], output_path: Path) -> Path:
    """Assemble les diapositives et la narration en MP4 H.264/AAC."""
    audio_path = Path(audio_path)
    output_path = Path(output_path)
    if not audio_path.is_file() or audio_path.stat().st_size < 1000:
        raise ValueError("La narration audio est absente ou trop petite.")
    if not slides:
        raise ValueError("Aucune diapositive à rendre.")
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("FFmpeg et FFprobe doivent être installés pour produire le MP4.")

    probe = subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        check=True, capture_output=True, text=True, timeout=30,
    )
    duration = float(probe.stdout.strip())
    if duration <= 0:
        raise RuntimeError("Durée audio invalide.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="observatoire-video-") as temporary:
        temp = Path(temporary)
        image_paths = []
        for index, (label, title, body) in enumerate(slides, 1):
            target = temp / f"slide-{index:02d}.png"
            creer_diapositive(label, title, body, target)
            image_paths.append(target)

        per_slide = duration / len(image_paths)
        concat = temp / "slides.txt"
        lines = []
        for path in image_paths:
            safe_path = str(path).replace("'", "'\\''")
            lines.extend((f"file '{safe_path}'", f"duration {per_slide:.6f}"))
        lines.append(f"file '{str(image_paths[-1])}'")
        concat.write_text("\n".join(lines) + "\n", encoding="utf-8")

        subprocess.run(
            [ffmpeg, "-hide_banner", "-loglevel", "error", "-y",
             "-f", "concat", "-safe", "0", "-i", str(concat),
             "-i", str(audio_path),
             "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,"
                    "pad=1280:720:(ow-iw)/2:(oh-ih)/2,format=yuv420p",
             "-r", "24", "-c:v", "libx264", "-preset", "veryfast", "-crf", "27",
             "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
             "-shortest", str(output_path)],
            check=True, capture_output=True, text=True, timeout=900,
        )

    if not output_path.is_file() or output_path.stat().st_size < 10_000:
        raise RuntimeError("Le rendu MP4 est absent ou incomplet.")
    return output_path
