from pathlib import Path
import qrcode
import qrcode.image.svg

from app.core.config import settings


BASE_DIR = Path(__file__).resolve().parents[2]  # backend/
QR_DIR = BASE_DIR / "generated" / "qr"
QR_DIR.mkdir(parents=True, exist_ok=True)


def build_mix_url(slug: str) -> str:
    return f"{settings.base_public_url}/mixes/{slug}"


def generate_qr_assets(slug: str) -> tuple[str, str]:
    url = build_mix_url(slug)

    png_path = QR_DIR / f"{slug}.png"
    svg_path = QR_DIR / f"{slug}.svg"

    img = qrcode.make(url)
    img.save(png_path)

    factory = qrcode.image.svg.SvgImage
    svg_img = qrcode.make(url, image_factory=factory)
    with open(svg_path, "wb") as f:
        svg_img.save(f)

    return str(png_path), str(svg_path)
