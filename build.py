from __future__ import annotations

import os
import subprocess
from pathlib import Path


def run_command(command: list[str], cwd: Path, *, shell: bool = False) -> None:
    subprocess.run(command, cwd=cwd, shell=shell, check=True)


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    frontend_dir = root_dir / "frontend"

    print(">>> Building frontend...")
    run_command(["npm", "run", "build"], cwd=frontend_dir, shell=True)

    print(">>> Building desktop executable...")
    frontend_data = f"frontend{os.path.sep}dist{os.pathsep}frontend{os.path.sep}dist"
    bootstrap_data = (
        f"backend{os.path.sep}app{os.path.sep}services{os.path.sep}bootstrap.sh"
        f"{os.pathsep}"
        f"app{os.path.sep}services"
    )

    run_command(
        [
            "uv",
            "run",
            "pyinstaller",
            "--name",
            "deplock",
            "--onefile",
            "--windowed",
            "--noconfirm",
            "--clean",
            "--add-data",
            frontend_data,
            "--add-data",
            bootstrap_data,
            "main.py",
        ],
        cwd=root_dir,
    )

    print(">>> Desktop build complete.")


if __name__ == "__main__":
    main()
