from setuptools import setup, find_packages
import python_markers.version_info as version_info
import os
import glob

# Helper to find all non-pyc files in directory:
def files(path):
	return [
		fname
		for fname in glob.glob(path) if os.path.isfile(fname)
		and not fname.endswith('.pyc')
	]



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
    # py_modules = ["python_markers"],
    packages = find_packages(include = ["python_markers.marker_management", "python_markers.version_info"])
    # data_files=[("utils",
	# 	 files("utils/*"))]
)


# from setuptools import setup, find_packages

# setup(
#     name='example',
#     version='0.1.0',
#     packages=find_packages(include=['exampleproject', 'exampleproject.*'])
# )