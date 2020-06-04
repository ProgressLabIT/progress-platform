from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from modules import (
  bom,
  item,
  org,
  process,
  product,
  production, 
  traceability
)




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
app.include_router(product.router, prefix="/product", tags=['Product'])
app.include_router(bom.router, prefix="/product", tags=['Product'])
app.include_router(process.router, tags=['Process'])
app.include_router(item.router, tags=['Library'])
app.include_router(production.router, tags=['Production'])
app.include_router(org.router, tags=['Organization'])
app.include_router(traceability.router, tags=['Traceability'])


if __name__ == "__main__":
  app.main()