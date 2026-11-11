"""Unit tests for the frozen release gate, promotion and rollback (no models or audio needed)."""
from pathlib import Path
import sys
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "code" / "a2_part_e_monitoring"))
sys.path.insert(0, str(ROOT / "code" / "a2_part_d_deployment"))
from release_drift_loop import gate_decision, rollback, update_registry  # noqa: E402

CRITERIA = yaml.safe_load((ROOT / "configs/gate_release.yaml").read_text())["criteria"]


class GateTest(unittest.TestCase):
    def test_promotes_only_with_gain_and_small_test_drop(self):
        self.assertTrue(gate_decision({"heldout": 0.50, "test": 0.60}, {"heldout": 0.57, "test": 0.575}, CRITERIA)[0])
        self.assertFalse(gate_decision({"heldout": 0.50, "test": 0.60}, {"heldout": 0.54, "test": 0.60}, CRITERIA)[0])
        self.assertFalse(gate_decision({"heldout": 0.50, "test": 0.60}, {"heldout": 0.70, "test": 0.55}, CRITERIA)[0])

    def test_promotion_then_rollback_restores_previous_model(self):
        reg = {"production": {"name": "v1", "train_clips": 77}}
        self.assertEqual(update_registry(reg, "v2", 87, False), reg)
        promoted = update_registry(reg, "v2", 87, True)
        self.assertEqual(promoted["production"]["name"], "v2")
        self.assertEqual(promoted["rollback"]["name"], "v1")
        self.assertEqual(rollback(promoted)["production"]["name"], "v1")
        with self.assertRaises(ValueError):
            rollback(reg)


if __name__ == "__main__":
    unittest.main()
