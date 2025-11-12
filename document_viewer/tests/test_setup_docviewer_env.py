import os
import subprocess
from pathlib import Path


def run_setup(script_path: Path, src: Path, target: Path, log_dir: str | None) -> None:
    cmd = [str(script_path), "--source", str(src), "--target", str(target), "--user", os.getenv("USER", "tester"), "--skip-root-check", "--force"]
    if log_dir:
        cmd.extend(["--log-dir", log_dir])
    subprocess.run(cmd, check=True)


def test_setup_docviewer_env(tmp_path):
    script_path = Path("scripts/setup_docviewer_env.sh").resolve()
    sample = tmp_path / "docviewer.env.sample"
    sample.write_text("VIEWER_LOG_PATH=/tmp/docviewer-test.log\n")
    target = tmp_path / "docviewer.env"
    log_dir = tmp_path / "logdir"

    run_setup(script_path, sample, target, str(log_dir))

    assert target.exists()
    assert (log_dir).is_dir()
    assert (log_dir / "client.log").exists()


def test_setup_docviewer_env_reads_log_from_env(tmp_path):
    script_path = Path("scripts/setup_docviewer_env.sh").resolve()
    sample = tmp_path / "docviewer.env.sample"
    sample.write_text("VIEWER_LOG_PATH=${TMPDIR}/docviewer\n")
    target = tmp_path / "docviewer.env"
    os.environ["TMPDIR"] = str(tmp_path)
    expected_log_dir = tmp_path / "docviewer"

    run_setup(script_path, sample, target, None)

    assert target.exists()
    assert expected_log_dir.is_dir()
    assert (expected_log_dir / "client.log").exists()
    os.environ.pop("TMPDIR", None)
