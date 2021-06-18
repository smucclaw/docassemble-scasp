import pytest
from lark import Lark
from lark import Transformer

from docassemble.scasp.responseparser import annotate_indents


class JustificationTransformer(Transformer):

    def justification_tree(self, items):
        return items

    def justification_elem(self, items):
        return items[0]

    def justification(self, items):
        if type(items[0]) == str:
            # justification is single term.
            return [items[0]]
        else:
            return items[0]

    def answer(self, items):
        return items[2]

    def answer_block(self, items):
        return items[0]

    def value(self, items):
        return items[1:]

    def atom(self, items):
        return items[0].value

    def functor(self, items):
        params = ", ".join(items[1:])
        return f"{items[0]}({params})"

    def term(self, items):
        return items[0]

    def term_list(self, items):
        terms = ", ".join(items)
        return terms

    def variable(self, items):
        result = f"{items[0]}"
        if len(items) > 1:
            result += f" | {{{items[1]} {items[2]} {items[3]}}}"
        return result

json_parser = Lark(r"""

    value: query ( answer_block+ | "no models")

    query : "QUERY:?-" term "."
    answer_block: "ANSWER:" answer "MODEL:" model "BINDINGS:" (binding+)?
    answer: INT "(in" DECIMAL "ms)" justification
    justification: "JUSTIFICATION_TREE:" justification_elem ","? "global_constraint."?

    justification_tree: term ":-" "{{UP}}" justification_elem (","? justification_elem)* "."? "{{DOWN}}"
    justification_elem: term | justification_tree

    term : atom | functor | variable
    variable : VARNAME ("|" "{" VARNAME BIND_OP atom "}")?
    atom : CNAME | INT
    functor : atom "(" term_list ")"
    term_list : term ("," term)*

    model : "{" term_list "}"
    
    binding: VARNAME BIND_OP atom
    
    BIND_OP: "=" | "\="
    VARNAME: ("_"|UCASE_LETTER) ("_"|LETTER|DIGIT)*
    
    %import common.INT
    %import common.DECIMAL
    %import common.WORD
    %import common.CNAME
    %import common.UCASE_LETTER
    %import common.LETTER
    %import common.DIGIT
    %import common.SIGNED_NUMBER
    %import common.WS
    %ignore WS

    """, start='value')

model1_list = ['winner_of_game(1, testgame)',
               'player(1)',
               'player(2)',
               'game(testgame)',
               ['player_in_game(1, testgame)',
                'chs(player_in_game(1, testgame))',
                ['abducible(player_in_game(1, testgame))',
                 'abducible(player_in_game(1, testgame))']],
               ['player_in_game(2, testgame)',
                'chs(player_in_game(2, testgame))',
                ['abducible(player_in_game(2, testgame))',
                 'abducible(player_in_game(2, testgame))']],
               ['player_threw_sign(1, rock)',
                'chs(player_threw_sign(1, rock))',
                ['abducible(player_threw_sign(1, rock))',
                 'abducible(player_threw_sign(1, rock))']],
               ['player_threw_sign(2, scissors)',
                'chs(player_threw_sign(2, scissors))',
                ['abducible(player_threw_sign(2, scissors))',
                 'abducible(player_threw_sign(2, scissors))']],
               'sign_beats_sign(rock, scissors)']

disunity_list = ['winner_of_game(P | {P \= 1}, G)',
                 ['player(P | {P \= 1})',
                  'chs(player(P | {P \= 1}))',
                  ['abducible(player(P | {P \= 1}))',
                   'abducible(player(P | {P \= 1}))']],
                 ['player(1)',
                  'chs(player(1))',
                  'proved(player(1))',
                  ['abducible(player(1))',
                   'abducible(player(1))',
                   'proved(abducible(player(1)))']],
                 ['game(G)',
                  'chs(game(G))',
                  ['abducible(game(G))',
                   'abducible(game(G))']],
                 ['player_in_game(P | {P \= 1}, G)',
                  'chs(player_in_game(P | {P \= 1}, G))',
                  ['abducible(player_in_game(P | {P \= 1}, G))',
                   'abducible(player_in_game(P | {P \= 1}, G))']],
                 ['player_in_game(1, G)',
                  'chs(player_in_game(1, G))',
                  ['abducible(player_in_game(1, G))',
                   'abducible(player_in_game(1, G))']],
                 ['player_threw_sign(P | {P \= 1}, rock)',
                  'chs(player_threw_sign(P | {P \= 1}, rock))',
                  ['abducible(player_threw_sign(P | {P \= 1}, rock))',
                   'abducible(player_threw_sign(P | {P \= 1}, rock))']],
                 ['player_threw_sign(1, scissors)',
                  'chs(player_threw_sign(1, scissors))',
                  ['abducible(player_threw_sign(1, scissors))',
                   'abducible(player_threw_sign(1, scissors))']],
                 'sign_beats_sign(rock, scissors)']

no_bindings_list = ['winner_of_game(jason, game)']


@pytest.mark.parametrize("scasp_output", ["mortal"], indirect=True)
def test_mortal(scasp_output):
    scasp_output_text = scasp_output
    indents = annotate_indents(scasp_output_text)

    tree = json_parser.parse(indents)
    transformed = JustificationTransformer().transform(tree)
    assert transformed == [['mortal(socrates)', 'human(socrates)']]


@pytest.mark.parametrize("scasp_output", ["model1"], indirect=True)
def test_model1(scasp_output):
    scasp_output_text = scasp_output
    indents = annotate_indents(scasp_output_text)

    tree = json_parser.parse(indents)
    transformed = JustificationTransformer().transform(tree)
    assert transformed == [model1_list]


@pytest.mark.parametrize("scasp_output", ["model"], indirect=True)
def test_model(scasp_output):
    scasp_output_text = scasp_output
    indents = annotate_indents(scasp_output_text)

    tree = json_parser.parse(indents)
    transformed = JustificationTransformer().transform(tree)
    assert len(transformed) == 6


@pytest.mark.parametrize("scasp_output", ["disunity"], indirect=True)
def test_disunity(scasp_output):
    scasp_output_text = scasp_output
    indents = annotate_indents(scasp_output_text)

    tree = json_parser.parse(indents)
    transformed = JustificationTransformer().transform(tree)
    assert transformed == [disunity_list]


@pytest.mark.parametrize("scasp_output", ["no_model"], indirect=True)
def test_no_model(scasp_output):
    scasp_output_text = scasp_output
    indents = annotate_indents(scasp_output_text)

    tree = json_parser.parse(indents)
    transformed = JustificationTransformer().transform(tree)
    assert transformed == []


@pytest.mark.parametrize("scasp_output", ["no_bindings"], indirect=True)
def test_no_bindings(scasp_output):
    scasp_output_text = scasp_output
    indents = annotate_indents(scasp_output_text)

    tree = json_parser.parse(indents)
    transformed = JustificationTransformer().transform(tree)
    assert transformed == [no_bindings_list]
