import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gnucash-ixbrl",
    version="1.0",
    author="Cybermaggedon",
    author_email="mark@cyberapocalypse.co.uk",
    description="Production of iXBRL reports from GnuCash accounts",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cybermaggedon/gnucash-ixbrl",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    download_url = "https://github.com/cybermaggedon/gnucash-ixbrl/archive/refs/tags/v1.0.tar.gz",
    install_requires=[
        "requests"
    ],
    scripts=[
        "scripts/gnucash-ixbrl"
    ]
)
