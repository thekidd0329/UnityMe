"""Behavioral tests with synthetic images; not hardware/likeness tests."""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from scan_qa import analyze_session, classify_view, evaluate_frame, safe_frame_path


def patterned_image(size=512):
    # Dense deterministic checkerboard, mid-gray on average, no clipped pixels.
    yy, xx = np.indices((size, size))
    p = np.where(((xx // 6 + yy // 6) % 2) == 0, 95, 165).astype(np.uint8)
    return cv2.cvtColor(p, cv2.COLOR_GRAY2BGR)


def test_accurate_view_bins():
    assert classify_view(0, 0) == "front"
    assert classify_view(-35, 0) == "left_oblique"
    assert classify_view(35, 0) == "right_oblique"
    assert classify_view(-65, 0) == "left_profile"
    assert classify_view(65, 0) == "right_profile"
    assert classify_view(0, 24) == "chin_up"
    assert classify_view(0, -24) == "chin_down"
    assert classify_view(15, 0) is None


def test_quality_accepts_clear_midrange_frame():
    r = evaluate_frame(patterned_image(), [0.1, 0.1, 0.8, 0.8])
    assert r["accepted"], r


def test_quality_rejects_blur_and_bad_exposure():
    original = patterned_image()
    blurred = cv2.GaussianBlur(original, (41, 41), 10)
    assert "low_sharpness" in evaluate_frame(blurred, [0, 0, 1, 1])["reasons"]
    assert "underexposed" in evaluate_frame(np.full_like(original, 2), [0, 0, 1, 1])["reasons"]
    assert "overexposed" in evaluate_frame(np.full_like(original, 254), [0, 0, 1, 1])["reasons"]


@pytest.mark.parametrize("roi", [[-0.1, 0, 0.5, 1], [0.8, 0.8, 0.5, 0.5], [0, 0, 0, 1]])
def test_bad_roi_fails_closed(roi):
    with pytest.raises(ValueError):
        evaluate_frame(patterned_image(), roi)


def make_session(tmp_path, views, source="mediapipe"):
    frame = patterned_image()
    items = []
    for i, (yaw, pitch) in enumerate(views):
        name = f"frame-{i}.png"
        cv2.imwrite(str(tmp_path / name), frame)
        items.append({"file": name, "face_roi": [0.1, 0.1, 0.8, 0.8],
                      "pose": {"yaw_deg": yaw, "pitch_deg": pitch, "confidence": 0.98,
                               "source": source}})
    (tmp_path / "capture_manifest.json").write_text(json.dumps({"schema_version": 1, "frames": items}))


def test_front_only_is_not_complete(tmp_path):
    make_session(tmp_path, [(0, 0), (3, 2), (-2, 0)])
    r = analyze_session(tmp_path)
    assert not r["capture_quality_gate_passed"]
    assert r["selected_views"]["front"]["file"] == "frame-0.png"
    assert len(r["missing_views"]) == 6
    assert r["ready_for_reconstruction"] is False


def test_all_seven_pose_proxies_gate_but_do_not_prove_reconstruction(tmp_path):
    make_session(tmp_path, [(0, 0), (-35, 0), (35, 0), (-65, 0), (65, 0), (0, 24), (0, -24)])
    r = analyze_session(tmp_path)
    assert r["capture_quality_gate_passed"]
    assert r["missing_views"] == []
    assert r["ready_for_reconstruction"] is False
    assert len(r["selected_views"]) == 7


def test_unknown_pose_source_cannot_pass(tmp_path):
    make_session(tmp_path, [(0, 0)], source="manual_guess")
    r = analyze_session(tmp_path)
    assert not r["capture_quality_gate_passed"]
    assert "invalid_observation" in r["frames"][0]["reasons"][0]


def test_path_traversal_rejected(tmp_path):
    with pytest.raises(ValueError):
        safe_frame_path(tmp_path, "../outside.png")
    with pytest.raises(ValueError):
        safe_frame_path(tmp_path, "/tmp/another.png")


def test_roi_too_small_rejected():
    r = evaluate_frame(patterned_image(), [0.0, 0.0, 0.10, 0.10])
    assert "face_roi_too_small" in r["reasons"]
