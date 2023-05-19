from setuptools import setup, find_packages
import subprocess


def get_long_desc():
    """Use Pandoc to convert the readme to ReST for the PyPI."""
    try:
        return subprocess.check_output(['pandoc', '-f', 'markdown', '-t', 'rst', 'README.mdown'])
    except Exception:
        print("WARNING: The long readme wasn't converted properly")


readme = open('README.md', 'r')
long_desc = readme.read()

setup(name='python-repository-interface',
      version='0.0.1',
      description='Interface with several repositories vendors for common operations',
      long_description=long_desc,
      author='Raphaël Yancey',
      author_email='pypi@raphaelyancey.fr',
      url='https://github.com/Ircam-Web/python-repository-interface',
      packages=find_packages(),
      zip_safe=False,
      include_package_data=True,
      classifiers=[],
      install_requires=[
        "python-gitlab==1.7.0",
        "PyGithub==1.58.2",
        "markdown==3.2.1",
        "pymdown-extensions==6.3",
        "pygments==2.7.4",
        "mdx_truly_sane_lists==1.2",
        "docutils==0.14",
        "pydash",
        "bleach==4.x",
        "beautifulsoup4==4.10.0"
      ]
)
