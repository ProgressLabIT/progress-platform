import json
import math

from arango import ArangoClient
from fastapi.encoders import jsonable_encoder

from utils import config

# ArangoDB connection and custom serializer with float precision management.
# The encoder() function rounds all float values to 6 decimal places before
# database writes to prevent floating-point noise and ensure clean numeric data.


def _round_floats_recursive(obj, decimals: int):
  """
  Recursively round all float values in nested data structures.

  This function walks through dictionaries and lists to find and round all
  float values to the specified decimal precision. Used by the serializer
  to ensure clean numeric data in the database.

  Args:
    obj: Object to process (can be dict, list, float, or any other type)
    decimals: Number of decimal places to round to

  Returns:
    Processed object with all floats rounded

  Note: Infinity and NaN values are preserved as-is since rounding them
        is mathematically undefined.
  """
  if isinstance(obj, float):
    # Handle special float values
    if math.isinf(obj) or math.isnan(obj):
      return obj
    return round(obj, decimals)
  elif isinstance(obj, dict):
    return {k: _round_floats_recursive(v, decimals) for k, v in obj.items()}
  elif isinstance(obj, list):
    return [_round_floats_recursive(item, decimals) for item in obj]
  # All other types (int, str, bool, None, etc.) pass through unchanged
  return obj


def model_to_db_dict(pydantic_model):
  prepped_data = jsonable_encoder(pydantic_model, by_alias=True)

  # remove null _id / _key fields
  for field in ['_id', '_key']:
    if field in prepped_data:
      if prepped_data[field] is None:
        del prepped_data[field]

  return prepped_data


def encoder(data):
  # Convert Pydantic models to dicts (plain dicts pass through unchanged)
  dict_data = model_to_db_dict(data)

  # Round all float values to configured precision before database write.
  # This prevents floating-point noise (e.g., 100.000001) from being stored,
  # ensuring clean numeric data for UI display and reliable comparisons.
  # Uses 6-decimal precision by default (configurable via PROGRESS_FLOAT_PRECISION_DECIMALS).
  precision = conf.float_precision_decimals
  rounded_data = _round_floats_recursive(dict_data, precision)

  return json.dumps(rounded_data)


conf = config.get_config()

client = ArangoClient(hosts=conf.arango_url, serializer=encoder)

db = client.db(conf.db_name, username=conf.api_db_username, password=conf.api_db_pwd)
