// a lark grammar for parsing notebooks into source
// this grammar extracts a subset of nbformat (cells, cell_type, source)
// to generate a line for line reconstruction of the source.
             

// rules for the top level notebook.
// notebook files are json encoded and back with a json schema.
// the schema allows us to create a more specific grammar
// that is a aware of the schema supporting validation sooner in the parsing stage.
?start: nb
?nb: "{" (_nb ("," _nb)*)+ "}"
_nb: cells | metadata | nbformat | nbformat_minor
_cells: "[" cell ("," cell)* "]"
cells: _pair{ "cells", _cells }
metadata: _pair{"metadata", object}
nbformat: _pair{"nbformat", SIGNED_NUMBER}
nbformat_minor: _pair{"nbformat_minor", SIGNED_NUMBER}
cell: "{" _cell ("," _cell)* "}"

// rules for the notebook cells
_cell: source | outputs | attachments | cell_type | execution_count | metadata 
_source: "[" (string ("," string)*)? "]" | string
source: _pair{"source", _source}
outputs: _pair{"outputs", array}
attachments: _pair{"attachments", object}
cell_type: _pair{"cell_type", string}
_execution_count: "null" | SIGNED_NUMBER
execution_count: _pair{"execution_count", _execution_count}

// terminals and rules for parsing generic json.
_QUOTE: /"/
_COLON: ":"
array  : "[" [_any ("," _any)*] "]"
object : "{" items* "}"
item: string _COLON _any
items: item ("," item)*
string: STRING
_any: object
        | array
        | string
        | SIGNED_NUMBER      
        | "true"             
        | "false"            
        | "null"

_key{key}: _QUOTE key _QUOTE
_pair{key, target}: _key{key} _COLON target

        
%import common.ESCAPED_STRING -> STRING
%import common.SIGNED_NUMBER
%import common.WS
%ignore WS