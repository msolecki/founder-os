"""Chart geometry, pinned as numbers rather than judged by eye.

The domain rule is the one worth stating: a sparkline's ceiling is one above the
larger of the series maximum and the top of the normal band. That keeps the
shaded band inside the plot with headroom, and it means two signals with
different scales are never drawn on one axis.
"""
import importlib
import importlib.util
import re
import sys
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN_ROOT = REPO_ROOT / "founder-os"
DASHBOARD = PLUGIN_ROOT / "scripts" / "dashboard"


def load_dashboard(name):
    if "fos_dashboard" not in sys.modules:
        spec = importlib.util.spec_from_file_location(
            "fos_dashboard", DASHBOARD / "__init__.py",
            submodule_search_locations=[str(DASHBOARD)])
        package = importlib.util.module_from_spec(spec)
        sys.modules["fos_dashboard"] = package
        spec.loader.exec_module(package)
    return importlib.import_module("fos_dashboard.%s" % name)


charts = load_dashboard("charts")


class TestDomain(unittest.TestCase):
    def test_ceiling_is_one_above_the_larger_of_series_and_band(self):
        self.assertEqual(charts.domain_max([4, 3, 3, 2], 5), 6)
        self.assertEqual(charts.domain_max([6, 5, 4, 2], 7), 8)
        self.assertEqual(charts.domain_max([1, 1, 0, 0], 2), 3)

    def test_no_band_falls_back_to_the_series(self):
        self.assertEqual(charts.domain_max([2, 4], None), 5)

    def test_all_zero_series_still_has_a_ceiling(self):
        self.assertEqual(charts.domain_max([0, 0], None), 1)


class TestPoints(unittest.TestCase):
    def test_four_points_span_the_plot_area(self):
        xs = [charts.point_at(i, 0, 4, 8)[0] for i in range(4)]
        self.assertEqual(xs, [8.0, 56.0, 104.0, 152.0])

    def test_value_maps_to_the_expected_baseline_offset(self):
        self.assertEqual(charts.point_at(0, 6, 4, 8)[1], 17.0)
        self.assertEqual(charts.point_at(0, 2, 4, 8)[1], 35.0)
        self.assertEqual(charts.point_at(0, 0, 4, 8)[1], 44.0)

    def test_single_point_series_sits_at_the_left_edge(self):
        self.assertEqual(charts.point_at(0, 1, 1, 2)[0], 8.0)


class TestSparkline(unittest.TestCase):
    def test_band_rectangle_covers_the_normal_range(self):
        svg = charts.sparkline([6, 5, 4, 2], 5, 7, "var(--crit)", "Proof hours")
        rect = re.search(r'<rect[^>]*y="([\d.]+)"[^>]*height="([\d.]+)"', svg)
        self.assertEqual(float(rect.group(1)), 12.5)
        self.assertEqual(float(rect.group(2)), 9.0)

    def test_endpoint_marker_is_larger_than_the_others(self):
        svg = charts.sparkline([6, 5, 4, 2], 5, 7, "var(--crit)", "Proof hours")
        radii = [float(value) for value in re.findall(r'<circle[^>]*r="([\d.]+)"', svg)]
        self.assertEqual(radii[-1], 5.0)
        self.assertTrue(all(value < 5.0 for value in radii[:-1]))

    def test_accessible_label_is_present(self):
        svg = charts.sparkline([1, 2], 1, 2, "var(--good)", "Proposals sent")
        self.assertIn('role="img"', svg)
        self.assertIn("Proposals sent", svg)

    def test_empty_series_renders_nothing_rather_than_a_flat_line(self):
        self.assertEqual(charts.sparkline([], 1, 2, "var(--good)", "x"), "")


class TestTrack(unittest.TestCase):
    def test_segments_carry_widths_and_tooltips(self):
        html = charts.track([(0.6, "var(--neutral-mark)", "delivery 24h", False),
                             (0.4, "var(--bet-1)", "B1 4.5h", False)])
        self.assertIn("width:60%", html.replace(" ", ""))
        self.assertIn('data-tip="delivery 24h"', html)

    def test_hatched_segment_uses_the_hatch_class(self):
        html = charts.track([(0.5, "var(--bet-2)", "in flight", True)])
        self.assertIn("hatch", html)

    def test_marker_is_positioned_as_a_percentage(self):
        html = charts.track([(0.9, "var(--good)", "rate", False)], marker=0.833)
        self.assertIn("83.3%", html)

    def test_fractions_are_clamped(self):
        html = charts.track([(1.8, "var(--good)", "over", False)])
        self.assertIn("width:100%", html.replace(" ", ""))

    def test_tooltip_text_from_state_is_escaped(self):
        html = charts.track([(0.5, "var(--good)", '<b>"x"</b>', False)])
        self.assertNotIn("<b>", html)
        self.assertIn("&lt;b&gt;", html)

    def test_a_single_quote_from_state_cannot_close_an_attribute(self):
        html = charts.track([(0.5, "var(--good)", "it's 3 of 4", False)])
        self.assertNotIn("it's", html)
        self.assertIn("it&#39;s", html)

    def test_the_segment_label_is_readable_without_javascript(self):
        # `data-tip` is a hook nothing in the page reads: no stylesheet rule and
        # no script consumes it, and a data-* attribute contributes no
        # accessible name. The number the segment stands for has to reach the
        # reader some other way, or the chart is a bar with no legend.
        html = charts.track([(0.6, "var(--neutral-mark)", "delivery 24h", False)])
        self.assertIn('title="delivery 24h"', html)

    def test_the_segment_label_reaches_assistive_technology(self):
        # A `title` on a bare div is a mouse-hover tooltip and nothing more: a
        # generic div takes no accessible name from it and cannot be focused,
        # so the number the segment stands for reaches a screen reader only
        # through the pattern `sparkline` already uses one function above.
        html = charts.track([(0.6, "var(--neutral-mark)", "delivery 24h", False)])
        self.assertIn('role="img"', html)
        self.assertIn('aria-label="delivery 24h"', html)

    def test_every_segment_carries_its_own_label(self):
        html = charts.track([(0.5, "var(--bet-1)", "B1 11h", False),
                             (0.4, "var(--bet-2)", "B2 11.5h", False)])
        self.assertEqual(re.findall(r'title="([^"]+)"', html),
                         ["B1 11h", "B2 11.5h"])


if __name__ == "__main__":
    unittest.main()
