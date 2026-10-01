import io
import unittest

import bmi_core as core

try:
    import bmi_chart
except ImportError:  # matplotlib is optional
    bmi_chart = None


@unittest.skipIf(bmi_chart is None, "matplotlib is not installed")
class ChartTests(unittest.TestCase):
    def test_single_record(self):
        figure = bmi_chart.build_figure([core.make_record(70, 175)])
        self.assertEqual(len(figure.axes), 1)

    def test_many_records_can_be_saved_as_png(self):
        history = [core.make_record(60 + i, 175) for i in range(30)]
        figure = bmi_chart.build_figure(history)
        buffer = io.BytesIO()
        figure.savefig(buffer, format="png")
        self.assertGreater(len(buffer.getvalue()), 1000)

    def test_extreme_values_stay_inside_the_axes(self):
        history = [core.make_record(core.MAX_WEIGHT, core.MIN_HEIGHT),
                   core.make_record(core.MIN_WEIGHT, core.MAX_HEIGHT)]
        low, high = bmi_chart.build_figure(history).axes[0].get_ylim()
        for record in history:
            self.assertTrue(low <= record["bmi"] <= high)

    def test_old_records_without_time_work(self):
        record = {"weight": 70, "height": 175, "bmi": 22.9, "status": "normal"}
        self.assertEqual(len(bmi_chart.build_figure([record]).axes), 1)


if __name__ == "__main__":
    unittest.main()
