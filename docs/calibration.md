# Coffee SO-101 calibration

Calibrate the Hiwonder SO-101 leader and follower separately. No camera, desktop,
or model is needed. `calibrate.py` is a local launcher using Hiwonder's actual
motor driver and interactive calibration routine, not a standalone servo driver.

## Install on the Ubuntu robot laptop

Use Python 3.12+ and a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install 'lerobot[hiwonder] @ git+https://github.com/Hiwonder-official/hiwonder-SoArm-101.git'
```

This downloads dependencies when you run it. Use the manufacturer's fork because
its SO-101 configuration supports Hiwonder motors. No installation or hardware
calibration has been performed by this project setup.

## Identify ports and calibrate

Connect one USB controller at a time to identify which port belongs to each arm:

```bash
ls /dev/serial/by-id/
```

Use the full stable `/dev/serial/by-id/...` path if available. The example ports
below are placeholders; confirm yours before running:

```bash
python calibrate.py leader --port /dev/ttyACM0
python calibrate.py follower --port /dev/ttyACM1
```

Arms must already be assembled with motor IDs configured according to Hiwonder's
instructions. Support the arm when torque is disabled. Follow the terminal
prompts for the reference pose and joint travel; do not force joints against
mechanical stops. If offered an existing calibration, choose recalibration only
when you intend to replace it. Ctrl+C interrupts the script.

Calibration is saved under `calibration/leader/` and `calibration/follower/`, with
IDs `coffee_leader` and `coffee_follower`. Future teleoperation must use those
same IDs and calibration directories. These files belong to your physical arms;
do not reuse someone else's calibration.

The default motor model is `hx30hm`, matching the manufacturer's current SO-101
configuration. Use `--motor-model sts3215` only if your hardware uses that model.
For serial permission errors on Ubuntu, add your user to `dialout` and log out
and back in: `sudo usermod -aG dialout "$USER"`.

## Sources

- https://github.com/Hiwonder-official/hiwonder-SoArm-101
- https://wiki.hiwonder.com/projects/LeRobot/en/latest/docs/1_SO_ARM101_Open_Source_6_Axis_Robotic_Arm_User_Manual.html

The launcher has not been tested on physical hardware. Manual teleoperation is
the next step after both calibrations succeed.
