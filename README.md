# Coach AI for Home Assistant

Coach AI is a custom Home Assistant integration for cycling training analysis, recovery insights, workout planning, and Garmin-related workflows.

## Installation

This repository is structured as a Home Assistant custom integration repository.

1. In HACS, open **Integrations**.
2. Open the menu and choose **Custom repositories**.
3. Add this repository URL and select **Integration** as the category.
4. Find **Coach AI**, install it, and restart Home Assistant.
5. Add the integration from **Settings → Devices & services** if the integration provides a config flow.

## Requirements

Dependencies are declared in `custom_components/coach_ai/manifest.json` and are installed by Home Assistant.

## Notes

- Back up your Home Assistant configuration before installing or upgrading.
- Do not publish Garmin credentials, tokens, personal exports, or local secrets.
- This project is provided as-is; review the code and test changes before using them in a live training workflow.

## Repository layout

- `custom_components/coach_ai/` — integration source.
- `hacs.json` — HACS repository metadata.
