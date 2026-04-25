import subprocess
import time
from datetime import datetime
from pathlib import Path

SERVICES = [
    # "scs",
    # "restcountries",
    # "languagetool",
    # "ncs",
    "news",
    # "petstore",
    # "youtube",
    # "person",
    # "user",
    # "genome",
]

ROUND_COUNT = 5
TIME_LIMIT = 3600
REQUESTS = 1000
STARTUP_WAIT_SECONDS = 8


def run_cmd(cmd: list[str], cwd: Path) -> None:
    print(f"[{datetime.now().isoformat(timespec='seconds')}] RUN: {' '.join(cmd)} (cwd={cwd})")
    subprocess.run(cmd, cwd=str(cwd), check=True)


def run_one_round(service: str, round_idx: int, project_root: Path) -> None:
    scripts_dir = project_root / "scripts"

    print(
        f"\n=== Service={service} Round={round_idx}/{ROUND_COUNT} "
        f"time_limit={TIME_LIMIT} requests={REQUESTS} ==="
    )

    # 1) Start service with jacoco agent
    run_cmd(["python", "run_service_jacoco.py", service], scripts_dir)

    # 2) Wait for service warm-up
    print(f"[{datetime.now().isoformat(timespec='seconds')}] Waiting {STARTUP_WAIT_SECONDS}s for service startup...")
    time.sleep(STARTUP_WAIT_SECONDS)

    # 3) Execute fuzzing
    run_cmd(
        [
            "python",
            "examples/fuzzing.py",
            "--service",
            service,
            "--time_limit",
            str(TIME_LIMIT),
            "--requests",
            str(REQUESTS),
            "--exec-log-only",
        ],
        project_root,
    )

    # 4) Dump jacoco result
    run_cmd(["python", "jacoco_dump.py", service], scripts_dir)


def main() -> None:
    project_root = Path(__file__).resolve().parent
    if not SERVICES:
        print("SERVICES is empty. Please set at least one service name in quick_start_1000hits.py")
        return

    for service in SERVICES:
        for round_idx in range(1, ROUND_COUNT + 1):
            try:
                run_one_round(service, round_idx, project_root)
            except subprocess.CalledProcessError as exc:
                print(
                    f"[ERROR] Service={service} Round={round_idx} failed with exit code {exc.returncode}. "
                    f"Continue to next round."
                )


if __name__ == "__main__":
    main()