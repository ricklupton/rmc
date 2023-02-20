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
    if tree.root_text:
        print_root_text(tree.root_text, fout)

    JOIN_TOLERANCE = 2
    print("\n# Highlights", file=fout)
    last_pos = 0
    for item in walk_items(tree.root):
        if isinstance(item, si.GlyphRange):
            if item.start > last_pos + JOIN_TOLERANCE:
                print(file=fout)
            print(">", item.text, file=fout)
            last_pos = item.start + len(item.text)
    print(file=fout)


def print_root_text(root_text, fout):
    for fmt, line in extract_text_lines(root_text):
        if fmt == TextFormat.BULLET:
            print("- " + line, file=fout)
        elif fmt == TextFormat.BULLET2:
            print("  + " + line, file=fout)
        elif fmt == TextFormat.BOLD:
            print("> " + line, file=fout)
        elif fmt == TextFormat.HEADING:
            print("# " + line, file=fout)
        elif fmt == TextFormat.PLAIN:
            print(line, file=fout)
        else:
            print(("[unknown format %s] " % fmt) + line, file=fout)

def walk_items(item):
    if isinstance(item, si.Group):
        for child in item.children.values():
            yield from walk_items(child)
    else:
        yield item
