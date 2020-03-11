import os

class UserFile:

  public_path = "/Volumes/Luca/DEV/Progress/WebApps/Library/public"

  def __init__(self, base_path, append_path=None, file=None, name=None):
   
    if append_path:
      self.folder_path = os.path.join(self.public_path, base_path, append_path)
    else:
      self.folder_path = os.path.join(self.public_path, base_path)
    
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

  @classmethod
  def product_image(cls, file=None, name=None):
    base_path = "pics/products"
    return cls(base_path, file=file, name=name)

  @classmethod
  def product_doc(cls, append_path, file=None, name=None):
    base_path = "docs"
    return cls(base_path, append_path, file, name)

  @classmethod
  def user_pic(cls, append_path, file):
    base_path = "media/users"
    return cls(base_path, append_path, file)

  @classmethod
  def step_media(cls, append_path, file=None, name=None):
    base_path = "media/step"
    return cls(base_path, append_path, file, name)

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


  def get_folder_contents(self, append_path=None):
    if append_path:
      self.folder_path = os.path.join(self.folder_path, append_path)
  
    return [ f.name for f in os.scandir(self.folder_path) ]
