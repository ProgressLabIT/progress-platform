import importlib.util
import os
import sys

from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

from flowcode import pause_offline_jobs



deployment = Deployment.build_from_flow(
  flow=pause_offline_jobs,
  name="main",
  description=pause_offline_jobs.__doc__.strip(),
  work_queue_name='system',
  schedule=CronSchedule(cron="0 * * * *"),
  output=f'deployments/{entry_name}.yaml',
  skip_upload=True,
  apply=True
)
