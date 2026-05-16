import os
import subprocess
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    frontend_dist = root / "frontend" / "dist"
    if not frontend_dist.exists():
        print("Frontend dist not found, building frontend...")
        subprocess.run(
            ["npm", "--prefix", str(root / "frontend"), "run", "build"], check=True
        )

    print("Running PyInstaller to build single exe...")
    # include frontend dist as data
    add_data = f"{frontend_dist!s}{os.pathsep}frontend/dist"
    cmd = [
        "pyinstaller",
        "--name",
        "deplock",
        "--onefile",
        "--windowed",
        "--add-data",
        add_data,
        str(root / "backend" / "desktop.py"),
    ]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
