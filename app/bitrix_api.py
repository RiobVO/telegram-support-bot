from typing import Any, Dict, Optional
import sys
import requests

from .config import (
    BITRIX_BASE,
    BITRIX_RESPONSIBLE_ID,
    BITRIX_MODE,
    BITRIX_SMART_ENTITY_ID,
    BITRIX_SMART_CATEGORY_ID,
    BITRIX_SMART_STAGE_ID,
    BITRIX_SMART_STAGE_WORK,
    BITRIX_SMART_STAGE_CLOSED,
)

def bitrix_task_add(title: str, description: str, responsible_id: int) -> Optional[int]:
    url = BITRIX_BASE + "tasks.task.add"
    try:
        resp = requests.post(url, data={
            "fields[TITLE]": title,
            "fields[DESCRIPTION]": description,
            "fields[RESPONSIBLE_ID]": str(responsible_id),
        }, timeout=8)
        data = resp.json()
        # Ожидаемый ответ: {"result":{"task":{"id":"123", ...}}}
        task_id = int(data["result"]["task"]["id"])
        return task_id
    except Exception:
        return None

def bitrix_task_update_status(task_id: int, status_code: int) -> bool:
    url = BITRIX_BASE + "tasks.task.update"
    try:
        resp = requests.post(url, data={
            "taskId": str(task_id),
            "fields[STATUS]": str(status_code),  # 2 = в работе, 5 = закрыто (зависит от портала)
        }, timeout=8)
        data = resp.json()
        return "result" in data
    except Exception:
        return False

def bitrix_task_complete(task_id: int) -> bool:
    url = BITRIX_BASE + "tasks.task.complete"
    try:
        resp = requests.post(url, data={"taskId": str(task_id)}, timeout=8)
        data = resp.json()
        return "result" in data
    except Exception:
        return False

def bitrix_task_comment(task_id: int, message: str) -> bool:
    url = BITRIX_BASE + "task.commentitem.add"
    try:
        resp = requests.post(url, data={
            "fields[TASK_ID]": str(task_id),
            "fields[POST_MESSAGE]": message,
        }, timeout=8)
        data = resp.json()
        return "result" in data
    except Exception:
        return False

# --- CRM Smart Process helpers ---
def bitrix_crm_item_add(entity_type_id: int, fields: Dict[str, Any]) -> Optional[int]:
    """
    Create Smart Process element.
    REST: crm.item.add
    """
    url = BITRIX_BASE + "crm.item.add"
    try:
        payload: Dict[str, Any] = {"entityTypeId": str(entity_type_id)}
        for k, v in fields.items():
            payload[f"fields[{k}]"] = v
        resp = requests.post(url, data=payload, timeout=10)
        data = resp.json()
        item_id = (data.get("result") or {}).get("item", {}).get("id")
        if not item_id:
            # Не трогаем asyncio из рабочего потока: просто логируем.
            try:
                err = data.get("error_description") or str(data)
                print(f"[CRM ADD] Ошибка: {err}", file=sys.stderr)
            except Exception:
                pass
            return None
        return int(item_id)
    except Exception:
        return None

def bitrix_crm_item_update(entity_type_id: int, item_id: int, fields: Dict[str, Any]) -> bool:
    """
    Update Smart Process element.
    REST: crm.item.update
    """
    url = BITRIX_BASE + "crm.item.update"
    try:
        payload: Dict[str, Any] = {"entityTypeId": str(entity_type_id), "id": str(item_id)}
        for k, v in fields.items():
            payload[f"fields[{k}]"] = v
        resp = requests.post(url, data=payload, timeout=10)
        data = resp.json()
        return "result" in data
    except Exception:
        return False

def bitrix_crm_timeline_comment(entity_type_id: int, item_id: int, comment: str) -> bool:
    """
    Add timeline comment to Smart Process element.
    REST: crm.timeline.comment.add
    """
    url = BITRIX_BASE + "crm.timeline.comment.add"
    try:
        resp = requests.post(url, data={
            "fields[ENTITY_TYPE_ID]": str(entity_type_id),
            "fields[ENTITY_ID]": str(item_id),
            "fields[COMMENT]": comment
        }, timeout=10)
        data = resp.json()
        return "result" in data
    except Exception:
        return False
