import importlib.util
import os
from pathlib import Path


def load_build_module():
    root_dir = Path(__file__).resolve().parents[2]
    module_path = root_dir / "build.py"
    spec = importlib.util.spec_from_file_location("deplock_build", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_pyinstaller_command_includes_backend_package_paths():
    build_module = load_build_module()
    root_dir = Path("C:/tmp/deplock")

    command = build_module.build_pyinstaller_command(root_dir)

    assert "--paths" in command
    assert command[command.index("--paths") + 1] == str(root_dir / "backend")

    assert "--collect-submodules" in command
    assert command[command.index("--collect-submodules") + 1] == "app"

    aiosqlite_index = command.index("aiosqlite")
    assert command[aiosqlite_index - 1] in {"--collect-submodules", "--hidden-import"}

    assert "--hidden-import" in command
    assert command[command.index("--hidden-import") + 1] == "app.main"

    assert "--distpath" in command
    assert command[command.index("--distpath") + 1] == str(root_dir / "dist")

    assert "--specpath" in command
    assert command[command.index("--specpath") + 1] == str(
        root_dir / "build" / "pyinstaller" / "spec"
    )

    frontend_data = (
        f"{root_dir / 'frontend' / 'dist'}{os.pathsep}frontend{os.path.sep}dist"
    )
    assert frontend_data in command

    bootstrap_data = (
        f"{root_dir / 'backend' / 'app' / 'services' / 'bootstrap.sh'}"
        f"{os.pathsep}app{os.path.sep}services"
    )
    assert bootstrap_data in command
    assert command[-1] == "main.py"
