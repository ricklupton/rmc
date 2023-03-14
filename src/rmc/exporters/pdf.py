"""Convert blocks to pdf file.

Code originally from https://github.com/lschwetlick/maxio through
https://github.com/chemag/maxio .
"""

import logging
from tempfile import NamedTemporaryFile
from subprocess import check_call

from .svg import rm_to_svg

_logger = logging.getLogger(__name__)


def rm_to_pdf(rm_path, pdf_path, debug=0):
    """Convert `rm_path` to PDF at `pdf_path`."""
    with NamedTemporaryFile(suffix=".svg") as f_temp:
        rm_to_svg(rm_path, f_temp.name)

        # use inkscape to convert svg to pdf
        check_call(["inkscape", f_temp.name, "--export-filename", pdf_path])


def svg_to_pdf(svg_file, pdf_file):
    """Read svg data from `svg_file` and write PDF data to `pdf_file`."""

    with NamedTemporaryFile("wt", suffix=".svg") as fsvg, NamedTemporaryFile("rb", suffix=".pdf") as fpdf:
        fsvg.write(svg_file.read())

        # use inkscape to convert svg to pdf
        check_call(["inkscape", fsvg.name, "--export-filename", fpdf.name])

        pdf_file.write(fpdf.read())
