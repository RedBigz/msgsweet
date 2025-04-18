import argparse
import os
import hashlib
import time
import shutil
from PIL import Image, ImageFont, ImageDraw
import moviepy.editor as ed
from PIL.Image import Dither
from string import ascii_letters
from random import choice, randint

col = 15

frameskip = 4

import textwrap

def skip(l: list):
    newlist = []
    
    for i, item in enumerate(l):
        if i % frameskip == 0:
            newlist.append(item)
    
    return newlist

fortunes = []

with open("fortunes.txt", "r") as fd:
    fortunes = [fort.strip() for fort in fd.read().split("%")]

get_fortune = lambda: choice(fortunes)

def main(args):
    device = "CPU" if args.cpu else ( "OPTIX" if args.rtx else ( "CUDA" if args.cuda else ( "HIP" if args.hip else "CPU" ) ) )

    folder = ".msgsweet-" + hashlib.md5(str(time.time()).encode()).hexdigest()

    subf = lambda x: os.path.join(folder, x)
    subf_full = lambda x: os.path.join(os.getcwd(), folder, x)

    os.mkdir(folder)

    frames = subf("frames")
    print(frames)
    os.mkdir(frames)

    shutil.copy(os.path.join("blends", args.style, "main.blend"), subf("main.blend"))

    args.input = [f"img/{randint(1, 3)}.jpg", get_fortune()]

    with open(os.path.join("blends", args.style, "settings"), "r") as l:
        s = l.read().strip().split()
        fps = int(s[0])
        s = s[1:]
        for i, name in enumerate(s):
            if os.path.isfile(args.input[i]):
                shutil.copy(args.input[i], subf(name))
            else:
                img = Image.new(mode="RGB", size=(512, 512))
                bbox = [0, 0, 513, 0]

                draw = ImageDraw.Draw(img)
                draw.rectangle((0, 0, 511, 511), fill="white")

                font = None
                tw, th, lc, wc = 0, 0, 0, 0 # text width, text height, line count, word wrap columns

                for fs in range(5, 65):
                    font = ImageFont.truetype("arial.ttf", fs)

                    tw = sum(font.getbbox(char)[2] for char in ascii_letters) / len(ascii_letters) # get average width of text character
                    th = max(font.getbbox(char)[3] - font.getbbox(char)[1] for char in ascii_letters) # get max height of text character

                    lc = int(512 / th)
                    wc = int(512 / tw)

                    if (wc * lc) < len(args.input[i]) or len(textwrap.wrap(args.input[i], wc)) > lc:
                        font = ImageFont.truetype("arial.ttf", fs)
                        break
                
                if font == None:
                    raise ValueError("Fortune message too large, please re-execute program.")
                
                print(tw, th, lc, wc, font.size)
                    
                wrapped = textwrap.wrap(args.input[i], wc)

                print(wrapped, len(wrapped))

                th -= 3 # pack together more

                for i, wrap in enumerate(wrapped):
                    height = int(0 - (len(wrapped) - 1) * th / 2 + i * th)
                    _, _, w, h = draw.textbbox((0, 0), wrap, font=font)
                    draw.text((256 - int(w/2), 256 - int(h/2) + height), wrap, font=font, fill="black")
                
                img.save(subf(name))

    process = f"\"{args.blender}\" -b {subf('main.blend')} -o {os.path.join(subf_full('frames'), '#####')} -a -- --cycles-device {device}"

    os.system(process)

    # imgs = [Image.open(os.path.join(subf(f"frames"), n)) for n in os.listdir(subf("frames"))]
    # imgs[0].save(args.output, save_all=True, append_images=imgs[1:], format="GIF", duration=fps, optimize=False, loop=0, disposal=2)

    # MPEG
    imgs = [ed.ImageClip(os.path.join(subf(f"frames"), n), duration=1 / fps) for n in os.listdir(subf("frames"))]
    concatenated = ed.concatenate_videoclips(imgs, method="compose")
    concatenated: ed.VideoClip = concatenated.set_fps(fps)
    concatenated.write_videofile(filename=args.output + ".mp4", codec="mpeg4")

    # GIF
    # imgs = skip(imgs)
    # concatenatedgif = ed.concatenate_videoclips(imgs, method="compose")
    # concatenatedgif: ed.VideoClip = concatenatedgif.set_fps(fps)
    # concatenatedgif.write_gif(filename=args.output + ".gif", program="ffmpeg")

    imgs = [Image.open(os.path.join(subf(f"frames"), n)).convert("P", dither=Dither.FLOYDSTEINBERG) for n in skip(os.listdir(subf("frames")))]
    imgs[0].save(args.output + ".gif", save_all=True, append_images=imgs[1:], format="GIF", duration=1 / (fps / frameskip), optimize=True, loop=0, disposal=2)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MakeSweet in Python + Cycles (FORTUNE EDITION)")

    parser.add_argument("--output", "-o", default="output")

    parser.add_argument("-cpu", default=False, action="store_true", help="Use CPU when rendering")
    parser.add_argument("-rtx", default=False, action="store_true", help="Use OptiX (RTX 2060 - RTX 4090)")
    parser.add_argument("-cuda", default=False, action="store_true", help="Enable CUDA (CUDA 3.0 or later, ~GTX 650+)")
    parser.add_argument("-hip", default=False, action="store_true", help="Enable HIP (AMD)")
    parser.add_argument("--blender-path", dest="blender", default="C:/Program Files/Blender Foundation/Blender 4.0/blender.exe", help="Custom Blender Path (defaults to Blender 4.0)")
    
    parser.add_argument("--style", "-s", default="heart")
    # parser.add_argument("input", nargs="+")


    parsed = parser.parse_args()

    main(parsed)