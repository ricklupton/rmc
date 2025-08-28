"""Convert blocks to pdf file.

Code originally from https://github.com/lschwetlick/maxio through
https://github.com/chemag/maxio .
"""

import logging
from tempfile import NamedTemporaryFile
from cairosvg import svg2pdf

from .svg import rm_to_svg

_logger = logging.getLogger(__name__)


def rm_to_pdf(rm_path, pdf_path, debug=0):
    """Convert `rm_path` to PDF at `pdf_path`."""
    with NamedTemporaryFile(suffix=".svg") as f_temp:
        rm_to_svg(rm_path, f_temp.name)
        svg2pdf(url=f_temp.name, write_to=pdf_path)


def svg_to_pdf(svg_file, pdf_file):
    """Read svg data from `svg_file` and write PDF data to `pdf_file`."""
    svg2pdf(bytestring=svg_file.getvalue().encode('utf-8'), write_to=pdf_file.name)

