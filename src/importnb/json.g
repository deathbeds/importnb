// a lark grammar for parsing notebooks into source
// this grammar extracts a subset of nbformat (cells, cell_type, source)
// to generate a line for line reconstruction of the source.

?start: value
?value: object
        | array
        | string
        | SIGNED_NUMBER      
        | "true"             
        | "false"            
        | "null"             


COLON: ":"
array  : "[" [value ("," value)*] "]"
object : "{" [_items] "}"

item: string COLON value
        
_items: item ("," item)*

string : ESCAPED_STRING
        
%import common.ESCAPED_STRING
%import common.SIGNED_NUMBER
%import common.WS
 
%ignore WS