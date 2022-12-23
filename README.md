# Marker Management # 
The module marker_management.py is meant for sending markers using the various digital output devices used at the FSW.

## Background information ##
Measuring physiological signals, such as electrocardiography (ECG), skin conductance, blood pressure, respiration, etc. is common practice within different disciplines of social and behavioral sciences. 
Usually during an experiment, a participant performs a (computer) task and physiological signals are measured simultaneously.
In order to analyze the physiological signals, it is necessary that the physiological signals are segmented into meaningful segments. These segments are usually created based on certain moments in the task.
Markers (which are managed by this python module) signal the occurrence of these moments in an experiment.

Markers are sent by stimulus presentation software such as OpenSesame or E-Prime, from the stimulus pc, via a marker cable (LPT, UsbParMarker, EVA) to the physiology hardware (e.g. Biopac or BioSemi). Markers are recorded as a continuous signal and this signal typically looks as follows:

![Example of a marker signal over time](marker_signal_example.png "Markdown graph example")

These markers have the following properties:
- **A value (positive non-zero integer):** This is the value or height of the marker.
- **Start and end:** The timepoint at which the marker assumes its value is referred to as the start of a marker. When the marker releases that value is called the end.
- **Duration:** The time between the start and end of a marker is the duration of the marker.
- **Occurrence (number):** The same marker value can be sent multiple times, thus each marker has an occurrence.

At the FSW, markers are typically sent in an 8-bit format using a parallel port. Since the parallel port is no longer implemented in newer devices SOLO developed two devices capable of replacing the parallel port by converting binary signals to decimal signals and thereby facilitating a transition from the parallel port to a usb port. These devices are called _UsbParMarker_ and _Eva_. The marker_management module provides the software necesarry for this conversion.

## Getting started ##


# References #
~ *Links to relevant wiki pages*.

- [SOLO wiki on markers](https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/)
- [SOLO wiki on the UsbParMarker](https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/UsbParMarker/)
- [UsbParMarker github page](https://github.com/solo-fsw/UsbParMarker)
- [SOLO wiki on Eva](https://researchwiki.solo.universiteitleiden.nl/xwiki/wiki/researchwiki.solo.universiteitleiden.nl/view/Hardware/Markers%20and%20Events/EVA/)
- [Eva github page](https://github.com/solo-fsw/Eva)

## Using Submodules ##
It is strongly recommended to add this repository as a git submodule to your project. This can be done as follows:

~ *Concise description and code snippets for using git submodules.*

## Examples ##
~ *Links to OpenSesame and psychopy examples.*