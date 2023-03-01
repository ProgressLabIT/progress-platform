# Workflows in the Progress Platform

## High-level Architecture
Workflows are managed by the Prefect orchestration suite, which includes two components, the Prefect Server and Prefect Agents.

The Server stores metadata, handles scheduling, and provides a management and monitoring UI. The server is oblivious of the actual logic of flows, it just receives status updates about the flow tasks and stores state to handle retries etc. The actual workflow is carried out by the Agents, which run on a separate container and require access to all the libraries/packages/modules needed and, obviously to the code to run.

## System and Integration workflows
The Progress Platform has features that rely on workflows handled by Prefect. This are called "System" workflows. However most clients will have the need to implement their own data flows to exchange data with other business systems. These are called "Integration" workflows.

To keep concerns separate, the stack provides two different services to run System and Integration workflows, each associated to a different "queue" in the Prefect server.

## Setting up workflows

### System workflows
System workflows are stored in the `flows` directory. Each one must have its own directory and the actual flow code must be stored in a code.py file.
This structure allows the automatic registration of flows during the deployment phase via the `loader.py` script.

### Integration workflows
For the time being, Integration workflows will be created and managed manually.
