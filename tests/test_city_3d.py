import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class City3DTests(unittest.TestCase):
    def test_2d_fallback_and_webgl_canvas_are_both_present(self):
        html = (ROOT / "site" / "ville-demo.html").read_text(encoding="utf-8")
        self.assertIn('id="city-view"', html)
        self.assertIn('id="city-view-3d"', html)
        self.assertIn('id="view-2d"', html)
        self.assertIn('id="view-3d"', html)

    def test_webgl_uses_low_power_mode_and_no_external_engine(self):
        html = (ROOT / "site" / "ville-demo.html").read_text(encoding="utf-8")
        self.assertIn('getContext("webgl"', html)
        self.assertIn('powerPreference:"low-power"', html)
        self.assertIn('requestAnimationFrame(renderCity3d)', html)
        self.assertNotIn("three.min.js", html)
        self.assertNotIn("unpkg.com", html)

    def test_2d_canvas_remains_available_when_webgl_is_unavailable(self):
        html = (ROOT / "site" / "ville-demo.html").read_text(encoding="utf-8")
        self.assertIn('button.disabled=true', html)
        self.assertIn('cityViewMode="2d"', html)
        self.assertIn('cityViewMode!=="2d"', html)


if __name__ == "__main__":
    unittest.main()
