from __future__ import unicode_literals

import re
from collections import defaultdict
from datetime import datetime, timedelta

from data_models import Activity, ActivityType


class TimeTracker:
    def __init__(self) -> None:
        self.activities = []
        self.current_activity = None

    def log_activity(self, activity, start_time=None, category_name=None):
        if self.current_activity is not None:
            raise ValueError("activity_in_progress")

        now = datetime.now()
        start_time = start_time or now

        if isinstance(start_time, str):
            temp = datetime.strptime(start_time, "%H:%M").time()
            start_time = datetime.combine(now.date(), temp)

        if start_time > now:
            raise ValueError("start_time_bigger_than_now")

        category = ActivityType(category_name) if category_name else ActivityType.OTHER
        activity = Activity(name=activity, start_time=start_time, category=category)
        self.current_activity = activity

    def finish(self, end_time=None):
        if not self.current_activity:
            raise ValueError("no_active_activity")

        start_time = self.current_activity.start_time
        now = datetime.now()
        end_time = end_time or now

        if isinstance(end_time, str):
            temp = datetime.strptime(end_time, "%H:%M").time()
            end_time = datetime.combine(start_time.date(), temp)

        if end_time > now:
            raise ValueError("end_time_bigger_than_now")

        if end_time < start_time:
            raise ValueError("end_time_less_than_start_time")

        self.current_activity.end_time = end_time
        self.activities.append(self.current_activity)
        self.current_activity = None

    def export(self):
        return "\n".join([activity.to_line() for activity in self.activities])

    def parse_line(self, line):
        if line.startswith("* "):
            line = line[2:]
        first_part, activity = line.split(" -> ")
        splitted = re.sub(r"[\[\-\]]", "", first_part).split()
        if len(splitted) == 3:
            category_name, start_time, end_time = splitted
        else:
            category_name = None
            start_time, end_time = splitted
        return activity, category_name, start_time, end_time

    def initial(self, text):
        lines = text.strip().split("\n")
        for line in lines:
            activity, category_name, start_time, end_time = self.parse_line(line)
            self.log_activity(
                activity, start_time=start_time, category_name=category_name
            )
            self.finish(end_time=end_time)

    def categorize_activities(self):
        category_activities = defaultdict(list)
        for activity in self.activities:
            category_activities[activity.category.value].append(activity)

        return category_activities

    def get_total_time(self, activities):
        total_time = timedelta(0)
        for activity in activities:
            duration = activity.get_duration()
            total_time += duration
        return total_time

    def get_category_times(self, category_activities):
        category_times = {category: [] for category in category_activities}
        for category, activities in category_activities.items():
            category_times[category] = self.get_total_time(activities)
        return category_times

    def get_activity_times(self):
        activity_times = defaultdict(lambda: timedelta(0))
        for activity in self.activities:
            duration = activity.get_duration()
            activity_times[str(activity)] += duration
        return activity_times

    def stats(self):
        activity_times = self.get_activity_times()
        category_activities = self.categorize_activities()
        category_times = self.get_category_times(category_activities)
        category_times_sorted = sorted(
            list(category_times.items()), key=lambda x: x[1], reverse=True
        )
        activity_times_sorted = sorted(
            list(activity_times.items()), key=lambda x: x[1], reverse=True
        )

        total_activity_times = sum(list(category_times.values()), timedelta(0))
        stats = {
            "activities": {},
            "activity_types": defaultdict(dict),
            "total_time": str(total_activity_times),
        }
        for category, duration in category_times_sorted:
            stats["activity_types"][category]["time"] = str(duration)
            stats["activity_types"][category]["percent"] = int(
                round(duration / total_activity_times, 2) * 100
            )

        for activity_name, duration in activity_times_sorted:
            stats["activities"][activity_name] = str(duration)

        return stats
