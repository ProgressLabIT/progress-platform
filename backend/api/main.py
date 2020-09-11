from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

import endpoints



app = FastAPI()

# origins = [
#   "http://127.0.0.1:8080",
#   "http://localhost:8080",
# ]

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
app.include_router(endpoints.product, prefix="/product", tags=['Product'])
app.include_router(endpoints.bom, prefix="/product", tags=['Product'])
app.include_router(endpoints.process, tags=['Process'])
app.include_router(endpoints.item, tags=['Library'])
app.include_router(endpoints.production, tags=['Production'])
app.include_router(endpoints.org, tags=['Organization'])
app.include_router(endpoints.traceability, tags=['Traceability'])
app.include_router(endpoints.auth, tags=['security'])


if __name__ == "__main__":
  app.main()