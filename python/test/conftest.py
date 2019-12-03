import pytest

def pytest_addoption(parser):
    parser.addoption(
        "--conformance-data",
        action="store",
        help="absolute path to the charls conformance test folder"
    )

@pytest.fixture
def conformance(request):
    return request.config.getoption("--conformance-data")