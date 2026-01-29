import importlib.util
import os
from prefect.client.orchestration import get_client
from prefect.client.schemas.actions import WorkPoolCreate
from prefect.exceptions import ObjectNotFound

def check_entry(entry):
  return (
    entry.name != '__init__.py'
    and not os.path.isdir(entry)
  )

def ensure_work_pool_exists(pool_name: str, pool_type: str = "process"):
  """
  Check if a work pool exists and create it if it doesn't.
  """
  try:
    # Use sync client (Prefect 2.x supports both sync and async)
    with get_client(sync_client=True) as client:
      # Try to read the work pool by name
      try:
        pool = client.read_work_pool(pool_name)
        print(f"Work pool '{pool_name}' already exists.")
        return
      except ObjectNotFound:
        # Work pool doesn't exist, create it
        print(f"Work pool '{pool_name}' not found. Creating...", end="")
        create_payload = WorkPoolCreate(
          name=pool_name,
          type=pool_type,
        )
        pool = client.create_work_pool(work_pool=create_payload)
        print(f" Created work pool: {pool.name}")
      except Exception as e:
        print(f"Error checking/creating work pool: {e}")
        raise
  except Exception as e:
    print(f"Warning: Could not ensure work pool exists: {e}")
    print("You may need to create it manually: prefect work-pool create system --type process")

flow_list = [entry for entry in os.scandir('flowcode') if check_entry(entry)]

"""
This script loads the flows contained in the each folder under the `flowcode` directory,
deploying them to the Prefect server using the Prefect 3.x API.
"""

# Ensure the 'system' work pool exists before deploying
ensure_work_pool_exists('system', 'process')

# Get the absolute path to the flows directory (where this script is located)
flows_base_dir = os.path.abspath(os.path.dirname(__file__))

# run script to build and apply the flow
for entry in flow_list:
  # Strip .py from entry name
  entry_name = entry.name[:-3]
  print(f"Loading {entry_name}...", end="")

  # Load modules to get the flow object (for validation)
  flow_module = importlib.util.spec_from_file_location(entry_name, entry.path).loader.load_module()
  flow = flow_module.main

  # Prepare deployment parameters
  deploy_kwargs = dict(
    name=entry_name,
    work_pool_name='system',
    build=False,  # Don't build Docker image for local process pool
    push=False,   # Don't push to registry for local process pool
  )

  # Add description if available
  if flow_module.main.__doc__:
    deploy_kwargs['description'] = flow_module.main.__doc__.strip()

  # Add schedule if present (Prefect 3.x uses 'schedules' as a list)
  try:
    schedule = flow_module.schedule
    if schedule:
      deploy_kwargs['schedules'] = [schedule]
  except AttributeError:
    # Do not add schedules if not present in the flow
    pass

  # Deploy the flow using Prefect 2.x API with from_source to specify local code location
  # The entrypoint is relative to the flows_base_dir (flows directory)
  flow.from_source(
    source=flows_base_dir,  # Absolute path to flows directory
    entrypoint=f"flowcode/{entry_name}.py:main"  # Entrypoint relative to flows_base_dir
  ).deploy(**deploy_kwargs)

  print("Done.")
