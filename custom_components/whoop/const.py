DOMAIN = "whoop"

OAUTH2_AUTHORIZE = "https://api.prod.whoop.com/oauth/oauth2/auth"
OAUTH2_TOKEN = "https://api.prod.whoop.com/oauth/oauth2/token"

SCOPES = [
    "offline",
    "read:recovery",
    "read:sleep",
    "read:profile",
    "read:workout",
    "read:body_measurement",
    "read:cycles",
]

# Two separate update intervals
DAILY_UPDATE_INTERVAL_MINUTES = 15   # recovery, sleep, cycle, workout
HEART_RATE_UPDATE_INTERVAL_SECONDS = 60  # live heart rate

COORDINATOR_DAILY = "coordinator_daily"
COORDINATOR_HR = "coordinator_hr"
