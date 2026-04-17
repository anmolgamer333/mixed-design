from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse
import qrcode
import qrcode.image.svg

from app.core.config import settings


BASE_DIR = Path(__file__).resolve().parents[2]  # backend/
QR_DIR = BASE_DIR / "generated" / "qr"
QR_DIR.mkdir(parents=True, exist_ok=True)


def build_mix_url(slug: str) -> str:
    base = settings.base_public_url.rstrip("/")
    parsed = urlparse(base)

    if parsed.scheme and parsed.netloc:
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        query["slug"] = slug
        return urlunparse(parsed._replace(query=urlencode(query)))

    return f"{base}?slug={slug}"


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
