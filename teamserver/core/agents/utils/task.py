from core.utils import common
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

TASK_STATUS_PENDING = "pending"
# TASK_STATUS_FAIL = "fail"
TASK_STATUS_DONE = "done"

TASKS: Dict[str, List["Task"]] = {}
_task_counter = 1


@dataclass
class Task:
    id: str
    agent_id: str
    command: str
    header: str
    status: str = TASK_STATUS_PENDING
    result: Optional[str] = None
    result_at: str = None 
    created_at: str = common.time_now_str()


def add_task(agent_id: str, command: str, header :str ="") -> int:
    global _task_counter
    task = Task(id=str(_task_counter), agent_id=agent_id, command=command, header=header)
    _task_counter += 1
    TASKS.setdefault(agent_id, []).append(task)
    return task.id

def get_all() -> List[Task]:
    return [task for task in TASKS.values()]

def get_tasks(agent_id: str) -> List[Task]:
    return [task for task in TASKS.get(agent_id, []) if task.status == TASK_STATUS_PENDING]


def get_all_tasks(agent_id: str) -> List[Task]:
    return TASKS.get(agent_id, [])


def get_task_by_id(agent_id: str, task_id: str) -> Optional[Task]:
    for task in TASKS.get(agent_id, []):
        if task.id == task_id:
            return task
    return None

def get_earliest_task(agent_id: str) -> Optional[Task]:
    tasks = get_tasks(agent_id)
    if not tasks:
        return None
    return min(tasks, key=lambda task: task.created_at)

def get_earliest_result(agent_id: str) -> Optional[Task]:
    tasks = get_all_tasks(agent_id)
    if not tasks:
        return None
    
    done_tasks = [task for task in tasks if task.status == TASK_STATUS_DONE]
    if not done_tasks:
        return None
    return max(done_tasks, key=lambda task: task.id)


def mark_task_done(agent_id: str, task_id: int, result: Optional[str] = None) -> bool:
    task = get_task_by_id(agent_id, task_id)
    if task:
        task.status = TASK_STATUS_DONE
        task.result = result
        task.result_at = common.time_now_str()
        return True
    return False

# def mark_task_fail(agent_id: str, task_id: int, result: Optional[str] = None) -> bool:
#     task = get_task_by_id(agent_id, task_id)
#     if task:
#         task.status = TASK_STATUS_FAIL
#         task.result = result
#         return True
#     return False

# def delete_task(agent_id: str, task_id: int) -> bool:
#     task_list = TASKS.get(agent_id, [])
#     for i, task in enumerate(task_list):
#         if task.id == task_id:
#             del task_list[i]
#             return True
#     return False

def get_task_dicts(agent_id: str) -> List[dict]:
    return [asdict(task) for task in get_all_tasks(agent_id)]
