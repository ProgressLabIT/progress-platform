from fastapi import FastAPI

from modules import product


app = FastAPI()

app.include_router(product.router, prefix="/product", tags=["product"])

if __name__ == "__main__":
  app.main()