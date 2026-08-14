# SciCalc - Scientific Calculator for Autodesk Fusion

![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS-lightgrey.svg)
![License](https://img.shields.io/badge/license-Free-green.svg)

A fully-featured scientific calculator that lives inside Autodesk Fusion as a docked panel.
SciCalc reads geometry values directly from your active selection - edges, faces, bodies
and sketch entities - and lets you use those values straight in your calculations.

---

## Features

### Calculator
- Full scientific calculator with trig, log, hyperbolic and root functions
- **SHIFT mode** for inverse and secondary functions (asin, acos, atan, log2, exp, etc.)
- **DEG, RAD and GRAD** angle modes plus **ENG** engineering notation
- Inline expression editing - click anywhere in the expression to position the cursor
- Bracket balance indicator and scientific notation input (e.g. `1.5e6`)
- `Ctrl+Z` undo, Up/Down arrow history recall
- Full keyboard and numpad support
- **Light and Dark** themes
- **Compact / Full** view toggle to save panel space

### Persistent Data
All data survives Fusion updates and restarts.
- Calculation **history** with notes, pin and search
- Named **variables**
- Expression **bookmarks**
- **Settings** - theme, font size, decimal places, compact mode

### Geometry Panels
| Panel | Description |
|-------|-------------|
| **Triangle Solver** | Enter any 3 known values (sides a, b, c / angles A, B, C) - solves the full triangle |
| **Circle Geometry** | Enter any one value - computes radius, diameter, area, circumference, arc length, sector area |
| **Beam Section Properties** | Solid rectangle, hollow rectangle, solid circle, hollow circle - area, I, S, r |
| **Spring Calculator** | Helical compression spring - rate, spring index, Wahl factor |
| **Bolt / Thread Data** | M1-M36 metric and common UNC sizes - pitch, minor diameter, stress area |

### Conversion Panels
| Panel | Description |
|-------|-------------|
| **Unit Conversions** | 12 categories: length, area, volume, mass, temperature, force, pressure, angle, speed, energy, torque, power |
| **DMS / Decimal** | Degrees / minutes / seconds conversion |
| **Polar / Rectangular** | Coordinate conversion using current angle mode |
| **Vector Maths** | Add, subtract, dot product, cross product, magnitude, normalise, angle between vectors. Select a vertex to auto-fill coordinates. |

### Selection Values
Automatically reads the active Fusion selection every 0.4 seconds.

**3D Model**
- Edge - length, radius, diameter
- Face - area, cylinder (radius, diameter, height), sphere, torus, cone
- Body - bounding box, volume, surface area, mass, centre of mass
- Vertex - world X, Y, Z coordinates
- Two vertices / points - distance and midpoint
- Two edges - angle between them
- Two faces - face normal angle and dihedral angle (or distance if parallel)

**Sketch**
- Line - length
- Circle - radius, diameter, circumference
- Arc - radius, diameter, arc length, sweep angle
- Spline - length, start / end world coordinates
- Conic curve - length, rho, start / end / apex world coordinates
- Point - sketch X/Y and world X/Y/Z

Every value has a **Use** button to insert it directly into the calculator expression.

---

## Installation

### Windows
1. Download and unzip `SciCalc.zip`
2. Copy the `SciCalc` folder to:
   ```
   %APPDATA%\Autodesk\Autodesk Fusion\API\AddIns\
   ```
3. Open Autodesk Fusion
4. Go to **Tools -> Scripts and Add-Ins** (or press `Shift+S`)
5. Click the **Add-Ins** tab
6. Find **SciCalc** in the list and tick **Run on Startup**
7. Click **Run**
8. The **Scientific Calculator** button appears in the **Inspect** toolbar panel

### macOS
1. Download and unzip `SciCalc.zip`
2. Copy the `SciCalc` folder to:
   ```
   ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/
   ```
3. Follow steps 3-8 from the Windows instructions above

### Updating
Replace `SciCalc.py`, `calculator.html`, `help.html` and the `icons` folder with the new versions.
Do **not** replace `history.json`, `variables.json`, `settings.json` or `bookmarks.json` - these contain your saved data.

### Uninstalling
1. Go to **Tools -> Scripts and Add-Ins -> Add-Ins**, select SciCalc and click **Stop**
2. Delete the `SciCalc` folder from the AddIns directory

---

## Files

| File | Description |
|------|-------------|
| `SciCalc.py` | Add-in entry point - registers toolbar button and reads Fusion selection |
| `SciCalc.manifest` | Fusion registration file |
| `calculator.html` | Calculator user interface |
| `help.html` | Built-in help documentation |
| `icons/` | Toolbar button icons (SVG + PNG) |
| `README.md` | This file |
| `INSTALL.txt` | Plain text installation guide |
| `PRIVACY.md` | Privacy policy |

The following files are created automatically on first use and are **not included** in the repository:

| File | Contents |
|------|----------|
| `history.json` | Calculation history |
| `variables.json` | Named constants |
| `settings.json` | UI preferences |
| `bookmarks.json` | Saved expressions |

---

## Privacy

SciCalc collects no data whatsoever. All saved data is stored locally on your machine only.
See [PRIVACY.md](PRIVACY.md) for the full privacy policy.

---

## Licence

Free to use, modify and distribute. Attribution appreciated but not required.

---

## Support

- Open an [issue](../../issues) on this repository for bug reports or feature requests
- Check the [Autodesk App Store](https://apps.autodesk.com) listing for updates
- Built-in help is available via the **?** button in the calculator toolbar
