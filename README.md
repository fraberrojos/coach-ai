<p align="center">
  <img
    src="https://raw.githubusercontent.com/fraberrojos/coach-ai/main/coach-ai-banner.png"
    alt="Coach AI — intelligent cycling coach"
    width="100%"
  >
</p>

<h1 align="center">Coach AI for Home Assistant</h1>

<p align="center">
  An AI-assisted cycling coach for training analysis, recovery insights,
  adaptive workout planning, and Garmin-related workflows.
</p>

<p align="center">
  <strong>TRAIN · ANALYSE · PROGRESS</strong>
</p>

<p align="center">
  <a href="https://github.com/fraberrojos/coach-ai">
    GitHub repository
  </a>
  ·
  <a href="https://github.com/fraberrojos/coach-ai/issues">
    Report a problem
  </a>
</p>

---

## Features

- Cycling training and training-load analysis.
- Recovery and training-readiness insights.
- Adaptive workout planning.
- Training progression and performance trends.
- Garmin-related workout creation and calendar workflows.
- Home Assistant integration with sensors, entities, and services.

Available features depend on the connected data sources and the configuration of your Home Assistant instance.

## Installation with HACS

1. Open **HACS → Integrations**.
2. Open the three-dot menu and select **Custom repositories**.
3. Add the following repository URL:

   `https://github.com/fraberrojos/coach-ai`

4. Select **Integration** as the category and add the repository.
5. Search for **Coach AI** in HACS and install it.
6. Restart Home Assistant.
7. Open **Settings → Devices & services → Add integration**.
8. Search for **Coach AI** and complete the setup, if required by the installed version.

### Manual installation

1. Download or clone this repository.
2. Copy the `custom_components/coach_ai` folder into your Home Assistant configuration directory:

   `/config/custom_components/coach_ai`

3. Restart Home Assistant.
4. Open **Settings → Devices & services** and configure Coach AI, if a configuration flow is available.

Back up your Home Assistant configuration before installing or updating the integration.

## Requirements

Dependencies are declared in:

`custom_components/coach_ai/manifest.json`

Home Assistant installs the declared Python dependencies when the integration loads.

Some features require compatible data sources or additional services to be configured.

## Support Coach AI ☕

If Coach AI is useful to you, you can support its continued development through Buy Me a Coffee.

<p align="center">
  <img
    src="https://raw.githubusercontent.com/fraberrojos/coach-ai/main/buy-me-a-coffee-qr.png"
    alt="Buy Me a Coffee QR code for supporting Coach AI"
    width="280"
  >
</p>

<p align="center">
  <strong>Thank you for supporting Coach AI!</strong>
</p>

## Repository structure

```text
coach-ai/
├── custom_components/
│   └── coach_ai/
│       ├── brand/
│       │   ├── icon.png
│       │   └── logo.png
│       ├── manifest.json
│       └── ...
├── coach-ai-banner.png
├── buy-me-a-coffee-qr.png
├── hacs.json
├── LICENSE
└── README.md
