"""Export text content of rm files as Markdown."""

from rmscene import TextFormat
from rmscene.text import extract_text

import logging



def print_text(f, fout):
    for fmt, line in extract_text(f):
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
