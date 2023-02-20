"""Export text content of rm files as Markdown."""

from rmscene import TextFormat, read_blocks
from rmscene.text import extract_text_lines

from rmscene import scene_items as si
from rmscene.scene_tree import SceneTree
from rmscene.scene_stream import build_tree

import logging



def print_text(f, fout):
    tree = SceneTree()
    build_tree(tree, read_blocks(f))

    # Find out what anchor characters are used
    anchor_ids = set(collect_anchor_ids(tree.root))

    if tree.root_text:
        print_root_text(tree.root_text, fout, anchor_ids)

    JOIN_TOLERANCE = 2
    print("\n\n# Highlights", file=fout)
    last_pos = 0
    for item in walk_items(tree.root):
        if isinstance(item, si.GlyphRange):
            if item.start > last_pos + JOIN_TOLERANCE:
                print(file=fout)
            print(">", item.text, file=fout)
            last_pos = item.start + len(item.text)
    print(file=fout)


def print_root_text(root_text, fout, anchor_ids):
    for fmt, line, ids in extract_text_lines(root_text):
        annotated_line = annotate_anchor_ids(anchor_ids, line, ids)
        if fmt == TextFormat.BULLET:
            fout.write("- " + annotated_line)
        elif fmt == TextFormat.BULLET2:
            fout.write("  + " + annotated_line)
        elif fmt == TextFormat.BOLD:
            fout.write("> " + annotated_line)
        elif fmt == TextFormat.HEADING:
            fout.write("# " + annotated_line)
        elif fmt == TextFormat.PLAIN:
            fout.write(annotated_line)
        else:
            fout.write(("[unknown format %s] " % fmt) + annotated_line)


def annotate_anchor_ids(anchor_ids, line, ids):
    """Annotate appearances of `anchor_ids` in `line`."""
    result = ""
    for char, char_id in zip(line, ids):
        if char_id in anchor_ids:
            result += f"<<{char_id.part1},{char_id.part2}>>"
        result += char
    return result


def walk_items(item):
    if isinstance(item, si.Group):
        for child in item.children.values():
            yield from walk_items(child)
    else:
        yield item


def collect_anchor_ids(item):
    if isinstance(item, si.Group):
        if item.anchor_id is not None:
            yield item.anchor_id.value
        for child in item.children.values():
            yield from collect_anchor_ids(child)
