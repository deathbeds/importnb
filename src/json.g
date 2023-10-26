
// a lark grammar for parsing notebooks into source
// this grammar extracts a subset of nbformat (cells, cell_type, source)
// to generate a line for line reconstruction of the source.

%import common.ESCAPED_STRING -> STRING
%import common.SIGNED_NUMBER -> _NUMBER
%import common.WS
%ignore WS

_STRING: STRING

// rules for the top level notebook.
// notebook files are json encoded and back with a json schema.
// the schema allows us to create a more specific grammar
// that is a aware of the schema supporting validation sooner in the parsing stage.
?start: nb
?nb: "{" (_nb ("," _nb)*)+ "}"
_nb: cells | _metadata | _nbformat | _nbformat_minor
_cells: "[" cell ("," cell)* "]"
cells: _pair{ "cells", _cells }
_metadata: _pair{"metadata", _object}
_nbformat: _pair{"nbformat", _NUMBER}
_nbformat_minor: _pair{"nbformat_minor", _NUMBER}
cell: "{" _cell ("," _cell)* "}"

// rules for the notebook cells
_cell: source | _outputs | _attachments | cell_type | _execution_count | _metadata 
_source: "[" (string ("," string)*)? "]" | string
source: _pair{"source", _source}
_outputs: _pair{"outputs", _array}
_attachments: _pair{"attachments", _object}
_id: _pair{"id", _string}
cell_type: _pair{"cell_type", string}
_execution_count_: "null" | _NUMBER
_execution_count: _pair{"execution_count", _execution_count_}

// terminals and rules for parsing generic json.
_QUOTE: /"/
_COLON: ":"
_array  : "[" [_any ("," _any)*] "]"
_object : "{" _items* "}"
_item: _string _COLON _any
_items: _item ("," _item)*
string: STRING
_string: _STRING
_T: "true"
_F: "false"
_N: "null"
_any: _object
        | _array
        | _string
        | _NUMBER      
        | _T
        | _F
        | _N

_key{key}: _QUOTE key _QUOTE
_pair{key, target}: _key{key} _COLON target

