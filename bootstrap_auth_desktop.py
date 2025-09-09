import json, time
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/spreadsheets",
]

CLIENT_SECRET_PATH = "client-secret-desktop-test.json"
OUTPUT_OAUTH_BLOB = "google_oauth.json"

def main():
    data = json.load(open(CLIENT_SECRET_PATH, "r"))
    try:
        installed = data["installed"]
    except KeyError:
        raise SystemExit("Not a Desktop (installed) client JSON. Re-download as 'Desktop app'.")

    flow = InstalledAppFlow.from_client_config({"installed": installed}, SCOPES)

    # Local loopback (no OOB). Force refresh token issuance.
    creds = flow.run_local_server(
        host="127.0.0.1",
        port=0,
        prompt="consent",
        access_type="offline",
        include_granted_scopes="true",
    )

    if not creds.refresh_token:
        raise SystemExit(
            "Google did not return a refresh_token. "
            "Make sure you used prompt='consent', access_type='offline', and haven't suppressed consent."
        )

    blob = {
        "client_id": installed["client_id"],
        "client_secret": installed["client_secret"],
        "refresh_token": creds.refresh_token,
        # Access token is short-lived; optional to persist:
        "access_token": getattr(creds, "token", None),
        "scopes": SCOPES,
        "saved_at": int(time.time()),
    }

    with open(OUTPUT_OAUTH_BLOB, "w") as f:
        json.dump(blob, f, indent=2)

    print(f"Wrote {OUTPUT_OAUTH_BLOB}. Copy it to VPS (e.g., /etc/mybot/google_oauth.json).")

if __name__ == "__main__":
    main()
