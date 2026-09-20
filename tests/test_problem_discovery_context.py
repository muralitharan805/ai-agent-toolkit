"""Real context.sh integration smoke test for the two selected agent suites."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ProblemDiscoveryContextTest(unittest.TestCase):
    def test_generators_and_problem_discovery_are_loadable_through_context_sh(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            command = [str(ROOT / "bin/context.sh"), "-w",
                       "tools/generators/generate-agent-suite", "shared/problem-discovery",
                       "--tool", "antigravity", "--target", str(root)]
            initial = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(initial.returncode, 0, initial.stderr + initial.stdout)
            self.assertTrue((root / ".agents/skills/generate-agent-suite/SKILL.md").exists())
            self.assertTrue((root / ".agents/skills/problem-discovery/SKILL.md").exists())
            self.assertTrue((root / ".agents/rules/problem-discovery-rules.md").exists())
            self.assertTrue((root / ".agents/skills/problem-discovery/scripts/score_problem_candidate.py").exists())
            second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(second.returncode, 0, second.stderr + second.stdout)


if __name__ == "__main__":
    unittest.main()
