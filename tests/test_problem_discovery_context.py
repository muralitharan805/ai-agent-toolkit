"""Context.sh integration smoke test for modular Problem Discovery suites."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProblemDiscoveryContextTest(unittest.TestCase):
    def test_modular_problem_discovery_suites_are_loadable_through_context_sh(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = [
                str(ROOT / "bin/context.sh"),
                "-w",
                "tools/generators/generate-agent-suite",
                "shared/problem-discovery-suites/problem-evaluation",
                "shared/problem-discovery-suites/discovery-state",
                "--tool",
                "antigravity",
                "--target",
                str(root),
            ]
            initial = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(initial.returncode, 0, initial.stderr + initial.stdout)

            self.assertTrue((root / ".agents/skills/generate-agent-suite/SKILL.md").exists())
            self.assertTrue((root / ".agents/skills/problem-evaluation/SKILL.md").exists())
            self.assertTrue((root / ".agents/rules/problem-evaluation-rules.md").exists())
            self.assertTrue(
                (root / ".agents/skills/problem-evaluation/scripts/score_problem_candidate.py").exists()
            )
            self.assertTrue((root / ".agents/skills/discovery-state/SKILL.md").exists())
            self.assertTrue((root / ".agents/rules/discovery-state-rules.md").exists())
            self.assertTrue(
                (root / ".agents/skills/discovery-state/scripts/discovery_db.py").exists()
            )

            # Syncing the same modular capabilities twice must remain idempotent.
            second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)


if __name__ == "__main__":
    unittest.main()
