"""Frozen DEVELOPMENT Gold conformance; comparison only after engine output."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("development_comparison", ROOT/"evaluation/compare_development.py")
comparison = importlib.util.module_from_spec(spec)
spec.loader.exec_module(comparison)
shape_spec = importlib.util.spec_from_file_location("contract_shapes_for_output", ROOT/"validate_contracts.py")
shapes = importlib.util.module_from_spec(shape_spec)
shape_spec.loader.exec_module(shapes)


class DevelopmentConformanceTests(unittest.TestCase):
    def test_frozen_development_conformance(self):
        paths=sorted((ROOT/"evaluation/development").rglob("*.json"))
        self.assertEqual([p.stem for p in paths],[f"C{i:02d}" for i in range(1,13)]+[f"D{i}" for i in range(13,19)])
        for path in paths:
            with self.subTest(case=path.stem):
                actual,diffs=comparison.compare_case(path)
                self.assertFalse(diffs,"\n".join(diffs))
                self.assertNotIn("rationale",actual["results"][0])
                # The frozen Gold schema alone requires rationale; validate the
                # shared operational shape with a test-only explanatory string.
                for result in actual["results"]:
                    shapes.validate_shape(dict(result, rationale="Output shape check only"), "expected_result")


if __name__ == "__main__":
    unittest.main()
