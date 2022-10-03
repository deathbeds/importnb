## appendix
### line-for-line translation and natural error messages

a challenge with Jupyter notebooks is that they are `json` data. this poses problems:

1. every valid line of code in a Jupyter notebook is a quoted `json` string
2. `json` parsers don't have a reason to return line numbers.

#### the problem with quoted code

#### line-for-line `json` parser

python's `json` module is not pluggable in the way we need to find line numbers. since `importnb` is meant to be dependency free on installation we couldn't look to any other packages like `ujson` or `json5`. 

the need for line numbers is enough that we ship a standalone `json` grammar parser. to do this without extra dependencies we use the `lark` grammar package at build time:
* we've defined a `json.g`ramar
* we use `hatch` hooks to invoke `lark-standalone` that generates a standalone parser for the grammar. the generated file is shipped with the package.

the result of `importnb` is `json` data translated into vertically sparse, valid python code.

#### reproducibility caution with the fuzzy finder 

⚠️ fuzzy finding is not reproducible as your system will change over time. in python, "explicit is better than implicit" so defining strong fuzzy strings is best practice if you MUST use esotric names. an alternative option is to use the `importlib.import_module` machinery
