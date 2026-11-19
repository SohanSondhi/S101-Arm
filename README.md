# S101 Arm: Vision-Driven Keurig Operator

A computer vision project using an SO-101 arm to load a K-Cup, operate a Keurig, and remove the used pod. The goal is to demonstrate perception, spatial reasoning, inference optimization, and quantitative evaluation through a complete physical workflow.

**Status:** planning and hardware validation. No autonomous brewing capability has been implemented or measured yet.

## Scope

The operator places a cup under the dispenser and fills the water reservoir. The robot handles only the pod and brewer controls.

Target sequence:

1. Observe the brewer and confirm a cup is present and the machine is ready.
2. Locate a fresh K-Cup in a defined pickup area.
3. Open the brewer, pick up the pod, and insert it into the holder.
4. Close the brewer and press the appropriate brew control.
5. Verify brewing started and wait for completion.
6. Open the brewer and deposit the used pod in a designated waste container.
7. Verify the holder is empty and report completion.

Cup movement, reservoir manipulation, and automatic water filling are out of scope. Begin with one brewer model, one pod type, fixed brewer placement, and a constrained pickup area; expand variation only after the baseline works.

## Build roadmap

### 1. Validate hardware feasibility

- Record the exact Keurig model, arm configuration, gripper, cameras, and compute device.
- With the brewer unplugged and cool, measure reach, handle travel, button position, pod clearance, and required opening/closing force.
- Test whether the stock gripper can hold both fresh and used pods without crushing or slipping.
- Confirm the arm can actuate the handle without exceeding its limits or moving the brewer; fixture the brewer if needed.
- If a motion is infeasible, design a handle adapter, button tool, or pod gripper before proceeding.
- Establish an accessible stop control, conservative speed/force limits, and a workspace clear of people during motion.

**Exit criterion:** all required movements are physically reachable and repeatable with a cool, unplugged brewer. Document any mechanical adaptations.

### 2. Bring up the arm and cameras

- Select and document the minimum compatible driver/control stack after identifying the actual hardware.
- Calibrate joints and gripper, verify joint limits, and record a safe home pose.
- Mount an overhead or oblique RGB camera with visibility of the pickup area and brewer; add depth or a wrist camera only if measurements justify it.
- Calibrate camera intrinsics and camera-to-robot coordinates. Measure calibration error at multiple points across the working area.
- Log synchronized images, robot state, commands, and timestamps.

**Exit criterion:** repeatably reach measured targets in the working area, with recorded error small enough for the measured pod-holder clearance.

### 3. Collect and label a perception dataset

- Capture fresh pods, used pods, the pod holder, handle, brew controls, and the waste area across lighting, backgrounds, and partial occlusions.
- Include states such as lid open/closed, holder empty/occupied, cup present/absent, and machine ready/brewing/finished when visually observable.
- Label boxes or masks for objects, keypoints for interaction targets, and state labels for workflow decisions.
- Split training, validation, and test data by recording session and scene configuration so adjacent frames do not leak across splits.
- Preserve a held-out set for new pod appearances, shifted pickup positions, and changed lighting.

**Exit criterion:** versioned dataset, label definitions, and fixed evaluation splits.

### 4. Build and compare perception baselines

- Establish a simple baseline using fixed geometry or fiducials for calibration and repeatable targets.
- Compare an object detector against segmentation or keypoint prediction for pod grasping and holder alignment.
- Compare planar calibrated localization against depth-based localization if depth hardware is available.
- Measure object detection quality, interaction-point error, state-classification accuracy, and end-to-end perception latency.
- Inspect failure cases and choose the smallest representation/model that meets the measured alignment requirements.

**Exit criterion:** reproducible comparison with a documented model-selection decision and spatial-error results.

### 5. Implement individual manipulation skills

- Implement home, approach, grasp, lift, insert, release, handle actuation, button press, and disposal as separately callable skills.
- Use visual observations to update target positions; use staged approach poses near the brewer.
- Add post-action checks for successful grasp, seated pod, closed lid, and empty holder.
- Start with a cool, unplugged machine and dry runs. Test supervised brewing only after the full dry sequence is reliable.
- Treat hot used-pod removal as a separate validation step; establish a cooldown condition and verify grip and disposal behavior.

**Exit criterion:** each skill has recorded trials, success criteria, and a defined response to failure.

### 6. Connect skills with a verified task state machine

- Use explicit states: inspect, open, acquire pod, insert, close, start brew, wait, reopen, dispose, verify, complete.
- Require visual confirmation before each transition; ambiguous observations cause a stop or a bounded retry.
- Check cup presence and brewer readiness before activating brewing. Stop for missing water or machine faults rather than manipulating the reservoir.
- Define timeouts, maximum retries, and recovery rules for missed grasps, misplaced pods, failed closure, and uncertain machine state.
- Combine observable lights, motion, and elapsed time to assess brewing; elapsed time alone does not prove completion.
- Record the state trace and failure reason for every attempt.

**Exit criterion:** supervised end-to-end runs with observable transitions and no unbounded retries.

### 7. Optimize inference and measure robustness

- Profile capture, preprocessing, inference, localization, and control separately on the actual compute device.
- Compare input resolution, model size, and supported runtime/precision choices against accuracy and spatial error.
- Test lighting changes, pickup offsets, pod appearance changes, and partial occlusions one variable at a time.
- Perform ablations: fixed targets versus visual localization, boxes versus masks/keypoints, and open-loop versus visual verification.

**Exit criterion:** a repeatable evaluation report showing accuracy/latency tradeoffs and remaining failure modes.

### 8. Package the portfolio project

- Provide installation instructions, hardware list, calibration procedure, dataset documentation, and commands to reproduce evaluations.
- Publish an architecture diagram, representative predictions, error analysis, and measured results.
- Record a full workflow demonstration and a robustness demonstration with moved pods or changed lighting.
- Clearly distinguish autonomous actions, manual setup, interventions, and edited footage.

## Evaluation plan

Report trial counts and uncertainty alongside success rates. Set numerical acceptance targets after measuring mechanical clearance and baseline performance; do not present planned targets as results.

| Area | Measurements |
| --- | --- |
| Perception | Detection precision/recall or mAP, mask IoU when relevant, keypoint error, state confusion matrix |
| Spatial reasoning | Target localization error in millimeters and orientation error in degrees; median and upper-percentile error |
| Runtime | Per-stage and total latency, median and p95, compute device and runtime settings |
| Manipulation | Success rate per skill, pod drops, insertion failures, retries |
| Full workflow | Completed cycles / attempted cycles, cycle time, interventions, failures by stage |
| Robustness | Results by lighting, pod appearance, pickup offset, and occlusion condition |

Suggested initial evaluation: at least 20 trials per individual skill and 20 complete cycles in the baseline condition, followed by separately reported changed conditions. Expand the sample size before making broad reliability claims.

## Intended repository structure

```text
configs/                 # Hardware, camera, model, and task settings
src/s101_arm/
  hardware/              # Minimal arm and camera adapters
  perception/            # Detection, keypoints, segmentation, state recognition
  geometry/              # Calibration and coordinate transforms
  skills/                # Individual motion/manipulation actions
  workflow/              # State machine, verification, and recovery
  evaluation/            # Metrics and experiment runners
scripts/                 # Capture, calibrate, train, evaluate, and demo commands
tests/                   # Geometry and workflow logic checks
docs/                    # Hardware notes, experiments, and results
data/README.md           # Dataset location and acquisition instructions
```

This structure is a plan, not a list of implemented modules. Keep recordings, datasets, model weights, credentials, and machine-specific settings out of normal Git history.

## Relationship to Hiwonder software

This repository starts independently of the Hiwonder checkout. Reuse only the hardware interfaces or calibration utilities that are actually required. Prefer a documented dependency or a small adapter; if vendor source is copied, preserve its license and attribution and record the upstream version. Do not import the entire vendor repository as the project foundation.

## First milestone

Identify the exact brewer and arm hardware, prove cool-machine mechanical feasibility, mount the camera, and collect an initial labeled recording. The first vision demo should locate a fresh pod and predict its pickup position; brewing comes after reliable individual skills and verified dry runs.

## Leader and follower calibration

See [calibration setup](docs/calibration.md) for installation and commands to calibrate each Hiwonder SO-101 arm using calibrate.py.


## Pod picking scaffold

See [pod picking](docs/pod-picking.md) for the Python state machine, simulation scenarios, adapter contracts, and tests. This scaffold implements pod pick/place orchestration; camera localization and physical motion adapters remain to be connected.

