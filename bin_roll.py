import os
import os.path
import argparse
import PIL
from PIL import Image

def section(a, start, length):
    return a[start:start+length]

def roll_x(im, delta):
    """Roll an image sideways."""
    ''' https://pillow.readthedocs.io/en/stable/handbook/tutorial.html?highlight=Roll#rolling-an-image '''
    xsize, ysize = im.size

    delta = delta % xsize
    if delta == 0:
        return im

    part1 = im.crop((0, 0, delta, ysize))
    part2 = im.crop((delta, 0, xsize, ysize))
    im.paste(part1, (xsize - delta, 0, xsize, ysize))
    im.paste(part2, (0, 0, xsize - delta, ysize))

    return im

def roll_y(im, delta):
    xsize, ysize = im.size

    delta = delta % ysize
    if delta == 0:
        return im

    part1 = im.crop((0, 0, xsize, delta))
    part2 = im.crop((0, delta, xsize, ysize))
    im.paste(part1, (0, ysize - delta, xsize, ysize))
    im.paste(part2, (0, 0, xsize, ysize - delta))

    return im


def bin_to_pil(infile, width, height, bpp):
    bytes_per_tile = (8 * 8 * bpp // 8)
    if len(infile) < width * height * bytes_per_tile:
        infile = infile + bytes(width * height * bytes_per_tile - len(infile))
        print('Warning: input file is too small. Transparent tiles will be added.')

    palette = list(range(bpp ** 2))

    im = PIL.Image.new('P', (8 * width, 8 * height), (0, 0, 0, 255))

    for i in range(0, width * height * bytes_per_tile, bytes_per_tile):
        x = (((i // bytes_per_tile) * 8) % (8 * width)) // 8
        y = ((i // bytes_per_tile) * 8) // (8 * width)
        decodedtile = [0] * (8 * 8)
        intile = infile[i:i + bytes_per_tile]
        for xx in range(8):
            for yy in range(8):
                decodedtile[(yy*8)+7-xx] = \
                    (( intile[ yy<<1    ]>>xx)&1)    + \
                    (((intile[(yy<<1)|1 ]>>xx)&1)<<1)+ \
                    (((intile[(yy<<1)|16]>>xx)&1)<<2)+ \
                    (((intile[(yy<<1)|17]>>xx)&1)<<3)
        out_img = PIL.Image.frombytes('P', (8, 8), bytes(decodedtile))
        out_img.putpalette(palette, rawmode="RGB")
        out_img.info['transparency'] = 0
        out_img.apply_transparency()
        im.paste(out_img, (x * 8, y * 8))
        # print((x, y))
    return im

def pil_to_bin(output_filename, im, bpp):
    bytes_per_tile = (8 * 8 * bpp // 8)
    with open(output_filename, 'wb') as gfxfile:
        px = im.load()
        for y in range(im.size[1] // 8):
            for x in range(im.size[0] // 8):
                assert bpp == 4
                decodedtile = [0] * 8 * 8
                for i in range(8):
                    for j in range(8):
                        decodedtile[i + j * 8] = px[x * 8 + i, y * 8 + j]
                outtile = [0] * bytes_per_tile
                for xx in range(8):
                    outtile[ xx<<1    ]= \
                        ((decodedtile[ xx<<3   ]&1)<<7)|((decodedtile[(xx<<3)|1]&1)<<6)| \
                        ((decodedtile[(xx<<3)|2]&1)<<5)|((decodedtile[(xx<<3)|3]&1)<<4)| \
                        ((decodedtile[(xx<<3)|4]&1)<<3)|((decodedtile[(xx<<3)|5]&1)<<2)| \
                        ((decodedtile[(xx<<3)|6]&1)<<1)| (decodedtile[(xx<<3)|7]&1)
                    outtile[(xx<<1)|1 ]= \
                        ((decodedtile[ xx<<3   ]&2)<<6)|((decodedtile[(xx<<3)|1]&2)<<5)| \
                        ((decodedtile[(xx<<3)|2]&2)<<4)|((decodedtile[(xx<<3)|3]&2)<<3)| \
                        ((decodedtile[(xx<<3)|4]&2)<<2)|((decodedtile[(xx<<3)|5]&2)<<1)| \
                         (decodedtile[(xx<<3)|6]&2)    |((decodedtile[(xx<<3)|7]&2)>>1)
                    outtile[(xx<<1)|16]= \
                        ((decodedtile[ xx<<3   ]&4)<<5)|((decodedtile[(xx<<3)|1]&4)<<4)| \
                        ((decodedtile[(xx<<3)|2]&4)<<3)|((decodedtile[(xx<<3)|3]&4)<<2)| \
                        ((decodedtile[(xx<<3)|4]&4)<<1)| (decodedtile[(xx<<3)|5]&4)    | \
                        ((decodedtile[(xx<<3)|6]&4)>>1)|((decodedtile[(xx<<3)|7]&4)>>2)
                    outtile[(xx<<1)|17]= \
                        ((decodedtile[ xx<<3   ]&8)<<4)|((decodedtile[(xx<<3)|1]&8)<<3)| \
                        ((decodedtile[(xx<<3)|2]&8)<<2)|((decodedtile[(xx<<3)|3]&8)<<1)| \
                         (decodedtile[(xx<<3)|4]&8)    |((decodedtile[(xx<<3)|5]&8)>>1)| \
                        ((decodedtile[(xx<<3)|6]&8)>>2)|((decodedtile[(xx<<3)|7]&8)>>3)
                gfxfile.write(bytes(outtile))
                # print(repr(bytes(outtile)))

def roll_bin(input_filename, output_filename, roll_x_n, roll_y_n, width=16, height=8):
    bpp = 4
    infile = open(input_filename, 'rb').read()

    im = bin_to_pil(infile, width, height, bpp)
    im = roll_y(im, roll_y_n)
    im = roll_x(im, roll_x_n)
    pil_to_bin(output_filename, im, bpp)

def composite(input_filename1, input_filename2, output_filename, bpp, width, height):
    infile1 = open(input_filename1, 'rb').read()
    infile2 = open(input_filename2, 'rb').read()

    im1 = bin_to_pil(infile1, width, height, bpp)
    im2 = bin_to_pil(infile2, width, height, bpp)

    palette = list(range(bpp ** 2))
    im1.putpalette(palette, rawmode="RGB")
    im2.putpalette(palette, rawmode="RGB")
    im1.info['transparency'] = 0
    im1.apply_transparency()
    im2.info['transparency'] = 0
    im2.apply_transparency()

    mask = Image.new("RGBA", im2.size, (255, 255, 255, 255))
    mask.paste(im2)

    im1.paste(im2, (0, 0), mask)
    pil_to_bin(output_filename, im1, bpp)

if __name__ == '__main__':
    parser = argparse.ArgumentParser('bin_roll', 'Shifts pixels in a SNES .bin file, copying the pixels shifted out of the image to the other end')
    parser.add_argument('-x', type=int, default=0, help='shift to the left this number of pixels (negative numbers shift right)')
    parser.add_argument('-y', type=int, default=0, help='shift up this number of pixels (negative numbers shift down)')
    parser.add_argument('--width', type=int, default=16, help='width of input file in number of 8x8 tiles (default 16)')
    parser.add_argument('--height', type=int, default=8, help='height of input file in number of 8x8 tiles (default 8)')
    parser.add_argument('input_filename')
    parser.add_argument('output_filename')

    args = parser.parse_args()

    if args.x == 0 and args.y == 0:
        print("output will be unmodified. Specify -x and/or -y.")
    roll_bin(args.input_filename, args.output_filename, args.x, args.y, args.width, args.height)
