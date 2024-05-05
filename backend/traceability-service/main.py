import requests
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from commons.utils.config import get_config
from commons.kafka_utils.kafka_producer import KafkaProducer
from commons.kafka_utils.kafka_consumer import KafkaConsumer
from commons.executors.executor_manager import ExecutorManager
from commons.websockets.websocket_manager import WebsocketManager

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
    KafkaConsumer.getInstance().subscribe_topic("serial")
    WebsocketManager.getInstance()


@app.on_event("shutdown")
def shutdown_event():
   KafkaProducer.getInstance().close()
   KafkaConsumer.getInstance().close()
   WebsocketManager.getInstance().close()
   ExecutorManager.getInstance().close()



# app.include_router(global_router, prefix="/v1")

if __name__ == "__main__":
  app.main()
