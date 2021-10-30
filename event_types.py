from typing import Any, Dict


class CalEvent:
    def __init__(
        self,
        event: Dict[str, Any]
    ) -> None:
        self.id = event["id"]
        self.location = event.get("location")
        self.start_time = event["start"]["date"]
        self.end_time = event["end"]["date"]
        self.summary = event["summary"]
        self.desc =  event.get("description")


class NotionPage:
    def __init__(
        self,
        page_info: Dict[str, Any],
    ) -> None:
        self.id = page_info["id"]

        self.google_cal_id = None
        if page_info["properties"]["Google_Cal_ID"]["rich_text"]:
            self.google_cal_id = page_info["properties"]["Google_Cal_ID"]["rich_text"][
                0
            ]["text"]["content"]

        self.start_time = None
        self.end_time = None
        if page_info["properties"]["Date"]["date"]:
            date = page_info["properties"]["Date"]["date"]
            self.start_time = date["start"]
            self.end_time = date["end"]

        self.summary = None
        if page_info["properties"]["Name"]["title"]:
            title = page_info["properties"]["Name"]["title"]
            self.summary = title[0]["text"]["content"]

    # Convert properties to a property dict to update notion
    def to_property(self) -> Dict[str, Any]:
        date = {
            "id": "YM%5DV",
            "type": "date",
            "date": {"start": "2021-10-31", "end": None},
        }
        if self.start_time or self.end_time:
            date = {
                "id": "YM%5DV",
                "type": "date",
                "date": {"start": self.start_time, "end": self.end_time},
            }

        google_cal_id = {"id": "v%7DUP", "type": "rich_text", "rich_text": []}
        if self.google_cal_id:
            google_cal_id = {
                "id": "v%7DUP",
                "type": "rich_text",
                "rich_text": [
                    {
                        "type": "text",
                        "text": {"content": self.google_cal_id, "link": None},
                        "annotations": {
                            "bold": False,
                            "italic": False,
                            "strikethrough": False,
                            "underline": False,
                            "code": True,
                            "color": "default",
                        },
                        "plain_text": self.google_cal_id,
                        "href": None,
                    }
                ],
            }

        name = {"id": "title", "type": "title", "title": []}
        if self.summary:
            name = {
                "id": "title",
                "type": "title",
                "title": [
                    {
                        "type": "text",
                        "text": {"content": self.summary, "link": None},
                        "annotations": {
                            "bold": False,
                            "italic": False,
                            "strikethrough": False,
                            "underline": False,
                            "code": False,
                            "color": "default",
                        },
                        "plain_text": self.summary,
                        "href": None,
                    }
                ],
            }
        return {
            "Tags": {
                "id": "B%5Eej",
                "type": "multi_select",
                "multi_select": [
                    {
                        "id": "0f83c03f-85f5-40ef-9f46-948779f6a8b8",
                        "name": "Cal Import",
                        "color": "red",
                    }
                ],
            },
            "Date": date,
            "Google_Cal_ID": google_cal_id,
            "Name": name,
        }
