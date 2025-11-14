import requests
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

import endpoints.inventory
from utils.config import get_config
from utils.kafka.kafka_producer import KafkaProducer
from managers.kafka_consumer_manager import KafkaConsumerManager
from utils.kafka.kafka_admin import KafkaAdmin
from managers.executor_manager import ExecutorManager
from managers.websocket_manager import WebsocketManager
from managers.server_event_manager import ServerEventManager
from managers.notification_manager import NotificationManager
from utils.notification_kafka_consumer import NotificationsKafkaConsumer
from middlewares.notification_middleware import NotificationMiddleware
from middlewares.gzipfilter_middleware import GZipFilterMiddleware


import endpoints

config = get_config()

KafkaAdmin.getInstance().create_topic("notifications")

app = FastAPI(
	root_path=config.api_root_path
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

app.add_middleware(NotificationMiddleware)


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
    notificationsConsumer = NotificationsKafkaConsumer()
    KafkaConsumerManager.getInstance().registerConsumer(notificationsConsumer)
    WebsocketManager.getInstance()

def broadcast_message(self, msg):
      print("%% %s [%d] at offset %d with key %s:\n" %(msg.topic(), msg.partition(), msg.offset(),str(msg.key())))
      WebsocketManager.getInstance().enqueue(msg.value().decode('utf-8'))

@app.on_event("shutdown")
def shutdown_event():
   KafkaProducer.getInstance().close()
   KafkaConsumerManager.getInstance().closeAllConsumers()
   WebsocketManager.getInstance().close()
   ExecutorManager.getInstance().close()
   ServerEventManager.getInstance().close()
   NotificationManager.getInstance().close()

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
app.include_router(endpoints.inventory, tags=['Warehouse'])
app.include_router(endpoints.counting, tags=['Warehouse'])

# app.include_router(global_router, prefix="/v1")

if __name__ == "__main__":
  app.main()
