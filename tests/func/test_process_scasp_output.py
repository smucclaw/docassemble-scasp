import os

import pytest

from docassemble.scasp.responseparser import response, annotate_indents
from docassemble.scasp.scaspquery import process_scasp_output, extract_answers

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'test_files',
)


@pytest.mark.parametrize("scasp_data", ["model", "disunity"], indirect=True)
def test_e2e(scasp_data):
    (scasp_output, html_output) = scasp_data
    parse = response.parseString(annotate_indents(scasp_output))
    extract_answers(parse)
    assert False
