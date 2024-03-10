from __future__ import unicode_literals

from collections import defaultdict
from dataclasses import dataclass, fields
from datetime import datetime, timedelta
from enum import Enum


class TaskCategory(Enum):
    OTHER = "other"
    MEETING = "meeting"
    DEVELOP = "develop"
    REVIEW = "review"
    ONCALL = "oncall"
    DEPLOYMENT = "deployment"
    BREAK = "break"
    LEARNING = "learning"


@dataclass
class Task:
    name: str
    start_time: datetime
    end_time: datetime = None
    category: TaskCategory = TaskCategory.OTHER

    def __post_init__(self):
        if self.category == TaskCategory.OTHER:
            self.guess_category()

    def __repr__(self):
        return f"[{self.category.value}] {self.name}"

    def __str__(self):
        return self.__repr__()

    def guess_category(self):
        if "review" in self.name.lower():
            self.category = TaskCategory.REVIEW
        elif any(
            ext in self.name.lower()
            for ext in ["breakfast update", "daily", "devcom", "meeting", "session"]
        ):
            self.category = TaskCategory.MEETING
        elif any(ext in self.name.lower() for ext in ["breakfast", "break time"]):
            self.category = TaskCategory.BREAK

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
        self.tasks = []
        self.current_task = None

    def log_activity(self, activity, start_time=None):
        if self.current_task is not None:
            raise ValueError("task_in_progress")

        now = datetime.now()
        if start_time and start_time > now:
            raise ValueError("start_time_bigger_than_now")

        start_time = start_time or now
        task = Task(name=activity, start_time=start_time)
        self.current_task = task

    def finish(self, end_time=None):
        if not self.current_task:
            raise ValueError("no_active_task")

        now = datetime.now()
        if end_time and end_time > now:
            raise ValueError("end_time_bigger_than_now")

        end_time = end_time or now
        self.current_task.end_time = end_time
        self.tasks.append(self.current_task)
        self.current_task = None

    def export(self):
        return "\n".join([task.to_line() for task in self.tasks])

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

    def categorize_tasks(self):
        category_tasks = defaultdict(list)
        for task in self.tasks:
            category_tasks[task.category.value].append(task)

        return category_tasks

    def get_total_time(self, tasks):
        total_time = timedelta(0)
        for task in tasks:
            duration = task.get_duration()
            total_time += duration
        return total_time

    def get_category_times(self, category_tasks):
        category_times = {category: [] for category in category_tasks}
        for category, tasks in category_tasks.items():
            category_times[category] = self.get_total_time(tasks)
        return category_times

    def get_task_times(self):
        task_times = defaultdict(lambda: timedelta(0))
        for task in self.tasks:
            duration = task.get_duration()
            task_times[str(task)] += duration

        return sorted(list(task_times.items()), key=lambda x: x[1], reverse=True)

    def stats(self):
        task_times = self.get_task_times()
        category_tasks = self.categorize_tasks()
        category_times = self.get_category_times(category_tasks)

        stats = {"tasks": {}}
        for category, duration in category_times.items():
            stats[f"total {category} time"] = str(duration)

        for task_name, duration in task_times:
            stats["tasks"][task_name] = str(duration)

        return stats
