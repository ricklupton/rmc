"""Convert blocks to svg file.

Code originally from https://github.com/lschwetlick/maxio through
https://github.com/chemag/maxio .
"""

import logging
import math
import string

from typing import Iterable

from dataclasses import dataclass

from rmscene import scene_items as si
from rmscene.text import extract_text_lines
from rmscene import (
    read_blocks,
    SceneTree,
    build_tree,
    TextFormat,
    Block,
    RootTextBlock,
    AuthorIdsBlock,
    MigrationInfoBlock,
    PageInfoBlock,
    SceneTreeBlock,
    TreeNodeBlock,
    SceneGroupItemBlock,
    SceneLineItemBlock,
)

from .writing_tools import (
    Pen,
)

_logger = logging.getLogger(__name__)


SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872

PAGE_WIDTH_PT = 445
SCALE = float(PAGE_WIDTH_PT) / SCREEN_WIDTH
X_SHIFT = PAGE_WIDTH_PT // 2


def xx(screen_x):
    return screen_x * SCALE #+ X_SHIFT


def yy(screen_y):
    return screen_y * SCALE


LINE_HEIGHTS = {
    TextFormat.PLAIN: 70,
    TextFormat.BULLET: 35,
    TextFormat.BOLD: 35,
    TextFormat.HEADING: 70,
}


SVG_HEADER = string.Template("""
<html>
<body>
<div style="border: 1px solid grey; margin: 2em; float: left;">
<svg xmlns="http://www.w3.org/2000/svg" height="$height" width="$width">
    <script type="application/ecmascript"> <![CDATA[
        var visiblePage = 'p1';
        function goToPage(page) {
            document.getElementById(visiblePage).setAttribute('style', 'display: none');
            document.getElementById(page).setAttribute('style', 'display: inline');
            visiblePage = page;
        }
    ]]>
    </script>
""")




@dataclass
class SvgDocInfo:
    height: int
    width: int
    xpos_delta: float
    ypos_delta: float


def rm_to_svg(rm_path, svg_path, debug=0):
    """Convert `rm_path` to SVG at `svg_path`."""
    with open(rm_path, "rb") as infile, open(svg_path, "wt") as outfile:
        blocks = read_blocks(infile)
        blocks_to_svg(blocks, outfile, debug)


def blocks_to_svg(blocks, outfile):
    tree = SceneTree()
    build_tree(tree, blocks)
    tree_to_svg(tree, outfile)


def tree_to_svg(tree: SceneTree, output):
    """Convert Blocks to SVG."""

    # get document dimensions
    # svg_doc_info = get_dimensions(tree)

    # add svg header
    output.write(
        SVG_HEADER.substitute(
            height=1000,
            width=PAGE_WIDTH_PT,
            # viewbox=" ".join(
            #     str(x) for x in [-PAGE_WIDTH_PT // 2, 0, PAGE_WIDTH_PT, SCREEN_HEIGHT]
            # ),
        )
    )
    output.write('\n')

    # add svg page info
    output.write(f'    <g id="p1" style="display:inline" transform="translate({X_SHIFT},100)">\n')
    output.write('        <filter id="blurMe"><feGaussianBlur in="SourceGraphic" stdDeviation="10" /></filter>\n')

    anchor_pos = {}
    draw_text(tree.root_text, output, anchor_pos)
    _logger.debug("anchor_pos: %s", anchor_pos)

    draw_group(tree.root, output, anchor_pos)

    # # Overlay the page with a clickable rect to flip pages
    # output.write('\n')
    # output.write('        <!-- clickable rect to flip pages -->\n')
    # output.write(f'        <rect x="0" y="0" width="{svg_doc_info.width}" height="{svg_doc_info.height}" fill-opacity="0"/>\n')
    # Closing page group
    output.write('    </g>\n')
    # END notebook
    output.write('</svg>\n')


def draw_group(item: si.Group, output, anchor_pos):
    anchor_x = 0.0
    anchor_y = 0.0
    if item.anchor_id is not None:
        assert item.anchor_origin_x is not None
        anchor_x = item.anchor_origin_x.value
        if item.anchor_id.value in anchor_pos:
            anchor_y = anchor_pos[item.anchor_id.value]
            _logger.debug("Group anchor: %s -> y=%.1f", item.anchor_id.value, anchor_y)
        else:
            _logger.warning("Group anchor: %s is unknown!", item.anchor_id.value)
    output.write(f'    <g id="{item.node_id}" transform="translate({xx(anchor_x)}, {yy(anchor_y)})">\n')
    for child_id in item.children:
        child = item.children[child_id]
        _logger.debug("Group child: %s %s", child_id, type(child))
        output.write(f'    <!-- child {child_id} -->\n')
        if isinstance(child, si.Group):
            draw_group(child, output, anchor_pos)
        elif isinstance(child, si.Line):
            draw_stroke(child, output, anchor_pos)
    output.write(f'    </g>\n')


def draw_stroke(item: si.Line, output, anchor_pos):
    _logger.debug("Writing line: %s", item)

    # initiate the pen
    pen = Pen.create(item.tool.value, item.color.value, item.thickness_scale/10)
    K = 5

    # BEGIN stroke
    output.write(f'        <!-- Stroke tool: {item.tool.name} color: {item.color.name} thickness_scale: {item.thickness_scale} -->\n')
    output.write('        <polyline ')
    output.write(f'style="fill:none;stroke:{pen.stroke_color};stroke-width:{pen.stroke_width/K};opacity:{pen.stroke_opacity}" ')
    output.write(f'stroke-linecap="{pen.stroke_linecap}" ')
    output.write('points="')

    last_xpos = -1.
    last_ypos = -1.
    last_segment_width = 0
    # Iterate through the point to form a polyline
    for point_id, point in enumerate(item.points):
        # align the original position
        xpos = point.x
        ypos = point.y
        # stretch the original position
        # ratio = (svg_doc_info.height / svg_doc_info.width) / (1872 / 1404)
        # if ratio > 1:
        #    xpos = ratio * ((xpos * svg_doc_info.width) / 1404)
        #    ypos = (ypos * svg_doc_info.height) / 1872
        # else:
        #    xpos = (xpos * svg_doc_info.width) / 1404
        #    ypos = (1 / ratio) * (ypos * svg_doc_info.height) / 1872
        # process segment-origination points
        if point_id % pen.segment_length == 0:
            segment_color = pen.get_segment_color(point.speed, point.direction, point.width, point.pressure, last_segment_width)
            segment_width = pen.get_segment_width(point.speed, point.direction, point.width, point.pressure, last_segment_width)
            segment_opacity = pen.get_segment_opacity(point.speed, point.direction, point.width, point.pressure, last_segment_width)
            # print(segment_color, segment_width, segment_opacity, pen.stroke_linecap)
            # UPDATE stroke
            output.write('"/>\n')
            output.write('        <polyline ')
            output.write(f'style="fill:none; stroke:{segment_color} ;stroke-width:{segment_width/K:.3f};opacity:{segment_opacity}" ')
            output.write(f'stroke-linecap="{pen.stroke_linecap}" ')
            output.write('points="')
            if last_xpos != -1.:
                # Join to previous segment
                output.write(f'{xx(last_xpos):.3f},{yy(last_ypos):.3f} ')
        # store the last position
        last_xpos = xpos
        last_ypos = ypos
        last_segment_width = segment_width

        # BEGIN and END polyline segment
        output.write(f'{xx(xpos):.3f},{yy(ypos):.3f} ')

    # END stroke
    output.write('" />\n')


def draw_text(block, output, anchor_pos):
    # a RootTextBlock contains text
    output.write('    <g class="root-text" style="display:inline">\n')
    output.write(f'        <!-- RootTextBlock item_id: {block.block_id} -->\n')

    # add some style to get readable text
    output.write('''
    <style>
        text.heading {
            font: 14pt serif;
        }
        text.bold {
            font: 8pt sans-serif bold;
        }
        text, text.plain {
            font: 7pt sans-serif;
        }
    </style>
    ''')

    y_offset = 0
    for fmt, line, ids in extract_text_lines(block):
        y_offset += LINE_HEIGHTS[fmt]

        # BEGIN text
        # https://developer.mozilla.org/en-US/docs/Web/SVG/Element/text
        xpos = block.pos_x
        ypos = block.pos_y + y_offset
        cls = fmt.name.lower()
        if line:
            output.write(f'        <!-- Text line char_id: {ids[0]} -->\n')
            output.write(f'        <text x="{xx(xpos)}" y="{yy(ypos)}" class="{cls}">{line.strip()}</text>\n')

        # Save y-coordinates of potential anchors
        for k in ids:
            anchor_pos[k] = ypos

    output.write('    </g>\n')


# def get_dimensions(tree):
#     # {xpos,ypos} coordinates are based on the top-center point
#     # of the doc **iff there are no text boxes**. When you add
#     # text boxes, the xpos/ypos values change.
#     xpos_delta = XPOS_SHIFT
#     # if xmin is not None and (xmin + XPOS_SHIFT) < 0:
#     #     # make sure there are no negative xpos
#     #     xpos_delta += -(xmin + XPOS_SHIFT)
#     #ypos_delta = SCREEN_HEIGHT / 2
#     ypos_delta = 0
#     # adjust dimensions if needed
#     # width = int(math.ceil(max(SCREEN_WIDTH, xmax - xmin if xmin is not None and xmax is not None else 0)))
#     # height = int(math.ceil(max(SCREEN_HEIGHT, ymax - ymin if ymin is not None and ymax is not None else 0)))
#     width = SCREEN_WIDTH
#     height = SCREEN_HEIGHT
#     # if debug > 0:
#     #     print(f"height: {height} width: {width} xpos_delta: {xpos_delta} ypos_delta: {ypos_delta}")
#     return SvgDocInfo(height=height, width=width, xpos_delta=xpos_delta, ypos_delta=ypos_delta)
