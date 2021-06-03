import os

import pytest

FIXTURE_DIR = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'test_files',
)

@pytest.fixture
def scasp_tree(request):
    filename = os.path.join(FIXTURE_DIR, request.param)
    f = open(filename, 'r')
    file_content = f.read()
    yield file_content
    f.close()


@pytest.fixture
def scasp_data(request):
    scasp_output_filename = f"scasp_output_{request.param}.txt"
    scasp_output_full_filename = os.path.join(FIXTURE_DIR, scasp_output_filename)

    html_output_filename = f"{request.param}_explanation.html"
    html_output_full_filename = os.path.join(FIXTURE_DIR, html_output_filename)

    with open(scasp_output_full_filename) as scasp_output:
        with open(html_output_full_filename) as html_output:
            yield scasp_output.read(), html_output.read()


@pytest.fixture
def scasp_tree(request):
    scasp_output_filename = f"scasp_tree_{request.param}.txt"
    scasp_output_full_filename = os.path.join(FIXTURE_DIR, scasp_output_filename)

    html_output_filename = f"{request.param}_explanation.html"
    html_output_full_filename = os.path.join(FIXTURE_DIR, html_output_filename)

    with open(scasp_output_full_filename) as scasp_output:
        with open(html_output_full_filename) as html_output:
            yield scasp_output.read(), html_output.read()