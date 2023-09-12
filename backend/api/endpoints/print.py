from fastapi import APIRouter

from models.print import PrintTemplate
from utils.db import db

router = APIRouter()



# Fetch Print Templates
@router.get('/print-template')
async def get_print_templates(key: str = None):
  # If none get all of them
  ...


# Create PrintTemplate
@router.post('/print-template')
async def create_print_template(template_data: PrintTemplate):
  ...

# Update Print Template
@router.put('/print-template')
async def update_print_template(template_data: PrintTemplate):
  ...


# Delete Print Template
@router.delete('/print-template/{template_key}')
async def delete_print_template(template_key: str):
  ...
