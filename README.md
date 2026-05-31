# Whoop Integration for Home Assistant

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/DennisGoss99/WhoopIntegrationHA)](https://github.com/DennisGoss99/WhoopIntegrationHA/releases)
[![GitHub Actions](https://github.com/DennisGoss99/WhoopIntegrationHA/actions/workflows/validate.yml/badge.svg)](https://github.com/DennisGoss99/WhoopIntegrationHA/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Bring your **Whoop** fitness data directly into Home Assistant — no Docker, no extra server, no hassle.

---

## Features

- **Native OAuth2** — authenticates directly in Home Assistant, no external service needed
- **25+ sensors** — Recovery, Sleep, Strain, HRV, SpO2, Skin Temperature and more
- **Smart polling** — Cycle data refreshes every 10 minutes, daily metrics every 60 minutes
- **Always available** — last known values are kept if the API is temporarily unreachable
- **HACS compatible** — install and update with one click

---

## Requirements

- Home Assistant 2023.1.0 or newer
- HACS installed
- A [Whoop Developer](https://developer.whoop.com) account with an app configured

### Whoop Developer App Setup

1. Go to [developer.whoop.com](https://developer.whoop.com) and create a new application
2. Set the **Redirect URI** to:
   ```
   https://<your-ha-domain>/auth/external/callback
   ```
3. Copy your **Client ID** and **Client Secret**

---

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations
2. Click the three-dot menu → **Custom repositories**
3. Add `https://github.com/DennisGoss99/WhoopIntegrationHA` as an **Integration**
4. Search for **Whoop** and click **Download**
5. Restart Home Assistant

### Setup

1. Go to **Settings → Devices & Services → Add Integration → Whoop**
2. Enter your **Client ID** and **Client Secret**
3. Complete the OAuth2 login in the browser popup
4. Done — your Whoop sensors will appear automatically

---

## Sensors

### Cycle — updates every 10 minutes

| Sensor | Unit | Description |
|---|---|---|
| Cycle State | — | `SCORED`, `PENDING_SLEEP`, etc. |
| Day Strain | — | Overall strain for the current day |
| Day Average Heart Rate | bpm | Average HR over the current day |
| Day Max Heart Rate | bpm | Peak HR over the current day |
| Day Kilojoules | kJ | Energy expenditure for the day |

### Recovery — updates every 60 minutes

| Sensor | Unit | Description |
|---|---|---|
| Recovery State | — | `SCORED`, `PENDING_SLEEP`, etc. |
| Recovery Score | % | Daily readiness score |
| Resting Heart Rate | bpm | Overnight resting HR |
| HRV (RMSSD) | ms | Heart rate variability |
| SpO2 | % | Blood oxygen saturation |
| Skin Temperature | °C | Overnight skin temperature |

### Sleep — updates every 60 minutes

| Sensor | Unit | Description |
|---|---|---|
| Sleep State | — | `SCORED`, `PENDING_SLEEP`, etc. |
| Sleep Performance | % | Overall sleep quality score |
| Sleep Efficiency | % | Time asleep vs. time in bed |
| Sleep Duration | min | Total time in bed |
| REM Sleep | min | REM sleep duration |
| Deep Sleep | min | Slow-wave sleep duration |
| Respiratory Rate | breaths/min | Average breathing rate during sleep |

### Workout — updates every 60 minutes

| Sensor | Unit | Description |
|---|---|---|
| Latest Workout Sport | — | Activity type (e.g. "Running") |
| Latest Workout Strain | — | Cardiovascular strain score |
| Latest Workout Avg Heart Rate | bpm | Average HR during workout |
| Latest Workout Max Heart Rate | bpm | Peak HR during workout |
| Latest Workout Kilojoules | kJ | Energy burned during workout |

### Body Measurements — updates every 60 minutes

| Sensor | Unit | Description |
|---|---|---|
| Max Heart Rate | bpm | Physiological max HR |
| Weight | kg | Body weight |
| Height | m | Body height |

---

## Notes

> **Recovery, Sleep and Workout sensors** only populate after the respective activity has been completed and scored by Whoop. Cycle sensors are available immediately.

> **No real-time heart rate** is available — the Whoop Public API does not expose a live HR endpoint. The closest values are Resting HR (from Recovery) and Day Average/Max HR (from Cycle).

---

## Contributing

Pull requests are welcome! Please target the `dev` branch.

1. Fork the repo
2. Create a feature branch from `dev`
3. Submit a PR against `dev`

---

## License

MIT — see [LICENSE](LICENSE)
