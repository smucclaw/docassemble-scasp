import pytest
from lark import Lark
from lark import Transformer


class MyTransformer(Transformer):

    def justification_tree(self, items):
        x = f"Head: {items[0]}, justified by {items[1]}"
        print(x)
        return x

    def atom(self, items):
        # Here we always get [Term(XX, value)]
        return items[0].value

    def functor(self, items):
        params = ", ".join(items[1:])
        return f"{items[0]}({params})"

    def term(self, items):
        # Here we always get [Term(XX, value)]
        return items[0]

    def term_list(self, items):
        terms = ", ".join(items[1:])
        return terms

json_parser = Lark(r"""
    ?value: query answer_block+

    query : "QUERY:?-" term "."
    answer_block: "ANSWER:" answer "MODEL:" model "BINDINGS:" binding+
    answer: INT "(in" DECIMAL "ms)" justification
    justification: "JUSTIFICATION_TREE:" justification_tree "global_constraint."?
    justification_tree: term ":-" justification_elem (","? justification_elem)* "."
    justification_elem: term | justification_tree

    term : atom | functor
    atom : CNAME | INT
    functor : atom "(" term_list ")" 
    term_list : term ("," term)*

    model : "{" term_list "}"
    
    binding: WORD "=" atom
    
    %import common.INT
    %import common.DECIMAL
    %import common.WORD
    %import common.CNAME
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS

    """, start='value')


@pytest.mark.parametrize("scasp_output", ["mortal", "model1"], indirect=True)
def test_1(scasp_output):
    scasp_output_text = scasp_output
    tree = json_parser.parse(scasp_output_text)
    MyTransformer().transform(tree)
    print(tree.pretty())

