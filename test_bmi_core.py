import json
import os
import tempfile
import unittest
from datetime import datetime

import bmi_core as core


class ParseNumberTests(unittest.TestCase):
    def test_accepts_dot_and_comma(self):
        self.assertEqual(core.parse_number("70.5"), 70.5)
        self.assertEqual(core.parse_number("70,5"), 70.5)

    def test_ignores_surrounding_spaces(self):
        self.assertEqual(core.parse_number("  65 "), 65.0)

    def test_rejects_text(self):
        with self.assertRaises(ValueError):
            core.parse_number("abc")


class CalculateTests(unittest.TestCase):
    def test_known_value(self):
        self.assertAlmostEqual(core.calculate_bmi(70, 175), 22.857, places=3)

    def test_rejects_out_of_range_values(self):
        bad_inputs = [(0, 175), (-5, 175), (70, 0), (70, 10000), (700, 175), (float("nan"), 175)]
        for weight, height in bad_inputs:
            with self.subTest(weight=weight, height=height):
                with self.assertRaises(ValueError):
                    core.calculate_bmi(weight, height)

    def test_limits_are_inclusive(self):
        core.calculate_bmi(core.MIN_WEIGHT, core.MIN_HEIGHT)
        core.calculate_bmi(core.MAX_WEIGHT, core.MAX_HEIGHT)


class ClassifyTests(unittest.TestCase):
    def test_category_boundaries(self):
        expected = {
            10: "underweight", 18.4: "underweight",
            18.5: "normal", 24.9: "normal",
            25: "overweight", 29.9: "overweight",
            30: "obese", 45: "obese",
        }
        for bmi, name in expected.items():
            with self.subTest(bmi=bmi):
                self.assertEqual(core.classify(bmi).name, name)


class HealthyRangeTests(unittest.TestCase):
    def test_range_for_175_cm(self):
        low, high = core.healthy_weight_range(175)
        self.assertAlmostEqual(low, 56.66, places=2)
        self.assertAlmostEqual(high, 76.26, places=2)


class RecordTests(unittest.TestCase):
    def test_make_record(self):
        record = core.make_record(70, 175, now=datetime(2026, 10, 1, 14, 30))
        self.assertEqual(record["time"], "2026-10-01 14:30")
        self.assertEqual(record["status"], "normal")
        self.assertAlmostEqual(record["bmi"], 22.857, places=3)

    def test_make_record_validates(self):
        with self.assertRaises(ValueError):
            core.make_record(0, 175)

    def test_describe_record(self):
        record = {"time": "2026-10-01 14:30", "weight": 70.5, "height": 175.0,
                  "bmi": 23.02, "status": "normal"}
        self.assertEqual(
            core.describe_record(record),
            "2026-10-01 14:30 | 70.5 kg | 175 cm | BMI 23.0 | normal",
        )

    def test_describe_old_record_without_time(self):
        record = {"weight": 70, "height": 175, "bmi": 22.9, "status": "normal"}
        self.assertTrue(core.describe_record(record).startswith("-- |"))


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.folder.name, "history.json")

    def tearDown(self):
        self.folder.cleanup()

    def test_round_trip(self):
        history = [core.make_record(70, 175), core.make_record(80, 180)]
        core.save_history(self.path, history)
        self.assertEqual(core.load_history(self.path), history)

    def test_missing_file_gives_empty_history(self):
        self.assertEqual(core.load_history(self.path), [])

    def test_corrupt_file_gives_empty_history(self):
        with open(self.path, "w") as file:
            file.write("{not valid json")
        self.assertEqual(core.load_history(self.path), [])

    def test_wrong_top_level_type_gives_empty_history(self):
        with open(self.path, "w") as file:
            json.dump({"weight": 70}, file)
        self.assertEqual(core.load_history(self.path), [])

    def test_malformed_records_are_dropped(self):
        good = core.make_record(70, 175)
        data = [good, {"weight": 70}, "text", {"weight": "x", "height": 1, "bmi": 1, "status": "s"}]
        with open(self.path, "w") as file:
            json.dump(data, file)
        self.assertEqual(core.load_history(self.path), [good])


if __name__ == "__main__":
    unittest.main()
