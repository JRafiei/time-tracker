from __future__ import unicode_literals

from collections import defaultdict
from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from enum import Enum


class ActivityType(Enum):
    OTHER = "other"
    MEETING = "meeting"
    DEVELOP = "develop"
    REVIEW = "review"
    ONCALL = "oncall"
    DEPLOYMENT = "deployment"
    BREAK = "break"
    LEARNING = "learning"


@dataclass
class Activity:
    name: str
    start_time: datetime
    end_time: datetime = None
    category: ActivityType = ActivityType.OTHER

    def __post_init__(self):
        if self.category == ActivityType.OTHER:
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

    def to_line(self):
        time_format = "%H:%M"
        start_time_str = self.start_time.strftime(time_format)
        end_time_str = self.end_time.strftime(time_format)
        return "[{}] {} - {} -> {}".format(
            self.category.value, start_time_str, end_time_str, self.name
        )

    def get_duration(self):
        return self.end_time - self.start_time


class TimeTracker:
    def __init__(self) -> None:
        self.activities = []
        self.current_activity = None

    def log_activity(self, activity, start_time=None):
        if self.current_activity is not None:
            raise ValueError("task_in_progress")

        now = datetime.now()
        if start_time and start_time > now:
            raise ValueError("start_time_bigger_than_now")

        start_time = start_time or now
        task = Activity(name=activity, start_time=start_time)
        self.current_activity = task

    def finish(self, end_time=None):
        if not self.current_activity:
            raise ValueError("no_active_task")

        now = datetime.now()
        if end_time and end_time > now:
            raise ValueError("end_time_bigger_than_now")

        end_time = end_time or now
        self.current_activity.end_time = end_time
        self.activities.append(self.current_activity)
        self.current_activity = None

    def export(self):
        return "\n".join([task.to_line() for task in self.activities])

    def initial(self, lines):
        for line in lines.split("\n"):
            if line == "":
                continue
            if line.startswith("* "):
                line = line[2:]
            times, task = line.split(" -> ")
            start_time, end_time = times.split(" - ")
            self.log_activity(task, start_time=datetime.strptime(start_time, "%H:%M"))
            self.finish(end_time=datetime.strptime(end_time, "%H:%M"))

    def categorize_activities(self):
        category_activities = defaultdict(list)
        for task in self.activities:
            category_activities[task.category.value].append(task)

        return category_activities

    def get_total_time(self, activities):
        total_time = timedelta(0)
        for task in activities:
            duration = task.get_duration()
            total_time += duration
        return total_time

    def get_category_times(self, category_activities):
        category_times = {category: [] for category in category_activities}
        for category, activities in category_activities.items():
            category_times[category] = self.get_total_time(activities)
        return category_times

    def get_task_times(self):
        task_times = defaultdict(lambda: timedelta(0))
        for task in self.activities:
            duration = task.get_duration()
            task_times[str(task)] += duration

        return sorted(list(task_times.items()), key=lambda x: x[1], reverse=True)

    def stats(self):
        task_times = self.get_task_times()
        category_activities = self.categorize_activities()
        category_times = self.get_category_times(category_activities)

        stats = {"activities": {}}
        for category, duration in category_times.items():
            stats[f"total {category} time"] = str(duration)

        for task_name, duration in task_times:
            stats["activities"][task_name] = str(duration)

        return stats
