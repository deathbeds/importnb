// a lark grammar for parsing notebooks into source
// this grammar extracts a subset of nbformat (cells, cell_type, source)
// to generate a line for line reconstruction of the source.

?start: nb

?value: object
        | array
        | string
        | SIGNED_NUMBER      
        | "true"             
        | "false"            
        | "null"             


_QUOTE: /"/
_COLON: ":"
array  : "[" [value ("," value)*] "]"
object : "{" items* "}"
item: string _COLON value
items: item ("," item)*
string: STRING

_key{key}: _QUOTE key _QUOTE
_pair{key, target}: _key{key} _COLON target

// notebook parts
?nb: "{" (_top ("," _top)*)+ "}"
_top: cells | metadata | nbformat | nbformat_minor
_cells: "[" cell ("," cell)* "]"
cells: _pair{ "cells", _cells }
metadata: _pair{"metadata", object}
nbformat: _pair{"nbformat", SIGNED_NUMBER}
nbformat_minor: _pair{"nbformat_minor", SIGNED_NUMBER}
cell: "{" _cell_pairs ("," _cell_pairs)* "}"

// cell parts
_cell_pairs: source | outputs | attachments | cell_type | execution_count | metadata 
_source: "[" (string ("," string)*)? "]" | string
source: _pair{"source", _source}
outputs: _pair{"outputs", array}
attachments: _pair{"attachments", object}
cell_type: _pair{"cell_type", string}
execution_count: _pair{"execution_count", value }
        
%import common.ESCAPED_STRING -> STRING
%import common.SIGNED_NUMBER
%import co`mmon.WS

%ignore WS