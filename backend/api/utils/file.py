import os
import shutil
from utils.config import get_config

media_root_path = get_config().media_path

class UserFile:

  def __init__(self, base_path, append_path=None, file=None, name=None):

    self.base_path = base_path # media type
    self.append_path = append_path # media item key

    if append_path:
      self.folder_path = os.path.join(media_root_path, base_path, append_path)
    else:
      self.folder_path = os.path.join(media_root_path, base_path)

    if file:
      self.file = file

    if name:
      self.name = name
    elif file:
      self.name = file.filename
    else:
      self.name = None


  def __repr__(self):
    return f'UserFile object:\nfolder_path: {self.folder_path}\nfilename: {self.name}'

  # @classmethod
  # def product_image(cls, file=None, name=None):
  #   base_path = "media/product"
  #   return cls(base_path, file=file, name=name)

  @classmethod
  def product_media(cls, append_path, file=None, name=None):
    base_path = "product"
    return cls(base_path, append_path, file, name)

  @classmethod
  def user_image(cls, append_path, file=None):
    base_path = "user"
    return cls(base_path, append_path, file)

  @classmethod
  def step_media(cls, append_path, file=None, name=None):
    base_path = "step"
    return cls(base_path, append_path, file, name)

  async def write_file(self, custom_name=None):
    if not os.path.isdir(self.folder_path):
      os.makedirs(self.folder_path)

    if custom_name:
      self.name = custom_name

    with open(os.path.join(self.folder_path, self.name), 'wb+') as f:
      file = await self.file.read()
      f.write(file)
      print(f"Image saved in {self.folder_path}")


  def copy_media(self, copy_key):
    copy_path = os.path.join(media_root_path, self.base_path, copy_key)
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


  def get_folder_contents(self, append_path=None, name_only=True):
    if append_path:
      self.folder_path = os.path.join(self.folder_path, append_path)

    contents = os.scandir(self.folder_path) if os.path.isdir(self.folder_path) else []

    if name_only:
      return [ f.name for f in contents ]
    else:
      return [ f for f in contents]
