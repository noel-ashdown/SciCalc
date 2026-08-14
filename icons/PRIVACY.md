# Privacy Policy for SciCalc

**Last updated: August 2025**

## Overview

SciCalc is a scientific calculator add-in for Autodesk Fusion developed by an independent developer.
This policy explains what data SciCalc does and does not collect.

## Data Collection

SciCalc **does not collect any personal data**.

Specifically, SciCalc:

- Does **not** transmit any data to any external server or third party
- Does **not** collect usage statistics, analytics or telemetry
- Does **not** collect any personally identifiable information
- Does **not** access your Fusion designs, files or account information beyond
  reading the active selection geometry values that you explicitly request
- Does **not** have any internet connectivity

## Local Data Storage

SciCalc stores the following data **locally on your machine only**,
in files within the SciCalc add-in folder:

| File | Contents |
|------|----------|
| `history.json` | Your calculation history, including expressions, results and notes |
| `variables.json` | Named constants you have saved |
| `bookmarks.json` | Named expressions you have saved |
| `settings.json` | UI preferences (theme, font size, decimal places, compact mode) |

This data:
- Never leaves your machine
- Is never transmitted to any server
- Can be deleted at any time by removing these files
- Is stored in plain JSON format that you can read and edit directly

## Fusion Integration

SciCalc reads geometry values (lengths, areas, radii, angles etc.) from your
active Autodesk Fusion selection when you select entities in the Fusion canvas.
This data is used only to display values in the Selection Values panel and is
never stored permanently or transmitted anywhere.

## Third Party Services

SciCalc uses no third party services, SDKs, analytics platforms or advertising networks.

## Children's Privacy

SciCalc does not knowingly collect any information from anyone, including children.

## Changes to This Policy

If this policy is updated, the updated version will be published at this location
with a revised date.

## Contact

If you have any questions about this privacy policy please open an issue on the
[SciCalc GitHub repository](https://github.com/yourusername/SciCalc) or contact
via the Autodesk App Store listing.
