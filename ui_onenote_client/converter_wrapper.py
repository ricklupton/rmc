import tempfile
import subprocess, sys
from pathlib import Path


class Converter:
    def __init__(self, inkml_dir: str = None):
        self.inkml_dir = Path(inkml_dir or Path(tempfile.gettempdir()))

    def convert(self, rm_path: str) -> str:
        rm_path = Path(rm_path)
        out_base = self.inkml_dir / rm_path.stem
        self.inkml_dir.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, '-m', 'rmc.cli', '-t', 'inkml', '-o', str(out_base), str(rm_path)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Conversion failed: {result.stderr.strip()}")
        xml_path = out_base.with_suffix('.xml')
        if not xml_path.exists():
            raise FileNotFoundError(f"Expected output InkML file not found: {xml_path}")
        return str(xml_path)