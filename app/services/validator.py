import logging
import subprocess
from typing import Dict
import re

from app.models.machine import Machine
from app.utils import get_device_credentials, iter_device_entries


logger = logging.getLogger("validator")


class Validator:
    """負責驗證機器狀態和配置的模組。"""

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
        """使用 ping 命令檢查機器是否可達。"""
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "1", machine.ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            reachable = result.returncode == 0
            if not reachable:
                logger.warning("Machine %s (%s) is unreachable.",
                               machine.serial, machine.ip)
            return reachable
        except Exception as e:
            logger.error(
                "Error while pinging machine %s (%s): %s",
                machine.serial,
                machine.ip,
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

    def _ssh_run(self, machine: Machine, username: str, password: str, commands: list[str]) -> str:
        """執行 SSH 命令,根據平台選擇適當的方式"""
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
                   f"{username}@{machine.ip}", commands[0]]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
        else:
            # 多個命令: 用 -tt + stdin (傳統方式)
            ssh_opts.append("-tt")
            cmd = ["sshpass", "-p", password, "ssh",
                   *ssh_opts, f"{username}@{machine.ip}"]
            input_text = "\n".join(commands + [""])

            result = subprocess.run(
                cmd,
                input=input_text,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )

        if result.returncode != 0:
            logger.warning("SSH returned %s, stderr=%s",
                           result.returncode, result.stderr.strip())

        return result.stdout

    def check_serial(self, machine: Machine) -> bool:
        creds = get_device_credentials(machine.serial)
        if not creds:
            logger.error("No credentials for %s, skip.", machine.serial)
            return True
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
                           machine.ip, key, out[:4000])
            return False

        if got_u == exp:
            return True

        logger.warning(
            "Serial mismatch for %s (%s): expected=%s got=%s",
            machine.ip, key, exp, got_u
        )
        return False


if __name__ == "__main__":
    # 測試用
    machines: Dict[str, Machine] = {}

    has_entries = False
    for vendor, model, version, version_entry in iter_device_entries():
        has_entries = True
        for dev in version_entry.get("devices", []):
            try:
                ip = str(dev["ip"])
                port = int(dev["port"])
                serial = str(dev["serial_number"])
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
                ip=ip,
                port=port,
                serial=serial,
            )
    validator = Validator(machines)
    # print(machines)
    for machine in machines.values():
        reachable = validator.validate_machine_reachability(machine)
        print(f"Ping {machine.serial} ({machine.ip}): reachable={reachable}")
        if reachable:
            serial_ok = validator.check_serial(machine)
            print(f"  Serial check: {serial_ok}")
