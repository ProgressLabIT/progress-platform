from models.base_models import ArangoDocument

class Config(ArangoDocument):
  # _key is the name of the config (e.g. company_name, default_phase_parameters)
  # If the value is a dict, it will have its own set of fields
  # If the value is a primitive(e.g. str, int, bool), it will be stored in the `value` field
  # If the value is a file, it will be stored in the `value` field as a path
  pass
