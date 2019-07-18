#!/usr/bin/python3
#
# This is for Triage USB stick on mini system
#
# This sets up the USB stick after installing mini.iso
#

import os, sys, subprocess

os.environ['WCE_TRIAGE_DISK'] = 'true'
os.environ['GRUB_DISABLE_OS_PROBER'] = 'true'
os.environ['TRIAGEUSER'] = 'triage'
os.environ['TRIAGEPASS'] = 'triage'
os.environ['PATCHES'] = 'triage'

if __name__ == "__main__":
  
  steps = ['install_packages',
           # Create triage account
           'config_triage_user',
           # Install Google Chrome
           'install_chrome',
           # Install triage software and services
           'install_assets',
           'install_wce_triage',
           'install_wce_kiosk',
           'install_live_triage',
           # patch up system and boot loader installation
           'patch_system',
           'install_boot'
  ]
  
  # Install Ubunto packages (some are python packages)
  for step in steps:
    package_name = 'wce_triage.setup.' + step
    subprocess.run(['sudo', '-H', 'python3', '-m', package_name])
    pass
  pass

