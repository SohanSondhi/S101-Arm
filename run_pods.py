"""Dependency-free simulation. No serial ports or hardware are opened."""
import argparse

from pod_control import Config, Pod, PodPicker, Pose


class SimArm:
    def home(self): print("SIM home")
    def can_pick_and_place(self, grasp, destination, clearance): return True
    def move_to(self, pose): print(f"SIM move {pose}")
    def open_gripper(self): print("SIM open")
    def close_gripper(self): print("SIM close")
    def stop(self): print("SIM stop")


class SimPerception:
    def __init__(self, scenario):
        self.scenario = scenario
        self.observations = 0
        self.grasps = 0

    def find_pod(self):
        self.observations += 1
        if self.scenario == "missing":
            return None
        # Changing location exercises fresh localization on retry.
        return Pod(f"pod-{self.observations}",
                   Pose(0.15 + self.observations * 0.005, 0.04, 0.02))

    def holding_pod(self, pod):
        self.grasps += 1
        return self.scenario != "retry" or self.grasps > 1

    def pod_placed(self, pod, destination):
        return self.scenario != "placement-failure"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=("success", "retry", "missing", "placement-failure"),
                        default="success")
    args = parser.parse_args()
    picker = PodPicker(SimArm(), SimPerception(args.scenario),
                       Config(destination=Pose(0.15, -0.08, 0.02)))
    raise SystemExit(0 if picker.run() else 1)


if __name__ == "__main__":
    main()
