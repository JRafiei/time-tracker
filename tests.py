from __future__ import unicode_literals

import json
import unittest
from datetime import datetime, timedelta

from data_models import Activity, ActivityType
from time_tracker import TimeTracker


class TimeTrackerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tracker = TimeTracker()
        self.start_time = datetime(2024, 1, 1, 10, 30, 0)

    def test_log_activity_set_current_activity_no_active_activity(self):
        self.tracker.log_activity("Test Line")
        self.assertIsInstance(self.tracker.current_activity, Activity)
        self.assertEqual(self.tracker.current_activity.name, "Test Line")
        self.assertIsInstance(self.tracker.current_activity.start_time, datetime)
        self.assertIsNone(self.tracker.current_activity.end_time)

    def test_log_activity_with_start_time_provided(self):
        self.tracker.log_activity("Test Line", self.start_time)
        self.assertEqual(self.tracker.current_activity.start_time, self.start_time)

    def test_log_activity_with_start_time_provided_as_string(self):
        start_time = "10:30"
        expected = datetime(year=2024, month=3, day=1, hour=10, minute=30)
        self.tracker.log_activity("Test Line", start_time)
        self.assertEqual(
            self.tracker.current_activity.start_time.time(), expected.time()
        )

    def test_activity_duration_start_time_as_datetime_end_time_as_string(self):
        end_time = "11:30"
        self.tracker.log_activity("Test Line", self.start_time)
        self.tracker.finish(end_time)

        duration = self.tracker.activities[0].get_duration()
        self.assertEqual(duration, timedelta(hours=1))

    def test_activity_duration_start_time_as_string_end_time_as_datetime(self):
        start_time = "10:30"
        end_time = datetime.now().replace(hour=11, minute=30, second=0, microsecond=0)
        self.tracker.log_activity("Test Line", start_time)
        self.tracker.finish(end_time)

        duration = self.tracker.activities[0].get_duration()
        self.assertEqual(duration, timedelta(hours=1))

    def test_log_activity_with_category_provided(self):
        self.tracker.log_activity(
            "Test Line", self.start_time, category=ActivityType.TASK
        )
        self.assertEqual(self.tracker.current_activity.category, ActivityType.TASK)

    def test_log_activity_no_category_provided_no_guess(self):
        self.tracker.log_activity("Test Line", self.start_time)
        self.assertEqual(self.tracker.current_activity.category, ActivityType.OTHER)

    def test_log_activity_no_category_provided_should_guess(self):
        self.tracker.log_activity("Review PR", self.start_time)
        self.assertEqual(self.tracker.current_activity.category, ActivityType.REVIEW)

    def test_log_activity_active_activity_exist(self):
        self.tracker.current_activity = Activity(
            name="Current Activity", start_time=self.start_time
        )

        with self.assertRaises(ValueError) as e:
            self.tracker.log_activity("Test Line")
        self.assertEqual(str(e.exception), "activity_in_progress")

    def test_finish_active_activity_exist(self):
        self.tracker.current_activity = Activity(
            name="Current Activity", start_time=self.start_time
        )

        self.assertIsNone(self.tracker.current_activity.end_time)
        self.tracker.finish()
        self.assertIsNone(self.tracker.current_activity)

    def test_finish_no_active_activity(self):
        with self.assertRaises(ValueError) as e:
            self.tracker.finish()
        self.assertEqual(str(e.exception), "no_active_activity")

    def test_finish_with_end_time_provided(self):
        self.tracker.current_activity = Activity(
            name="Current Activity", start_time=self.start_time
        )

        end_time = datetime(2024, 1, 2, 10, 30, 0)
        self.tracker.finish(end_time=end_time)
        self.assertEqual(self.tracker.activities[0].end_time, end_time)

    def test_log_activity_with_start_time_provided_as_string(self):
        self.tracker.current_activity = Activity(
            name="Current Activity", start_time=self.start_time
        )

        end_time = "10:30"
        expected = datetime(year=2024, month=1, day=2, hour=10, minute=30)
        self.tracker.finish(end_time=end_time)
        self.assertEqual(self.tracker.activities[0].end_time.time(), expected.time())

    def test_end_time_is_bigger_than_now(self):
        self.tracker.current_activity = Activity(
            name="Current Activity", start_time=self.start_time
        )

        with self.assertRaises(ValueError) as e:
            end_time = datetime.now() + timedelta(hours=1)
            self.tracker.finish(end_time=end_time)
        self.assertEqual(str(e.exception), "end_time_bigger_than_now")

    def test_end_time_is_less_than_start_time(self):
        self.tracker.current_activity = Activity(
            name="Current Activity", start_time=self.start_time
        )

        with self.assertRaises(ValueError) as e:
            end_time = self.start_time - timedelta(hours=1)
            self.tracker.finish(end_time=end_time)
        self.assertEqual(str(e.exception), "end_time_less_than_start_time")

    def test_add_current_activity_to_activities_after_finish(self):
        activity = Activity(name="Current Activity", start_time=self.start_time)
        self.tracker.current_activity = activity
        self.tracker.finish()
        self.assertEqual(self.tracker.activities, [activity])
        self.assertIsInstance(self.tracker.activities[0].end_time, datetime)

    def test_export(self):
        activity1 = Activity(
            name="Review PRs",
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 11, 30, 0),
        )

        activity2 = Activity(
            name="Update code",
            start_time=datetime(2024, 1, 1, 12, 0, 0),
            end_time=datetime(2024, 1, 1, 13, 30, 0),
        )
        self.tracker.activities = [activity1, activity2]

        lines = self.tracker.export()
        self.assertEqual(
            "[review] 10:00 - 11:30 -> Review PRs\n[other] 12:00 - 13:30 -> Update code",
            lines,
        )

    def test_initial(self):
        lines = "10:00 - 11:30 -> Task1\n12:00 - 13:30 -> Task2"

        self.tracker.initial(lines)

        self.assertEqual(self.tracker.activities[0].name, "Task1")
        self.assertEqual(
            self.tracker.activities[0].start_time.time(),
            datetime.strptime("10:00", "%H:%M").time(),
        )
        self.assertEqual(
            self.tracker.activities[0].end_time.time(),
            datetime.strptime("11:30", "%H:%M").time(),
        )
        self.assertEqual(self.tracker.activities[0].category, ActivityType.OTHER)

        self.assertEqual(self.tracker.activities[1].name, "Task2")
        self.assertEqual(
            self.tracker.activities[1].start_time.time(),
            datetime.strptime("12:00", "%H:%M").time(),
        )
        self.assertEqual(
            self.tracker.activities[1].end_time.time(),
            datetime.strptime("13:30", "%H:%M").time(),
        )
        self.assertEqual(self.tracker.activities[1].category, ActivityType.OTHER)

    def test_initial_with_category(self):
        lines = "[review] 10:00 - 11:30 -> Review PRs"
        self.tracker.initial(lines)
        self.assertEqual(self.tracker.activities[0].category, ActivityType.REVIEW)

    def test_stats(self):
        activity1 = Activity(
            name="Breakfast",
            start_time=datetime(2024, 1, 1, 10, 0, 0),
            end_time=datetime(2024, 1, 1, 10, 30, 0),
        )

        activity2 = Activity(
            name="Breakfast update",
            start_time=datetime(2024, 1, 1, 10, 30, 0),
            end_time=datetime(2024, 1, 1, 11, 15, 0),
        )

        activity3 = Activity(
            name="Review PRs",
            start_time=datetime(2024, 1, 1, 12, 0, 0),
            end_time=datetime(2024, 1, 1, 13, 30, 0),
        )

        activity4 = Activity(
            name="Update code",
            start_time=datetime(2024, 1, 1, 13, 30, 0),
            end_time=datetime(2024, 1, 1, 14, 30, 0),
            category=ActivityType.TASK,
        )

        self.tracker.activities = [activity1, activity2, activity3, activity4]

        # print(json.dumps(self.tracker.stats(), indent=4))
        self.assertEqual(
            self.tracker.stats(),
            {
                "total_time": "3:45:00",
                "activity_types": {
                    "task": {"time": "1:00:00", "percent": 27},
                    "meeting": {"time": "0:45:00", "percent": 20},
                    "break": {"time": "0:30:00", "percent": 13},
                    "review": {"time": "1:30:00", "percent": 40},
                },
                "activities": {
                    "[review] Review PRs": "1:30:00",
                    "[task] Update code": "1:00:00",
                    "[meeting] Breakfast update": "0:45:00",
                    "[break] Breakfast": "0:30:00",
                },
            },
        )


class ActivityTestCases(unittest.TestCase):
    def setUp(self) -> None:
        self.start_time = datetime(2024, 1, 1, 10, 0, 0)
        self.end_time = datetime(2024, 1, 1, 11, 30, 0)

    def test_to_line_all_values_proivded(self):
        activity = Activity(
            name="Review PRs",
            start_time=self.start_time,
            end_time=self.end_time,
            category=ActivityType.REVIEW,
        )
        line = activity.to_line()
        self.assertEqual(line, "[review] 10:00 - 11:30 -> Review PRs")

    def test_activity_default_category(self):
        activity = Activity(
            name="My activity", start_time=self.start_time, end_time=self.end_time
        )
        self.assertEqual(activity.category, ActivityType.OTHER)

    def test_activity_use_provided_valid_category(self):
        category = ActivityType.MEETING
        activity = Activity(
            name="My activity",
            start_time=self.start_time,
            end_time=self.end_time,
            category=category,
        )
        self.assertEqual(activity.category, category)

    def test_activity_use_provided_invalid_category(self):

        with self.assertRaises(AttributeError):
            category = ActivityType.INVALID
            Activity(
                name="My activity",
                start_time=self.start_time,
                end_time=self.end_time,
                category=category,
            )

    def test_get_duration(self):
        activity = Activity(
            name="My activity", start_time=self.start_time, end_time=self.end_time
        )
        self.assertEqual(activity.get_duration(), timedelta(hours=1, minutes=30))

    def test_do_not_guess_category_if_provided(self):
        activity = Activity(
            name="Break time",
            start_time=self.start_time,
            end_time=self.end_time,
            category=ActivityType.DEPLOYMENT,
        )
        self.assertEqual(activity.category, ActivityType.DEPLOYMENT)

    def test_guess_category_if_no_catgory_provided(self):
        activity = Activity(
            name="Break time",
            start_time=self.start_time,
            end_time=self.end_time,
        )
        self.assertEqual(activity.category, ActivityType.BREAK)
