"""Calibrate one Hiwonder SO-101 arm using the manufacturer's LeRobot driver."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("arm", choices=("leader", "follower"))
    parser.add_argument("--port", required=True, help="USB serial path, e.g. /dev/ttyACM0 or COM3")
    parser.add_argument("--id", help="Persistent calibration name; default: coffee_<arm>")
    parser.add_argument("--motor-model", choices=("hx30hm", "sts3215"), default="hx30hm")
    args = parser.parse_args()
    try:
        if args.arm == "leader":
            from lerobot.teleoperators.so_leader.config_so_leader import SO101LeaderConfig as Config
            from lerobot.teleoperators import make_teleoperator_from_config as make_device
        else:
            from lerobot.robots.so_follower.config_so_follower import SO101FollowerConfig as Config
            from lerobot.robots import make_robot_from_config as make_device
    except ImportError as exc:
        parser.exit(1, f"Install Hiwonder's LeRobot fork first (see README.md).\n{exc}\n")

    directory = Path(__file__).resolve().parent / "calibration" / args.arm
    directory.mkdir(parents=True, exist_ok=True)
    device = make_device(Config(
        port=args.port,
        id=args.id or f"coffee_{args.arm}",
        calibration_dir=directory,
        motor_model=args.motor_model,
    ))
    print(f"Calibrating {args.arm} on {args.port}. Files: {directory}")
    print("Support the arm before proceeding; calibration releases motor torque.")
    try:
        device.connect(calibrate=False)
        device.calibrate()
    finally:
        if device.is_connected:
            device.disconnect()


if __name__ == "__main__":
    main()
