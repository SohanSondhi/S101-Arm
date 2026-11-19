"""Pod picking orchestration. Coordinates are metres in the robot base frame."""
from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable, Protocol


@dataclass(frozen=True)
class Pose:
    x: float
    y: float
    z: float
    roll: float = 0.0
    pitch: float = 0.0
    yaw: float = 0.0  # radians


@dataclass(frozen=True)
class Pod:
    id: str
    grasp: Pose


class Perception(Protocol):
    def find_pod(self) -> Pod | None:
        """Return a fresh, calibrated grasp pose in the robot base frame."""
        ...

    def holding_pod(self, pod: Pod) -> bool: ...
    def pod_placed(self, pod: Pod, destination: Pose) -> bool: ...


class Arm(Protocol):
    def home(self) -> None: ...
    def can_pick_and_place(self, grasp: Pose, destination: Pose, clearance: float) -> bool:
        """Validate reachability and all approach, lift, and transfer paths."""
        ...

    def move_to(self, pose: Pose) -> None:
        """Execute a checked trajectory; return only after completion or raise."""
        ...

    def open_gripper(self) -> None: ...
    def close_gripper(self) -> None: ...
    def stop(self) -> None:
        """Stop motion safely; do not automatically release a held object."""
        ...


class State(str, Enum):
    HOME = "home"
    FIND = "find"
    VALIDATE = "validate"
    APPROACH = "approach"
    GRASP = "grasp"
    LIFT = "lift"
    VERIFY_GRASP = "verify_grasp"
    PLACE = "place"
    VERIFY_PLACE = "verify_place"
    DONE = "done"
    STOPPED = "stopped"


@dataclass(frozen=True)
class Config:
    destination: Pose
    clearance: float = 0.05
    max_attempts: int = 3

    def __post_init__(self):
        if self.clearance <= 0 or self.max_attempts < 1:
            raise ValueError("Positive clearance and at least one attempt required")


class PodPicker:
    def __init__(self, arm: Arm, perception: Perception, config: Config,
                 log: Callable[[str], None] = print):
        self.arm, self.perception, self.config = arm, perception, config
        self.log = log
        self.state = State.HOME
        self.error: str | None = None

    def transition(self, state: State):
        self.state = state
        self.log(f"STATE {state.value}")

    def above(self, pose: Pose) -> Pose:
        return replace(pose, z=pose.z + self.config.clearance)

    def run(self) -> bool:
        """One pick/place cycle with bounded perception and grasp retries.

        Adapter errors stop the cycle. Placement uncertainty requires operator
        inspection; never blindly pick another pod after an uncertain release.
        """
        try:
            self.transition(State.HOME)
            self.arm.home()
            for _ in range(self.config.max_attempts):
                self.transition(State.FIND)
                pod = self.perception.find_pod()
                if pod is None:
                    self.log("No pod found; acquiring a fresh observation")
                    continue
                self.transition(State.VALIDATE)
                if not self.arm.can_pick_and_place(
                    pod.grasp, self.config.destination, self.config.clearance
                ):
                    self.log(f"Rejected target {pod.id}; acquiring a fresh observation")
                    continue
                self.transition(State.APPROACH)
                self.arm.open_gripper()
                self.arm.move_to(self.above(pod.grasp))
                self.arm.move_to(pod.grasp)
                self.transition(State.GRASP)
                self.arm.close_gripper()
                self.transition(State.LIFT)
                self.arm.move_to(self.above(pod.grasp))
                self.transition(State.VERIFY_GRASP)
                if not self.perception.holding_pod(pod):
                    self.arm.open_gripper()
                    self.arm.home()
                    continue
                self.transition(State.PLACE)
                self.arm.move_to(self.above(self.config.destination))
                self.arm.move_to(self.config.destination)
                self.arm.open_gripper()
                self.arm.move_to(self.above(self.config.destination))
                self.transition(State.VERIFY_PLACE)
                if not self.perception.pod_placed(pod, self.config.destination):
                    raise RuntimeError("Placement unconfirmed; inspect workspace")
                self.transition(State.HOME)
                self.arm.home()
                self.transition(State.DONE)
                return True
            raise RuntimeError("Perception/grasp attempt limit reached")
        except (Exception, KeyboardInterrupt) as exc:
            self.error = str(exc) or type(exc).__name__
            self.transition(State.STOPPED)
            try:
                self.arm.stop()
            except Exception as stop_error:
                self.error += f"; stop failed: {stop_error}"
            self.log(self.error)
            return False
