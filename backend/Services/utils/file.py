import os

class UserFile:

  def __init__(self, base_path, append_path=None, file=None, name=None):
    if append_path:
      self.folder_path = os.path.join(base_path, append_path)
    
    if file:
      self.file = file

    if name:
      self.name = name


  @classmethod
  def product_image(cls, append_path, file=None):
    base_path = "/Volumes/Luca/DEV/Progress/WebApps/Library/public/pics/product"
    return cls(base_path, append_path, file)

  @classmethod
  def product_doc(cls, append_path, file=None, name=None):
    base_path = "/Volumes/Luca/DEV/Progress/WebApps/Library/public/docs"
    return cls(base_path, append_path, file, name)

  @classmethod
  def user_pic(cls, append_path, file):
    base_path = "/Volumes/Luca/DEV/Progress/WebApps/Library/public/pics/users"
    return cls(base_path, append_path, file)


  async def write_file(self, custom_name=None): 
    if not os.path.isdir(self.folder_path):
      os.mkdir(self.folder_path)

    if custom_name:
      self.name = custom_name

    with open(os.path.join(self.folder_path, self.name), 'wb+') as f:
      file = await self.file.read()
      f.write(file)


  def delete_file(self, name=None):
    if name:
      self.name = name

    file_path = os.path.join(self.folder_path, self.name)
    os.remove(file_path)
