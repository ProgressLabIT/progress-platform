import importlib.util
import os

from prefect.deployments import Deployment

flow_list = [entry.name for entry in os.scandir() if os.path.isdir(entry)]

"""
This script loads the flows contained in the each folder under the `flow` directory, generating the relative deployment file in the same folder.
"""

for entry in flow_list:
  # run script to build and apply the flow
  flow = importlib.util.spec_from_file_location(
    entry, f'{entry}/code.py'
  ).loader.load_module().main

  deployment = Deployment.build_from_flow(
    flow=flow,
    name='main',
    version=1,
    work_queue_name="system",
    output=f'{entry}/deployment.yaml',
    skip_upload=True,
    apply=True
  )
