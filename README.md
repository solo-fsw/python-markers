# Marker Management # 
The module marker_management.py is meant for sending markers using the various digital output devices used at the FSW.

## Background information ##
> *The background information provided here is an excerpt from the SOLO wiki on markers. For more information on markers and their usage, follow the link to the SOLO wiki provided under __References__.*
 
Measuring physiological signals, such as electrocardiography (ECG), skin conductance, blood pressure, respiration, etc. is common practice within different disciplines of social and behavioral sciences. 
Usually during an experiment, a participant performs a (computer) task and physiological signals are measured simultaneously.
In order to analyze the physiological signals, it is necessary that the physiological signals are segmented into meaningful segments. These segments are usually created based on certain moments in the task.
Markers (which are managed by this python module) signal the occurrence of these moments in an experiment.

Markers are sent by stimulus presentation software such as OpenSesame or E-Prime, from the stimulus pc, via a marker cable (LPT, UsbParMarker, EVA) to the physiology hardware (e.g. Biopac or BioSemi). Markers are recorded as a continuous signal and this signal typically looks as follows:

![Example of a marker signal over time](/images/marker-signal-example.png)

These markers have the following properties:
- **A value (positive non-zero integer):** This is the value or height of the marker.
- **Start and end:** The timepoint at which the marker assumes its value is referred to as the start of a marker. When the marker releases that value is called the end.
- **Duration:** The time between the start and end of a marker is the duration of the marker.
- **Occurrence (number):** The same marker value can be sent multiple times, thus each marker has an occurrence.

At the FSW, markers are typically sent in an 8-bit format using a parallel port. Since the parallel port is no longer implemented in newer devices SOLO developed two devices capable of replacing the parallel port by converting binary signals to decimal signals and thereby facilitating a transition from the parallel port to a usb port. These devices are called _UsbParMarker_ and _Eva_. The marker_management module provides the software necessary for this conversion.

## Getting started ##

### Development ###
> Some files were omitted from the file structure as shown below. These files were automatically generated, and require no alteration after modification of the repository.

In this section we will discuss the location and function of the files found in this repository (`python-markers`). Currently, the repository has the following structure:

```
PYTHON-MARKERS
│   .gitignore
│   example.py
│   LICENSE
│   README.md
│
├───.github
│   └───workflows
│           automated-tests.yml
│
├───images
│       marker-signal-example.png
│
├───test
│   │   test_device_coupeling.py
│   └───test_logic.py
│
└───python_markers
    |   marker_management.py
    |   version_info.py
    └───GS_timing.py 

```

Files used by GitHub (for rendering this text, showing the license, etc) can be found in the root of the repository (`python-markers`), and the `.github` and `images` directories. This type of files consists of:
- `.github/workflows/automated-tests.yml`: defines the workflow for automatic testing on pull-requests
- `images/marker-signal-example.png`: the picture used for explaining background information in `README.md`
- `.gitignore`: stores a list of local files that will not be included in the repository
- `LICENSE`: stores legal information for the usage and modification of this repository
- `README.md`: this text. A quick guide for users and developers aiming to get started with the `python-markers` repository

The `test` directory holds the files used for (automated) testing of the library. `test/test_device_coupeling.py` has (unfinished) tests for detecting hardware connections. `test/test_logic.py` uses patching to test the library without needing hardware.

The main libarary code is defined in `marker_management.py`. Helperfunctions for precise time management are stored in `GS_timing.py`. An example of usage of this library is given in `example.py`.

### Using pip ###

For ease of use the library can be imported into your project using `pip install`. This can be done by entering the following command in the terminal:

```
python -m pip install git+https://github.com/solo-fsw/python-markers
```

Where python is the path to your python executable. The main library can be used with `import python_markers.marker_manager`.

### Using Conda ###

The library can also be imported into your conda environment. This method also uses pip install, but then from within the conda environment:

1. Activate your conda environment
    - For activation use: `source activate myenv`
2. Ensure git and pip are installed in the conda environment
    - They can be installed with: `conda install git pip`
3. Use pip to install the library in the conda environment
    - The command is highly similar to the one shown above: `pip install git+https://github.com/solo-fsw/python-markers`

A conda environment containing the library can also be directly made from an `environment.yml` file using the command:

```
conda env create -f environment.yml
```

An example `.yml` file (creating an environment containing `numpy` and the marker management library for `python 3.8`) is shown below:

```yml
name: sample_env
channels:
dependencies:
    - python=3.8
    - numpy
    - pip
    - pip:
        - "--editable=git+https://github.com/solo-fsw/python-markers"
```

### Using Submodules ###
> *The information provided here is a summary of the information provided by github. For more information on git submodules, follow the link to the git documentation provided under __References__.*

Alternatively, this repository can be added to your project as a git submodule. This can be done as follows:
1. Adding the submodule
    - To use the a submodule in your repository, first add it using the `git submodule` command:
```
git submodule add <https://github.com/solo-fsw/python-markers.git> marker_management
``` 
2. Update the submodule
    - After adding the submodule to your repository, update it to the latest commit using:
```
git submodule update
```

Using this repository as a git submodule has the following advantages:
- The code will be version controlled, allowing you to track changes in this repository over time
- The code will be easy to set up and use
- Using the submodule allows you to keep your repository light, only including the submodule reference instead of the whole repository

### Examples ###

Example code on using the Marker Management library can be found in the root of the repository (example.py).

This example shows how python code can be used to create a connection with the device, how to send markers through the device and how to subsequently create a log containing information about the sent markers.

For OpenSesame, the marker_manager module has been implemented in a [plugin](https://github.com/solo-fsw/opensesame_plugin_markers).


## References ##

- [SOLO wiki on markers](https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/)
- [OpenSesame Markers plugin](https://github.com/solo-fsw/opensesame_plugin_markers)
- [SOLO wiki on the UsbParMarker](https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/UsbParMarker/)
- [UsbParMarker github page](https://github.com/solo-fsw/UsbParMarker)
- [SOLO wiki on Eva](https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/EVA/)
- [Eva github page](https://github.com/solo-fsw/Eva)
- [Git documentation on submodules](https://git-scm.com/book/en/v2/Git-Tools-Submodules)