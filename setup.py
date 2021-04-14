import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gnucash-ixbrl",
    version="1.1",
    author="Cybermaggedon",
    author_email="mark@cyberapocalypse.co.uk",
    description="Present GnuCash account in UK-style form including iXBRL",
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
    install_requires=[
    ],
    scripts=[
        "scripts/gnucash-ixbrl"
    ]
)
