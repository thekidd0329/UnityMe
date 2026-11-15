# UnityMe

On-device 3-pose phone scan → lightweight Unity character that looks like you.

Pixel 10 Pro (Tensor G5 TPU bake, Imagination DXT GPU runtime).  
60 FPS locked. Zero generative AI at runtime. Joystick/D-pad override + agent scene direction + audio lip-sync.

## Pipeline

1. **Capture** (7s, 3 poses) on Pixel  
2. **Bake** (TPU, pure geometry) → standard Unity mesh + textures + blendshape deltas  
3. **Runtime** (Vulkan + ASTC, URP) — pure game code

See `Docs/` for the locked architecture.

## Quick Start

1. Create a new Unity 6 URP project (Android, Vulkan, IL2CPP, ARM64).
2. Copy `Assets/` into it.
3. Set `Application.targetFrameRate = 60`.
4. Assign your baked mesh to the character prefab.
5. Build to Pixel.

## Runtime Layers

- `InputOverride` — joystick head/arms + face-button actions (priority)
- `AgentDirector` — reads timeline JSON, drives lights / Cinemachine / baseline body
- `LipSyncDriver` — audio → mouth blendshapes (uLipSync or custom)
- `SecondaryMotion` — spring bones, foot-lock IK, weight shift

All of it runs after the bake. No neural net on the GPU during performance.
