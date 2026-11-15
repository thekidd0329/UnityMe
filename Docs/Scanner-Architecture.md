# UnityMe scanner architecture: first verified slice

**Target:** one convincing, locally reconstructed digital likeness from a robust multi-view scan of a consenting subject. No live expression transfer, audio subsystem, agent-generated runtime code, or cloud processing is in this slice.

## Stage interfaces and authority

1. **Capture adapter (NOT YET IMPLEMENTED):** Android camera/AR provider emits original frames with camera calibration, timestamps, exposure/focus data, pose observations, and face ROI. Never fabricate tracker confidence or use human-entered yaw as verified observation.
2. **Local capture QA (IMPLEMENTED AS AN OFFLINE PYTHON REFERENCE):** `tools/scan_qa.py` measures face-ROI sharpness and exposure, rejects invalid input, sorts pose observations into seven guidance bins, selects the strongest observation in each bin, and hashes accepted input images. It needs labeled Pixel 10 Pro frames to calibrate thresholds.
3. **Multi-view measurement validation (NOT IMPLEMENTED):** camera intrinsics/extrinsics, calibrated correspondences, multi-view reprojection residuals, inconsistent measurement rejection, occlusion and face-region visibility maps. A pose bucket is **not** a surface-coverage measurement.
4. **Reconstruction (NOT IMPLEMENTED):** geometry fit with a per-region source label (measured, interpolated, inferred) and uncertainty; do not confuse a generic morphable head prior with observations.
5. **Likeness evaluation (NOT IMPLEMENTED):** hold-out views, aligned render-to-image comparison, silhouette/depth residuals, texture consistency, user inspection against reference photos. Do not label completion from SSIM alone.
6. **Offline bake (NOT IMPLEMENTED):** validated mesh/texture export for Unity. TPU acceleration only after profiling and confirming a supported local execution backend.

## Android capture decision gate

Google's ARCore list includes Pixel 10 Pro Depth API support, and Raw Depth includes a confidence image. However, **ARCore Augmented Faces is front-camera-only**. Do not assume front-camera face mesh and rear-camera depth can be obtained as a synchronized single stream. Prototype and benchmark front camera + face observations and rear camera + depth as **separate capture modes**, with verified calibration if combining observations.

References:
- https://developers.google.com/ar/devices
- https://developers.google.com/ar/reference/java/com/google/ar/core/AugmentedFace
- https://developers.google.com/ar/develop/unity-arf/depth/raw-depth

## Quality contract (v0, preliminary; not calibrated)

- Keep raw frames local, never upload automatically; no external service dependencies.
- Each candidate requires a relative image path, normalized face ROI, estimated yaw/pitch, source name, confidence. These are **caller assertions** and this harness cannot independently establish pose correctness.
- Reject malformed/unsafe paths, tiny faces, low sharpness, badly clipped exposures, nonfinite/out-of-range pose, or unrecognized pose sources.
- Seven view bins (`front`, left/right oblique, left/right profile, chin up/down) are a **capture planning proxy**, not a completeness guarantee.
- `capture_quality_gate_passed` refers *only* to these provisional quality/view checks. `ready_for_reconstruction` remains false until multi-view geometric and visibility tests exist.
- Scores and threshold need calibration using actual Pixel 10 Pro images under good lighting, dim light, motion blur, glasses, long hair, skin tone diversity, etc. A fixed Laplacian threshold is NOT universally reliable.
- Keep source images + hashes, capture timestamps, intrinsics and camera pose when available. Record inferred regions separately rather than quietly filling holes.

## Test locally

```
python -m pip install numpy opencv-python pytest
python -m pytest Tests/test_scan_qa.py -q
python tools/scan_qa.py /path/to/local_scan_session --out /path/to/report.json
```

`capture_manifest.json` example:

```json
{
  "schema_version": 1,
  "frames": [
    {
      "file": "frames/001.jpg",
      "face_roi": [0.22, 0.12, 0.54, 0.72],
      "pose": {
        "yaw_deg": 0.5,
        "pitch_deg": 1.0,
        "confidence": 0.93,
        "source": "mediapipe"
      }
    }
  ]
}
```

No real face images are provided in the current archive. The test images are synthetic patterns; passing tests establishes only the gate's behavior, **not** camera integration, depth accuracy, reconstruction accuracy, or likeness.

## Definition of done for scanner MVP

- Android camera capture + verified tracking metadata from Pixel 10 Pro with private, consented scan.
- Repeated capture under challenging conditions, measured failure rates, privacy checks, no cloud calls.
- Multi-view residual tests and surface coverage/uncertainty map; explicit rescan prompts when coverage is missing.
- Locally fitted 3D model with measured-vs-inferred face region map; likeness evaluated against held-out real images.
- Unity artifact produced from validated model; actual device performance captured in reproducible benchmarks.
