"""Convert blocks to pdf file.

Code originally from https://github.com/lschwetlick/maxio through
https://github.com/chemag/maxio .
"""

import os
import logging
import importlib.util
from tempfile import NamedTemporaryFile
from subprocess import check_call, CalledProcessError

from .svg import rm_to_svg

_logger = logging.getLogger(__name__)

_INKSCAPE_PATHS = [
    "inkscape",
    "/Applications/Inkscape.app/Contents/MacOS/inkscape",
]


def _try_inkscape(svg_path, pdf_path):
    """Try to convert SVG to PDF using Inkscape. Returns True on success."""
    last_error = None
    for inkscape_bin in _INKSCAPE_PATHS:
        try:
            _logger.debug("Trying Inkscape at: %s", inkscape_bin)
            check_call([inkscape_bin, svg_path, "--export-filename", pdf_path])
            return True
        except FileNotFoundError:
            _logger.debug("Inkscape not found at: %s", inkscape_bin)
        except CalledProcessError as e:
            _logger.warning("Inkscape failed (exit %d): %s", e.returncode, inkscape_bin)
            last_error = e
    if last_error is not None:
        raise last_error
    return False


def _try_cairosvg(svg_path, pdf_path):
    """Try to convert SVG to PDF using cairosvg. Returns True on success."""
    if importlib.util.find_spec("cairosvg") is None:
        _logger.debug("cairosvg is not installed")
        return False
    import cairosvg
    cairosvg.svg2pdf(url=svg_path, write_to=pdf_path)
    return True


def rm_to_pdf(rm_path, pdf_path, debug=0):
    """Convert `rm_path` to PDF at `pdf_path`."""
    with NamedTemporaryFile(suffix=".svg", delete=False) as f_temp:
        tmp_svg_path = f_temp.name

    with NamedTemporaryFile(suffix=".pdf", delete=False) as f_pdf_temp:
        tmp_pdf_path = f_pdf_temp.name

    try:
        rm_to_svg(rm_path, tmp_svg_path)

        if _try_inkscape(tmp_svg_path, tmp_pdf_path):
            os.replace(tmp_pdf_path, pdf_path)
            return
        if _try_cairosvg(tmp_svg_path, tmp_pdf_path):
            os.replace(tmp_pdf_path, pdf_path)
            return

        raise RuntimeError(
            "No PDF converter found. Install Inkscape or cairosvg (pip install cairosvg)."
        )
    finally:
        os.unlink(tmp_svg_path)
        if os.path.exists(tmp_pdf_path):
            os.unlink(tmp_pdf_path)


def svg_to_pdf(svg_file, pdf_file):
    """Read svg data from `svg_file` and write PDF data to `pdf_file`."""
    with NamedTemporaryFile("w", encoding="utf-8", suffix=".svg", delete=False) as fsvg:
        fsvg.write(svg_file.read())
        tmp_svg_path = fsvg.name

    with NamedTemporaryFile(suffix=".pdf", delete=False) as fpdf:
        tmp_pdf_path = fpdf.name

    try:
        if not _try_inkscape(tmp_svg_path, tmp_pdf_path) and not _try_cairosvg(tmp_svg_path, tmp_pdf_path):
            raise RuntimeError(
                "No PDF converter found. Install Inkscape or cairosvg (pip install cairosvg)."
            )

        with open(tmp_pdf_path, "rb") as f:
            pdf_file.write(f.read())
        pdf_file.flush()
    finally:
        os.unlink(tmp_svg_path)
        os.unlink(tmp_pdf_path)
