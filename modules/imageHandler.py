from flask import Blueprint, send_file
from PIL import Image, ImageOps

image_bp = Blueprint('image', __name__)

def changeIconColor(imagePath, color): 
  img = Image.open(f"{imagePath}.png").convert("L")  
  img_colored = ImageOps.colorize(img, black=color, white="white")  
  img_colored.save(f"{imagePath}_{color}.png")
  
def giveIconTexture(iconPath, texturePath):
  icon = Image.open(f"{iconPath}.png").convert("L") 
  texture = Image.open(f"{texturePath}.png").convert("RGBA") 
  texture = texture.resize(icon.size)
  result = Image.new("RGBA", icon.size)
  result.paste(texture, (0, 0), mask=icon)
  result.save(f"{iconPath}_{texturePath}.png")

@image_bp.route('/getImage', methods = ['POST'])
def get_image():
    return send_file("example.png", mimetype="image/png")