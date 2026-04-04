import PyInstaller.__main__
import os
import sys

def build():
    # Path to the main script (the cli entry point)
    # Based on pyproject.toml: rmc = "rmc.cli:cli"
    # We'll create a small wrapper to make it easy for PyInstaller
    
    wrapper_code = """
import sys
from rmc.cli import cli

if __name__ == "__main__":
    cli()
"""
    with open("rmc_wrapper.py", "w") as f:
        f.write(wrapper_code)

    PyInstaller.__main__.run([
        'rmc_wrapper.py',
        '--onefile',
        '--name=rmc',
        '--paths=src',
        '--collect-all=rmscene',
        '--collect-all=rmc',
        '--hidden-import=rmscene',
        '--clean'
    ])
    
    # Cleanup wrapper
    if os.path.exists("rmc_wrapper.py"):
        os.remove("rmc_wrapper.py")

if __name__ == "__main__":
    build()
