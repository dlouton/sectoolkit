import pathlib
from setuptools import find_packages, setup

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()

# This call to setup() does all the work
setup(
    name="sectoolkit",
    version="0.1.8",
    description="Tools for working with Securities and Exchange Commission (SEC) indices and filings.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/dlouton/sectoolkit",
    author="Dave Louton",
    author_email="dlouton@bryant.edu",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
    ],
    packages=find_packages(exclude=("tests",)),
    include_package_data=True,
    install_requires=["bs4", "numpy", "pandas", "xmltodict", "tqdm"],
    

    # entry_points={
    #     "console_scripts": [
    #         "realpython=reader.__main__:main",
    #     ]
    # },
)
