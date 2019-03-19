from setuptools import setup
import glob, re, os

## get documentation from README.md
with open("README.md", "r") as fh:
    long_description = fh.read()

## get version from spec file
with open('omdclient.spec', 'r') as fh:
    for line in fh:
        m = re.search("^Version:\s+(.*)\s*$", line)
        if m:
            version=m.group(1)
            break

## get list of files to install
pyfiles = glob.glob(os.path.join('*', '*.py'))
pyfiles = [pyfile[:-3] for pyfile in pyfiles]

scripts = glob.glob(os.path.join('usr/bin/*'))
man     = glob.glob(os.path.join('man/man1/*'))

setup (
  name             = 'omdclient',
  version          = version,
  description      = 'omdclient check_mk + WATO/OMD interface',
  long_description = long_description,
  long_description_content_type = 'text/markdown',
  author           = 'Tim Skirvin',
  author_email     = 'tskirvin@fnal.gov',
  url              = 'https://github.com/tskirvin/omdclient/',
  license          = 'Perl Artistic',
  maintainer       = 'Tim Skirvin',
  maintainer_email = 'tskirvin@fnal.gov',
  package_dir      = { 'omdclient': 'omdclient' },
  data_files       = [ ( 'share/man/man1', man ) ],
  scripts          = scripts,
  py_modules       = pyfiles,
  keywords         = ['check_mk', 'omd', 'nagios', 'api', 'wato']
)

# add classifiers, platforms
