import unittest

from pod_control import Config, PodPicker, Pose, State
from run_pods import SimArm, SimPerception


class RecordingArm(SimArm):
    def __init__(self):
        self.stopped = False
        self.moves = []

    def move_to(self, pose): self.moves.append(pose)
    def stop(self): self.stopped = True


class PickerTests(unittest.TestCase):
    def run_scenario(self, scenario, arm=None):
        arm = arm or RecordingArm()
        perception = SimPerception(scenario)
        picker = PodPicker(arm, perception, Config(Pose(0.15, -0.08, 0.02)), log=lambda _: None)
        result = picker.run()
        return result, picker, arm, perception

    def test_success(self):
        result, picker, arm, _ = self.run_scenario("success")
        self.assertTrue(result)
        self.assertEqual(picker.state, State.DONE)
        self.assertFalse(arm.stopped)

    def test_retry_uses_new_target(self):
        result, _, arm, perception = self.run_scenario("retry")
        self.assertTrue(result)
        self.assertEqual(perception.observations, 2)
        self.assertNotEqual(arm.moves[1].x, arm.moves[4].x)

    def test_missing_is_bounded(self):
        result, picker, arm, perception = self.run_scenario("missing")
        self.assertFalse(result)
        self.assertEqual(perception.observations, 3)
        self.assertEqual(picker.state, State.STOPPED)
        self.assertTrue(arm.stopped)

    def test_uncertain_placement_does_not_pick_again(self):
        result, _, arm, perception = self.run_scenario("placement-failure")
        self.assertFalse(result)
        self.assertTrue(arm.stopped)
        self.assertEqual(perception.observations, 1)

    def test_motion_error_stops(self):
        class BrokenArm(RecordingArm):
            def move_to(self, pose): raise RuntimeError("connection lost")
        result, picker, arm, _ = self.run_scenario("success", BrokenArm())
        self.assertFalse(result)
        self.assertTrue(arm.stopped)
        self.assertEqual(picker.error, "connection lost")

    def test_unreachable_target_never_moves(self):
        class UnreachableArm(RecordingArm):
            def can_pick_and_place(self, *args): return False
        result, _, arm, _ = self.run_scenario("success", UnreachableArm())
        self.assertFalse(result)
        self.assertEqual(arm.moves, [])


if __name__ == "__main__":
    unittest.main()
