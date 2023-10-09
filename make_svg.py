"""
Simple script to make an svg that wraps a .png in the images/raw/ folder.

The goal is to keep image markup separate from the underling picture of the map
"""

from typing import *
import os
import json

IMAGE_DIR_PATH = os.path.join(os.path.dirname(__file__), 'images')
SVG_TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates', 'template.svg')


def get_png_dimensions(png_filename: str) -> Tuple[int, int]:
    """
    Gets the dimensions of a .png file.
    Based on the header format laid out by wikipedia: https://en.wikipedia.org/wiki/PNG#File_header
    """
    PNG_HEADER_SIZE = 8
    IHDR_HEADER_SIZE = 8
    WIDTH_DATAFIELD_SIZE = 4
    HEIGHT_DATAFIELD_SIZE = 4
    with open(png_filename, 'rb') as fp:
        png_bytes = fp.read(PNG_HEADER_SIZE + IHDR_HEADER_SIZE + WIDTH_DATAFIELD_SIZE + HEIGHT_DATAFIELD_SIZE)
    assert png_bytes[:PNG_HEADER_SIZE] == b'\x89\x50\x4e\x47\x0d\x0a\x1a\x0a', "Invalid png header"
    assert png_bytes[PNG_HEADER_SIZE+4:PNG_HEADER_SIZE+IHDR_HEADER_SIZE] == b'IHDR', 'Invalid png; IHDR chunk did not come first'
    x = int.from_bytes(png_bytes[PNG_HEADER_SIZE + IHDR_HEADER_SIZE : PNG_HEADER_SIZE + IHDR_HEADER_SIZE + WIDTH_DATAFIELD_SIZE], byteorder='big')
    y = int.from_bytes(png_bytes[PNG_HEADER_SIZE + IHDR_HEADER_SIZE + WIDTH_DATAFIELD_SIZE:], byteorder='big')
    return (x, y)

_template_contents: List[str] = []
def fetch_template():
    if not len(_template_contents):
        with open(SVG_TEMPLATE_PATH, 'r', encoding='utf-8') as fp:
            _template_contents.append(fp.read())
    return _template_contents[0]

TMapInfo = Dict[Literal["points", "variables"], List[Dict[str, str]] | Dict[str, str]]
def svg_for_points(filename: str, map_info: TMapInfo) -> str:
    result: List[str] = []
    points: List[Dict[str, str]] = map_info.get('points')
    assert points is not None, f'No points were supplied in {filename}'
    for point in points:
        point_type = point.get("type", "bonus")
        result.append(f'  <circle cx="{point["x"]}" cy="{point["y"]}" r="{point.get("r", "20")}" class="{point_type}"/>')
        if label := point.get("label"):
            result.append(f'  <text x="{point["x"]}" y="{point["y"]}" class="{point_type}-text">{label}</text>')
    return '\n'.join(result)


def print_svg(input_json: str, target_file: str) -> None:
    with open(input_json, 'r', encoding='utf-8') as fp:
        map_info: TMapInfo = json.load(fp)
    variables: Dict[str, str] = map_info.get('variables')
    assert variables is not None, f'variables not specified in {input_json}'
    image_source = variables.get('image_source')
    assert image_source is not None, f'no source map image was specified in {input_json}'
    dimensions = get_png_dimensions(os.path.join(IMAGE_DIR_PATH, image_source))
    variables['width'] = dimensions[0]
    variables['height'] = dimensions[1]
    variables.setdefault('bonus_colour', '#b9f')
    variables.setdefault('progression_colour', 'yellow')
    variables.setdefault('annotation_colour', '#fa66a9')
    variables.setdefault('label_offset', '0, -35px')
    contents = fetch_template()
    for variable_name, variable_value in variables.items():
        contents = contents.replace(f'$({variable_name})', str(variable_value))
    points = svg_for_points(input_json, map_info)
    contents = contents.replace(f'$(points)', points)
    with open(target_file, 'w', encoding='utf-8') as fp:
        fp.write(contents)


if __name__ == '__main__':
    import glob
    map_info_pattern = os.path.join(os.path.dirname(__file__), 'map_info', '*.json')
    for file in glob.glob(map_info_pattern):
        print(f'Making an .svg from {file}')
        stem = os.path.basename(os.path.splitext(file)[0])
        print_svg(file, os.path.join(IMAGE_DIR_PATH, f'{stem}.svg'))
