import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ixbrl-reporter",
    version="1.0.13",
    author="Cybermaggedon",
    author_email="mark@cyberapocalypse.co.uk",
    description="Production of iXBRL reports from templates and accounts files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cybermaggedon/ixbrl-reporter",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    download_url = "https://github.com/cybermaggedon/ixbrl-reporter/archive/refs/tags/v1.0.13.tar.gz",
    install_requires=[
        "requests", "lxml", "piecash", "PyYAML"
    ],
    scripts=[
        "scripts/ixbrl-reporter"
    ]
)
