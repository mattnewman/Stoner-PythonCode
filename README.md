Stoner-PythonCode
=================

Introduction
------------
This is the  *Stoner* Python package for writing data analysis code. It was written within the Condensed Matter Physis group at the University of Leeds as a shared resource for quickly writing simple data analysis programs.

For a general introduction, users are ferered to the User Guid pdf file that can be found in the *doc* directory. There is also an API reference in the form of a compiled help file in the *doc* directory.
 
Overview
-------- 
The **Stoner** package provides two basic top-level classes that describe an individual file of experimental data and a list (such as a directory on disc) of many experimental files.
 
**Stoner.Core.DataFile** is the base class for representing individual experimental data sets. It provides basic methods to examine and manipulate data, manage metadata and load and save data files. It has a large number of sub classes - most of these are in Stoner.FileFormats and are used to handle the loading of specific file formats. Two, however, contain additional functionality for writing analysis programs.
 
**Stoner.Folders.DataFolder** is a class for assisting with the work of processing lots of files in a common directory structure. It provides methods to list. filter and group data according to filename patterns or metadata.

**Stoner.Analysis.AnalyseFile** provides additional methods for curve-fitting, differentiating, smoothing and carrying out basic calculations on data. **Stoner.Plot.PlotFile** provides additional routines for plotting data on 2D or 3D plots. There are subclasses of **DataFile** in the **Stoner.FileFormats** module that support loading many of the common file formats used in our research.
 
Resources
---------
 
Included in the package are a (small) collection of sample scripts for carrying out various operations and some sample data files for testing the loading and processing of data. Finally, this folder contains the LaTeX source code, dvi file and pdf version of the User Guide and this compiled help file which has been gerneated from by Docygen from the contents of the python docstrings in the source code. 

Contact and Licensing
---------------------

The lead developer for this code is Dr Gavin Burnell <g.burnell@leeds.ac.uk> http://www.stoner.leeds.ac.uk/people/gb. The User Guide gives the current list of other contributors to the project.

This code and the sample data are all (C) The University of Leeds 2008-2013 unless otherwise indficated in the source file. The contents of this package are licensed under the terms of the GNU Public License v3