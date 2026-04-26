from collections.abc import Callable
from typing import Any

from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler


def create_scheduler() -> AsyncIOScheduler:
    return AsyncIOScheduler()


def schedule_subscription_job(
    scheduler: AsyncIOScheduler,
    job_func: Callable[..., Any],
) -> Job:
    return scheduler.add_job(
        job_func,
        trigger="interval",
        minutes=1,
        id="subscription_dispatch",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )
