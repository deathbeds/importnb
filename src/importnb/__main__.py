from .parameterize import Parameterize
import sys
file = sys.argv[1] if len(sys.argv) > 1 else None

sys.argv = [sys.argv[0], *sys.argv[2:]]

file and Parameterize.load(file)