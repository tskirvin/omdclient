from distutils.core import setup

import os
import glob

pyfiles = glob.glob(os.path.join('*', '*.py'))
pyfiles = [pyfile[:-3] for pyfile in pyfiles]

scripts = glob.glob(os.path.join('usr/bin/*'))
man     = glob.glob(os.path.join('man/man1/*'))
# manpages are built earlier

setup (
  name             = 'omdclient',
  version          = '1.3.3-1',
  description      = 'omdclient check_mk + WATO/OMD interface',
  maintainer       = 'Tim Skirvin',
  maintainer_email = 'tskirvin@fnal.gov',
  package_dir      = { 'omdclient': 'omdclient' },
  data_files       = [ ( 'share/man/man1', man ) ],
  scripts          = scripts,
  url              = 'https://github.com/tskirvin/omdclient',
  py_modules       = pyfiles,
)

