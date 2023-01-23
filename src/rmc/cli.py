"""CLI for converting rm files."""

import os
import sys
import io
from pathlib import Path
from contextlib import contextmanager
import click
from rmscene import read_blocks, write_blocks, TextFormat
from rmscene.text import extract_text, simple_text_document
from .exporters.svg import blocks_to_svg
from .exporters.pdf import svg_to_pdf


@click.command
@click.option("-f", "--from", "from_")
@click.option("-t", "--to")
@click.option("-o", "--output", type=click.Path())
@click.argument("input", nargs=-1, type=click.Path(exists=True))
def cli(from_, to, output, input):
    input = [Path(p) for p in input]
    if output is not None:
        output = Path(output)

    if from_ is None:
        if not input:
            raise click.UsageError("Must specify input filename or --from")
        from_ = guess_format(input[0])
    if to is None:
        if output is None:
            raise click.UsageError("Must specify --output or --to")
        to = guess_format(output)

    if from_ == "rm":
        with open_output(to, output) as fout:
            for fn in input:
                convert_rm(Path(fn), to, fout)
    elif from_ == "markdown":
        text = "".join(
            Path(fn).read_text() for fn in input
        )
        with open_output(to, output) as fout:
            convert_text(text, fout)
    else:
        raise click.UsageError("source format %s not implemented yet" % from_)


@contextmanager
def open_output(to, output):
    to_binary = to in ("pdf", "rm")
    if output is None:
        # Write to stdout
        if to_binary:
            with os.fdopen(sys.stdout.fileno(), "wb", closefd=False) as f:
                yield f
        else:
            yield sys.stdout
    else:
        with open(output, "w" + ("b" if to_binary else "t")) as f:
            yield f


def guess_format(p: Path):
    # XXX could be neater
    if p.suffix == ".rm":
        return "rm"
    if p.suffix == ".svg":
        return "svg"
    elif p.suffix == ".pdf":
        return "pdf"
    elif p.suffix == ".md" or p.suffix == ".markdown":
        return "markdown"
    else:
        return "blocks"


def convert_rm(filename: Path, to, fout):
    with open(filename, "rb") as f:
        if to == "blocks":
            pprint_file(f, fout)
        elif to == "markdown":
            print_text(f, fout)
        elif to == "svg":
            blocks = read_blocks(f)
            blocks_to_svg(blocks, fout)
        elif to == "pdf":
            buf = io.StringIO()
            blocks = read_blocks(f)
            blocks_to_svg(blocks, buf)
            buf.seek(0)
            svg_to_pdf(buf, fout)
        else:
            raise click.UsageError("Unknown format %s" % to)


def pprint_file(f, fout) -> None:
    import pprint
    result = read_blocks(f)
    for el in result:
        print(file=fout)
        pprint.pprint(el, stream=fout)


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


def convert_text(text, fout):
    write_blocks(fout, simple_text_document(text))


if __name__ == "__main__":
    cli()
