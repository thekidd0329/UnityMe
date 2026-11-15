# Architecture Lock

## Capture (Pixel 10 Pro)
- 7-second guided 3-pose scan
- Neutral, smile (teeth), brow + open O
- Pure geometry path after capture

## Bake (Tensor G5 TPU, once)
- Non-rigid shrink-wrap onto locked ~12k topology
- Real teeth extraction from smile pose
- Deformation-transfer expressions + corrective deltas from the three poses
- Landmark-masked smoothing, frequency separation, teeth clamp, neck blend
- Output: standard Unity Mesh + Texture2D (ASTC) + blendshape deltas
- TPU session ends. No neural code remains loaded.

## Runtime (Imagination DXT, 60 FPS locked)
- Vulkan + ASTC
- FaceDriver: mouth from LipSyncDriver, other shapes from agent/buttons
- InputOverride: joystick head/arms + face buttons (highest priority)
- AgentDirector: JSON timeline for lights, camera, baseline groove
- Secondary: spring bones, foot-lock IK, weight shift
- Post: half-res SSAO, light grain + CA, ACES + agent LUTs

## What stays out of the frame loop
- Any generative model
- Full-body reconstruction
- Per-frame neural inference
