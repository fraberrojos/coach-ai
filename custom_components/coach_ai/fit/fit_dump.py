from pathlib import Path

from .fit_parser import FitParser

data = Path("garmin.fit").read_bytes()

FitParser(data).parse()