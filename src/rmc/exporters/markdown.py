"""Export text content of rm files as Markdown."""

from rmscene.scene_items import ParagraphStyle
from rmscene.scene_stream import RootTextBlock, read_blocks
from rmscene.text import TextDocument


def extract_text(f):
    for block in read_blocks(f):
        if isinstance(block, RootTextBlock):
            for p in TextDocument.from_scene_item(block.value).contents:
                yield (p.style.value, str(p))



def print_text(f, fout):
    for fmt, line in extract_text(f):
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
