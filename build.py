#!/usr/bin/env python3

import json
import os
import subprocess


HERE = os.path.dirname(__file__)
IDOL_DIRNAME = 'idols'
IDOLS_DIR = os.path.join(HERE, IDOL_DIRNAME)
THUMBS_DIR = os.path.join(HERE, 'idol-thumbs')
POSES = set()
SKIN_COLOURS = set()
HAIR_COLOURS = set()
LAYERS = set()

if not os.path.isdir(THUMBS_DIR):
    os.mkdir(THUMBS_DIR)


def part(
    path, thumb_path, med_path, bodytype, layer, colour, number,
    pose=None,
):
    attrs = {
        'path': path,
        'thumbPath': thumb_path,
        'medPath': med_path,
        'bodytype': bodytype,
        'layer': layer,
        'number': number,
        'pose': pose,
    }

    LAYERS.add(layer)

    if pose is not None:
        POSES.add(pose)
    if layer in ('hd', 'bd'):
        attrs['skinColour'] = colour
        SKIN_COLOURS.add(colour)
    elif layer in ('hbe', 'hb', 'hf', 'hfe', 'ah'):
        attrs['hairColour'] = colour
        HAIR_COLOURS.add(colour)

    return attrs


def build_idols():
    parts = []

    for d in os.scandir(IDOLS_DIR):
        if not d.is_dir():
            continue

        for entry in os.scandir(os.path.join(IDOLS_DIR, d.name)):
            fn = entry.name.replace('.png', '')

            basename, ext = os.path.splitext(entry.name)

            thumb_name = '{}-thumb{}'.format(basename, ext)
            med_name = '{}-med{}'.format(basename, ext)

            img_path = os.path.join(IDOLS_DIR, d.name, entry.name)
            thumb_path = os.path.join(THUMBS_DIR, thumb_name)
            med_path = os.path.join(THUMBS_DIR, med_name)

            parts.append(part(
                '/'.join([IDOL_DIRNAME, d.name, entry.name]),
                '/'.join([THUMBS_DIR, thumb_name]),
                '/'.join([THUMBS_DIR, med_name]),
                *fn.split('_')
            ))

            if not os.path.exists(thumb_path):
                subprocess.check_call(
                    ['convert', img_path, '-resize', '400x400^', thumb_path])
                subprocess.check_call(['optipng', thumb_path])

            if not os.path.exists(med_path):
                subprocess.check_call(
                    ['convert', img_path, '-resize', '1000x1000^', med_path])
                subprocess.check_call(['optipng', med_path])

    return {
        pose: {
            skin_colour: {
                hair_colour: {
                    layer: [
                        p for p in parts if
                        p['layer'] == layer and
                        p.get('hairColour') in (hair_colour, None) and
                        p.get('skinColour') in (skin_colour, None) and
                        p.get('pose') in (pose, None)
                    ] for layer in LAYERS
                } for hair_colour in HAIR_COLOURS
            } for skin_colour in SKIN_COLOURS
        } for pose in POSES
    }


def build_bios():
    bios = []

    with open(os.path.join(HERE, 'idol bios.txt')) as f:
        for bio in f.readlines():
            bio = bio.strip()
            if bio:
                bios.append(bio)

    return bios


def build_abilities():
    parts = []

    with open(os.path.join(HERE, 'idol attack names word list.txt')) as f:
        for line in f.readlines():
            line = line.strip()

            if line.startswith('//') or not line:
                continue

            elif line.startswith('#'):
                subparts = []
                parts.append(subparts)
                continue

            bonus = 0
            healing = False

            while line[0] in '+-@':
                char = line[0]

                if char == '+':
                    bonus += 1
                elif char == '-':
                    bonus -= 1
                elif char == '@':
                    healing = True

                line = line[1:]

            parts[-1].append({
                'bonus': bonus,
                'healing': healing,
                'word': line,
            })

    return parts


if __name__ == '__main__':
    with open('parts.js', 'w') as p:
        p.write('PARTS = {};'.format(json.dumps(build_idols())))
        p.write('BIOS = {};'.format(json.dumps(build_bios())))
        p.write('ABILITIES = {};'.format(json.dumps(build_abilities())))
