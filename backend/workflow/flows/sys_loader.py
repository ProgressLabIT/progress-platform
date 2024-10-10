import importlib.util
import os
import sys

from prefect.deployments import Deployment

def check_entry(entry):
  return (
    entry.name != '__init__.py'
    and not os.path.isdir(entry)
  )

flow_list = [entry for entry in os.scandir('flowcode') if check_entry(entry)]

"""
This script loads the flows contained in the each folder under the `flowcode` directory, generating the relative deployment file in the same folder.
"""


# run script to build and apply the flow
for entry in flow_list:
  # Strip .py from entry name
  entry_name = entry.name[:-3]
  print(f"Loading {entry_name}...", end="")

  # Load modules
  flow = importlib.util.spec_from_file_location(entry_name, entry.path).loader.load_module()

  deploy_options = dict(
    flow=flow.main,
    name="main",
    description=flow.main.__doc__.strip(),
    work_queue_name='system',
    output=f'deployments/{entry_name}.yaml',
    skip_upload=True,
    apply=True
  )

  try:
    deploy_options.update(schedules=[flow.schedule])
  except AttributeError:
    # Do not add schedules if not present in the flow
    pass

  deployment = Deployment.build_from_flow(**deploy_options)

  print("Done.")
