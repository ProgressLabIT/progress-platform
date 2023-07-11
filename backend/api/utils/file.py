import os
import shutil
from utils.config import get_config

media_root_path = get_config().media_path

class FileHandler:

  def __init__(self, bucket, object_key=None, subfolder=None, file=None, name=None):

    self.bucket = bucket # media type
    self.object_key = object_key # media item key
    self.subfolder = subfolder
    self.bucket_path = os.path.join(media_root_path, bucket)
    self.object_path = None
    self.folder_path = self.bucket_path

    if object_key:
      self.object_path = os.path.join(self.bucket_path, object_key)
      self.folder_path = self.object_path

      # Field path makes sense only under a specific object instance folder
      if subfolder:
        self.folder_path = os.path.join(self.object_path, subfolder)

    if file:
      self.file = file

    if name:
      self.name = name
    elif file:
      self.name = file.filename
    else:
      self.name = None


  def __repr__(self):
    return f'FileHandler object:\nfolder_path: {self.folder_path}\nfilename: {self.name}'

  # @classmethod
  # def product_image(cls, file=None, name=None):
  #   bucket = "media/product"
  #   return cls(bucket, file=file, name=name)

  @classmethod
  def product_media(cls, object_key, subfolder=None, file=None, name=None):
    bucket = "product"
    return cls(bucket=bucket, object_key=object_key, subfolder=subfolder, file=file, name=name)

  @classmethod
  def user_image(cls, object_key=None, subfolder=None, file=None, name=None):
    bucket = "user"
    return cls(bucket=bucket, object_key=object_key, subfolder=subfolder, file=file, name=name)


  @classmethod
  def step_media(cls, object_key, subfolder=None, file=None, name=None):
    bucket = "step"
    return cls(bucket=bucket, object_key=object_key, subfolder=subfolder, file=file, name=name)


  async def write_file(self, custom_name=None):
    if not os.path.isdir(self.folder_path):
      os.makedirs(self.folder_path)

    if custom_name:
      self.name = custom_name

    with open(os.path.join(self.folder_path, self.name), 'wb+') as f:
      file = await self.file.read() # self.file is a `UploadFile` object, and the write method requires a bytes-like object
      f.write(file)
      print(f"File saved in {self.folder_path}")


  def copy_media(self, copy_key):
    copy_path = os.path.join(media_root_path, self.bucket, copy_key)
    shutil.copytree(
      self.folder_path,
      copy_path,
      dirs_exist_ok=True
    )

  def delete_file(self, name=None):
    if name:
      self.name = name

    file_path = os.path.join(self.folder_path, self.name)
    os.remove(file_path)


  def get_folder_contents(self, object_key=None, name_only=True):
    if object_key:
      self.folder_path = os.path.join(self.folder_path, object_key)

    contents = os.scandir(self.folder_path) if os.path.isdir(self.folder_path) else []

    if name_only:
      return [ f.name for f in contents ]
    else:
      return [ f for f in contents]
