from models.base_models import ArangoDocument

class Config(ArangoDocument):
  """Platform configuration entry stored in the `Config` ArangoDB collection.

  Each document's `_key` is the configuration parameter name
  (e.g. `company_name`, `default_production_position`).

  - Scalar values (str, int, bool) are stored under a `value` field.
  - Dict values store their sub-fields directly on the document.
  - File-backed values store the absolute filesystem path under `value`.

  This model carries only the ArangoDocument identity fields (`_key`, `_id`,
  `_rev`). The actual payload shape is open and varies per configuration entry.
  """
  # _key is the name of the config (e.g. company_name, default_phase_parameters)
  # If the value is a dict, it will have its own set of fields
  # If the value is a primitive(e.g. str, int, bool), it will be stored in the `value` field
  # If the value is a file, it will be stored in the `value` field as a path
  pass
