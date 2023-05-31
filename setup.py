from setuptools import setup, find_packages
from python_markers import version_info

setup(
    name="marker_management",
    version="0.0.1",
    packages=["python_markers"],
    install_requires=[
        "pyserial",
        "pandas",
        "prettytable"
    ]
)
