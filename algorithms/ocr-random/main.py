import itertools
import random
from dataclasses import dataclass
from os.path import basename, splitext
from pathlib import Path

import faker
from jinja2 import Template
from glob import glob
from PIL import Image
from shapely.geometry import Polygon

image_paths = glob('/tmp/images/*.tif')
image_paths = glob('/home/tom/Downloads/*.tif')

output_folder = './'

with open('template.xml') as f:
    template = Template(f.read())

@dataclass
class Box:
    width: int
    height: int
    x: int
    y: int


@dataclass
class TextBox:
    text: str
    points: [(int, int)]


def get_image_dimension(path: str) -> (int, int):
    img = Image.open(path)
    dimensions = (img.width, img.height)
    img.close()
    return dimensions


def get_random_box(dimensions):
    min_width = int(dimensions[0] / 10)
    max_width = int(dimensions[0] / 4)
    min_height = int(dimensions[1] / 8)
    max_height = int(dimensions[1] / 3)

    width = random.randint(min_width, max_width)
    height = random.randint(min_height, max_height)

    return Box(
        width=width,
        height=height,
        x=random.randint(0, dimensions[0] - width),
        y=random.randint(0, dimensions[1] - height)
    )


def box_to_points(box: Box):
    return [
        (box.x, box.y),
        (box.x + box.width, box.y),
        (box.x + box.width, box.y + box.height),
        (box.x, box.y + box.height)
    ]


def box_to_polygon(box: Box):
    return Polygon(box_to_points(box))


def does_overlap(boxes):
    polygons = map(box_to_polygon, boxes)
    for combi in itertools.combinations(polygons, 2):
        if combi[0].intersects(combi[1]):
            return True
    return False


def get_n_non_overlapping_random_boxes(dimensions, n):
    boxes = []
    retries = 100
    for i in range(0, n):
        new_box = get_random_box(dimensions)
        if not does_overlap(boxes + [new_box]):
            boxes.append(new_box)
        else:
            retries = retries - 1
            i -= 1
            if retries == 0:
                break

    return boxes


def get_random_textboxes(dimensions):
    fake = faker.Faker(['nl_NL'])
    boxes = get_n_non_overlapping_random_boxes(dimensions, 8)
    text_boxes = []
    for box in boxes:
        n_sentences = random.randint(1, 5)
        text = ' '.join([fake.sentence() for i in range(n_sentences)])
        text_boxes.append(TextBox(
            text=text,
            points=box_to_points(box)
        ))
    return text_boxes


def image_to_xml(image_path):
    dimensions = get_image_dimension(image_path)
    text_boxes = get_random_textboxes(dimensions)
    return template.render(
        text_boxes=text_boxes,
        dimensions=dimensions,
        filename=basename(image_path),
        id=splitext(basename(image_path))[0]
    )


if __name__ == '__main__':
    for path in image_paths:
        output_path = Path(output_folder) / Path(splitext(basename(path))[0] + '.xml')
        with open(output_path, 'w+') as f:
            f.write(image_to_xml(path))


