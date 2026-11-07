"""Regression checks for distributable AdSense examples.

These source templates must not ship a maintainer account ID as a default.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "frameworks/angular/angular-spa-google-suite/skills/SKILL.md"
COMPONENT = ROOT / "frameworks/angular/angular-spa-google-suite/skills/assets/adsense.component.ts"
RULE = ROOT / "shared/google-suite/rules/google-adsense-monetization-rules.md"


class AdsensePublisherConfigurationTests(unittest.TestCase):
    def test_sample_sources_do_not_embed_numeric_publisher_ids(self):
        pattern = re.compile(r"\b(?:ca-)?pub-\d{16}\b")
        for path in (SKILL, COMPONENT, RULE):
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertIsNone(
                    pattern.search(path.read_text(encoding="utf-8")),
                    "Reusable skill/template must use placeholders, not numeric publisher IDs",
                )

    def test_client_input_is_required_in_both_examples(self):
        for path in (SKILL, COMPONENT):
            with self.subTest(path=str(path.relative_to(ROOT))):
                self.assertIn(
                    "readonly client = input.required<string>();",
                    path.read_text(encoding="utf-8"),
                )


if __name__ == "__main__":
    unittest.main()
