#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import string
import time
import pytz
from datetime import datetime
from astral import Astral
from PIL import Image, ImageDraw, ImageFont, ImageFile
from pcd8544 import lcd
from fontdemo import Font
from pi_logo import demo

VOLUME_LEVELS = {
    '-144.000000': 0,
    '-28.125000': 1,
    '-26.250000': 2,
    '-24.375000': 3,
    '-22.500000': 4,
    '-20.625000': 5,
    '-18.750000': 6,
    '-16.875000': 7,
    '-15.000000': 8,
    '-13.125000': 9,
    '-11.250000': 10,
    '-9.375000': 11,
    '-7.500000': 12,
    '-5.625000': 13,
    '-3.750000': 14,
    '-1.875000': 15,
    '0.000000': 16,
}

VOLUME_FULL_BLOCK = [0x41, 0x41, 0x41, 0x41, 0x7F]
VOLUME_BLANK_BLOCK = [0x7F, 0x7F, 0x7F, 0x7F, 0x7F]
VOLUME_BAR_HEAD = [0x7F, 0x7F]
VOLUME_BAR_TAIL = [0x7F, 0x7F]


def get_volume_bar_data(volume):
    volume_level = VOLUME_LEVELS.get(volume, 0)
    return VOLUME_BAR_HEAD + VOLUME_FULL_BLOCK * volume_level + VOLUME_BLANK_BLOCK * (16 - volume_level) + VOLUME_BAR_TAIL


def display_banner():
    lcd.locate(0, 5)
    lcd.text('  @wolfg1969  ')


def display_volume_bar(volume='-24.375000'):
    lcd.locate(0, 4)
    lcd.data(get_volume_bar_data(volume))


def is_night():
    a = Astral()
    city = a['Beijing'] # Replace with your city
    now = datetime.now(pytz.utc)
    sun = city.sun(date=now, local=True)
    return now >= sun['dusk'] or now <= sun['dawn'] # "It's dark outside"


def get_bitmap(text, **kwargs):
    fnt = kwargs.get('font')

    font = kwargs.get('imageFont1')
    font2 = kwargs.get('imageFont2')

    im = Image.new('L', (84, 32))
    draw = ImageDraw.Draw(im)

    width, height, baseline = fnt.text_dimensions(text)

    previous_char = None

    pos_x = 0
    pos_y = 0

    line_break = False
    line_start = 0
    line = 1

    for char in text:

        char_left = line_start

        glyph = fnt.glyph_for_character(char)

        # Take kerning information into account before we render the
        # glyph to the output bitmap.
        kerning_offset = fnt.kerning_offset(previous_char, char)
        line_start += kerning_offset

        previous_char = char

        line_start += glyph.advance_width

        if line_start > 84 or char == '\n':
            line_start = kerning_offset + glyph.advance_width
            line += 1
            char_left = 0

        if char == '\n':
            line_start = 0
            continue

        pos_x = char_left
        pos_y = (line - 1) * (height+1)

        if (pos_y + height) > 32:
            break

        # print line, line_start, pos_x, pos_y, char
        if char in string.printable:
            draw.text((pos_x, pos_y), char, font=font2, fill=1)
        else:
            draw.text((pos_x, pos_y), char, font=font, fill=1)

    img_bytes = im.tobytes()
    # print(len(img_bytes), [ord(x) for x in img_bytes])

    cols = []
    for x in range(84):
        col = []
        for y in range(32):
            p = ord(img_bytes[y*84 + x])
            if (p > 1):
                p = 1
            col.append(str(p))
        cols.append(col)

    # print(len(cols))
    bitmap = []
    x = 1
    for i in range(4):
        # print col
        j = i * 8
        for col in cols:
            b = col[j:j+8]
            b.reverse()
            bitmap.append(int(''.join(b), 2))

    del im
    return bitmap


def display_song_meta(text, **kwargs):
    lcd.locate(0, 0)
    bitmap = get_bitmap(text, **kwargs)
    lcd.data(bitmap)

def send_to_display(fields, **kwargs):

    artist=fields[0]
    title=fields[1]
    volume = fields[6]

    text = u"{artist} {title}".format(artist=artist, title=title, )

    lcd.backlight(not is_night())
    # lcd.backlight(1)

    display_song_meta(text, **kwargs)
    display_volume_bar(volume)
    display_banner()


def read_now_playing(**kwargs):
    bufferSize = 1024
    PATH = "/home/pi/shairport/now_playing"

    fifo = os.open(PATH, os.O_RDONLY)
    fd = os.fdopen(fifo, 'r', bufferSize)

    fields = []
    while True:
        line = fd.readline()

        if not line or line == '\n':
            # print(u', '.join(fields))
            send_to_display(fields, **kwargs)
            fields = []
            continue

        field = line.strip().split('=')
        # print(field)
        fields.append(field[1].decode('utf-8'))

    fd.close()
    os.close(fifo)

    lcd.cls()


if __name__ == '__main__':

    lcd.init(contrast=0xBB)
    demo()

    time.sleep(2)
    lcd.cls()

    display_volume_bar()
    display_banner()

    font_info = {
        'font': Font('Zpix.ttf', 12),
        'imageFont1': ImageFont.truetype("Zpix.ttf", 12),
        'imageFont2': ImageFont.truetype("DejaVuSansMono.ttf", 12),
    }

    read_now_playing(**font_info)
