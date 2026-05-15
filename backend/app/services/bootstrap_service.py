import logging
from pathlib import Path
import paramiko

logger = logging.getLogger(__name__)

async def bootstrap_server_via_ssh(ip_address: str, ssh_user: str) -> str:
    """
    Запускает sh-скрипт инициализации на удаленном
    сервере
    """
    script_path = Path(__file__).parent / "bootstrap.sh"
    if not script_path.exists():
        raise FileNotFoundError(f"Bootstrap script not found: {script_path}")

    with script_path.open("r", encoding="utf-8") as f:
        script_content = f.read()

    logger.info(f"Bootstrapping {ip_address} as {ssh_user} via Paramiko...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        # Пытаемся подключиться с использованием ключей из ~/.ssh/ (SSH Agent или id_rsa)
        key_path = Path.home() / ".ssh" / "id_rsa"
        connect_kwargs = {
            "hostname": ip_address,
            "username": ssh_user,
            "timeout": 15
        }
        if key_path.exists():
            connect_kwargs["key_filename"] = str(key_path)
            
        ssh.connect(**connect_kwargs)
        
        # Запускаем bash и передаем скрипт через stdin
        stdin, stdout, stderr = ssh.exec_command("bash -s")
        stdin.write(script_content)
        stdin.channel.shutdown_write()
        
        exit_status = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8')
        err = stderr.read().decode('utf-8')
        
        if exit_status != 0:
            logger.error(f"Bootstrap failed on {ip_address}: {err}")
            raise RuntimeError(f"Server bootstrap failed. Error: {err}")
            
        logger.info(f"Bootstrap completed for {ip_address}:\n{out}")
        return out
    except Exception as e:
        logger.error(f"SSH Bootstrap error: {e}")
        raise RuntimeError(f"SSH connection or execution failed: {str(e)}")
    finally:
        ssh.close()
