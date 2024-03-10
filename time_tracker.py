from __future__ import unicode_literals

from collections import defaultdict
from datetime import datetime, timedelta
from data_models import Activity


class TimeTracker:
    def __init__(self) -> None:
        self.activities = []
        self.current_activity = None

    def log_activity(self, activity, start_time=None):
        if self.current_activity is not None:
            raise ValueError("activity_in_progress")

        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, "%H:%M")

        now = datetime.now()
        if start_time and start_time > now:
            raise ValueError("start_time_bigger_than_now")

        start_time = start_time or now
        activity = Activity(name=activity, start_time=start_time)
        self.current_activity = activity

    def finish(self, end_time=None):
        if not self.current_activity:
            raise ValueError("no_active_activity")

        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, "%H:%M")

        now = datetime.now()
        if end_time and end_time > now:
            raise ValueError("end_time_bigger_than_now")

        end_time = end_time or now
        self.current_activity.end_time = end_time
        self.activities.append(self.current_activity)
        self.current_activity = None

    def export(self):
        return "\n".join([activity.to_line() for activity in self.activities])

    def initial(self, lines):
        for line in lines.split("\n"):
            if line == "":
                continue
            if line.startswith("* "):
                line = line[2:]
            times, activity = line.split(" -> ")
            start_time, end_time = times.split(" - ")
            self.log_activity(activity, start_time=start_time)
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

        return sorted(list(activity_times.items()), key=lambda x: x[1], reverse=True)

    def stats(self):
        activity_times = self.get_activity_times()
        category_activities = self.categorize_activities()
        category_times = self.get_category_times(category_activities)

        stats = {"activities": {}}
        for category, duration in category_times.items():
            stats[f"total {category} time"] = str(duration)

        for activity_name, duration in activity_times:
            stats["activities"][activity_name] = str(duration)

        return stats
