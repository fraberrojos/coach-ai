<p align="center">
  <img src="coach-ai-banner.png" alt="Coach AI — intelligent cycling coach" width="100%">
</p>

<h1 align="center">Coach AI for Home Assistant</h1>

<p align="center">
  An AI-assisted cycling coach for training analysis, recovery insights, workout planning, and Garmin-related workflows.
</p>

<p align="center">
  <a href="https://github.com/fraberrojos/coach-ai">GitHub repository</a>
  ·
  <a href="https://github.com/fraberrojos/coach-ai/issues">Report an issue</a>
</p>

## Features

- Cycling training and load analysis.
- Recovery and training-readiness insights.
- Workout planning and adaptive training workflows.
- Garmin-related workout and training-calendar workflows.

Features depend on the connected data sources and the configuration of your Home Assistant instance.

## Installation with HACS

1. Open **HACS → Integrations**.
2. Open the menu and select **Custom repositories**.
3. Add `https://github.com/fraberrojos/coach-ai` and choose **Integration** as the category.
4. Find **Coach AI** and install it.
5. Restart Home Assistant.
6. Go to **Settings → Devices & services → Add integration** and search for **Coach AI**, if the integration has a config flow in the installed version.

## Requirements

Dependencies are declared in `custom_components/coach_ai/manifest.json`; Home Assistant installs these when the integration loads.

## Support the project ☕

If Coach AI is useful to you, you can support its continued development through **Buy Me a Coffee**. Scan the QR code below with your phone's camera.

<p align="center">
  <img src="buy-me-a-coffee-qr.png" alt="Buy Me a Coffee QR code" width="280">
</p>

<p align="center">
  <strong>Thank you for supporting Coach AI!</strong>
</p>

## Notes

- Back up your Home Assistant configuration before installing or upgrading.
- Never publish Garmin credentials, tokens, personal exports, or local secrets.
- This project is provided as-is. Review changes and test them before using the integration in a live training workflow.

## Repository layout

- `custom_components/coach_ai/` — Home Assistant integration source.
- `hacs.json` — HACS repository metadata.
- `coach-ai-banner.png` — repository header banner.
- `buy-me-a-coffee-qr.png` — project support QR code.
