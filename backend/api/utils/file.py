import os
import shutil
from io import BufferedReader

from fastapi import UploadFile

from utils.config import get_config
from models.form import FileBucket

# TODO: OBJECT STORAGE MIGRATION - This entire file needs to be rewritten to use object storage
# instead of local filesystem operations. Key changes needed:
# 1. Replace all os.path operations with object storage key generation
# 2. Replace file I/O operations with object storage SDK calls
# 3. Update bucket_path, object_path, folder_path concepts for object storage
# 4. Replace os.makedirs, open(), os.remove, shutil operations
# 5. Add support for signed URLs and streaming uploads/downloads

media_root_path = get_config().media_path

class FileHandler:
  def __init__(
    self,
    bucket: FileBucket,
    object_key: str | None = None,
    subfolder: str | None = None,
    file: UploadFile | BufferedReader | None = None,
    name: str | None = None
  ):
    # TODO: OBJECT STORAGE MIGRATION - Update path building logic for object storage keys
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
    return cls(bucket=FileBucket.PRODUCT, object_key=object_key, subfolder=subfolder, file=file, name=name)

  @classmethod
  def user_image(cls, object_key=None, subfolder=None, file=None, name=None):
    return cls(bucket=FileBucket.USER, object_key=object_key, subfolder=subfolder, file=file, name=name)


  @classmethod
  def step_media(cls, object_key, subfolder=None, file=None, name=None):
    return cls(bucket=FileBucket.STEP, object_key=object_key, subfolder=subfolder, file=file, name=name)


  async def write_file(self, file: UploadFile | BufferedReader | None = None, custom_name: str | None = None):
    # TODO: OBJECT STORAGE MIGRATION - Replace file writing with object storage upload
    # Use object storage SDK to upload file to bucket with appropriate key
    if file:
      self.file = file
      if not custom_name:
        self.name = file.filename

    if custom_name:
      self.name = custom_name

    if not os.path.isdir(self.folder_path):
      os.makedirs(self.folder_path)

    with open(os.path.join(self.folder_path, self.name), 'wb+') as target_file:
      if isinstance(self.file, BufferedReader):
        file = self.file.read()
      else:
        file = await self.file.read()
      target_file.write(file)
      print(f"File saved in {self.folder_path}")


  # TODO: Check and do nothing if folder_path does not exist
  # TODO: Clean the contents of copy_path before copying
  def copy_media(self, copy_key):
    # TODO: OBJECT STORAGE MIGRATION - Replace shutil.copytree with object storage copy operation
    copy_path = os.path.join(media_root_path, self.bucket, copy_key)
    shutil.copytree(
      src=self.folder_path,
      dst=copy_path,
      dirs_exist_ok=True
    )

  def delete_file(self, name=None):
    # TODO: OBJECT STORAGE MIGRATION - Replace file deletion with object storage delete operation
    if name:
      self.name = name

    file_path = os.path.join(self.folder_path, self.name)
    os.remove(file_path)
    # Delete directory if empty
    if not os.listdir(self.folder_path):
      os.rmdir(self.folder_path)
      # remove Object directory if that is empty too
      if self.subfolder and not os.listdir(self.object_path):
        os.rmdir(self.object_path)

  def get_folder_contents(self, object_key=None, name_only=True):
    # TODO: OBJECT STORAGE MIGRATION - Replace os.scandir with object storage list operation
    if object_key:
      self.folder_path = os.path.join(self.folder_path, object_key)

    contents = os.scandir(self.folder_path) if os.path.isdir(self.folder_path) else []

    if name_only:
      return [ f.name for f in contents ]
    else:
      return [ f for f in contents]


  def clean_dir(self):
    # TODO: OBJECT STORAGE MIGRATION - Replace directory cleaning with object storage bulk delete
    if os.path.isdir(self.folder_path):
      for filename in os.listdir(self.folder_path):
        os.remove(os.path.join(self.folder_path, filename))

  def remove_dir(self):
    # TODO: OBJECT STORAGE MIGRATION - Replace directory removal with object storage prefix delete
    if os.path.isdir(self.folder_path):
      shutil.rmtree(self.folder_path)
