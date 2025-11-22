import asyncio
import logging
import re
import shutil
import subprocess
from typing import Optional, Tuple

from app.core.config import get_settings
from app.models.machine import Machine

logger = logging.getLogger(__name__)

class DeviceConnector:
    """負責處理與設備的底層連線 (SSH, Ping)。"""

    def __init__(self):
        self.settings = get_settings()
        self._sshpass = shutil.which("sshpass")
        if not self._sshpass:
            logger.warning("sshpass not found in system PATH. SSH functionality will fail.")

        # 預載入憑證
        self.credentials, self.default_cred = self.settings.load_credentials()

    def _get_auth(self, serial: str) -> Tuple[str, str]:
        cred = self.credentials.get(serial, self.default_cred)
        return cred.get("username", "admin"), cred.get("password", "")

    async def is_reachable(self, ip: str) -> bool:
        """非同步 Ping 檢查"""
        # 使用 asyncio.create_subprocess_exec 進行真正的非同步呼叫
        try:
            proc = await asyncio.create_subprocess_exec(
                "ping", "-c", "1", "-W", "1", ip,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL
            )
            await proc.wait()
            return proc.returncode == 0
        except Exception as e:
            logger.error(f"Ping error for {ip}: {e}")
            return False

    async def get_serial_via_ssh(self, machine: Machine) -> Optional[str]:
        """透過 SSH 取得設備序號 (非阻塞)"""
        user, password = self._get_auth(machine.serial)
        if not password:
            logger.error(f"No credentials for {machine.serial}")
            return None

        cmd_list = self._get_inventory_command(machine.vendor, machine.model)
        if not cmd_list:
            return None

        # 在 Thread Pool 中執行 Blocking 的 SSH 呼叫
        output = await asyncio.to_thread(
            self._ssh_exec, machine, user, password, cmd_list
        )
        
        if not output:
            return None
        
        return self._parse_serial(machine.vendor, machine.model, output)

    async def reset_device(self, machine: Machine) -> bool:
        """重置設備 (非阻塞)"""
        user, password = self._get_auth(machine.serial)
        
        if machine.vendor == "cisco" and machine.model == "n9k":
            commands = ["copy initial.cfg startup-config", "", "reload", "y", ""]
            
            # N9K reload 會導致連線中斷，這是預期的
            try:
                await asyncio.to_thread(
                    self._ssh_exec, machine, user, password, commands, timeout=3
                )
            except subprocess.TimeoutExpired:
                logger.info(f"Reset triggered for {machine.serial} (timeout expected)")
                return True
            except Exception as e:
                logger.error(f"Reset failed for {machine.serial}: {e}")
                return False
        else:
            logger.info(f"Reset not implemented for {machine.vendor}/{machine.model}")
            return False
            
        return True

    def _ssh_exec(self, machine: Machine, username: str, password: str, commands: list[str], timeout: int = 10) -> str:
        """Execute the commands by using SSH to the machine

        Args:
            machine (Machine): The machine to be connected
            username (str): The SSH username
            password (str): The SSH password
            commands (list[str]): The list of commands to execute
            timeout (int): Timeout in seconds for the SSH command

        Returns:
            str: The output from the SSH command execution
        """
        ssh_opts = [
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-o", "HostKeyAlgorithms=+ssh-rsa",
            "-o", "PubkeyAcceptedKeyTypes=+ssh-rsa",
            "-o", "KexAlgorithms=+diffie-hellman-group14-sha1",
        ]

        # IOS-XR: 直接在命令行執行單個命令,不要用 -tt 和 stdin
        # 其他平台: 用 -tt + stdin 逐行送指令
        if machine.vendor.lower() == "cisco" and machine.model.lower() == "xrv":
            cmd = ["sshpass", "-p", password, "ssh", *ssh_opts,
                   f"{username}@{machine.mgmt_ip}", commands[0]]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )
        else:
            ssh_opts.append("-tt")
            cmd = ["sshpass", "-p", password, "ssh",
                   *ssh_opts, f"{username}@{machine.mgmt_ip}"]
            input_text = "\n".join(commands + [""])

            result = subprocess.run(
                cmd,
                input=input_text,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
            )

        if result.returncode != 0:
            logger.warning("SSH returned %s, stderr=%s",
                           result.returncode, result.stderr.strip())

        return result.stdout

    def _get_inventory_command(self, vendor: str, model: str) -> list[str]:
        mapping = {
            ("cisco", "n9k"): ["terminal length 0", "show inventory", "exit"],
            ("cisco", "c8k"): ["terminal length 0", "show inventory", "exit"],
            ("cisco", "xrv"): ["show inventory"],
            ("hp", "5945"): ["screen-length disable", "display device manuinfo", "exit"],
        }
        return mapping.get((vendor.lower(), model.lower()), [])

    def _parse_serial(self, vendor: str, model: str, output: str) -> str:

        if vendor == "cisco" and model == "n9k":
            m = re.search(
                r'NAME:\s*"Chassis".*?SN:\s*([A-Z0-9]+)', output, re.I | re.S)
            if m:
                return m.group(1).strip()

        elif vendor == "cisco" and model == "c8k":
            m = re.search(
                r'NAME:\s*"Chassis".*?SN:\s*([A-Z0-9]+)', output, re.I | re.S)
            if m:
                return m.group(1).strip()

        elif vendor == "cisco" and model == "xrv":
            m = re.search(
                r'NAME:\s*"Rack 0".*?SN:\s*([A-Z0-9]+)', output, re.I | re.S)
            if m:
                return m.group(1).strip()

        elif vendor == "hp" and model == "5945":
            # Comware: display device manuinfo → DEVICE_SERIAL_NUMBER
            m = re.search(r'DEVICE_SERIAL_NUMBER\s*:\s*([A-Z0-9]+)', output, re.I)
            if m:
                return m.group(1).strip()
            
        else:
            logger.warning(f"Serial parsing not implemented for {vendor}/{model}")
            
        return ""