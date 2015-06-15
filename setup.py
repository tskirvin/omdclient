from distutils.core import setup

import os
import glob

pyfiles = glob.glob(os.path.join('*', '*.py'))
pyfiles = [pyfile[:-3] for pyfile in pyfiles]

setup (
  name             = 'omdclient',
  version          = '1.0.0',
  description      = 'omdclient check_mk + WATO/OMD interface',
  maintainer       = 'Tim Skirvin',
  maintainer_email = 'tskirvin@fnal.gov',
  package_dir      = { 'omdclient': 'omdclient' },
  url              = 'http://cms-git.fnal.gov/omdclient',
  py_modules       = pyfiles,
)
