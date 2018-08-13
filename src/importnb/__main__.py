from .parameterize import Parameterize
import sys
file, sys.argv = sys.argv[1], [sys.argv[0], *sys.argv[2:]]
Parameterize.load(file)