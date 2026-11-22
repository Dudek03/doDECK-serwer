from flask import Blueprint, send_file, Response
from PIL import Image, ImageOps

image_bp = Blueprint("image", __name__)


def changeIconColor(image_path: str, color: str) -> None:
    """Recolors a grayscale icon using the specified color."""
    img = Image.open(f"{image_path}.png").convert("L")
    img_colored = ImageOps.colorize(img, black=color, white="white")
    img_colored.save(f"{image_path}_{color}.png")


def giveIconTexture(icon_path: str, texture_path: str) -> None:
    """Applies a texture image to an icon using alpha masking."""
    icon = Image.open(f"{icon_path}.png").convert("L")
    texture = Image.open(f"{texture_path}.png").convert("RGBA")
    texture = texture.resize(icon.size)
    result = Image.new("RGBA", icon.size)
    result.paste(texture, (0, 0), mask=icon)
    result.save(f"{icon_path}_{texture_path}.png")


@image_bp.route("/getImage", methods=["POST"])
def get_image() -> Response:
    """Returns example image file."""
    return send_file("example.png", mimetype="image/png")
