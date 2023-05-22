from setuptools import setup, find_packages

setup(name='python-repository-interface',
      version='0.1.0',
      description='Interface with several repositories vendors for common operations',
      long_description='Interface with several repositories vendors for common operations',
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
        "pymdown-extensions==9.2",
        "pygments==2.11.2",
        "mdx_truly_sane_lists==1.2",
        "docutils==0.18.1",
        "pydash",
        "bleach==4.1.0",
        "beautifulsoup4==4.10.0"
      ]
)
