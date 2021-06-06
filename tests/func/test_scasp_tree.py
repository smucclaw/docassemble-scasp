import os

import pytest

from docassemble.scasp.scaspquery import make_tree, display_list, display_list_from_lists, make_tree_list, \
    get_depths_list


@pytest.mark.parametrize("scasp_tree", ["mortal", "model", "disunity"], indirect=True)
def test_e2e_tree(scasp_tree):
    (scasp_tree, html_output) = scasp_tree

    tree_map = make_tree(scasp_tree)

    assert display_list(tree_map) == html_output


@pytest.mark.parametrize("scasp_tree", ["mortal", "model", "disunity"], indirect=True)
def test_e2e_list(scasp_tree):
    (scasp_tree, html_output) = scasp_tree

    tree_list = make_tree_list(scasp_tree)

    assert display_list_from_lists(tree_list) == html_output


def test_simple():
    tree_list = get_depths_list(["socrates is mortal, because"])

    assert tree_list == ["socrates is mortal, because"]


def test_one_level():
    tree_list = get_depths_list(["socrates is mortal, because",
                                 "    socrates is human."])

    assert tree_list == ["socrates is mortal, because", ["socrates is human"]]


def test_one_level_two_elem():
    tree_list = get_depths_list(["top level message",
                                 "    second level message#1.",
                                 "    second level message#2."])

    assert tree_list == ["top level message", ["second level message#1", "second level message#2"]]


def test_drop_one_level():
    tree_list = get_depths_list(["top level message",
                                 "    second level message#1.",
                                 "        third level message#1.",
                                 "    second level message#2."])

    assert tree_list == ["top level message",
                         ["second level message#1",
                          ["third level message#1"],
                          "second level message#2"]]


def test_drop_two_levels():
    tree_list = get_depths_list(["top level message",
                                 "    second level message#1.",
                                 "        third level message#1.",
                                 "            fourth level message#1.",
                                 "    second level message#2."])

    assert tree_list == ["top level message",
                         ["second level message#1",
                          ["third level message#1",
                           ["fourth level message#1"]],
                          "second level message#2"]]
