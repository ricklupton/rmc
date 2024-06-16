"""Export text content of rm files as Markdown."""

from rmscene import read_tree
from rmscene import scene_items as si

from rmscene.text import TextDocument


def print_text(f, fout):
    tree = read_tree(f)

    if tree.root_text:
        print_root_text(tree.root_text, fout)


def print_root_text(root_text: si.Text, fout):
    doc = TextDocument.from_scene_item(root_text)
    for p in doc.contents:
        line = str(p)
        if p.style.value == si.ParagraphStyle.BULLET:
            fout.write("- " + line)
        elif p.style.value == si.ParagraphStyle.BULLET2:
            fout.write("  + " + line)
        elif p.style.value == si.ParagraphStyle.BOLD:
            fout.write("> " + line)
        elif p.style.value == si.ParagraphStyle.HEADING:
            fout.write("# " + line)
        elif p.style.value == si.ParagraphStyle.PLAIN:
            fout.write(line)
        else:
            fout.write(("[unknown format %s] " % p.style.value) + line)
