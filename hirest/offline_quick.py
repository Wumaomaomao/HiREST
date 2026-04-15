#!/usr/bin/env python3
"""Launch offline partition pipeline for one service.

Default behavior:
- Accept one service name.
- Auto-discover OpenAPI file from ./apis/<service>/spec/.
- Start offline pipeline in background and write logs.
"""

import argparse
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def discover_spec_file(spec_dir: Path) -> Path:
	candidates = []
	for ext in ("*.yaml", "*.yml", "*.json"):
		candidates.extend(spec_dir.glob(ext))

	candidates = sorted(candidates)
	if not candidates:
		raise FileNotFoundError(f"No spec file found in: {spec_dir}")
	if len(candidates) > 1:
		names = ", ".join(p.name for p in candidates)
		raise ValueError(
			"Multiple spec files found. Please specify --spec-file explicitly. "
			f"Candidates: {names}"
		)
	return candidates[0]


def build_command(
	repo_root: Path,
	spec_file: Path,
	seed_size: int | None,
	ablation_no_constraints: bool,
	no_misp: bool,
	extra_args: list[str],
) -> list[str]:
	cmd = [
		sys.executable,
		str(repo_root / "examples" / "offline" / "offline_debug.py"),
		"-i",
		str(spec_file),
	]
	if seed_size is not None:
		cmd.extend(["-s", str(seed_size)])
	if ablation_no_constraints:
		cmd.append("--ablation_no_constraints")
	if no_misp:
		cmd.append("--no_misp")
	if extra_args:
		cmd.extend(extra_args)
	return cmd


def main() -> int:
	parser = argparse.ArgumentParser(
		description="Run offline partition pipeline for one service (background by default)."
	)
	parser.add_argument(
		"--service",
		required=True,
		help="Service name, e.g. project/news/person",
	)
	parser.add_argument(
		"--spec-file",
		help="Optional explicit spec file path. Default: auto-discover under ./apis/<service>/spec/",
	)
	parser.add_argument(
		"--seed-size",
		type=int,
		default=None,
		help="Optional seed size forwarded to offline_debug.py (-s)",
	)
	parser.add_argument(
		"--ablation-no-constraints",
		action="store_true",
		help="Forward --ablation_no_constraints to offline_debug.py",
	)
	parser.add_argument(
		"--foreground",
		action="store_true",
		help="Run in foreground (default is background).",
	)
	parser.add_argument(
		"--extra-args",
		nargs=argparse.REMAINDER,
		default=[],
		help="Additional args passed through to offline_debug.py (put this at the end).",
	)
	parser.add_argument(
		"--no-misp",
		action="store_true",
		help="Do not run MISP (only SISP) in offline_debug.py",
	)

	args = parser.parse_args()

	repo_root = Path(__file__).resolve().parents[1]
	service = args.service.strip()
	service_root = repo_root / "apis" / service
	spec_dir = service_root / "spec"
	if not service_root.exists():
		print(f"[offline_quick] Service not found: {service_root}")
		return 1
	if not spec_dir.exists():
		print(f"[offline_quick] Spec directory not found: {spec_dir}")
		return 1

	if args.spec_file:
		spec_file = (repo_root / args.spec_file).resolve() if not Path(args.spec_file).is_absolute() else Path(args.spec_file)
		if not spec_file.exists():
			print(f"[offline_quick] Spec file not found: {spec_file}")
			return 1
	else:
		try:
			spec_file = discover_spec_file(spec_dir)
		except (FileNotFoundError, ValueError) as exc:
			print(f"[offline_quick] {exc}")
			return 1

	cmd = build_command(
		repo_root=repo_root,
		spec_file=spec_file,
		seed_size=args.seed_size,
		ablation_no_constraints=args.ablation_no_constraints,
		no_misp=args.no_misp,
		extra_args=args.extra_args,
	)

	timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
	log_dir = service_root / "exec_log"
	log_dir.mkdir(parents=True, exist_ok=True)
	log_file = log_dir / f"offline_quick_{timestamp}.log"

	printable_cmd = " ".join(shlex.quote(x) for x in cmd)

	if args.foreground:
		print(f"[offline_quick] Running (foreground): {printable_cmd}")
		print(f"[offline_quick] Log file: {log_file}")
		with log_file.open("w", encoding="utf-8") as lf:
			proc = subprocess.run(
				cmd,
				cwd=str(repo_root),
				stdout=lf,
				stderr=subprocess.STDOUT,
				check=False,
			)
		return proc.returncode

	with log_file.open("w", encoding="utf-8") as lf:
		proc = subprocess.Popen(
			cmd,
			cwd=str(repo_root),
			stdout=lf,
			stderr=subprocess.STDOUT,
			start_new_session=True,
		)

	print(f"[offline_quick] Started in background. PID={proc.pid}")
	print(f"[offline_quick] Service: {service}")
	print(f"[offline_quick] Spec: {spec_file}")
	print(f"[offline_quick] Log: {log_file}")
	print(f"[offline_quick] Command: {printable_cmd}")
	return 0


if __name__ == "__main__":
	raise SystemExit(main())

