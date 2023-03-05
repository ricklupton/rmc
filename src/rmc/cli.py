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
from .exporters.markdown import print_text

import logging


@click.command
@click.version_option()
@click.option('-v', '--verbose', count=True)
@click.option("-f", "--from", "from_", metavar="FORMAT", help="Format to convert from (default: guess from filename)")
@click.option("-t", "--to", metavar="FORMAT", help="Format to convert to (default: guess from filename)")
@click.option("-o", "--output", type=click.Path(), help="Output filename (default: write to standard out)")
@click.argument("input", nargs=-1, type=click.Path(exists=True))
def cli(verbose, from_, to, output, input):
    """Convert to/from reMarkable v6 files.

    Available FORMATs are: `rm` (reMarkable file), `markdown`, `svg`, `pdf`,
    `blocks`, `blocks-data`.

    Formats `blocks` and `blocks-data` dump the internal structure of the `rm`
    file, with and without detailed data values respectively.

    """

    if verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)
    elif verbose >= 1:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)

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
        elif to == "blocks-data":
            pprint_file(f, fout, data=False)
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


def pprint_file(f, fout, data=True) -> None:
    import pprint
    depth = None if data else 1
    result = read_blocks(f)
    for el in result:
        print(file=fout)
        pprint.pprint(el, depth=depth, stream=fout)


def convert_text(text, fout):
    write_blocks(fout, simple_text_document(text))


if __name__ == "__main__":
    cli()
