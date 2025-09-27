import json
import logging
import os
import shutil
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Deque, Dict, Optional
from uuid import uuid4

import yaml

from app.models.ticket import Ticket, TicketStatus
from app.services.machine_manager import MachineManager
from app.services.task_processor import TaskProcessor
from app.utils import iter_device_entries

logger = logging.getLogger("ticket_manager")


class TicketManager:
    """管理票據的類別 - 負責票據的CRUD操作和處理邏輯"""

    def __init__(self):
        """
        初始化 TicketManager
        """
        # 載入配置
        self.CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"

        with open(self.CONFIG_PATH, "r", encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)

        self.TICKET_PATH = Path(config["TICKET_PATH"])
        self.TICKET_ACTIVE_PATH = self.TICKET_PATH / "active"
        self.TICKET_ARCHIVE_PATH = self.TICKET_PATH / "archive"
        self.TICKET_ACTIVE_PATH.mkdir(parents=True, exist_ok=True)
        self.TICKET_ARCHIVE_PATH.mkdir(parents=True, exist_ok=True)
        
        self._ticket_queue: Deque[Ticket] = deque()
        
        # 在記憶體中的票據資料庫
        self._tickets_db: Dict[str, Ticket] = {}
        
        # 機器管理器
        self.machine_manager = MachineManager()
        
        # 初始化 TaskProcessor，傳入完成回調函數
        self.task_processor = TaskProcessor(completion_callback=self._complete_ticket)
        
        unprocess_tickets = self._reload_tickets()
        if not unprocess_tickets:
            return
        
        for ticket in unprocess_tickets:
            self._enqueue_ticket(ticket)
            self._consume_ticket()
        logger.info("Reloaded %s unprocessed tickets from storage.", len(unprocess_tickets))
    
    def _reload_tickets(self) -> list[Ticket]:
        """
        從 {TICKET_PATH}/{vendor}/{model}/{version}/*.txt 重新載入未處理票據
        """
        tickets: list[Ticket] = []

        has_entries = False
        for vendor, model, version, _ in iter_device_entries():
            has_entries = True
            ticket_folder: Path = (
                self.TICKET_ACTIVE_PATH / vendor / model / str(version)
            )
            if not ticket_folder.exists():
                continue

            for ticket_file in ticket_folder.glob("*.txt"):
                logger.info("Reloading ticket from %s", ticket_file)
                ticket_id = ticket_file.stem

                ticket = Ticket(
                    id=ticket_id,
                    version=str(version),
                    vendor=vendor,
                    model=model,
                    testing_config_path=ticket_file.as_posix(),
                    status=TicketStatus.queued,
                )
                # 覆蓋/更新快取中的舊 ticket
                self._tickets_db[ticket_id] = ticket
                tickets.append(ticket)

        if not has_entries:
            logger.warning("No valid machines found in config, skipping ticket reload.")

        return tickets
                        
    # ===== 票據 CRUD 操作 =====

    def _create_ticket(self, version: str, vendor: str, model: str, data: bytes) -> Ticket:
        """
        創建票據，寫入檔案，並加入票據資料庫
        
        Args:
            version: 版本
            vendor: 廠商
            model: 模組
            data: 檔案資料
        """
        id = str(uuid4())
        ticket_dir = (
            self.TICKET_ACTIVE_PATH
            / vendor
            / model
            / version
        )
        ticket_dir.mkdir(parents=True, exist_ok=True)

        testing_config_path = ticket_dir / f"{id}.txt"
        ticket = Ticket(
            id=id,
            version=version,
            vendor=vendor,
            model=model,
            testing_config_path=testing_config_path.as_posix(),
            status=TicketStatus.queued,
        )

        # 儲存檔案和票據資料
        with open(testing_config_path, "wb") as f:
            f.write(data)
            
        self._tickets_db[id] = ticket
        
        logger.info("Created ticket: %s", ticket.id)
        return ticket
    
    def _enqueue_ticket(self, ticket: Ticket) -> bool:
        """
        將票據加入佇列
        
        Args:
            ticket: 票據物件

        Returns:
            bool: 是否成功加入佇列
        """
        if not ticket:
            logger.warning("Invalid ticket provided for enqueue")
            return False
        if ticket.status != TicketStatus.queued:
            logger.warning("Ticket %s is not in queued status", ticket.id)
            return False

        self._ticket_queue.append(ticket)
        logger.info("Enqueued ticket: %s", ticket.id)
        return True

    def _update_ticket(self, ticket: Ticket, **kwargs) -> bool:
        """
        更新票據資訊
        
        Args:
            ticket: 票據物件
            **kwargs: 要更新的欄位
            
        Returns:
            bool: 是否更新成功
        """
        if not ticket:
            logger.warning("Invalid ticket provided for update")
            return False
        
        for key, value in kwargs.items():
            if hasattr(ticket, key):
                setattr(ticket, key, value)
        
        return True
    
    def _complete_ticket(self, ticket: Ticket, result_data: Optional[str] = None, success: bool = True) -> None:
        """
        完成票據處理
        
        Args:
            ticket: 票據物件
            result_data: 結果資料
            success: 是否成功
        """
        if not ticket:
            logger.error("Ticket %s not found for completion", getattr(ticket, "id", "<unknown>"))
            return

        if not ticket.machine:
            logger.error("Ticket %s has no machine allocated", ticket.id)
            return

        # 確認機器確實被分配給這個票據
        if not self.machine_manager.validate_ticket_machine(ticket.id, ticket.machine.serial):
            logger.error(
                "Machine %s is not allocated to ticket %s", ticket.machine.serial, ticket.id
            )
            return

        # 釋放機器
        self.machine_manager.release_machine(ticket.machine)

        # 更新狀態
        status = TicketStatus.completed if success else TicketStatus.failed
        self._update_ticket(
            ticket=ticket,
            status=status,
            completed_at=datetime.utcnow(),
            result_data=result_data
        )

        self._archive_ticket(ticket)

        logger.info("curl \"http://127.0.0.1:8000/result/%s\" | jq .", ticket.id)

        self._consume_ticket()  # 嘗試處理下一個票據
    
    # ===== 佇列處理邏輯 =====
    
    def _consume_ticket(self) -> bool:
        """
        處理佇列中的票據
        """
        if not len(self._ticket_queue):
            # print(f"[TicketManager] No tickets in the queue to process.")
            return False
        
        # 使用機器管理器分配機器
        ticket = self._ticket_queue.popleft()
        allocated_machine = self.machine_manager.allocate_machine(ticket.id, ticket.vendor, ticket.model, ticket.version)
        
        if not allocated_machine:
            # 如果沒有可用機器，將票據放回佇列前端
            self._ticket_queue.appendleft(ticket)
            # print(f"[TicketManager] No available machines to process ticket {ticket.id}")
            return False
        
        # 更新票據狀態
        self._update_ticket(
            ticket=ticket,
            status=TicketStatus.running,
            started_at=datetime.utcnow(),
            machine=allocated_machine
        )

        # 使用 TaskProcessor 啟動背景任務
        self.task_processor.start_background_task(ticket)
        return True
    
    def get_ticket_response(self, id: str) -> Optional[dict]:
        """取得票據回傳內容，優先從 active 票據，若無則從 archive 讀取"""
        ticket = self._tickets_db.get(id)
        if ticket:
            queue_status = self.get_queue_status()
            return self._build_ticket_response(ticket, queue_status)

        return self._load_archived_ticket_response(id)
    
    def process_ticket(self, version: str, vendor: str, model: str, data: bytes) -> Optional[Ticket]:
        ticket = self._create_ticket(version, vendor, model, data)
        
        if not self._enqueue_ticket(ticket):
            return None
        
        self._consume_ticket()
        return ticket
    
    # ===== 狀態查詢 =====
    
    def get_queue_status(self) -> Dict:
        """
        取得佇列和機器狀態

        Returns:
            Dict: 包含佇列狀態的字典
        """
        queue_tickets = list(self._ticket_queue)

        return {
            "queued_count": len(self._ticket_queue),
            "running_count": self.machine_manager.get_running_count(),
            "machines": self.machine_manager.get_machine_status(),
            "queue_position": {
                ticket.id: idx + 1
                for idx, ticket in enumerate(queue_tickets)
            }
        }

    def _build_ticket_response(self, ticket: Ticket, queue_status: Dict) -> dict:
        position = queue_status.get("queue_position", {}).get(ticket.id, 0)

        status_value = ticket.status.value if isinstance(ticket.status, TicketStatus) else ticket.status

        response = {
            "id": ticket.id,
            "status": status_value,
            "vendor": ticket.vendor,
            "model": ticket.model,
            "version": ticket.version,
            "enqueued_at": ticket.enqueued_at,
            "started_at": ticket.started_at,
            "completed_at": ticket.completed_at,
            "machine": {
                "serial": ticket.machine.serial,
                "ip": ticket.machine.ip,
                "port": ticket.machine.port
            } if ticket.machine else None,
            "completed": ticket.status in {TicketStatus.completed, TicketStatus.failed},
        }

        if ticket.status == TicketStatus.queued:
            response["message"] = f"Ticket is in queue at position {position}"
            response["position"] = position
        elif ticket.status == TicketStatus.running:
            response["message"] = (
                f"Ticket is running on {ticket.machine.serial if ticket.machine else 'unknown machine'}"
            )
        elif ticket.status == TicketStatus.completed:
            response["message"] = "Ticket completed successfully"
            response["result_data"] = ticket.result_data
        elif ticket.status == TicketStatus.failed:
            response["message"] = "Ticket processing failed"
            response["result_data"] = ticket.result_data

        return response

    def _archive_ticket(self, ticket: Ticket) -> None:
        """將票據移動到 archive 並保存回傳 JSON"""
        # 完成後不再需要佇列資訊
        response = self._build_ticket_response(ticket, {"queue_position": {}})

        archive_dir = (
            self.TICKET_ARCHIVE_PATH
            / ticket.vendor
            / ticket.model
            / ticket.version
            / ticket.id
        )
        archive_dir.mkdir(parents=True, exist_ok=True)

        active_file_path = Path(ticket.testing_config_path)
        if active_file_path.exists():
            archive_config_path = archive_dir / f"{ticket.id}.txt"
            try:
                shutil.move(active_file_path, archive_config_path)
            except shutil.Error:
                logger.warning(
                    "Failed to move ticket config for %s, attempting copy", ticket.id
                )
                shutil.copy(active_file_path, archive_config_path)
                os.remove(active_file_path)
        else:
            logger.warning(
                "Active config file not found for ticket %s when archiving", ticket.id
            )

        json_path = archive_dir / f"{ticket.id}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(response, f, ensure_ascii=False, indent=2, default=str)

        # 從 active 清除票據
        self._tickets_db.pop(ticket.id, None)

    def _load_archived_ticket_response(self, ticket_id: str) -> Optional[dict]:
        json_files = list(self.TICKET_ARCHIVE_PATH.rglob(f"{ticket_id}.json"))
        if not json_files:
            return None

        json_path = json_files[0]

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                response = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("Failed to load archived response for %s: %s", ticket_id, exc)
            return None

        return response
