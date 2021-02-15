from setuptools import setup, find_packages
from repository import __version__
import subprocess


def get_long_desc():
    """Use Pandoc to convert the readme to ReST for the PyPI."""
    try:
        return subprocess.check_output(['pandoc', '-f', 'markdown', '-t', 'rst', 'README.mdown'])
    except:
        print("WARNING: The long readme wasn't converted properly")

readme = open('README.md', 'r')
long_desc = readme.read()

setup(name='python-repository',
    version=__version__,
    description='Interface with several repositories vendors for common operations',
    long_description=long_desc,
    author='Raphael Yancey',
    author_email='pypi@raphaelyancey.fr',
    url='https://github.com/Ircam-Web/python-repository',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    classifiers = [
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: User Interfaces",
        "Topic :: Software Development :: Version Control",
        "Topic :: Software Development :: Version Control :: Git",
    ],
    license='MIT',
    install_requires = [
        'python-gitlab==2.6.0',
        'PyGithub==1.54.1',
        'markdown==2.6.11',
        'pydash==4.9.2',
    ],
)
