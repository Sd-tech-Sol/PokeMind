"""Nonexecuting PATH diagnostic; separate opt-in for operator-reviewed OCR."""
from __future__ import annotations

import platform
import re
import shutil
import subprocess


def ocr_preflight(*, policy_path=None, execute=False):
    from pokemind.ocr_trust import reviewed_policy, run_reviewed
    report = {"status": "OCR_ENGINE_NOT_INSTALLED", "read_only": not execute,
              "binary_executed": False,
              "network_used": False, "installed_by_command": False,
              "architecture": platform.machine(), "version": None,
              "binary_architecture": None, "language_pack_hashes": {"eng": None, "fra": None},
              "executable_sha256": None, "distribution_origin_verified": False,
              "languages": {"eng": False, "fra": False}, "calibrated": False,
              "engine_cpu_seconds": None, "engine_peak_bytes": None,
              "visual_certain_allowed": False}
    if policy_path is None:
        if execute:
            report["status"] = "OCR_TRUST_POLICY_REQUIRED"
        elif shutil.which("tesseract") is not None:
            report["status"] = "OCR_BINARY_UNATTESTED"
        return report
    try:
        policy, evidence = reviewed_policy(policy_path)
        report.update(evidence, status="OCR_REVIEWED_EXECUTION_REQUIRED")
        if not execute:
            return report
        report["binary_executed"] = True
        version = re.search(rb"(?:^|\n)tesseract v?([0-9]{1,10}\.[0-9]{1,10}(?:\.[0-9]{1,10}){0,2})(?:\s|$)", run_reviewed(policy_path, ["--version"], expected_policy_sha256=evidence["policy_sha256"]))
        if version is None or version[1].decode("ascii") != policy["version"]:
            raise ValueError("OCR_VERSION_MISMATCH")
        languages = set(run_reviewed(policy_path, ["--list-langs"], expected_policy_sha256=evidence["policy_sha256"]).decode("utf-8", errors="strict").splitlines())
        report.update(version=version[1].decode("ascii"),
                      languages={lang: lang in languages for lang in ("eng", "fra")},
                      status="OCR_INSTALLED_UNCALIBRATED" if {"eng", "fra"} <= languages else "OCR_LANGUAGE_PACKS_MISSING")
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        report["status"] = "OCR_DIAGNOSTIC_REJECTED"
    return report
