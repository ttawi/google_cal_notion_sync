from __future__ import annotations
from typing import Any, Dict, List, Optional


class Event:
    def __init__(
        self,
        id: Optional[str] = None,
        google_cal_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        location: Optional[str] = None,
        summary: Optional[str] = None,
        desc: Optional[str] = None,
    ) -> None:
        self.id = id
        self.google_cal_id = google_cal_id
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.summary = summary
        self.desc = desc

    @classmethod
    def from_page_info(cls, page_info: Dict[str, Any]) -> Event:
        id = page_info.get("id")

        google_cal_id = None
        if page_info["properties"]["Google_Cal_ID"]["rich_text"]:
            google_cal_id = page_info["properties"]["Google_Cal_ID"]["rich_text"][0][
                "text"
            ]["content"]

        start_time = None
        end_time = None
        if page_info["properties"]["Date"]["date"]:
            date = page_info["properties"]["Date"]["date"]
            start_time = date["start"]
            end_time = date["end"]

        summary = None
        if page_info["properties"]["Name"]["title"]:
            title = page_info["properties"]["Name"]["title"]
            summary = title[0]["text"]["content"]
        return Event(id=id, start_time=start_time, end_time=end_time, summary=summary)

    @classmethod
    def from_cal_event(cls, google_cal_event: Dict[str, Any]) -> Event:
        return Event(
            google_cal_id=google_cal_event.get("id"),
            start_time=google_cal_event.get("start_time"),
            end_time=google_cal_event.get("end_time"),
            location=google_cal_event.get("location"),
            summary=google_cal_event.get("summary"),
            desc=google_cal_event.get("desc"),
        )

    # Convert desc to a content block list
    def to_content(self) -> List[Dict[str, Any]]:
        content = []
        return content

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
