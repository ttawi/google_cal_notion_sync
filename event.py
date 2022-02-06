from __future__ import annotations
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


class Event:
    def __init__(
        self,
        notion_page_id: Optional[str] = None,
        google_cal_id: Optional[str] = None,
        google_cal_link: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        location: Optional[str] = None,
        summary: Optional[str] = None,
        desc: Optional[str] = None,
    ) -> None:
        self.notion_page_id = notion_page_id
        self.google_cal_id = google_cal_id
        self.google_cal_link = google_cal_link
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.summary = summary
        self.desc = desc

    @classmethod
    def from_page_info(cls, page_info: Dict[str, Any]) -> Event:
        notion_page_id = page_info.get("id")

        google_cal_id = None
        if page_info["properties"]["Google Cal ID"]["rich_text"]:
            google_cal_id = page_info["properties"]["Google Cal ID"]["rich_text"][0][
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
        return Event(
            notion_page_id=notion_page_id,
            google_cal_id=google_cal_id,
            start_time=start_time,
            end_time=end_time,
            summary=summary,
        )

    @classmethod
    def from_cal_event(cls, google_cal_event: Dict[str, Any]) -> Event:
        # all-day event & time-specific event in google cal are different
        all_day_event = google_cal_event.get("start", {}).get("date")
        if all_day_event:
            # if it is all-day event, end time in google cal is exclusive
            start_time = google_cal_event.get("start", {}).get("date")
            end_time = google_cal_event.get("end", {}).get("date")
            end_time = (
                (datetime.fromisoformat(end_time) - timedelta(days=1))
                .date()
                .isoformat()
            )
        else:
            start_time = google_cal_event.get("start", {}).get("dateTime")
            end_time = google_cal_event.get("end", {}).get("dateTime")

        return Event(
            google_cal_id=google_cal_event.get("id"),
            google_cal_link=google_cal_event.get("htmlLink"),
            start_time=start_time,
            end_time=end_time,
            location=google_cal_event.get("location"),
            summary=google_cal_event.get("summary"),
            desc=google_cal_event.get("description"),
        )

    # Convert desc to a content block list
    def to_content(self) -> List[Dict[str, Any]]:
        content = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "text": [
                        {
                            "type": "text",
                            "text": {
                                "content": "Calendar Link",
                                "link": {"url": self.google_cal_link},
                            },
                            "annotations": {
                                "bold": False,
                                "italic": False,
                                "strikethrough": False,
                                "underline": False,
                                "code": False,
                                "color": "default",
                            },
                            "plain_text": "Calendar Link",
                            "href": self.google_cal_link,
                        }
                    ]
                },
            }
        ]
        if self.location:
            content.append(
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "text": [{"type": "text", "text": {"content": "Location"}}]
                    },
                },
            )
            content.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": self.location,
                                },
                            }
                        ]
                    },
                },
            )

        if self.desc:
            content.append(
                {
                    "object": "block",
                    "type": "heading_1",
                    "heading_1": {
                        "text": [{"type": "text", "text": {"content": "Description"}}]
                    },
                },
            )
            content.append(
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "text": [
                            {
                                "type": "text",
                                "text": {
                                    # Limit the desc length to 2000
                                    "content": self.desc[:2000],
                                },
                            }
                        ]
                    },
                },
            )
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
                        "name": "From calendar",
                        "color": "red",
                    }
                ],
            },
            "Date": date,
            "Google Cal ID": google_cal_id,
            "Name": name,
        }
