import logging
from pathlib import Path

import paramiko

logger = logging.getLogger(__name__)


def generate_ssh_key_if_missing(key_path: Path) -> str:
    """Генерирует RSA SSH ключ, если его нет. Возвращает публичный ключ в виде строки."""
    pub_key_path = key_path.with_name(f"{key_path.name}.pub")

    if not key_path.exists():
        logger.info(f"SSH key not found at {key_path}, generating a new one...")
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key = paramiko.RSAKey.generate(2048)
        key.write_private_key_file(str(key_path))
        # Сохраняем публичный ключ
        with open(pub_key_path, "w") as pub_file:
            pub_file.write(f"{key.get_name()} {key.get_base64()}")

    with open(pub_key_path) as pub_file:
        return pub_file.read().strip()


def install_public_key_via_password(
    ip_address: str, ssh_user: str, password: str
) -> None:
    """
    Подключается к серверу по паролю и добавляет локальный публичный ключ в ~/.ssh/authorized_keys.
    """
    # Определяем пути по умолчанию для текущего пользователя ОС
    ssh_dir = Path.home() / ".ssh"
    key_path = ssh_dir / "id_rsa"

    # 1. Получаем или генерируем ключ
    public_key = generate_ssh_key_if_missing(key_path)

    # 2. Подключаемся через paramiko по паролю
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    logger.info(f"Connecting to {ip_address} using password auth to install SSH key...")
    try:
        ssh.connect(
            hostname=ip_address, username=ssh_user, password=password, timeout=10
        )

        # 3. Создаем директорию ~/.ssh на сервере и записываем ключ
        commands = [
            "mkdir -p ~/.ssh",
            "chmod 700 ~/.ssh",
            f"echo '{public_key}' >> ~/.ssh/authorized_keys",
            "chmod 600 ~/.ssh/authorized_keys",
        ]

        for cmd in commands:
            _stdin, stdout, stderr = ssh.exec_command(cmd)
            exit_status = stdout.channel.recv_exit_status()
            if exit_status != 0:
                err = stderr.read().decode().strip()
                logger.error(f"Error executing '{cmd}': {err}")
                raise RuntimeError(f"Failed to setup SSH key on remote host: {err}")

        logger.info(f"Successfully installed SSH key on {ip_address}")
    except Exception as e:
        logger.error(f"SSH setup failed: {e}")
        raise RuntimeError(f"SSH setup failed: {e!s}") from e
    finally:
        ssh.close()
