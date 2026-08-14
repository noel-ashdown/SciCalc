SciCalc - Scientific Calculator for Autodesk Fusion
====================================================
Version 1.1.0

OVERVIEW
--------
SciCalc is a fully-featured scientific calculator that lives inside Autodesk
Fusion as a docked panel. It reads dimensions directly from your selected
geometry and lets you use those values straight in your calculations.

FEATURES
--------
Calculator
	- Full scientific calculator with trig, log, hyperbolic and root functions
	- SHIFT mode for inverse and secondary functions (asin, acos, atan, etc.)
	- DEG, RAD and GRAD angle modes
	- ENG notation, Fix decimal places, adjustable font size
	- Inline expression editing - click anywhere to position the cursor
	- Bracket balance indicator, scientific notation input (e.g. 1.5e6)
	- Ctrl+Z undo, up/down arrow history recall
	- Full keyboard and numpad support
	- Light and Dark themes
	- Compact / Full view toggle to save panel space

Persistent Data (survives Fusion updates)
	- Calculation history with notes, pin and search
	- Named variables
	- Expression bookmarks
	- Settings (theme, font size, Fix decimal, compact mode)

Geometry Panels
	- Triangle Solver		any 3 known values -> full solution
	- Circle Geometry		any one value -> radius, diameter, area, circumference
	- Beam Section		area, Ixx, Iyy, section moduli, radii of gyration
	- Spring Calculator	rate, spring index, Wahl factor
	- Bolt / Thread Data	M1-M36 and common UNC sizes

Conversion Panels
	- Unit Conversions	12 categories including length, force, pressure, torque
	- DMS <-> Decimal		degrees/minutes/seconds conversion
	- Polar <-> Rect		coordinate conversion
	- Vector Maths		add, subtract, dot, cross, magnitude, normalise, angle
	Select a vertex or point to auto-fill vector coordinates

Selection Values
Automatically reads the active Fusion selection and displays:
	- Edge length, radius, diameter
	- Face area, cylinder/sphere/torus/cone dimensions
	- Body bounding box, volume, surface area, mass, centre of mass
	- Vertex and sketch point world coordinates
	- Distance and midpoint between two selected points
	- Angle between two selected edges
	- Angle between two selected faces (normal and dihedral)
	- Sketch lines, circles, arcs, splines, conic curves and points
	Every value has a Use button to insert it directly into the expression.

FILES
-----
	SciCalc.py			Add-in entry point
	SciCalc.manifest	Fusion registration file
	calculator.html		Calculator user interface
	help.html			Help file
	README.txt			Readme file
	INSTALL.txt			Installation guide
	icons/				Toolbar button icons (SVG + PNG)

The following data files are created automatically on first use:
	history.json		Calculation history
	variables.json		Named constants
	settings.json		UI preferences
	bookmarks.json		Saved expressions

LICENCE
-------
This add-in is provided free of charge. You are free to use, modify and
distribute it. Attribution appreciated but not required.

SUPPORT
-------
If you encounter any issues please check the Autodesk Community forums or
the Autodesk App Store listing for updates.
