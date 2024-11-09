"""Convert blocks to json file.

Code based on the SVG converter class .
"""

import logging
import json
import decimal

from typing import Iterable

from dataclasses import dataclass

from rmscene import (
    read_blocks,
    Block,
    RootTextBlock,
    SceneLineItemBlock,
)

from .writing_tools import (
    Pen,
)

from .svg import (
    SvgDocInfo,
    get_dimensions
)

DECIMAL_PRECISION = 3

_logger = logging.getLogger(__name__)

@dataclass
class Point:
    x: float
    y: float

    def toJSON(self):
        return {
            'x': formatFloat(self.x),
            'y': formatFloat(self.y)
        }
    

@dataclass
class PolyLine:
    stroke: str
    width: float
    opacity: float
    points: list[Point]

    def toJSON(self):
        return {
            'stroke': self.stroke,
            'width': formatFloat(self.width),
            'opacity': formatFloat(self.opacity),
            'points': [point.toJSON() for point in self.points],
        }
    

@dataclass
class TextElement(Point):
    text: str

    def toJSON(self):
        return {
            'x': formatFloat(self.x),
            'y': formatFloat(self.y),
            'text': self.text
        }
    

@dataclass
class Page:
    page_number: int
    height: float
    width: float
    lines: list[PolyLine]
    texts: list[TextElement]

    def toJSON(self):
        return {
            'page_number': self.page_number, 
            'height': formatFloat(self.height), 
            'width': formatFloat(self.width),
            'lines': [line.toJSON() for line in self.lines],
            'texts': [text.toJSON() for text in self.texts],
        }


def formatFloat(val: float) -> float:
    return float(round(decimal.Decimal(val), DECIMAL_PRECISION))

def parse_line_block(block: SceneLineItemBlock, doc_info: SvgDocInfo) -> Iterable[PolyLine]:
    # make sure the object is not empty
    if block.value is None:
        return

    # initiate the pen
    pen = Pen.create(block.value.tool.value, block.value.color.value, block.value.thickness_scale)

    last_xpos: float = None
    last_ypos: float = None
    last_segment_width = 0.
    polyline: PolyLine = None

    for point_id, point in enumerate(block.value.points):
        # align the original position
        xpos = point.x + doc_info.xpos_delta
        ypos = point.y + doc_info.ypos_delta

        if point_id % pen.segment_length == 0:
            segment_color = pen.get_segment_color(point.speed, point.direction, point.width, point.pressure, last_segment_width)
            segment_width = pen.get_segment_width(point.speed, point.direction, point.width, point.pressure, last_segment_width)
            segment_opacity = pen.get_segment_opacity(point.speed, point.direction, point.width, point.pressure, last_segment_width)

            if polyline != None:
                yield polyline

            polyline = PolyLine(segment_color, segment_width, segment_opacity, []) 
            if last_xpos != None:
                # Join to previous segment
                polyline.points.append(Point(last_xpos, last_ypos))

        # store the last position
        last_xpos = xpos
        last_ypos = ypos
        last_segment_width = segment_width

        polyline.points.append(Point(last_xpos, last_ypos))

    if polyline != None:
        yield polyline

def parse_text_block(block: RootTextBlock, doc_info: SvgDocInfo) -> Iterable[TextElement]:
    xpos = block.pos_x + doc_info.width / 2.
    ypos = block.pos_y + doc_info.height / 2.

    for text_item in block.text_items:
        if text_item.text.strip():
            yield TextElement(xpos, ypos, text_item.text.strip())

def page_to_json(blocks: Iterable[Block], output, page_number = 0, debug=0):
    """Convert Blocks to SVG."""

    # we need to process the blocks twice to understand the dimensions, so
    # let's put the iterable into a list
    blocks = list(blocks)

    # get document dimensions
    doc_info = get_dimensions(blocks, debug) 

    # add json page info
    page = Page(page_number, doc_info.height, doc_info.width, [], [])

    for block in blocks:
        if isinstance(block, SceneLineItemBlock):
            page.lines.extend(parse_line_block(block, doc_info))
        elif isinstance(block, RootTextBlock):
            page.texts.extend(parse_text_block(block, doc_info))
        else:
            if debug > 0:
                print(f'warning: not converting block: {block.__class__}')

    json.dump(page.toJSON(), output)

def rm_to_json(rm_path, json_path, debug=0):
    """Convert `rm_path` to JSON at `json_path`."""
    with open(rm_path, "rb") as infile, open(json_path, "wt") as outfile:
        blocks = read_blocks(infile)
        page_to_json(blocks, outfile, debug)