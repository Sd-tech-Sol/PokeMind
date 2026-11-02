"""Explicit operator-reviewed OCR policy; no PATH execution or supply-chain claim."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import threading
from pathlib import Path
from urllib.parse import urlsplit


def _safe_file(path, maximum, *, executable=False, include_payload=False):
    path = Path(path)
    if (not path.is_absolute() or str(path).startswith(("\\\\", "//"))
        or any(":" in part for part in path.parts[1:])
        or any(p.is_symlink() or (p.exists() and getattr(p.lstat(), "st_file_attributes", 0) & 0x400)
               for p in (path, *path.parents))):
        raise ValueError("OCR_PATH_REJECTED")
    with path.open("rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or not 0 < before.st_size <= maximum:
            raise ValueError("OCR_FILE_REJECTED")
        payload = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns)
    if identity(before) != identity(after) or identity(after) != identity(path.stat()) or len(payload) != before.st_size:
        raise ValueError("OCR_FILE_CHANGED")
    architecture = None
    if executable:
        if path.suffix.lower() in {".bat", ".cmd", ".ps1", ".com"}:
            raise ValueError("OCR_CONSOLE_SCRIPT_REJECTED")
        if os.name == "nt":
            if path.suffix.lower() != ".exe" or payload[:2] != b"MZ" or len(payload) < 64:
                raise ValueError("OCR_PE_REQUIRED")
            offset = int.from_bytes(payload[60:64], "little")
            if offset + 6 > len(payload) or payload[offset:offset + 4] != b"PE\0\0":
                raise ValueError("OCR_PE_REQUIRED")
            architecture = {0x8664: "AMD64", 0x14c: "x86", 0xaa64: "ARM64"}.get(int.from_bytes(payload[offset + 4:offset + 6], "little"))
            if architecture is None:
                raise ValueError("OCR_PE_ARCHITECTURE_UNKNOWN")
    result = hashlib.sha256(payload).hexdigest(), architecture
    return (*result, payload) if include_payload else result


def reviewed_policy(policy_path):
    """Hash explicit files without running code. Policy is private operator input."""
    policy_sha, _, payload = _safe_file(policy_path, 16_384, include_payload=True)
    policy = json.loads(payload.decode("utf-8"))
    if not isinstance(policy, dict) or policy.get("schema_version") != 1:
        raise ValueError("OCR_TRUST_POLICY_INVALID")
    if (not isinstance(policy.get("source_url"), str) or len(policy["source_url"]) > 2048
        or not isinstance(policy.get("license"), str) or not 1 <= len(policy["license"]) <= 200
        or not isinstance(policy.get("language_pack_hashes"), dict)):
        raise ValueError("OCR_TRUST_POLICY_INVALID")
    source = urlsplit(policy["source_url"])
    if (source.scheme != "https" or not source.hostname or source.username or source.password
        or policy.get("dependencies_reviewed") is not True or not policy.get("license")
        or not re.fullmatch(r"\d{1,10}\.\d{1,10}(?:\.\d{1,10}){0,2}", str(policy.get("version", "")))):
        raise ValueError("OCR_ORIGIN_REVIEW_REQUIRED")
    measured, architecture = _safe_file(policy["executable"], 100 * 1024 * 1024, executable=True)
    if not re.fullmatch(r"[0-9a-f]{64}", str(policy.get("sha256", ""))) or measured != policy["sha256"]:
        raise ValueError("OCR_BINARY_HASH_MISMATCH")
    if os.name == "nt" and policy.get("architecture") != architecture:
        raise ValueError("OCR_ARCHITECTURE_MISMATCH")
    # Pin local DLLs too: an unchanged executable does not attest its runtime.
    dependencies = policy.get("dependency_hashes", {})
    if (not isinstance(dependencies, dict) or len(dependencies) > 100
            or any(not re.fullmatch(r"[A-Za-z0-9_.+-]+\.dll", name, re.IGNORECASE)
                   or not re.fullmatch(r"[0-9a-f]{64}", str(digest))
                   for name, digest in dependencies.items())):
        raise ValueError("OCR_DEPENDENCY_POLICY_INVALID")
    executable_dir = Path(policy["executable"]).parent
    if {p.name for p in executable_dir.iterdir() if p.suffix.lower() == ".dll"} != set(dependencies):
        raise ValueError("OCR_DEPENDENCY_INVENTORY_MISMATCH")
    for name, digest in dependencies.items():
        actual, _ = _safe_file(executable_dir / name, 100 * 1024 * 1024)
        if actual != digest:
            raise ValueError("OCR_DEPENDENCY_HASH_MISMATCH")
    support_files = policy.get("support_file_hashes", {})
    if (not isinstance(support_files, dict) or set(support_files) - {"tessdata/configs/tsv"}
            or any(not re.fullmatch(r"[0-9a-f]{64}", str(d)) for d in support_files.values())):
        raise ValueError("OCR_SUPPORT_POLICY_INVALID")
    for name, digest in support_files.items():
        actual, _ = _safe_file(executable_dir / name, 16_384)
        if actual != digest:
            raise ValueError("OCR_SUPPORT_HASH_MISMATCH")
    directory = Path(policy["tessdata_dir"])
    packs = {}
    for lang in ("eng", "fra"):
        digest, _ = _safe_file(directory / (lang + ".traineddata"), 100 * 1024 * 1024)
        if digest != policy.get("language_pack_hashes", {}).get(lang):
            raise ValueError("OCR_LANGUAGE_PACK_HASH_MISMATCH")
        packs[lang] = digest
    return policy, {"policy_sha256": policy_sha, "executable_sha256": measured, "binary_architecture": architecture,
                    "language_pack_hashes": packs, "origin_attestation": "operator_reviewed",
                    "local_dependency_count": len(dependencies), "local_dependencies_hash_checked": True,
                    "signature_status": "unknown_not_checked", "dependencies_independently_verified": False}


def bounded_process(arguments, *, input_bytes=b"", limit=32_000, timeout=5, env=None):
    """Bound stdout AND stderr in memory; kill and reap on overflow/deadline."""
    chunks, overflow = {}, threading.Event()
    with subprocess.Popen(arguments, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          shell=False, env=env, cwd=str(Path(arguments[0]).parent),
                          creationflags=0x08000000 if os.name == "nt" else 0) as child:
        def writer():
            try:
                child.stdin.write(input_bytes)
                child.stdin.close()
            except (OSError, ValueError):
                pass
        def reader(name, pipe):
            try:
                chunks[name] = pipe.read(limit + 1)
                if len(chunks[name]) > limit:
                    overflow.set()
                    child.kill()
            except OSError:
                overflow.set()
        readers = [threading.Thread(target=reader, args=(name, pipe), daemon=True)
                   for name, pipe in (("stdout", child.stdout), ("stderr", child.stderr))]
        readers.append(threading.Thread(target=writer, daemon=True))
        for thread in readers:
            thread.start()
        try:
            child.wait(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            child.kill()
            child.wait()
            raise ValueError("OCR_PROCESS_TIMEOUT") from exc
        finally:
            for thread in readers:
                thread.join(timeout=1)
        if overflow.is_set() or any(thread.is_alive() for thread in readers):
            raise ValueError("OCR_OUTPUT_REJECTED")
        if child.returncode:
            raise ValueError("OCR_PROCESS_FAILED")
    return chunks.get("stdout", b"")


def run_reviewed(policy_path, options, *, input_bytes=b"", limit=32_000, timeout=5, expected_policy_sha256=None):
    policy, before = reviewed_policy(policy_path)
    if expected_policy_sha256 is not None and before["policy_sha256"] != expected_policy_sha256:
        raise ValueError("OCR_POLICY_CHANGED")
    environment = {k: v for k, v in os.environ.items() if not k.upper().startswith("TESSDATA")}
    output = bounded_process([policy["executable"], "--tessdata-dir", policy["tessdata_dir"], *options],
                             input_bytes=input_bytes, limit=limit, timeout=timeout, env=environment)
    _, after = reviewed_policy(policy_path)
    if before != after:
        raise ValueError("OCR_FILE_CHANGED")
    return output
