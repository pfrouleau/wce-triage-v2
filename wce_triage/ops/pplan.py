#!/usr/bin/env python3
#
from wce_triage.components.disk import Disk, Partition

EFI_NAME = 'EFI_System_Partition'
EFI_PART_OPT ='boot,esp'


class PartPlan:
  attribs = ['no', 'name', 'filesys', 'start', 'size', 'parttype', 'flags', 'mkfs_opts']

  def __init__(self, no, name, filesys, start, size, parttype, flags, mkfs_opts):
    self.no = no
    self.name = name
    self.filesys = filesys
    self.start = start
    self.size = size # Size is in MiB
    self.parttype = parttype
    self.flags = flags
    self.mkfs_opts = mkfs_opts
    pass

  def __get__(self, tag):
    if tag not in self.attribs:
      raise("NO %s!" % tag)
    return super().__get__(tag)

  def __set__(self, tag, value):
    if tag not in self.attribs:
      raise("NO %s!" % tag)
    super().__set__(tag, value)
    pass

  pass


def _ext4_version_to_mkfs_opts(ext4_version):
  # extfs 1.42 has no metadata_csum
  return [ '-O', '^metadata_csum'] if ext4_version == "1.42" else None
  
#
# This is univeral partition plan, should work for efi or traditional boot.
# I think Ubuntu 18.04LTS and up should use EFI boot.
# 
def make_efi_partition_plan(disk, ext4_version=None, efi_boot=False):
  diskmbsize = int(disk.get_byte_size() / (1024*1024))
  # Use up to 5% of disk for swap, but stop at 8GB. 
  swapsize = int(diskmbsize * 0.05)
  swapsize = 8192 if swapsize > 8192 else (2048 if swapsize < 2048 else swapsize)


  mkfs_opts = _ext4_version_to_mkfs_opts(ext4_version)

  if efi_boot:
    bios_part_opt = None
    efi_part_opt = EFI_PART_OPT
  else:
    bios_part_opt = 'boot'
    efi_part_opt = None
    pass
  
  pplan = [PartPlan(0, None,     None,         0,        2, Partition.MBR,      None,          None),
           PartPlan(1, 'BOOT',   None,         0,       32, Partition.BIOSBOOT, bios_part_opt, None),
           PartPlan(2, EFI_NAME, 'fat32',      0,      512, Partition.UEFI,     efi_part_opt,  None),
           PartPlan(3, 'SWAP',   'linux-swap', 0, swapsize, Partition.SWAP,     None,          None),
           PartPlan(4, 'Linux',  'ext4',       0,        0, Partition.EXT4,     None,          mkfs_opts) ]
  partion_start = 0
  for part in pplan:
    part.start = partion_start
    if part.size == 0:
      diskmbsize = diskmbsize - 1
      part.size = diskmbsize
      pass
      
    partion_start = partion_start + part.size
    diskmbsize = diskmbsize - part.size
    pass
  return pplan


def make_usb_stick_partition_plan(disk, partition_id=None, ext4_version=None, efi_boot=False):
  diskmbsize = int(disk.get_byte_size() / (1024*1024))
  # This is for gpt/grub. Set aside the EFI partition so we can 
  # make this usb stick for EFI if needed.
  mkfs_opts = _ext4_version_to_mkfs_opts(ext4_version)

  if efi_boot:
    pplan = [PartPlan(0, None,         None,         0,        2, Partition.MBR,   None,         None),
             # For desktop and Windows, etc., the EFI partition is 512MiB but for USB stick,
             # it's only for installation. 32MiB is plenty big.
             PartPlan(1, EFI_NAME,     'fat32',      0,       32, Partition.UEFI,  EFI_PART_OPT, None),
             PartPlan(2, partition_id, 'ext4',       0,        0, Partition.EXT4,  None,         mkfs_opts) ]
  else:
    pplan = [PartPlan(0, None,         None,         0,        2, Partition.MBR,   None,  None),
             PartPlan(1, partition_id, 'ext4',       0,        0, Partition.EXT4, 'boot', mkfs_opts) ]
    pass
  partion_start = 0
  for part in pplan:
    part.start = partion_start
    if part.size == 0:
      diskmbsize = diskmbsize - 1
      part.size = diskmbsize
      pass
    partion_start = partion_start + part.size
    diskmbsize = diskmbsize - part.size
    pass
  return pplan