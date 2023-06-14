from setuptools import setup, find_packages
from python_markers import version_info

setup(
    name=version_info.name,
    description=version_info.description,
    url = version_info.url,
    version=version_info.version,
    author=version_info.author,
    author_email=version_info.author_email,
    packages=["python_markers"],
    install_requires=[
        "pyserial",
        "pandas",
        "prettytable"
    ]
)
