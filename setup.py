# minimal setuptools support for installing with pip install -e .
# also, tox --devenv is calling pop install -e, so this file enables that feature to work.
from setuptools import setup

setup()
