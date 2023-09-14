import requests
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from utils.config import get_config
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


app.include_router(endpoints.admin, tags=['Administration'])
app.include_router(endpoints.auth, tags=['Security'])
app.include_router(endpoints.bom, prefix="/product", tags=['Product'])
app.include_router(endpoints.file, tags=['Attachments'])
app.include_router(endpoints.form, tags=['Quality', 'Traceability'])
app.include_router(endpoints.org, tags=['Organization'])
app.include_router(endpoints.print, tags=['Quality', 'Traceability'])
app.include_router(endpoints.process, tags=['Process'])
app.include_router(endpoints.product, prefix="/product", tags=['Product'])
app.include_router(endpoints.production, tags=['Production'])
app.include_router(endpoints.quality, tags=['Quality'])
app.include_router(endpoints.traceability, tags=['Traceability'])

# app.include_router(global_router, prefix="/v1")

if __name__ == "__main__":
  app.main()
