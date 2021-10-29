from __future__ import print_function
import datetime
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

APP_CLIENT_CREDENTIAL_PATH = 'secret/credentials.json'
USER_TOKEN_PAHT = 'secret/token.json'

def read_cred() -> Credentials:
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(USER_TOKEN_PAHT):
        creds = Credentials.from_authorized_user_file(USER_TOKEN_PAHT, SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                APP_CLIENT_CREDENTIAL_PATH, SCOPES
            )
            # OAuth through an offline way to work w/ faceless docker env.
            creds = flow.run_console(port=8090)
        # Save the credentials for the next run
        with open(USER_TOKEN_PAHT, "w") as token:
            token.write(creds.to_json())

    return creds


def read_calendar() -> None:
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = read_cred()
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    two_yr_later = (
        datetime.datetime.utcnow() + datetime.timedelta(days=365 * 2)
    ).isoformat() + "Z"  # 'Z' indicates UTC time
    print(two_yr_later)

    print("Getting the upcoming events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            timeMax=two_yr_later,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])

    if not events:
        print("No upcoming events found.")
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["start"].get("dateTime", event["start"].get("date"))
        print(start, end, event["summary"])


if __name__ == "__main__":
    read_calendar()
