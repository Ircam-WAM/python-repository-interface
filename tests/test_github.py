import pytest

from repository.repository import Repository

@pytest.fixture
def settings():
    settings = {}
    settings['API_TOKEN'] = "xxxxxxxxxxx"
    settings['README_TESTS'] = [
        # See repository.VendorMixin._find_readme()
        ("README.md", "md"),
        ("README.rst", "rst"),
        ("README", "raw"),
        ("README.txt", "raw"),
        ("ReadMe.md", "md"),
        ("ReadMe.rst", "rst"),
        ("ReadMe", "raw"),
        ("ReadMe.txt", "raw"),
        ("readme.md", "md"),
        ("readme.rst", "rst"),
        ("readme", "raw"),
        ("readme.txt", "raw"),
    ]
    return settings

@pytest.fixture
def url():
    return "https://github.com/Ircam-WAM/TimeSide"

def test_readme(url, settings):
    repo = Repository(url=url, vendor="github", settings=settings, debug=True)
    _, readme = repo.get_readme()
    print("README", readme)



