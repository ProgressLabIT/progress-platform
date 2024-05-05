import requests
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from commons.utils.config import get_config
from commons.kafka_utils.kafka_producer import KafkaProducer
from commons.kafka_utils.kafka_consumer import KafkaConsumer
from commons.kafka_utils.kafka_admin import KafkaAdmin
from commons.executors.executor_manager import ExecutorManager
from commons.websockets.websocket_manager import WebsocketManager


import endpoints

config = get_config()

app = FastAPI(
	# openapi_url=f"{config.root_path}/openapi.json",
	root_path=config.api_root_path
)
# global_router = APIRouter()


app.add_middleware(
  CORSMiddleware,
  allow_origins=["*"],
  allow_credentials=True,
  allow_methods=["*"],
  allow_headers=["*"],
)

"""
Each package __init__ file imports the router object from the
relative endpoint.py module, so it's easily available here
"""

@app.get("/hello")
async def hello():
  return 'Hi!'

@app.on_event("startup")
async def startup_event():
    KafkaProducer.getInstance()
    KafkaConsumer.getInstance()
    KafkaAdmin.getInstance()
    WebsocketManager.getInstance()


@app.on_event("shutdown")
def shutdown_event():
   KafkaProducer.getInstance().close()
   KafkaConsumer.getInstance().close()
   WebsocketManager.getInstance().close()
   ExecutorManager.getInstance().close()

app.include_router(endpoints.admin, tags=['Administration'])
app.include_router(endpoints.auth, tags=['Security'])
app.include_router(endpoints.bom, prefix="/product", tags=['Product'])
app.include_router(endpoints.config, tags=['Administration'])
app.include_router(endpoints.file, tags=['Attachments'])
app.include_router(endpoints.form, tags=['Quality'])
app.include_router(endpoints.serial, tags=['Serial'])
app.include_router(endpoints.media, tags=['Attachments'])
app.include_router(endpoints.org, tags=['Organization'])
app.include_router(endpoints.print, tags=['Quality', 'Traceability'])
app.include_router(endpoints.process, tags=['Process'])
app.include_router(endpoints.product, prefix="/product", tags=['Product'])
app.include_router(endpoints.production, tags=['Production'])
app.include_router(endpoints.tag)
app.include_router(endpoints.collaboration, tags=['Collaboration'])
app.include_router(endpoints.traceability, tags=['Traceability'])
app.include_router(endpoints.counter, tags=['Traceability'])
app.include_router(endpoints.notification, tags=['Notification'])

# app.include_router(global_router, prefix="/v1")

if __name__ == "__main__":
  app.main()
