#!/usr/bin/env python3
"""Offline, local capture-quality reference gate for UnityMe.

This checks *images* and claimed per-frame tracker metadata. It does not
reconstruct geometry, verify the tracker, or prove likeness. No network I/O.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import cv2
import numpy as np

REQUIRED_VIEWS = (
    "front", "left_oblique", "right_oblique", "left_profile",
    "right_profile", "chin_up", "chin_down",
)
MAX_IMAGE_BYTES = 40_000_000


def classify_view(yaw_deg: float, pitch_deg: float) -> str | None:
    """Yaw sign is camera-relative: negative=subject turns viewer-left.

    Pitch > 0 = chin up. Angles are tracker estimates, NOT surface coverage.
    """
    if pitch_deg >= 18 and abs(yaw_deg) <= 35:
        return "chin_up"
    if pitch_deg <= -18 and abs(yaw_deg) <= 35:
        return "chin_down"
    if abs(pitch_deg) > 18:
        return None
    if yaw_deg <= -55:
        return "left_profile"
    if yaw_deg >= 55:
        return "right_profile"
    if -55 < yaw_deg <= -20:
        return "left_oblique"
    if 20 <= yaw_deg < 55:
        return "right_oblique"
    if abs(yaw_deg) <= 12 and abs(pitch_deg) <= 12:
        return "front"
    return None


def safe_frame_path(root: Path, candidate: str) -> Path:
    """Reject absolute paths, traversal, and references outside session root."""
    rel = Path(candidate)
    if rel.is_absolute() or not candidate or ".." in rel.parts:
        raise ValueError("frame path must be a relative path inside the scan directory")
    path = (root / rel).resolve(strict=True)
    if not path.is_relative_to(root.resolve(strict=True)) or not path.is_file():
        raise ValueError("frame path escapes the scan directory or is not a file")
    if path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError("image exceeds local safety limit")
    return path


def evaluate_frame(image: np.ndarray, roi: list[float],
                   min_sharpness: float = 65.0) -> dict[str, Any]:
    """Compute crude *face ROI* image checks, not perceptual image quality.

    Sharpness thresholds vary by camera/scale and require Pixel calibration.
    ROI is [x, y, width, height] normalized to 0..1.
    """
    if image is None or image.ndim not in (2, 3):
        raise ValueError("image could not be decoded")
    if not isinstance(roi, list) or len(roi) != 4 or not all(
        isinstance(v, (int, float)) and math.isfinite(v) for v in roi
    ):
        raise ValueError("invalid normalized face ROI")
    x, y, w, h = map(float, roi)
    if x < 0 or y < 0 or w <= 0 or h <= 0 or x + w > 1 or y + h > 1:
        raise ValueError("face ROI out of image bounds")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    ih, iw = gray.shape
    left, top = int(x * iw), int(y * ih)
    right, bottom = min(iw, math.ceil((x + w) * iw)), min(ih, math.ceil((y + h) * ih))
    face = gray[top:bottom, left:right]
    if face.size == 0:
        raise ValueError("empty face ROI")
    # Normalize ROI width: score compares similar pixel scales across captures.
    # This still needs calibration on camera output; it is not scale invariant.
    target_w = 256
    if face.shape[1] > target_w:
        target_h = max(1, round(face.shape[0] * target_w / face.shape[1]))
        score_img = cv2.resize(face, (target_w, target_h), interpolation=cv2.INTER_AREA)
    else:
        score_img = face
    lap = cv2.Laplacian(score_img, cv2.CV_64F)
    sharpness = float(lap.var())
    dark_fraction = float(np.count_nonzero(face <= 8) / face.size)
    bright_fraction = float(np.count_nonzero(face >= 247) / face.size)
    median_luma = float(np.median(face))
    min_face_dimension = min(face.shape)
    reasons = []
    if min_face_dimension < 128:
        reasons.append("face_roi_too_small")
    if sharpness < min_sharpness:
        reasons.append("low_sharpness")
    if dark_fraction > 0.12 or median_luma < 45:
        reasons.append("underexposed")
    if bright_fraction > 0.12 or median_luma > 210:
        reasons.append("overexposed")
    return {
        "accepted": not reasons,
        "reasons": reasons,
        "sharpness": round(sharpness, 3),
        "dark_fraction": round(dark_fraction, 4),
        "bright_fraction": round(bright_fraction, 4),
        "median_luma": median_luma,
        "face_size_pixels": [right - left, bottom - top],
    }


def analyze_session(directory: Path, min_sharpness: float = 65.0) -> dict[str, Any]:
    root = directory.resolve(strict=True)
    manifest_path = safe_frame_path(root, "capture_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("frames"), list):
        raise ValueError("unsupported capture manifest schema")
    results = []
    selected: dict[str, dict[str, Any]] = {}
    for idx, item in enumerate(manifest["frames"]):
        try:
            if not isinstance(item, dict) or not isinstance(item.get("pose"), dict):
                raise ValueError("missing pose object")
            pose = item["pose"]
            yaw = float(pose["yaw_deg"])
            pitch = float(pose["pitch_deg"])
            confidence = float(pose["confidence"])
            if not all(math.isfinite(v) for v in (yaw, pitch, confidence)):
                raise ValueError("nonfinite pose metadata")
            if not -90 <= yaw <= 90 or not -90 <= pitch <= 90:
                raise ValueError("pose out of supported range")
            if pose.get("source") not in ("arcore", "mediapipe", "calibrated_detector"):
                raise ValueError("pose source not recognized; values are not verified")
            path = safe_frame_path(root, str(item["file"]))
            image = cv2.imread(str(path), cv2.IMREAD_COLOR)
            metrics = evaluate_frame(image, item.get("face_roi"), min_sharpness)
            view = classify_view(yaw, pitch)
            if confidence < 0.8:
                metrics["reasons"].append("low_pose_confidence")
            if view is None:
                metrics["reasons"].append("no_guided_view_match")
            metrics["accepted"] = not metrics["reasons"]
            score = metrics["sharpness"] * min(confidence, 1.0)
            result = {"index": idx, "file": item["file"], "view": view,
                      "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                      "claimed_pose_source": pose["source"], **metrics}
            if result["accepted"] and view is not None:
                previous = selected.get(view)
                if previous is None or score > previous["_score"]:
                    selected[view] = {"index": idx, "file": item["file"], "_score": score}
        except (ValueError, TypeError, KeyError, OSError, cv2.error) as exc:
            result = {"index": idx, "file": item.get("file") if isinstance(item, dict) else None,
                      "view": None, "accepted": False, "reasons": [f"invalid_observation: {exc}"]}
        results.append(result)
    missing = [v for v in REQUIRED_VIEWS if v not in selected]
    return {
        "schema_version": 1,
        "capture_quality_gate_passed": not missing,
        "ready_for_reconstruction": False,
        "reconstruction_blockers": [
            "No calibrated multi-view image correspondences or reprojection residuals",
            "No validated surface coverage / visibility map",
            "No measurement-vs-inference uncertainty map",
        ],
        "required_view_proxies": list(REQUIRED_VIEWS),
        "selected_views": {k: {"file": v["file"], "index": v["index"]}
                           for k, v in selected.items()},
        "missing_views": missing,
        "frames": results,
        "warning": "Pose and ROI metadata supplied by caller are not authenticated; capture gate is not a 3D scan validator.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline UnityMe scan-capture QA; local files only")
    parser.add_argument("session_dir", type=Path)
    parser.add_argument("--min-sharpness", type=float, default=65.0,
                        help="Uncalibrated threshold. Tune with labeled Pixel frames.")
    parser.add_argument("--out", type=Path, help="Optional JSON report path")
    args = parser.parse_args()
    try:
        report = analyze_session(args.session_dir, args.min_sharpness)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    output = json.dumps(report, indent=2)
    if args.out:
        args.out.write_text(output + "\n", encoding="utf-8")
    else:
        print(output)
    return 0 if report["capture_quality_gate_passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
