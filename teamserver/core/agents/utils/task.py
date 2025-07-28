from core.utils import common
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

TASK_STATUS_PENDING = "pending"
TASK_STATUS_FAIL = "fail"
TASK_STATUS_DONE = "done"

TASKS: Dict[str, List["Task"]] = {}
_task_counter = 1


@dataclass
class Task:
    id: int
    agent_id: str
    command: str
    status: str = TASK_STATUS_PENDING
    result: Optional[str] = None
    created_at: str = common.time_now_str()


def add_task(agent_id: str, command: str) -> int:
    global _task_counter
    task = Task(id=_task_counter, agent_id=agent_id, command=command)
    _task_counter += 1
    TASKS.setdefault(agent_id, []).append(task)
    return task.id


def get_tasks(agent_id: str) -> List[Task]:
    return [task for task in TASKS.get(agent_id, []) if task.status == TASK_STATUS_PENDING]


def get_all_tasks(agent_id: str) -> List[Task]:
    return TASKS.get(agent_id, [])


def get_task_by_id(agent_id: str, task_id: int) -> Optional[Task]:
    for task in TASKS.get(agent_id, []):
        if task.id == task_id:
            return task
    return None


def mark_task_done(agent_id: str, task_id: int, result: Optional[str] = None) -> bool:
    task = get_task_by_id(agent_id, task_id)
    if task:
        task.status = TASK_STATUS_DONE
        task.result = result
        return True
    return False

def mark_task_fail(agent_id: str, task_id: int, result: Optional[str] = None) -> bool:
    task = get_task_by_id(agent_id, task_id)
    if task:
        task.status = TASK_STATUS_FAIL
        task.result = result
        return True
    return False

def delete_task(agent_id: str, task_id: int) -> bool:
    task_list = TASKS.get(agent_id, [])
    for i, task in enumerate(task_list):
        if task.id == task_id:
            del task_list[i]
            return True
    return False

def get_task_dicts(agent_id: str) -> List[dict]:
    return [asdict(task) for task in get_all_tasks(agent_id)]
