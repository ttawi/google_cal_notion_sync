from __future__ import print_function
from datetime import datetime, timedelta
import logging
import os.path
from time import sleep
from typing import Any, Optional
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from sys import argv, exit
from getopt import GetoptError, getopt
from google.oauth2.credentials import Credentials
from notion_client import Client

from event import Event


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# secret path
APP_CLIENT_CREDENTIAL_PATH = "secret/credentials.json"
USER_TOKEN_PAHT = "secret/token.json"
NOTION_INTEGRATION_CREDENTIAL_PATH = "secret/notion-secret.txt"

# notion
NOTION_CALENDAR_DB_ID = None

# pull interval in secs
PULL_INTERVAL = 60

# Because notion filters on time differently than google:
#   Currently ongoing event will not be returned by notion, but by google
# We will be looking at a larger time window for notion
# Google window:
#   now : now + NOTION_LOOKUP_WINDOW
# Notion window:
#   now - NOTION_LOOKUP_EXTRA_WINDOW : now + NOTION_LOOKUP_WINDOW + NOTION_LOOKUP_EXTRA_WINDOW
NOTION_LOOKUP_WINDOW = 90
NOTION_LOOKUP_EXTRA_WINDOW = 90


def __get_google_credential() -> Credentials:
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
            creds = flow.run_console(
                port=8090,
                # Enable offline access so that you can refresh an access token without
                access_type="offline",
                # Enable incremental authorization. Recommended as a best practice.
                include_granted_scopes="true",
            )
        # Save the credentials for the next run
        with open(USER_TOKEN_PAHT, "w") as token:
            token.write(creds.to_json())

    return creds


def __read_calendar(start_time: str, end_time: str) -> list[Event]:
    creds = __get_google_credential()
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API

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

    # print(events)

    return list(map(lambda _: Event.from_cal_event(_), events))


def __read_notion(start_time: str, end_time: str) -> list[Event]:
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
    date_sort = [{"property": "Date", "direction": "ascending"}]
    query_result = notion.databases.query(
        NOTION_CALENDAR_DB_ID, filter=date_filter, sorts=date_sort
    )
    notion_events = query_result["results"]
    while query_result["has_more"]:
        query_result = notion.databases.query(
            NOTION_CALENDAR_DB_ID,
            start_cursor=query_result["next_cursor"],
            filter=date_filter,
            sorts=date_sort,
        )
        notion_events.extend(query_result["results"])

    # print properties
    # print(notion_events)
    # print content
    # print(notion.blocks.children.list(notion_events[0]["id"]))

    return list(map(lambda _: Event.from_page_info(_), notion_events))


# An util function to give each page a default date equals to creation date if they do not have one
def __notion_set_date(start_cursor: Optional[str] = None):
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
            page["id"],
            properties={"Date": {"date": {"start": page["created_time"], "end": None}}},
        )
    if response["has_more"]:
        __notion_set_date(response["next_cursor"])


# Create a notion event based on google cal event
def __notion_create_page(event: Event) -> bool:
    credential = open(NOTION_INTEGRATION_CREDENTIAL_PATH, "r").readline()
    notion = Client(
        auth=credential,
    )

    # Create a page first
    parent = {"database_id": NOTION_CALENDAR_DB_ID}
    try:
        notion.pages.create(
            parent=parent, properties=event.to_property(), children=event.to_content()
        )
    except:
        logging.exception("Failed to create page")
        return False
    return True


def __notion_update_page(notion_event: Event, google_event: Event) -> bool:
    credential = open(NOTION_INTEGRATION_CREDENTIAL_PATH, "r").readline()
    notion = Client(
        auth=credential,
    )

    try:
        notion.pages.update(
            page_id=notion_event.notion_page_id,
            properties=google_event.to_property(),
        )
    except:
        logging.exception("Failed to update page")
        return False
    return True


def main(argv: list[str]) -> None:
    global NOTION_CALENDAR_DB_ID, PULL_INTERVAL

    try:
        opts, args = getopt(argv, "d:", ["data_base_id=", "pull_interval="])
    except GetoptError:
        print("app.py -d <notion_data_base_id>")
        exit(2)
    for opt, arg in opts:
        if opt in ("-d", "--data_base_id"):
            NOTION_CALENDAR_DB_ID = arg
        elif opt in ("--pull_interval"):
            PULL_INTERVAL = int(arg)
        else:
            print(
                "app.py -d <notion_data_base_id> --pull_interval <interval_between_pulls>"
            )
            exit(2)

    while True:
        try:
            now = datetime.utcnow()
            start_time = now.isoformat() + "Z"  # 'Z' indicates UTC time
            end_time = (
                now + timedelta(days=NOTION_LOOKUP_WINDOW)
            ).isoformat() + "Z"  # 'Z' indicates UTC time
            print("Start syncing @ ", start_time)

            print("Getting Google Calendar Events...")
            google_cal_events = __read_calendar(start_time, end_time)
            print("Got " + str(len(google_cal_events)))

            print("Getting Notion Pages...")
            # Because notion filters on time differently than google:
            #   Currently ongoing event will not be returned by notion, but by google
            # We will be looking at a larger time window for notion
            notion_start_time = (
                now - timedelta(days=NOTION_LOOKUP_EXTRA_WINDOW)
            ).isoformat() + "Z"  # 'Z' indicates UTC time
            notion_end_time = (
                now + timedelta(days=NOTION_LOOKUP_WINDOW + NOTION_LOOKUP_EXTRA_WINDOW)
            ).isoformat() + "Z"  # 'Z' indicates UTC time
            notion_pages = __read_notion(notion_start_time, notion_end_time)
            print("Got " + str(len(notion_pages)))

            # Try update existing notion events
            google_cal_id_to_event = {
                google_cal_event.google_cal_id: google_cal_event
                for google_cal_event in google_cal_events
                if google_cal_event.google_cal_id
            }
            updated_notion_events = [
                notion_event
                for notion_event in notion_pages
                if notion_event.google_cal_id in google_cal_id_to_event
                and (
                    datetime.fromisoformat(notion_event.start_time)
                    != datetime.fromisoformat(
                        google_cal_id_to_event[notion_event.google_cal_id].start_time
                    )
                    or datetime.fromisoformat(notion_event.end_time)
                    != datetime.fromisoformat(
                        google_cal_id_to_event[notion_event.google_cal_id].end_time
                    )
                )
            ]
            print(
                "Need to update " + str(len(updated_notion_events)) + " notion events."
            )
            updated = 0
            for notion_event in updated_notion_events:
                if __notion_update_page(
                    notion_event, google_cal_id_to_event[notion_event.google_cal_id]
                ):
                    updated += 1
            if updated > 0:
                print("Updated " + str(updated) + " pages!")

            # Find google cal events need to by synced
            synced_google_cal_ids = [
                page.google_cal_id for page in notion_pages if page.google_cal_id
            ]
            unsynced_google_cal_events = [
                event
                for event in google_cal_events
                if event.google_cal_id not in synced_google_cal_ids
            ]
            print(
                "Will sync "
                + str(len(unsynced_google_cal_events))
                + " google cal events..."
            )
            created = 0
            for event in unsynced_google_cal_events:
                if __notion_create_page(event):
                    print("Created: " + event.summary)
                    created += 1
            if created > 0:
                print("Successfully created " + str(created) + " pages!")

            print("\n")
        except:
            logging.exception("Failed to create page")

        sleep(PULL_INTERVAL)


if __name__ == "__main__":
    main(argv[1:])
