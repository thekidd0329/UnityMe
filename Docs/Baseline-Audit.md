# Original ZIP audit, 2026-11-15

Archive baseline is nine files, preserved unmodified under `Assets/` and original `Docs/Architecture.md` and `README.md`.

| Original path | Verified source observation | Testability today |
| --- | --- | --- |
| `Assets/Scripts/Runtime/FaceDriver.cs` | Non-held expression target is cleared at the beginning of `LateUpdate()`, before attack to target; pulse cannot rise by this state machine. `faceRenderer.sharedMesh` is dereferenced without null guard. | Needs Unity component tests |
| `Assets/Scripts/Agent/AgentDirector.cs` | Audio path references `AudioSource.time`; silent fallback uses absolute `Time.time`, not elapsed since `Play()`. Camera and groove events are stubs. | Needs Unity playback tests |
| `Assets/Scripts/LipSync/LipSyncDriver.cs` | Preallocates an FFT buffer and weights, but advertised Hz bands don't match index ranges at 48 kHz and FFT size 256. No true phoneme inference. | Needs audio/Unity tests |
| `Assets/Scripts/Input/InputOverride.cs` | Head rotation accumulates without bounds; IK targets and buttons are stubs. | Needs Animator/Unity tests |
| `Assets/Scripts/Runtime/PerformanceLock.cs` | Sets frame target and vsync but cannot guarantee 60 FPS. | Needs device profiling |
| `Assets/StreamingAssets/example_timeline.json` | Parses as JSON; requires downstream named shape and camera hooks. | JSON parse check possible |
| `Docs/Architecture.md` | Specifies three-pose scan and TPU bake without a scanner or bake implementation. | Architecture claim only |
| `.gitignore`, `README.md` | Original configuration/readme. Not an importable Unity project by itself. | Static inspection |

**Environment:** Unity Editor, C#/.NET compiler, Android device, real scan frames, and baked mesh are not available in this validation environment. No Unity runtime, Android, visual likeness, or TPU tests have been executed. This is a baseline review, not a claim of passing software.

**Scope decision:** runtime scripts stay untouched; new capture QA stays in a separate `tools/` slice until agreed Android APIs and calibrated hardware observations are available.
