from distutils.core import setup

import os
import glob

pyfiles = glob.glob(os.path.join('*', '*.py'))
pyfiles = [pyfile[:-3] for pyfile in pyfiles]

scripts = glob.glob(os.path.join('usr/bin/*'))
# still need to build the manpages

setup (
  name             = 'omdclient',
  version          = '1.0.0',
  description      = 'omdclient check_mk + WATO/OMD interface',
  maintainer       = 'Tim Skirvin',
  maintainer_email = 'tskirvin@fnal.gov',
  package_dir      = { 'omdclient': 'omdclient' },
  scripts = scripts,
  url              = 'https://github.com/tskirvin/omdclient',
  py_modules       = pyfiles,
)

