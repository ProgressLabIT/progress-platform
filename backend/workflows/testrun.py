from datetime import timedelta
from prefect import task, Flow
from prefect.schedules import IntervalSchedule


@task
def hello():
  print('Hi!')


schedule = IntervalSchedule(interval=timedelta(minutes=1))

with Flow("Test", schedule=schedule) as flow:
  hello()

flow.run()
