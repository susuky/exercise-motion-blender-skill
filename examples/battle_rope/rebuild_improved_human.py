"""Create or reuse the shared muscle human."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[2] / 'rebuild_human.py'), run_name='__main__')
