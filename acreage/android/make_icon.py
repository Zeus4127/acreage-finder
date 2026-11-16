"""Draws the Acreage Finder launcher icon at every Android size: blue sky with birds, a green mountain range,
green farmland with a fence, a farmer in an Akubra-style hat and a red cattle dog sitting beside him."""
import os
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))

def draw(n):
    S = 1024
    im = Image.new("RGBA", (S, S)); d = ImageDraw.Draw(im)
    for y in range(S):                                                          # sky: deeper blue at the top
        t = y / S; d.line([(0, y), (S, y)], fill=(int(70 + 90 * t), int(150 + 70 * t), int(225 + 25 * t)))
    d.ellipse([700, 110, 860, 270], fill=(255, 214, 90))                         # sun
    for x, y, s in ((210, 200, 34), (300, 160, 26), (380, 230, 22), (560, 140, 18)):   # birds
        d.arc([x - s, y - s // 2, x, y + s // 2], 200, 340, fill=(40, 55, 70), width=9)
        d.arc([x, y - s // 2, x + s, y + s // 2], 200, 340, fill=(40, 55, 70), width=9)
    d.polygon([(0, 560), (150, 380), (260, 470), (420, 300), (560, 450), (700, 330), (860, 470), (1024, 360), (1024, 640), (0, 640)], fill=(94, 140, 120))    # far range
    d.polygon([(0, 640), (180, 470), (330, 560), (520, 430), (690, 560), (850, 470), (1024, 560), (1024, 700), (0, 700)], fill=(60, 120, 88))             # near range
    d.ellipse([-300, 600, 1300, 1400], fill=(110, 180, 80))                      # farmland
    d.ellipse([-200, 690, 1400, 1500], fill=(78, 155, 65))
    for x in range(40, 1024, 120):                                               # fence
        d.rectangle([x, 640, x + 16, 740], fill=(250, 244, 225))
    d.rectangle([20, 665, 1024, 680], fill=(250, 244, 225)); d.rectangle([20, 705, 1024, 720], fill=(250, 244, 225))
    # farmer (left of centre): boots, jeans, checked shirt, arms, face, hat
    fx = 330
    d.rectangle([fx - 55, 860, fx - 10, 960], fill=(52, 76, 120)); d.rectangle([fx + 10, 860, fx + 55, 960], fill=(52, 76, 120))
    d.rounded_rectangle([fx - 62, 950, fx - 5, 980], 10, fill=(90, 58, 36)); d.rounded_rectangle([fx + 5, 950, fx + 62, 980], 10, fill=(90, 58, 36))
    d.rounded_rectangle([fx - 75, 700, fx + 75, 875], 30, fill=(200, 60, 50))
    for yy in range(715, 870, 32): d.line([(fx - 70, yy), (fx + 70, yy)], fill=(150, 40, 35), width=6)
    d.rounded_rectangle([fx - 105, 715, fx - 62, 850], 20, fill=(200, 60, 50)); d.rounded_rectangle([fx + 62, 715, fx + 105, 850], 20, fill=(200, 60, 50))
    d.ellipse([fx - 108, 830, fx - 62, 876], fill=(236, 190, 150)); d.ellipse([fx + 62, 830, fx + 108, 876], fill=(236, 190, 150))
    d.rectangle([fx - 18, 670, fx + 18, 705], fill=(236, 190, 150))
    d.ellipse([fx - 55, 575, fx + 55, 690], fill=(236, 190, 150))
    d.ellipse([fx - 120, 575, fx + 120, 620], fill=(120, 82, 45))                # hat brim
    d.rounded_rectangle([fx - 62, 505, fx + 62, 600], 30, fill=(140, 98, 55))    # hat crown
    d.rectangle([fx - 62, 570, fx + 62, 588], fill=(70, 48, 28))                 # hat band
    d.ellipse([fx - 30, 625, fx - 14, 641], fill=(40, 30, 25)); d.ellipse([fx + 14, 625, fx + 30, 641], fill=(40, 30, 25))
    d.arc([fx - 26, 640, fx + 26, 670], 20, 160, fill=(120, 60, 50), width=6)
    # red cattle dog sitting to the right, facing the farmer
    red, dark, cream = (196, 92, 48), (150, 62, 30), (246, 226, 200)
    gx = 650
    d.ellipse([gx - 20, 905, gx + 220, 985], fill=red)                           # haunches on the grass
    d.polygon([(gx + 30, 940), (gx + 60, 760), (gx + 170, 760), (gx + 190, 940)], fill=red)   # chest/body upright
    d.ellipse([gx + 70, 790, gx + 150, 930], fill=cream)                         # light chest
    d.rectangle([gx + 70, 880, gx + 100, 980], fill=red); d.rectangle([gx + 130, 880, gx + 160, 980], fill=red)  # front legs
    d.ellipse([gx + 62, 960, gx + 106, 990], fill=cream); d.ellipse([gx + 124, 960, gx + 168, 990], fill=cream)   # paws
    d.polygon([(gx + 205, 950), (gx + 300, 900), (gx + 310, 925), (gx + 215, 975)], fill=dark)   # tail
    d.ellipse([gx + 40, 640, gx + 190, 780], fill=red)                           # head
    d.polygon([(gx + 50, 680), (gx + 55, 560), (gx + 115, 660)], fill=red)        # ears up (heeler)
    d.polygon([(gx + 120, 660), (gx + 180, 565), (gx + 185, 690)], fill=red)
    d.polygon([(gx + 64, 660), (gx + 66, 600), (gx + 100, 662)], fill=dark); d.polygon([(gx + 135, 662), (gx + 172, 605), (gx + 172, 670)], fill=dark)
    d.ellipse([gx - 10, 710, gx + 90, 775], fill=red)                            # muzzle, pointing left at the farmer
    d.ellipse([gx - 6, 722, gx + 22, 746], fill=(35, 25, 20))                    # nose
    d.ellipse([gx + 70, 690, gx + 90, 710], fill=(35, 25, 20))                   # eye
    d.arc([gx + 5, 745, gx + 60, 772], 20, 150, fill=(35, 25, 20), width=5)      # smile
    d.ellipse([gx + 120, 690, gx + 160, 720], fill=cream)                        # pale face blaze
    # rounded app-icon corners
    mask = Image.new("L", (S, S), 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, S - 1, S - 1], radius=S // 5, fill=255)
    im.putalpha(mask)
    return im.resize((n, n), Image.LANCZOS)

if __name__ == "__main__":
    for name, n in (("mdpi", 48), ("hdpi", 72), ("xhdpi", 96), ("xxhdpi", 144), ("xxxhdpi", 192)):
        p = os.path.join(HERE, "res", "mipmap-" + name); os.makedirs(p, exist_ok=True)
        draw(n).save(os.path.join(p, "ic_launcher.png"))
    draw(512).save(os.path.join(HERE, "icon-512.png"))
    print("icons written")
