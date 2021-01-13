from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


app = FastAPI()
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
	return 'OK'

if __name__ == "__main__":
  app.main()