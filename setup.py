import pathlib
from setuptools import setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="readlif",
    version="0.1.0",
    description="Fast Leica LIF file reader written in python",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/nimne/readlif",
    author="Nick Negretti",
    author_email="nick.negretti@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
    packages=["readlif"],
    include_package_data=True,
    install_requires=["Pillow>=4.2.0"],
    test_suite='unittest2.collector'
)