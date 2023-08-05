"""Export text content of rm files as Markdown."""
import logging

from rmscene.scene_items import ParagraphStyle
from rmscene.scene_stream import read_tree
from rmscene.text import TextDocument

# From rmscene tests: test_text_files.py
def formatted_lines(doc):
    return [(p.style.value, str(p)) for p in doc.contents]

# From rmscene tests: test_text_files.py (modfied version extract_doc)
def extract_doc(fh):
    tree = read_tree(fh)
    if tree.root_text:
        assert tree.root_text
        TextDocument.from_scene_item(tree.root_text)
    else:
        return None

def print_text(fin, fout):

    doc = extract_doc(fin)
    if doc is  None:
        print("No text content found")
    else:
        for fmt, line in formatted_lines(doc):
            if fmt == ParagraphStyle.BULLET:
                print("- " + line, file=fout)
            elif fmt == ParagraphStyle.BULLET2:
                print("  + " + line, file=fout)
            elif fmt == ParagraphStyle.BOLD:
                print("> " + line, file=fout)
            elif fmt == ParagraphStyle.HEADING:
                print("# " + line, file=fout)
            elif fmt == ParagraphStyle.PLAIN:
                print(line, file=fout)
            else:
                print(("[unknown format %s] " % fmt) + line, file=fout)
