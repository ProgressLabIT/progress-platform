import requests
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from utils.config import get_config
from utils.kafka.kafka_producer import KafkaProducer
from managers.kafka_consumer_manager import KafkaConsumerManager
from managers.executor_manager import ExecutorManager
from consumer.serials_kafka_consumer import SerialsKafkaConsumer
from utils.serial_manager import SerialManager

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
    SerialManager.getInstance()
    consumer = SerialsKafkaConsumer()
    KafkaConsumerManager.getInstance().registerConsumer(consumer)


@app.on_event("shutdown")
def shutdown_event():
   KafkaProducer.getInstance().close()
   KafkaConsumerManager.getInstance().closeAllConsumers()
   ExecutorManager.getInstance().close()
   SerialManager.getInstance().close()



# app.include_router(global_router, prefix="/v1")

if __name__ == "__main__":
  app.main()
