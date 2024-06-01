from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum


class ActivityType(Enum):
    OTHER = "other"
    MEETING = "meeting"
    TASK = "task"
    REVIEW = "review"
    ONCALL = "oncall"
    BMS = "bms"
    DEPLOYMENT = "deployment"
    BREAK = "break"
    LEARNING = "learning"


@dataclass
class Activity:
    name: str
    start_time: datetime
    end_time: datetime = None
    category: ActivityType = None

    def __post_init__(self):
        if self.category is None:
            self.guess_category()

    def __repr__(self):
        return f"[{self.category.value}] {self.name}"

    def __str__(self):
        return self.__repr__()

    def guess_category(self):
        if "review" in self.name.lower():
            self.category = ActivityType.REVIEW
        elif any(
            ext in self.name.lower()
            for ext in ["breakfast update", "daily", "devcom", "meeting", "session"]
        ):
            self.category = ActivityType.MEETING
        elif any(ext in self.name.lower() for ext in ["breakfast", "break time"]):
            self.category = ActivityType.BREAK
        else:
            self.category = ActivityType.OTHER

    def to_line(self):
        time_format = "%H:%M"
        start_time_str = self.start_time.strftime(time_format)
        end_time_str = self.end_time.strftime(time_format)
        return "[{}] {} - {} -> {}".format(
            self.category.value, start_time_str, end_time_str, self.name
        )

    def get_duration(self):
        duration = self.end_time - self.start_time
        duration -= timedelta(microseconds=duration.microseconds)
        return duration
