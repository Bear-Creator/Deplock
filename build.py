from __future__ import annotations

import os
import subprocess
from pathlib import Path


def run_command(command: list[str], cwd: Path, *, shell: bool = False) -> None:
    subprocess.run(command, cwd=cwd, shell=shell, check=True)


def build_pyinstaller_command(root_dir: Path) -> list[str]:
    build_dir = root_dir / "build" / "pyinstaller"
    backend_path = root_dir / "backend"
    frontend_dist = root_dir / "frontend" / "dist"
    bootstrap_script = backend_path / "app" / "services" / "bootstrap.sh"
    frontend_data = f"{frontend_dist}{os.pathsep}frontend{os.path.sep}dist"
    bootstrap_data = f"{bootstrap_script}{os.pathsep}app{os.path.sep}services"

    return [
        "uv",
        "run",
        "pyinstaller",
        "--name",
        "deplock",
        "--onefile",
        "--windowed",
        "--noconfirm",
        "--clean",
        "--distpath",
        str(root_dir / "dist"),
        "--workpath",
        str(build_dir / "work"),
        "--specpath",
        str(build_dir / "spec"),
        "--paths",
        str(backend_path),
        "--collect-submodules",
        "app",
        "--collect-submodules",
        "aiosqlite",
        "--hidden-import",
        "app.main",
        "--hidden-import",
        "aiosqlite",
        "--add-data",
        frontend_data,
        "--add-data",
        bootstrap_data,
        "main.py",
    ]


def main() -> None:
    root_dir = Path(__file__).resolve().parent
    frontend_dir = root_dir / "frontend"

    print(">>> Building frontend...")
    run_command(["npm", "run", "build"], cwd=frontend_dir, shell=True)

    print(">>> Building desktop executable...")
    run_command(build_pyinstaller_command(root_dir), cwd=root_dir)

    print(">>> Desktop build complete.")


if __name__ == "__main__":
    main()
