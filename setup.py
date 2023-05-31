from setuptools import setup
import version_info

setup(
    name = version_info.name,
    description = version_info.description,
    version = version_info.version,
    url = version_info.url,
    author = version_info.author,
    author_email = version_info.author_email,
    
    install_requires = [
        "pyserial",
        "pandas",
        "prettytable"    
    ],
    py_modules = ["python_markers"],
)

