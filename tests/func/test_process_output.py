import os

import pytest

from docassemble.scasp.scaspquery import display_list_from_lists, process_output
from docassemble.scasp.scaspquery import display_list

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'test_files',
)

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


@pytest.mark.parametrize("scasp_data", ["mortal", "model", "disunity"], indirect=True)
def test_e2e(scasp_data):
    (scasp_output, html_output) = scasp_data
    output = process_output(scasp_output)
    assert output["answers"][0]["models"][0]["explanations"] == html_output


@pytest.mark.parametrize("scasp_data", ["disunity"], indirect=True)
def test_display_tree_disunity(scasp_data):
    (_, html_output) = scasp_data
    old = display_list(disunity)
    assert old == html_output


@pytest.mark.parametrize("scasp_data", ["model"], indirect=True)
def test_display_tree_model(scasp_data):
    (_, html_output) = scasp_data
    old = display_list(model)
    assert old == html_output


@pytest.mark.parametrize("scasp_data", ["mortal"], indirect=True)
def test_display_tree_mortal(scasp_data):
    (_, html_output) = scasp_data
    old = display_list(mortal)
    assert old == html_output


@pytest.mark.parametrize("scasp_data", ["disunity"], indirect=True)
def test_display_list_disunity(scasp_data):
    (_, html_output) = scasp_data
    old = display_list_from_lists(disunity_list)
    assert old == html_output


@pytest.mark.parametrize("scasp_data", ["model"], indirect=True)
def test_display_list_model(scasp_data):
    (_, html_output) = scasp_data
    old = display_list_from_lists(model_list)
    assert old == html_output


@pytest.mark.parametrize("scasp_data", ["mortal"], indirect=True)
def test_display_list_mortal(scasp_data):
    (_, html_output) = scasp_data
    old = display_list_from_lists(mortal_list)
    assert old == html_output
