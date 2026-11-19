# Pod picking state machine

With teleoperation verified, use the dependency-free scaffold to develop the
pick/place sequence:

```bash
python run_pods.py
python run_pods.py --scenario retry
python run_pods.py --scenario missing
python run_pods.py --scenario placement-failure
python -m unittest discover -s tests -v
```

The last two simulation scenarios intentionally exit with status 1. No hardware
is connected by this runner. Its poses and successful reachability/verification
responses are illustrative, not measured values for your arm.

`pod_control.py` defines the states, bounded retries, and the `Arm` and
`Perception` interfaces. `run_pods.py` supplies replaceable simulation adapters.
The cycle is:

```text
home -> find -> validate -> approach -> grasp -> lift -> verify_grasp
     -> place -> verify_place -> home -> done
```

Missing or unreachable targets trigger fresh observations. A failed grasp
returns home and reacquires a target. Attempts are bounded; exhausted attempts,
adapter exceptions, Ctrl+C, and uncertain placement stop the cycle. An uncertain
placement requires inspection rather than automatically picking another pod.

### Connecting real perception and motion

Implement the interfaces before creating a hardware runner:

- `Perception.find_pod`: detect a pod and estimate a fresh grasp pose, including
  orientation. Transform camera measurements into the robot base frame using
  your camera-to-robot calibration. Return `None` when no valid target exists.
- `holding_pod` and `pod_placed`: use actual sensor/image feedback. Gripper
  commands completing are not confirmation. Raise on unavailable or stale data.
- `Arm.can_pick_and_place`: validate joint limits, reachability, and collision
  clearance for the entire route, including home, approach, lift, and transfer.
- `Arm.move_to`: solve IK and execute a speed-limited, checked trajectory with
  feedback and a timeout. Each operation must finish or raise; the scaffold
  does not provide a background motion controller or enforce adapter deadlines.
- `Arm.home`, gripper methods, and `stop`: implement using the Hiwonder driver
  with the same calibration IDs/directories described above. Stop must halt
  motion without blindly opening the gripper or disabling supporting torque.

Pose positions are metres and roll/pitch/yaw are radians, all in the robot base
frame. Choose and document an orientation convention in your adapters. Grasp
and destination poses refer to the same calibrated tool frame; the destination
is the tool release pose, not simply the centre of the destination container.
The approach/lift offset is along base-frame +Z, appropriate only for an
upright tabletop setup. Select real poses and clearances before hardware use.

Keep adapter calls bounded and retain a hardware stop independent of this
Python loop. This scaffold provides orchestration, not collision checking, IK,
camera calibration, or an emergency-stop implementation. ROS 2/MoveIt can later
implement the same interfaces without changing the sequence.

