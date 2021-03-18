import requests
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from utils.config import get_config
import endpoints

config = get_config()

app = FastAPI(
	# openapi_url=f"{config.root_path}/openapi.json",
	root_path=config.root_path
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

@app.get("/test")
async def test_api():
	r = requests.get('http://mock.progress.localhost/test')
	return r.text


@app.get('/mock')
async def mock_response():
	return "TEST"


app.include_router(endpoints.product, prefix="/product", tags=['Product'])
app.include_router(endpoints.bom, prefix="/product", tags=['Product'])
app.include_router(endpoints.process, tags=['Process'])
app.include_router(endpoints.item, tags=['Library'])
app.include_router(endpoints.production, tags=['Production'])
app.include_router(endpoints.org, tags=['Organization'])
app.include_router(endpoints.traceability, tags=['Traceability'])
app.include_router(endpoints.auth, tags=['security'])

# app.include_router(global_router, prefix="/v1")

if __name__ == "__main__":
  app.main()
