import os.path
import sys

import setuptools

PACKAGE_NAME = "arrowbic"
repository_dir = os.path.dirname(__file__)

try:
    # READ README.md for long description on PyPi.
    long_description = open("README.md", encoding="utf-8").read()
except Exception as e:
    sys.stderr.write(f"Failed to read README.md:\n  {e}\n")
    sys.stderr.flush()
    long_description = ""

__version__ = None
with open(os.path.join(repository_dir, PACKAGE_NAME, "_version.py")) as fh:
    exec(fh.read())

with open(os.path.join(repository_dir, "requirements.txt")) as f:
    requirements = f.readlines()

with open(os.path.join(repository_dir, "test-requirements.txt")) as f:
    test_requirements = f.readlines()


setuptools.setup(
    name=PACKAGE_NAME,
    author="Paul Balanca",
    version=__version__,
    description="Pythonic Apache Arrow",
    long_description=long_description,
    packages=setuptools.find_packages(),
    long_description_content_type="text/markdown",
    keywords="arrow columnar data pandas pipeline",
    license="Apache License 2.0",
    test_suite="tests",
    tests_require=test_requirements,
    python_requires=">=3.7",
    install_requires=requirements,
    extras_require={"test": test_requirements},
    package_data={PACKAGE_NAME: ["py.typed"]},
)
