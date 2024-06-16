"""Convert blocks to svg file.

Code originally from https://github.com/lschwetlick/maxio through
https://github.com/chemag/maxio .
"""

import logging
import string

from rmscene import read_tree, SceneTree, CrdtId
from rmscene import scene_items as si
from rmscene.text import TextDocument

from .writing_tools import Pen

_logger = logging.getLogger(__name__)

SCREEN_WIDTH = 1404
SCREEN_HEIGHT = 1872
SCREEN_DPI = 226

SCALE = 72.0 / SCREEN_DPI

PAGE_WIDTH_PT = SCREEN_WIDTH * SCALE
PAGE_HEIGHT_PT = SCREEN_HEIGHT * SCALE
X_SHIFT = PAGE_WIDTH_PT // 2


def xx(screen_x):
    return screen_x * SCALE  # + X_SHIFT


def yy(screen_y):
    return screen_y * SCALE


TEXT_TOP_Y = -88
LINE_HEIGHTS = {
    # Tuned this line height using template grid -- it definitely seems to be
    # 71, rather than 70 or 72. Note however that it does interact a bit with
    # the initial text y-coordinate below.
    si.ParagraphStyle.PLAIN: 71,
    si.ParagraphStyle.BULLET: 35,
    si.ParagraphStyle.BOLD: 70,
    si.ParagraphStyle.HEADING: 150,

    # There appears to be another format code (value 0) which is used when the
    # text starts far down the page, which case it has a negative offset (line
    # height) of about -20?
    #
    # Probably, actually, the line height should be added *after* the first
    # line, but there is still something a bit odd going on here.
}

SVG_HEADER = string.Template("""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" height="$height" width="$width" viewBox="$viewbox">
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


def rm_to_svg(rm_path, svg_path):
    """Convert `rm_path` to SVG at `svg_path`."""
    with open(rm_path, "rb") as infile, open(svg_path, "wt") as outfile:
        tree = read_tree(infile)
        tree_to_svg(tree, outfile)


def tree_to_svg(tree: SceneTree, output):
    """Convert Blocks to SVG."""

    # add svg header
    output.write(SVG_HEADER.substitute(width=PAGE_WIDTH_PT,
                                       height=PAGE_HEIGHT_PT,
                                       viewbox=f"0 0 {PAGE_WIDTH_PT} {PAGE_HEIGHT_PT}") + "\n")

    output.write(f'    <g id="p1" style="display:inline" transform="translate({X_SHIFT},0)">\n')
    output.write('        <filter id="blurMe"><feGaussianBlur in="SourceGraphic" stdDeviation="10" /></filter>\n')

    # These special anchor IDs are for the top and bottom of the page.
    anchor_pos = {
        CrdtId(0, 281474976710654): 270,
        CrdtId(0, 281474976710655): 700,
    }
    if tree.root_text is not None:
        draw_text(tree.root_text, output, anchor_pos)
    _logger.debug("anchor_pos: %s", anchor_pos)

    draw_group(tree.root, output, anchor_pos)

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
            draw_stroke(child, output)
    output.write(f'    </g>\n')


def draw_stroke(item: si.Line, output):
    _logger.debug("Writing line: %s", item)

    # initiate the pen
    pen = Pen.create(item.tool.value, item.color.value, item.thickness_scale)

    # BEGIN stroke
    output.write(f'        <!-- Stroke tool: {item.tool.name} '
                 f'color: {item.color.name} thickness_scale: {item.thickness_scale} -->\n')
    output.write('        <polyline ')
    output.write(f'style="fill:none;stroke:{pen.stroke_color};'
                 f'stroke-width:{pen.stroke_width};opacity:{pen.stroke_opacity}" ')
    output.write(f'stroke-linecap="{pen.stroke_linecap}" ')
    output.write('points="')

    last_xpos = -1.
    last_ypos = -1.
    last_segment_width = segment_width = 0
    # Iterate through the point to form a polyline
    for point_id, point in enumerate(item.points):
        # align the original position
        xpos = point.x
        ypos = point.y
        if point_id % pen.segment_length == 0:
            segment_color = pen.get_segment_color(point.speed, point.direction, point.width, point.pressure,
                                                  last_segment_width)
            segment_width = pen.get_segment_width(point.speed, point.direction, point.width, point.pressure,
                                                  last_segment_width)
            segment_opacity = pen.get_segment_opacity(point.speed, point.direction, point.width, point.pressure,
                                                      last_segment_width)
            # UPDATE stroke
            output.write('"/>\n')
            output.write('        <polyline ')
            output.write(f'style="fill:none; stroke:{segment_color}; '
                         f'stroke-width:{segment_width:.3f}; opacity:{segment_opacity}" ')
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


def draw_text(text: si.Text, output, anchor_pos):
    output.write('    <g class="root-text" style="display:inline">\n')

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

    y_offset = TEXT_TOP_Y

    doc = TextDocument.from_scene_item(text)
    for p in doc.contents:
        y_offset += LINE_HEIGHTS[p.style.value]

        xpos = text.pos_x
        ypos = text.pos_y + y_offset
        cls = p.style.value.name.lower()
        if str(p):
            # TODO: this doesn't take into account the CrdtStr.properties (font-weight/font-style)
            output.write(f'        <!-- Text line char_id: {p.start_id} -->\n')
            output.write(f'        <text x="{xx(xpos)}" y="{yy(ypos)}" class="{cls}">{str(p).strip()}</text>\n')

        # Save y-coordinates of potential anchors
        for subp in p.contents:
            for k in subp.i:
                anchor_pos[k] = ypos

    output.write('    </g>\n')
