# File: src/compute/fairness.py
# Purpose: Dynamic max-min fairness over a fixed pool of shared-brain slots.
#
#   per-user cap = max(MIN_PER_USER, total // active_users)
#
# Alone -> cap = total (use the whole brain, no waste). Two busy users -> total/2
# each. Five -> total/5. No preemption: a user keeps the slots they hold; as each
# (short) job finishes, the freed slot goes to whoever is under their cap. Converges
# in seconds. In-process to the single consumer (multi-consumer -> Redis later).

import asyncio
import os
from collections import defaultdict
from contextlib import asynccontextmanager

LPCX_BRAIN_CAP = int(os.getenv("LPCX_BRAIN_CAP", "50"))
LPCX_MIN_PER_USER = int(os.getenv("LPCX_MIN_PER_USER", "1"))


class FairBrain:
    def __init__(self, total: int, min_per_user: int = 1):
        self.total = total
        self.min_per_user = min_per_user
        self.running: dict[str, int] = defaultdict(int)   # owner -> running slots
        self.waiting: dict[str, int] = defaultdict(int)   # owner -> queued waiters
        self._cond = asyncio.Condition()

    def _active_users(self) -> int:
        users = {u for u, c in self.running.items() if c > 0}
        users |= {u for u, c in self.waiting.items() if c > 0}
        return max(1, len(users))

    def _cap(self) -> int:
        return max(self.min_per_user, self.total // self._active_users())

    def _can_run(self, owner: str) -> bool:
        total_running = sum(self.running.values())
        return total_running < self.total and self.running[owner] < self._cap()

    @asynccontextmanager
    async def slot(self, owner: str):
        async with self._cond:
            self.waiting[owner] += 1
            while not self._can_run(owner):
                await self._cond.wait()
            self.waiting[owner] -= 1
            if self.waiting[owner] <= 0:
                self.waiting.pop(owner, None)
            self.running[owner] += 1
        try:
            yield
        finally:
            async with self._cond:
                self.running[owner] -= 1
                if self.running[owner] <= 0:
                    self.running.pop(owner, None)
                self._cond.notify_all()   # caps may have shifted -- re-evaluate waiters

    def snapshot(self) -> dict:
        return {
            "total": self.total,
            "running": sum(self.running.values()),
            "active_users": self._active_users(),
            "cap_per_user": self._cap(),
            "by_user": dict(self.running),
        }


fair_brain = FairBrain(LPCX_BRAIN_CAP, LPCX_MIN_PER_USER)
