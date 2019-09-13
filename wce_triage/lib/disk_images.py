# Copyright (c) 2019 Naoyuki tai
# MIT license - see LICENSE
"""disk_image scans the disk image candidate directories and returns availabe disk images for loading.
"""
import os, datetime, json, traceback
from ..lib.util import *

tlog = get_triage_logger()

IMAGE_META_JSON_FILE = ".disk_image_type.json"

# gets the potential directories to look for disk images
def get_maybe_disk_image_directories():
  dirs = []

  # No longer look for other directories.
  # It would make things rather complicated.

  wce_images = "/usr/local/share/wce/wce-disk-images"
  if os.path.exists(wce_images) and os.path.isdir(wce_images) and wce_images not in dirs:
    dirs.append(wce_images)
    pass

  return dirs

#
# 
#
def get_disk_images(wce_share_url=None):
  '''scans the known drectories for disk image and returns the list of disk images

    :arg none

    :returns: list of dict instances. 
      mtime: file modify time
      restoreType: keyword for restore type. [wce|wce-16|triage|clone]
                   The restore type is nothing more than the name of directory, and
                   should match exactly to the restore type.
      name: filename - this is shown to the user.
      size: file size
      fullpath: the full path.

    ..note the entries are deduped by the filename so if two directories
           contain the same file name, only one is pikced.
  '''
  # Dedup the same file name
  images = {}
  for subdir in get_maybe_disk_image_directories():
    for direntry in os.listdir(subdir):
      # Anything starting with "." is ignored
      if direntry[0:1] == '.':
        continue

      catalog_dir = os.path.join(subdir, direntry)
      image_meta_file = os.path.join(catalog_dir, IMAGE_META_JSON_FILE)
      if not os.path.exists(image_meta_file) or not os.path.isfile(image_meta_file):
        continue

      if direntry.endswith(".partclone.gz"):
        images[direntry] = (direntry, "", catalog_dir)
        pass

      if os.path.isdir(catalog_dir):
        for direntryinsubdir in os.listdir(catalog_dir):
          # Anything starting with "." is ignored
          if direntryinsubdir[0:1] == '.':
            continue
          if direntryinsubdir.endswith(".partclone.gz"):
            images[direntryinsubdir] = (direntryinsubdir, direntry, os.path.join(catalog_dir, direntryinsubdir))
            pass
          pass
        pass
      pass
    pass

  result = []
  for filename, image in images.items():
    fname, subdir, fullpath = image
    filestat = os.stat(fullpath)
    mtime = datetime.datetime.fromtimestamp(filestat.st_mtime)

    # If wce_share_url is provided, reconstruct the fullpath. HTTP server needs to respond to the route.
    if wce_share_url:
      fullpath = '{wce_share_url}/wce-disk-images/{restoretype}/{filename}'.format(wce_share_url=wce_share_url, restoretype=subdir, filename=filename)
      pass

    fattr = { "mtime": mtime.strftime('%Y-%m-%d %H:%M'),
              "restoreType" : subdir,
              "name": filename,
              "fullpath": fullpath,
              "size": filestat.st_size }
    result.append(fattr)
    pass

  return result


def read_disk_image_types(verbose=False):
  '''scans the known drectories for disk image and returns the list of disk image types

    :arg none

    :returns: list of dict instances which is .disk_image_type.json file in the directory. 

  '''
  image_metas = []
  for subdir in get_maybe_disk_image_directories():
    if verbose:
      print("Checking subdir " + subdir)
      pass
    for direntry in os.listdir(subdir):
      catalog_dir = os.path.join(subdir, direntry)
      image_meta = read_disk_image_type(catalog_dir)
      if verbose:
        print("Catalog dir " + catalog_dir)
        print(image_meta)
        pass
      if image_meta:
        image_metas.append(image_meta)
        pass
      pass
    pass
  return image_metas


def read_disk_image_type(catalog_dir):
  '''reads the disk image type file from the directory

    :arg dir

    :returns: a dict instance from the image-meta

  '''
  result = None
  try:
    image_meta_file = os.path.join(catalog_dir, IMAGE_META_JSON_FILE)
    if not os.path.exists(image_meta_file) or not os.path.isfile(image_meta_file):
      return None
  
    with open(image_meta_file) as meta_file:
      result = json.load(meta_file)
      pass
    pass
  except json.decoder.JSONDecodeError:
    tlog.debug('catalog_dir %s: JSON parse error. Check the contents.' % catalog_dir);
    pass
  except:
    # If anything goes wrong, just ignore the directory.
    tlog.debug('catalog_dir %s: %s' % (catalog_dir, traceback.format_exc()))
    pass
  # 
  if result:
    result["catalogDirectory"] = catalog_dir
    pass
  
  return result


def make_disk_image_name(destdir, inname, filesystem='ext4'):
  image_meta = read_disk_image_type(destdir)
  if image_meta is None:
    if inname is None:
      exc_msg = "Directory {dir} does not have '{json_file}' file.".format(dir=destdir, json_file=IMAGE_META_JSON_FILE)
      raise Exception(exc_msg)
    return inname

  imagename = image_meta["filestem"]
  if not imagename:
    imagename = inname
    pass
    
  if image_meta.get("timestamp", False):
    timestamp = datetime.date.today().isoformat()
    imagename = imagename + "-" + timestamp
    pass
  # Right now, this is making ext4
  imagename = imagename + ".%s.partclone.gz" % filesystem
  return os.path.join(destdir, imagename)


def get_file_system_from_source(source):
  filesystem_ext = None
  tail = ".partclone.gz"
  if source.endswith(tail):
    source = source[:-len(tail)]
  else:
    return None
  try:
    filesystem_ext = os.path.splitext(source)[1][1:]
  except:
    pass

  if filesystem_ext in ['ext4', 'ext3', 'fat32', 'vfat', 'fat16']:
    return filesystem_ext
  return None


def translate_disk_image_name_to_url(wce_share_url, disk_image_name):
  for source in get_disk_images(wce_share_url):
    if source["name"] == disk_image_name:
      return source
    pass
  return disk_image

#
if __name__ == "__main__":
  logging.basicConfig(level=logging.DEBUG,
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                      filename='/tmp/disk_images.log')
  
  print(read_disk_image_types(verbose=True))
  print(get_disk_images())
  print(get_file_system_from_source("a.ext4.partclone.gz"))
  print(get_file_system_from_source("a.ext4.partclone"))
  print(get_file_system_from_source("a.partclone.gz"))
  print(read_disk_image_type("/usr/local/share/wce/wce-disk-images/triage"))

  for disk_image in get_disk_images():
    print(translate_disk_image_name_to_url("http://10.3.2.1:8080/wce", disk_image["name"]))
    pass
  pass
