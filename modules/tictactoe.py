import sys
from PIL import Image

scale = 1/4
spacing = 8
maxLineImg = 12
prefix_file = 'assets/imgs/'

def imgWidth(widths):
    total_width = round((sum(widths) + (len(widths) * spacing) + (3 * spacing)) * scale)
    if total_width > 384:
        return 384, True
    else:
        return total_width, False

def imgHeight(heights, multiline):
    if not multiline:
        return round(max(heights) * scale)
    else:
        return round(((max(heights) + spacing) * (len(heights) // maxLineImg + 1)) * scale)


def saveImageTTT(text):
    file_imgs = []
    for i in text:
        letter = ''
        if 'A' <= i <= 'Z':
            letter = i.lower()
        elif 'a' <= i <= 'z':
            letter = i
        else:
            letter = 'blk'
        file_imgs.append(prefix_file + letter + '.png')

    images = [Image.open(x) for x in file_imgs]
    widths, heights = zip(*(i.size for i in images))

    total_width, multiline = imgWidth(widths)
    height = imgHeight(heights, multiline)
    max_height = max(heights)

    new_im = Image.new('RGBA', (total_width, height), (255, 0, 0, 0))

    x_offset = 0
    y_offset = 0
    line_index = 0
    for im in images:
        im_resized = im.resize((round(im.size[0]*scale), round(im.size[1]*scale)))
        new_im.paste(im_resized, (x_offset, y_offset))
        x_offset += round((im.size[0] + spacing) * scale)

        if line_index > 10:
            x_offset = 0
            y_offset += round((max_height + spacing) * scale)
            line_index = -1

        line_index += 1

    new_im.save(prefix_file + 'msg.png')
