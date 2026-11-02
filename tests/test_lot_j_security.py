"""Windows-first adversarial OCR and nonexecuting preview regressions."""
import hashlib
import json
import os
import sqlite3
import sys

import pytest

from pokemind.cli import main
from pokemind.ocr_preflight import ocr_preflight
from pokemind.ocr_benchmark import benchmark_ocr
from pokemind.ocr_trust import bounded_process, reviewed_policy, run_reviewed
from pokemind.public_campaign import _public_database_only
from pokemind.scheduler import scheduler_preview, SchedulerError
from test_local_ocr import _fixture


def _policy(root):
    binary = root / "chosen.exe"
    payload = bytearray(128)
    payload[:2], payload[60:64], payload[64:70] = b"MZ", (64).to_bytes(4, "little"), b"PE\0\0\x64\x86"
    binary.write_bytes(payload)
    packs = {}
    for lang in ("eng", "fra"):
        content = (lang + " synthetic never loaded").encode()
        (root / (lang + ".traineddata")).write_bytes(content)
        packs[lang] = hashlib.sha256(content).hexdigest()
    policy = {"schema_version": 1, "executable": str(binary), "sha256": hashlib.sha256(payload).hexdigest(),
              "version": "5.5.0", "architecture": "AMD64", "tessdata_dir": str(root),
              "language_pack_hashes": packs, "source_url": "https://example.invalid/reviewed-synthetic",
              "license": "synthetic fixture", "dependencies_reviewed": True}
    file = root / "trust.json"
    file.write_text(json.dumps(policy), encoding="utf-8")
    return file, binary, policy


def test_hostile_path_never_runs_in_default_preflight_benchmark_or_observation(local_tmp, monkeypatch):
    import pokemind.ocr_preflight as diagnostic
    import pokemind.ocr_trust as trust
    from pokemind.local_ocr import recognize_local_text, _run_tesseract
    hostile = local_tmp / "tesseract.cmd"
    hostile.write_text("@echo malicious executable must never run", encoding="ascii")
    monkeypatch.setattr(diagnostic.shutil, "which", lambda _: str(hostile))
    monkeypatch.setattr(trust, "bounded_process", lambda *a, **k: pytest.fail("Unreviewed program executed"))
    result = ocr_preflight()
    assert result["status"] == "OCR_BINARY_UNATTESTED" and not result["binary_executed"]
    benchmark = benchmark_ocr()
    assert benchmark["case_count"] == 22 and sum(m["samples"] for m in benchmark["fields"].values()) == 88
    assert not benchmark["real_ocr_executed"] and benchmark["identity_false_positives"] is None
    image, calibration, _ = _fixture(local_tmp)
    state, backend = recognize_local_text(local_tmp / "missing.sqlite3", image, calibration, local_tmp, turn=1)
    assert state is None and backend["reason_code"] == "OCR_BINARY_UNATTESTED"
    with pytest.raises(ValueError, match="TRUST_POLICY_REQUIRED"):
        _run_tesseract(b"synthetic", "eng")
    assert str(local_tmp) not in json.dumps(result)


def test_reviewed_hashes_require_separate_execution_and_remain_uncalibrated(local_tmp, monkeypatch):
    import pokemind.ocr_trust as trust
    policy, binary, _ = _policy(local_tmp)
    calls = []
    def run(args, **kwargs):
        calls.append(args)
        assert args[0] == str(binary) and "--tessdata-dir" in args
        return b"tesseract 5.5.0\n" if "--version" in args else b"private path\neng\nfra\n"
    monkeypatch.setattr(trust, "bounded_process", run)
    assert ocr_preflight(policy_path=policy)["status"] == "OCR_REVIEWED_EXECUTION_REQUIRED"
    assert not calls
    result = ocr_preflight(policy_path=policy, execute=True)
    assert result["status"] == "OCR_INSTALLED_UNCALIBRATED" and result["binary_executed"]
    assert not result["read_only"] and not result["distribution_origin_verified"]
    assert not result["calibrated"] and not result["visual_certain_allowed"]
    assert result["languages"] == {"eng": True, "fra": True}
    assert len(calls) == 2 and str(local_tmp) not in json.dumps(result)
    binary.write_bytes(binary.read_bytes() + b"tampered")
    assert ocr_preflight(policy_path=policy, execute=True)["status"] == "OCR_DIAGNOSTIC_REJECTED"
    assert len(calls) == 2


@pytest.mark.parametrize("mutation", ["changed", "unexpected", "hardlink", "support"])
def test_ocr_local_dependencies_are_pinned_before_any_execution(local_tmp, monkeypatch, mutation):
    import pokemind.ocr_trust as trust
    file, binary, policy = _policy(local_tmp)
    dependency = local_tmp / "synthetic.dll"
    dependency.write_bytes(b"synthetic dependency never executed")
    policy["dependency_hashes"] = {dependency.name: hashlib.sha256(dependency.read_bytes()).hexdigest()}
    support = local_tmp / "tessdata/configs/tsv"
    support.parent.mkdir(parents=True)
    support.write_bytes(b"synthetic config never executed")
    policy["support_file_hashes"] = {"tessdata/configs/tsv": hashlib.sha256(support.read_bytes()).hexdigest()}
    file.write_text(json.dumps(policy), encoding="utf-8")
    assert reviewed_policy(file)[1]["local_dependency_count"] == 1
    if mutation == "changed":
        dependency.write_bytes(b"changed")
    elif mutation == "unexpected":
        (local_tmp / "unlisted.DLL").write_bytes(b"unlisted")
    elif mutation == "hardlink":
        os.link(dependency, local_tmp / "alias.bin")
    else:
        support.write_bytes(b"changed")
    monkeypatch.setattr(trust, "bounded_process", lambda *a, **k: pytest.fail("Changed dependency executed"))
    report = ocr_preflight(policy_path=file, execute=True)
    assert report["status"] == "OCR_DIAGNOSTIC_REJECTED" and not report["binary_executed"]


@pytest.mark.parametrize("expected,reported,status", [
    ("5.5.3.20260724", "v5.5.3.20260724", "OCR_INSTALLED_UNCALIBRATED"),
    ("5.5.3", "v5.5.3.20260724", "OCR_DIAGNOSTIC_REJECTED"),
    ("5.5.3.20260724", "v5.5.3.20260725", "OCR_DIAGNOSTIC_REJECTED"),
])
def test_windows_distribution_version_requires_exact_reviewed_build(local_tmp, monkeypatch, expected, reported, status):
    import pokemind.ocr_trust as trust
    file, _, policy = _policy(local_tmp)
    policy["version"] = expected
    file.write_text(json.dumps(policy), encoding="utf-8")
    monkeypatch.setattr(trust, "bounded_process", lambda args, **_: (
        ("tesseract " + reported + "\r\n").encode() if "--version" in args else b"eng\nfra\n"))
    result = ocr_preflight(policy_path=file, execute=True)
    assert result["status"] == status
    if status == "OCR_INSTALLED_UNCALIBRATED":
        assert result["version"] == expected and not result["calibrated"]


@pytest.mark.parametrize("mutation", ["pack", "version", "origin", "script", "alias", "oversized"])
def test_ocr_rejects_unreviewed_or_changed_components(local_tmp, monkeypatch, mutation):
    import pokemind.ocr_trust as trust
    file, binary, policy = _policy(local_tmp)
    if mutation == "pack":
        (local_tmp / "fra.traineddata").write_bytes(b"wrong pack")
    elif mutation == "version":
        policy["version"] = "--evil"
    elif mutation == "origin":
        policy["dependencies_reviewed"] = False
    elif mutation == "script":
        script = local_tmp / "evil.cmd"
        script.write_bytes(binary.read_bytes())
        policy["executable"] = str(script)
    elif mutation == "alias":
        os.link(binary, local_tmp / "alias.exe")
    else:
        with binary.open("r+b") as stream:
            stream.truncate(100 * 1024 * 1024 + 1)
    file.write_text(json.dumps(policy), encoding="utf-8")
    monkeypatch.setattr(trust, "bounded_process", lambda *a, **k: pytest.fail("Rejected binary executed"))
    report = ocr_preflight(policy_path=file, execute=True)
    assert report["status"] == "OCR_DIAGNOSTIC_REJECTED" and not report["binary_executed"]
    assert str(local_tmp) not in json.dumps(report)


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_process_limits_both_output_pipes(stream):
    with pytest.raises(ValueError, match="OCR_OUTPUT_REJECTED"):
        bounded_process([sys.executable, "-c", f"import sys; sys.{stream}.write('x'*50000)"], limit=512)


def test_process_timeout_neutral_failure_and_literal_arguments():
    with pytest.raises(ValueError, match="OCR_PROCESS_TIMEOUT"):
        bounded_process([sys.executable, "-c", "import time; time.sleep(5)"], timeout=.1)
    literal = "$(private) & echo bad; `secret`"
    assert bounded_process([sys.executable, "-c", "import sys; print(sys.argv[1])", literal]).decode().strip() == literal
    with pytest.raises(ValueError, match="OCR_PROCESS_FAILED"):
        bounded_process([sys.executable, "-c", "raise SystemExit(3)"])


def test_mutation_after_process_is_not_accepted(local_tmp, monkeypatch):
    import pokemind.ocr_trust as trust
    file, binary, _ = _policy(local_tmp)
    def mutate(*args, **kwargs):
        binary.write_bytes(binary.read_bytes() + b"changed")
        return b"tesseract 5.5.0\n"
    monkeypatch.setattr(trust, "bounded_process", mutate)
    assert ocr_preflight(policy_path=file, execute=True)["status"] == "OCR_DIAGNOSTIC_REJECTED"


@pytest.mark.parametrize("version,languages,status", [
    (b"tesseract 9.9.9\n", b"eng\nfra\n", "OCR_DIAGNOSTIC_REJECTED"),
    (b"tesseract 5.5.0\n", b"private path\neng\n", "OCR_LANGUAGE_PACKS_MISSING"),
    (b"tesseract 5.5.0\n", b"\xff", "OCR_DIAGNOSTIC_REJECTED"),
])
def test_reviewed_diagnostics_abstain_on_version_language_or_encoding(local_tmp, monkeypatch, version, languages, status):
    import pokemind.ocr_trust as trust
    file, _, _ = _policy(local_tmp)
    monkeypatch.setattr(trust, "bounded_process", lambda args, **k: version if "--version" in args else languages)
    report = ocr_preflight(policy_path=file, execute=True)
    assert report["status"] == status and not report["visual_certain_allowed"]
    assert str(local_tmp) not in json.dumps(report) and "private path" not in json.dumps(report)


def test_runtime_preflight_never_resolves_or_opens_default_db(monkeypatch, capsys):
    import pokemind.cli as cli
    monkeypatch.setattr(cli, "_db_for", lambda *a: pytest.fail("Default database selected"))
    assert main(["preflight", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["fts5"] and not result["owner_database_opened"] and result["writes_to_disk"] == 0
    assert result["release_status"] == "NOT_RELEASE_READY"


def test_all_scheduler_previews_never_launch_system_tools(local_tmp, monkeypatch):
    import pokemind.scheduler as scheduler
    monkeypatch.setattr(scheduler.subprocess, "run", lambda *a, **k: pytest.fail("System tool launched"))
    with pytest.raises(SchedulerError, match="WINDOWS_TIMEZONE_REQUIRED"):
        scheduler_preview(local_tmp, daily_time="08:15", deep_time="19:30")
    for action in ("install", "status", "uninstall"):
        result = scheduler_preview(local_tmp, action=action, daily_time="08:15", deep_time="19:30", windows_timezone="Eastern Standard Time")
        assert not result["scheduler_contacted"] and not result["system_changed"]
        assert all(not m["timezone_precondition_verified"] for m in result["manifests"])
        assert json.loads(json.dumps(result))["action"] == action
    assert list(local_tmp.iterdir()) == []


def test_public_marker_cannot_allow_populated_personal_or_unknown_table(local_tmp):
    db = local_tmp / "public.sqlite3"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE deck_versions (private_value TEXT)")
    con.execute("INSERT INTO deck_versions VALUES ('synthetic private canary')")
    con.commit()
    con.close()
    before = db.read_bytes()
    with pytest.raises(ValueError, match="OWNER_OR_UNKNOWN_DATA_BLOCKED"):
        _public_database_only(db)
    assert db.read_bytes() == before
