#!/bin/bash
# Bruk: STATION=s1 bash scripts/teleop.sh
STATION=${STATION:-s1}

lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=${FOLLOWER_PORT:-COM3} --robot.id=follower_${STATION} \
  --robot.calibration_dir=calibration/robots/so101_follower \
  --robot.cameras="{ front: {type: opencv, index_or_path: ${CAM_FRONT:-0}, width: 640, height: 480, fps: 30}, wrist: {type: opencv, index_or_path: ${CAM_WRIST:-2}, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader --teleop.port=${LEADER_PORT:-COM4} --teleop.id=leader_${STATION} \
  --teleop.calibration_dir=calibration/teleoperators/so101_leader \
  --display_data=true