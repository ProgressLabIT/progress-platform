import asyncio
import logging

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from utils.config import get_config
import utils.nats_client as nats_client
from managers.server_event_manager import ServerEventManager
from middlewares.gzipfilter_middleware import GZipFilterMiddleware

import endpoints

logger = logging.getLogger("main")

config = get_config()

tags_metadata = [
    {
        "name": "Production",
        "description": "Work orders, jobs, batches, steps.",
        "externalDocs": {
            "description": "Events reference",
            "url": "https://progresslabit.github.io/progress-platform/events/production/",
        },
    },
    {
        "name": "Warehouse",
        "description": "Inventory positions, movements, counting sessions.",
        "externalDocs": {
            "description": "Events reference",
            "url": "https://progresslabit.github.io/progress-platform/events/inventory/",
        },
    },
    {
        "name": "Serial",
        "description": "Serial traceability lifecycle.",
        "externalDocs": {
            "description": "Events reference",
            "url": "https://progresslabit.github.io/progress-platform/events/serial/",
        },
    },
    {
        "name": "Collaboration",
        "description": "Issues, tasks, messages.",
        "externalDocs": {
            "description": "Events reference",
            "url": "https://progresslabit.github.io/progress-platform/events/collaboration/",
        },
    },
    {"name": "Security", "description": "Authentication, session management, password reset."},
    {"name": "Administration", "description": "System configuration, overrides, admin operations."},
    {"name": "Organization", "description": "Users, roles, org structure."},
    {"name": "Quality", "description": "Forms, print templates, DHR generation."},
    {
        "name": "Traceability",
        "description": "Batch execution records, counters, serial search.",
        "externalDocs": {
            "description": "Events reference",
            "url": "https://progresslabit.github.io/progress-platform/events/serial/",
        },
    },
    {"name": "Process", "description": "Process templates and phase configuration."},
    {"name": "Product", "description": "Product catalogue and BOM management."},
    {"name": "Attachments", "description": "File and media attachment management."},
    {"name": "Notification", "description": "SSE notification stream."},
    {"name": "Configuration", "description": "System-level tag, custom field, and configuration utilities."},
]

app = FastAPI(
    root_path=config.api_root_path,
    openapi_tags=tags_metadata,
)

app.add_middleware(
  CORSMiddleware,
  allow_origins=config.cors_allowed_origins,
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
  expose_headers=["Content-Disposition", "Content-Encoding", "Content-Length", "Content-Type"]
)

app.add_middleware(GZipFilterMiddleware, minimum_size=500, filtered_api="/notification")


"""
Each package __init__ file imports the router object from the
relative endpoint.py module, so it's easily available here
"""

@app.get("/hello")
async def hello():
  return 'Hi!'

@app.on_event("startup")
async def startup_event():
    nc = await nats_client.connect(config.nats_url)

    async def on_notification(msg):
        data = msg.data.decode()
        ServerEventManager.getInstance().enqueue(data)

    await nats_client.subscribe("progress.notification.>", cb=on_notification)

@app.on_event("shutdown")
async def shutdown_event():
   ServerEventManager.getInstance().close()
   await asyncio.sleep(0.5)
   await nats_client.drain()

app.include_router(endpoints.admin, tags=['Administration'])
app.include_router(endpoints.auth, tags=['Security'])
app.include_router(endpoints.bom, prefix="/product", tags=['Product'])
app.include_router(endpoints.config, tags=['Administration'])
app.include_router(endpoints.custom_data, tags=['Administration'])
app.include_router(endpoints.file, tags=['Attachments'])
app.include_router(endpoints.form, tags=['Quality'])
app.include_router(endpoints.serial, tags=['Serial'])
app.include_router(endpoints.media, tags=['Attachments'])
app.include_router(endpoints.org, tags=['Organization'])
app.include_router(endpoints.print, tags=['Quality', 'Traceability'])
app.include_router(endpoints.process, tags=['Process'])
app.include_router(endpoints.product, prefix="/product", tags=['Product'])
app.include_router(endpoints.production, tags=['Production'])
app.include_router(endpoints.tag, tags=['Configuration'])
app.include_router(endpoints.collaboration, tags=['Collaboration'])
app.include_router(endpoints.traceability, tags=['Traceability'])
app.include_router(endpoints.counter, tags=['Traceability'])
app.include_router(endpoints.notification, tags=['Notification'])
app.include_router(endpoints.inventory, tags=['Warehouse'])
app.include_router(endpoints.counting, tags=['Warehouse'])

if __name__ == "__main__":
  app.main()
