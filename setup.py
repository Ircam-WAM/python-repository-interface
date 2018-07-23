from setuptools import setup, find_packages
from organization_themes import __version__
import subprocess

def get_long_desc():
    """Use Pandoc to convert the readme to ReST for the PyPI."""
    try:
        return subprocess.check_output(['pandoc', '-f', 'markdown', '-t', 'rst', 'README.mdown'])
    except:
        print("WARNING: The long readme wasn't converted properly")

readme = open('README.md', 'r')
long_desc = readme.read()

setup(name='python-repository-interface',
    version=__version__,
    description='Interface with several repositories vendors for common operations',
    long_description=long_desc,
    author='Raphaël Yancey',
    author_email='pypi@raphaelyancey.fr',
    url='https://github.com/Ircam-Web/python-repository-interface',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    classifiers = [],
)
