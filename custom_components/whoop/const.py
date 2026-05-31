DOMAIN = "whoop"

OAUTH2_AUTHORIZE = "https://api.prod.whoop.com/oauth/oauth2/auth"
OAUTH2_TOKEN = "https://api.prod.whoop.com/oauth/oauth2/token"

SCOPES = [
    "offline",
    "read:recovery",
    "read:cycles",
    "read:workout",
    "read:sleep",
    "read:profile",
    "read:body_measurement",
]

CYCLE_UPDATE_INTERVAL_MINUTES = 10
DAILY_UPDATE_INTERVAL_MINUTES = 60

COORDINATOR_CYCLE = "coordinator_cycle"
COORDINATOR_DAILY = "coordinator_daily"
