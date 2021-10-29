from __future__ import print_function
import datetime
import logging
import os.path
from typing import Any
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import httpx
from notion_client import Client

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# secret path
APP_CLIENT_CREDENTIAL_PATH = "secret/credentials.json"
USER_TOKEN_PAHT = "secret/token.json"
NOTION_INTEGRATION_CREDENTIAL_PATH = "secret/notion-secret.txt"

# notion
NOTION_CALENDAR_DB_ID = "56de8fb5-bae9-47b2-80bc-7c79db8b5cba"


def _get_google_credential() -> Credentials:
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


def _read_calendar(start_time: str, end_time: str) -> None:
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = _get_google_credential()
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API

    print("Getting the upcoming events")
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=start_time,
            timeMax=end_time,
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


def _read_notion(start_time: str, end_time: str) -> None:
    credential = open(NOTION_INTEGRATION_CREDENTIAL_PATH, "r").readline()
    notion = Client(
        auth=credential,
    )

    date_filter = {
        "and": [
            {"property": "Date", "date": {"on_or_after": start_time}},
            {"property": "Date", "date": {"before": end_time}},
        ]
    }
    notion_events = notion.databases.query(NOTION_CALENDAR_DB_ID, filter=date_filter)
    print(notion_events)


# An util function to give each page a default date equals to creation date if they do not have one
def _notion_set_date(start_cursor: str = None):
    credential = open(NOTION_INTEGRATION_CREDENTIAL_PATH, "r").readline()
    notion = Client(
        auth=credential,
    )

    # we can use filter but I want to play w/ cursor.
    if start_cursor:
        response = notion.databases.query(
            NOTION_CALENDAR_DB_ID, start_cursor=start_cursor
        )
    else:
        response = notion.databases.query(NOTION_CALENDAR_DB_ID)
    pages = response["results"]
    pages = list(filter(lambda page: not page["properties"]["Date"]["date"], pages))

    for page in pages:
        notion.pages.update(
            page["id"], properties={"Date": {"date": {'start': page["created_time"], 'end': None}}}
        )
    if response["has_more"]:
        _notion_set_date(response["next_cursor"])

def main() -> None:
    now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
    two_yr_later = (
        datetime.datetime.utcnow() + datetime.timedelta(days=365 * 2)
    ).isoformat() + "Z"  # 'Z' indicates UTC time
    read_notion(now, two_yr_later)

if __name__ == "__main__":
    main()
