from docassemble.scasp.scaspquery import process_output, display_list_from_lists
from docassemble.scasp.scaspquery import display_list


def test_process_output_disunity():
    file = open("/home/ruslan/code/docassemble-scasp/docassemble/scasp/data/static/example_disunity.txt")
    line = file.read()
    output = process_output(line)
    assert output == {'query': '?- winner_of_game(jason,game).', 'result': 'No'}


mortal = [
    {'text': 'socrates is mortal, because', 'depth': 0.0},
    {'text': 'socrates is human', 'depth': 1.0}
]

mortal_list = ['socrates is mortal, because',
               [
                   'socrates is human'
               ]]

model = [
    {'text': 'winner_of_game(1,testgame) :-', 'depth': 0.0},
    {'text': 'player(1),', 'depth': 1.0},
    {'text': 'player(2),', 'depth': 1.0},
    {'text': 'game(testgame),', 'depth': 1.0},
    {'text': 'player_in_game(1,testgame) :-', 'depth': 1.0},
    {'text': 'chs(player_in_game(1,testgame)),', 'depth': 2.0},
    {'text': 'abducible(player_in_game(1,testgame)) :-', 'depth': 2.0},
    {'text': 'abducible(player_in_game(1,testgame))', 'depth': 3.0},
    {'text': 'player_in_game(2,testgame) :-', 'depth': 1.0},
    {'text': 'chs(player_in_game(2,testgame)),', 'depth': 2.0},
    {'text': 'abducible(player_in_game(2,testgame)) :-', 'depth': 2.0},
    {'text': 'abducible(player_in_game(2,testgame))', 'depth': 3.0},
    {'text': 'player_threw_sign(1,rock) :-', 'depth': 1.0},
    {'text': 'chs(player_threw_sign(1,rock)),', 'depth': 2.0},
    {'text': 'abducible(player_threw_sign(1,rock)) :-', 'depth': 2.0},
    {'text': 'abducible(player_threw_sign(1,rock))', 'depth': 3.0},
    {'text': 'player_threw_sign(2,scissors) :-', 'depth': 1.0},
    {'text': 'chs(player_threw_sign(2,scissors)),', 'depth': 2.0},
    {'text': 'abducible(player_threw_sign(2,scissors)) :-', 'depth': 2.0},
    {'text': 'abducible(player_threw_sign(2,scissors))', 'depth': 3.0},
    {'text': 'sign_beats_sign(rock,scissors)', 'depth': 1.0},
    {'text': 'global_constraint', 'depth': 0.0}
]

model_list = [
    'winner_of_game(1,testgame) :-',
    [
        'player(1),',
        'player(2),',
        'game(testgame),',
        'player_in_game(1,testgame) :-',
        [
            'chs(player_in_game(1,testgame)),',
            'abducible(player_in_game(1,testgame)) :-',
            [
                'abducible(player_in_game(1,testgame))'
            ]
        ],
        'player_in_game(2,testgame) :-',
        [
            'chs(player_in_game(2,testgame)),',
            'abducible(player_in_game(2,testgame)) :-',
         [
             'abducible(player_in_game(2,testgame))']
        ],
        'player_threw_sign(1,rock) :-',
        [
            'chs(player_threw_sign(1,rock)),',
            'abducible(player_threw_sign(1,rock)) :-',
         [
             'abducible(player_threw_sign(1,rock))'
         ]
        ],
        'player_threw_sign(2,scissors) :-',
        [
            'chs(player_threw_sign(2,scissors)),',
            'abducible(player_threw_sign(2,scissors)) :-',
         [
             'abducible(player_threw_sign(2,scissors))'
         ]
        ],
        'sign_beats_sign(rock,scissors)'
    ],
    'global_constraint'
]

disunity = [{'text': 'winner_of_game(P | {P \\= 1},G) :-', 'depth': 0.0},
            {'text': 'player(P | {P \\= 1}) :-', 'depth': 1.0},
            {'text': 'chs(player(P | {P \\= 1})),', 'depth': 2.0},
            {'text': 'abducible(player(P | {P \\= 1})) :-', 'depth': 2.0},
            {'text': 'abducible(player(P | {P \\= 1}))', 'depth': 3.0},
            {'text': 'player(1) :-', 'depth': 1.0},
            {'text': 'chs(player(1)),', 'depth': 2.0},
            {'text': 'proved(player(1)),', 'depth': 2.0},
            {'text': 'abducible(player(1)) :-', 'depth': 2.0},
            {'text': 'abducible(player(1)),', 'depth': 3.0},
            {'text': 'proved(abducible(player(1)))', 'depth': 3.0},
            {'text': 'game(G) :-', 'depth': 1.0},
            {'text': 'chs(game(G)),', 'depth': 2.0},
            {'text': 'abducible(game(G)) :-', 'depth': 2.0},
            {'text': 'abducible(game(G))', 'depth': 3.0},
            {'text': 'player_in_game(P | {P \\= 1},G) :-', 'depth': 1.0},
            {'text': 'chs(player_in_game(P | {P \\= 1},G)),', 'depth': 2.0},
            {'text': 'abducible(player_in_game(P | {P \\= 1},G)) :-', 'depth': 2.0},
            {'text': 'abducible(player_in_game(P | {P \\= 1},G))', 'depth': 3.0},
            {'text': 'player_in_game(1,G) :-', 'depth': 1.0},
            {'text': 'chs(player_in_game(1,G)),', 'depth': 2.0},
            {'text': 'abducible(player_in_game(1,G)) :-', 'depth': 2.0},
            {'text': 'abducible(player_in_game(1,G))', 'depth': 3.0},
            {'text': 'player_threw_sign(P | {P \\= 1},rock) :-', 'depth': 1.0},
            {'text': 'chs(player_threw_sign(P | {P \\= 1},rock)),', 'depth': 2.0},
            {'text': 'abducible(player_threw_sign(P | {P \\= 1},rock)) :-', 'depth': 2.0},
            {'text': 'abducible(player_threw_sign(P | {P \\= 1},rock))', 'depth': 3.0},
            {'text': 'player_threw_sign(1,scissors) :-', 'depth': 1.0},
            {'text': 'chs(player_threw_sign(1,scissors)),', 'depth': 2.0},
            {'text': 'abducible(player_threw_sign(1,scissors)) :-', 'depth': 2.0},
            {'text': 'abducible(player_threw_sign(1,scissors))', 'depth': 3.0},
            {'text': 'sign_beats_sign(rock,scissors)', 'depth': 1.0},
            {'text': 'global_constraint', 'depth': 0.0}
            ]

disunity_list = [
    'winner_of_game(P | {P \\= 1},G) :-',
    [
        'player(P | {P \\= 1}) :-',
        [
            'chs(player(P | {P \\= 1})),',
            'abducible(player(P | {P \\= 1})) :-',
            [
                'abducible(player(P | {P \\= 1}))'
            ]
        ],
        'player(1) :-',
        [
            'chs(player(1)),',
            'proved(player(1)),',
            'abducible(player(1)) :-',
            [
                'abducible(player(1)),',
                'proved(abducible(player(1)))'
            ]
        ],
        'game(G) :-',
        [
            'chs(game(G)),',
            'abducible(game(G)) :-',
            [
                'abducible(game(G))'
            ]
        ],
        'player_in_game(P | {P \\= 1},G) :-',
        [
            'chs(player_in_game(P | {P \\= 1},G)),',
            'abducible(player_in_game(P | {P \\= 1},G)) :-',
            [
                'abducible(player_in_game(P | {P \\= 1},G))'
            ]
        ],
        'player_in_game(1,G) :-',
        [
            'chs(player_in_game(1,G)),',
            'abducible(player_in_game(1,G)) :-',
            [
                'abducible(player_in_game(1,G))'
            ]
        ],
        'player_threw_sign(P | {P \\= 1},rock) :-',
        [
            'chs(player_threw_sign(P | {P \\= 1},rock)),',
            'abducible(player_threw_sign(P | {P \\= 1},rock)) :-',
            [
                'abducible(player_threw_sign(P | {P \\= 1},rock))'
            ]
        ],
        'player_threw_sign(1,scissors) :-',
        [
            'chs(player_threw_sign(1,scissors)),',
            'abducible(player_threw_sign(1,scissors)) :-',
            [
                'abducible(player_threw_sign(1,scissors))'
            ]
        ],
        'sign_beats_sign(rock,scissors)'
    ],
    'global_constraint'
]


def test_display_mortal():
    old = display_list(mortal)
    new = display_list_from_lists(mortal_list)
    assert old == new


def test_display_model():
    old = display_list(model)
    new = display_list_from_lists(model_list)
    assert old == new


def test_display_disunity():
    old = display_list(disunity)
    new = display_list_from_lists(disunity_list)
    assert old == new
