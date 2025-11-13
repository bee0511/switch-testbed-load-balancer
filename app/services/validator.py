import logging
import subprocess
from typing import Dict
import re

from app.models.machine import Machine
from app.utils import get_device_credentials, iter_device_entries


logger = logging.getLogger("validator")


class Validator:
    """The Validator class is responsible for validating machine reachability and serial numbers."""

    def __init__(self, machines: Dict[str, Machine]) -> None:
        self._machines = machines
        self.CMD_MAP = {
            ("cisco", "n9k"): [
                "terminal length 0",
                "show inventory",
                "exit"
            ],
            ("cisco", "c8k"): [
                "terminal length 0",
                "show inventory",
                "show version",
                "exit"
            ],
            ("cisco", "xrv"): [
                "show inventory"
            ],
            ("hp", "5945"): [
                "screen-length disable",
                "display device manuinfo",
                "exit"
            ],
        }

    def validate_machine_reachability(self, machine: Machine) -> bool:
        """Check the given machine is reachable or not with ping command.

        Args:
            machine (Machine): The machine to check reachability

        Returns:
            bool: True if the machine is reachable by ping command, False otherwise.
        """
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", machine.mgmt_ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            reachable = result.returncode == 0
            return reachable
        except Exception as e:
            logger.error(
                "Error while pinging machine %s (%s): %s",
                machine.serial,
                machine.mgmt_ip,
                e,
            )
            return False

    # --- 各平台拿「主機序號」的標準做法 ---
    # Cisco NX-OS (N9K): 用 show inventory，取 Chassis 的 SN
    # Cisco IOS-XE (C8K): show inventory，取 Chassis 的 SN；fallback show version 的 "System serial number"
    # Cisco IOS-XR (XRv9000): show inventory chassis 或 show inventory，取 "Rack 0" (Virtual Router) SN
    # HPE Comware (5945/5140): display device manuinfo，取 "DEVICE_SERIAL_NUMBER"

    # --- 解析：從完整輸出抓「整機/chassis」的序號 ---

    def parse_serial(self, vendor: str, model: str, out: str) -> str:
        """Parse the serial number for the given vendor and the model from the output

        Args:
            vendor (str): The vendor for the machine
            model (str): The model for the machine
            out (str): The command output to parse

        Returns:
            str: The parsed serial number, or an empty string if not found
        """
        txt = out

        if vendor == "cisco" and model == "n9k":
            # 1) 先抓 Chassis 行的 SN: <SERIAL>
            m = re.search(
                r'NAME:\s*"Chassis".*?SN:\s*([A-Z0-9]+)', txt, re.I | re.S)
            if m:
                return m.group(1).strip()
            # 2) 退而求其次：任一行 SN（但避免 Slot/Module 命中）
            m = re.search(r'SN:\s*([A-Z0-9]+)', txt, re.I)
            if m:
                return m.group(1).strip()
            # 3) 再退：show version 也許只給 Processor board ID（Supervisor，不建議）
            m = re.search(r'Processor board ID\s*([A-Z0-9]+)', txt, re.I)
            if m:
                return m.group(1).strip()

        if vendor == "cisco" and model == "c8k":
            m = re.search(
                r'NAME:\s*"Chassis".*?SN:\s*([A-Z0-9]+)', txt, re.I | re.S)
            if m:
                return m.group(1).strip()
            m = re.search(r'System serial number\s*:\s*([A-Z0-9]+)', txt, re.I)
            if m:
                return m.group(1).strip()
            m = re.search(
                r'Processor board ID\s*([A-Z0-9]+)', txt, re.I)  # 最後手段
            if m:
                return m.group(1).strip()

        if vendor == "cisco" and model == "xrv":
            # XRv9000：整機通常在 "Rack 0"；show inventory chassis 會只列 chassis
            m = re.search(
                r'NAME:\s*"Rack 0".*?SN:\s*([A-Z0-9]+)', txt, re.I | re.S)
            if m:
                return m.group(1).strip()
            m = re.search(
                # RP（非首選）
                r'NAME:\s*"0/RP0".*?SN:\s*([A-Z0-9]+)', txt, re.I | re.S)
            if m:
                return m.group(1).strip()
            m = re.search(r'SN:\s*([A-Z0-9]+)', txt, re.I)
            if m:
                return m.group(1).strip()

        if vendor == "hp" and model == "5945":
            # Comware: display device manuinfo → DEVICE_SERIAL_NUMBER
            m = re.search(r'DEVICE_SERIAL_NUMBER\s*:\s*([A-Z0-9]+)', txt, re.I)
            if m:
                return m.group(1).strip()

        # 通用備援
        m = re.search(
            r'(System serial number|Processor board ID|SN:)\s*([A-Z0-9]+)', txt, re.I)
        if m:
            last = m.lastindex or 0
            return (m.group(2) if last >= 2 else m.group(1)).strip()
        return ""

    def _ssh_run(self, machine: Machine, username: str, password: str, commands: list[str], timeout: int = 10) -> str:
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
            # 單一命令: 直接執行 (適合 IOS-XR)
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
            # 多個命令: 用 -tt + stdin (傳統方式)
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

    def check_serial(self, machine: Machine) -> bool:
        """Check the serial number is matched with the credentials.yaml

        Args:
            machine (Machine): The machine to check

        Returns:
            bool: True if the serial number matches, False otherwise.
        """
        creds = get_device_credentials(machine.serial)
        if not creds:
            logger.error("No credentials for %s, skip.", machine.serial)
            return False
        username, password = creds

        key = (machine.vendor.lower(), machine.model.lower())
        commands = self.CMD_MAP.get(key)
        if not commands:
            logger.error("Unknown platform: %s", key)
            return False

        out = self._ssh_run(machine, username, password, commands)
        got = self.parse_serial(machine.vendor.lower(),
                                machine.model.lower(), out)

        exp = (machine.serial or "").strip().upper()
        got_u = (got or "").strip().upper()

        if not got_u:
            logger.warning("No serial parsed from %s (%s). Raw:\n%s",
                           machine.mgmt_ip, key, out[:4000])
            return False

        if got_u == exp:
            return True

        logger.warning(
            "Serial mismatch for %s (%s): expected=%s got=%s",
            machine.mgmt_ip, key, exp, got_u
        )
        return False

    def reset_machine(self, machine: Machine) -> bool:
        """Reset the machine by 
        - copy initial.cfg startup.cfg
        - reload

        Args:
            machine (Machine): The machine to reset

        Returns:
            bool: True if the machine is successfully reset, False otherwise.
        """
        if machine.serial not in self._machines:
            logger.warning(
                "Attempted to reset unknown machine serial=%s", machine.serial)
            return False

        creds = get_device_credentials(machine.serial)
        if not creds:
            logger.error("No credentials for %s, skip.", machine.serial)
            return False
        username, password = creds
        if machine.vendor == "cisco":
            commands = [
                "copy initial.cfg startup.cfg",
                "",  # 按 Enter 確認預設檔名
                "reload",
                "yes",
                ""
            ]
            try:
                out = self._ssh_run(machine, username,
                                    password, commands, timeout=10)
                logger.info("Reset output for %s:\n%s", machine.serial, out)

                # 檢查是否有錯誤
                if "Error" in out or "Permission denied" in out:
                    logger.error(
                        "Failed to reset %s: found errors in output", machine.serial)
                    return True
            except Exception as e:
                logger.error(
                    "Exception while resetting machine %s: %s", machine.serial, e)
                return False

        elif machine.vendor == "hp":
            logger.info("Reset command for HP not implemented yet.")
            return False
        else:
            logger.error("Unknown vendor for reset: %s", machine.vendor)
            return False
        return True


if __name__ == "__main__":
    # 測試用
    machines: Dict[str, Machine] = {}

    has_entries = False
    for vendor, model, version, version_entry in iter_device_entries():
        has_entries = True
        for dev in version_entry.get("devices", []):
            try:
                mgmt_ip = str(dev["mgmt_ip"])
                port = int(dev["port"])
                serial = str(dev["serial_number"])
                default_gateway = str(dev["default_gateway"])
                hostname = str(dev["hostname"])
                netmask = str(dev["netmask"])
            except (KeyError, TypeError, ValueError) as error:
                logger.error(
                    "Bad device entry under %s/%s/%s: %s (%s)",
                    vendor,
                    model,
                    version,
                    dev,
                    error,
                )
                continue

            if serial in machines:
                logger.warning(
                    "Duplicate serial '%s' found; overriding previous entry.", serial
                )

            machines[serial] = Machine(
                vendor=vendor,
                model=model,
                version=version,
                mgmt_ip=mgmt_ip,
                port=port,
                serial=serial,
                hostname=hostname,
                default_gateway=default_gateway,
                netmask=netmask,
            )
    validator = Validator(machines)
    # print(machines)
    target = machines["97SQ3QZXPHF"]
    print(f"Validating reachability for {target.serial} ({target.mgmt_ip})...")
    reachable = validator.validate_machine_reachability(target)
    print(f"Reachable: {reachable}")
    if reachable:
        validator.reset_machine(target)
