# Whoop Integration for Home Assistant (HACS)

Native HACS-Integration — kein Docker, kein externer Server erforderlich.

## Verbesserungen gegenüber prankstr/hassio-whoop

| Problem | Diese Integration |
|---|---|
| Herzfrequenz fehlte | Live HR-Sensor via `/v1/user/measurement/heart_rate` |
| Sensoren wurden "unavailable" bei kurzem API-Fehler | Letzter bekannter Wert wird immer gehalten |
| Ein Poll-Intervall für alles | Zwei Koordinatoren: HR alle 60s, Tagesdaten alle 15min |
| Token-Ablauf führte zu Fehlern | OAuth2Session erneuert Token automatisch vor jedem Fetch |

## Voraussetzungen

1. **Whoop Developer Account** unter [developer.whoop.com](https://developer.whoop.com)
2. Neue App anlegen mit Redirect URI:
   ```
   https://<deine-ha-domain>/auth/external/callback
   ```
3. Client ID und Client Secret notieren.

## Installation via HACS

1. HACS → Integrations → Menü → **Custom repositories**
2. URL dieses Repos, Kategorie: **Integration**
3. Installieren → HA neu starten

## Einrichtung

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Whoop**
2. Client ID + Client Secret eingeben
3. OAuth2-Fenster öffnet sich → Mit Whoop-Account anmelden
4. Fertig

## Sensoren

### Tägliche Metriken (Update alle 15 Minuten)

| Sensor | Einheit |
|---|---|
| Recovery Score | % |
| HRV (RMSSD) | ms |
| Resting Heart Rate | bpm |
| SpO2 | % |
| Skin Temperature | °C |
| Sleep Performance | % |
| Sleep Efficiency | % |
| Sleep Duration | min |
| REM Sleep | min |
| Deep Sleep | min |
| Day Strain | — |
| Day Kilojoules | kJ |
| Day Average Heart Rate | bpm |
| Day Max Heart Rate | bpm |
| Latest Workout Strain | — |
| Latest Workout Avg Heart Rate | bpm |
| Latest Workout Max Heart Rate | bpm |
| Latest Workout Kilojoules | kJ |

### Live (Update alle 60 Sekunden)

| Sensor | Einheit | Hinweis |
|---|---|---|
| Heart Rate | bpm | Letztes Sample der vergangenen 5 Minuten |
