# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

## [1.4.1] - 2019-08-19

### Changed

* ran all python through flake8 python linter, cleaned it up to match

## [1.4.0] - 2019-08-16

### Changed

* `omdclient/__init__.py` - added some docs re: `tag_role` and
  `tag_instance` in the documentation (in short, we use them locally to
  tie together puppet + OMD, but they're not very interesting otherwise).
* converted everything to Python 3

### Removed

* dropping rpms for RHEL 6

## [1.3.5] - 2019-03-19

### Added

* CHANGELOG.md - standardizing on a single changelog file

### Changed

* Makefile.local - now includes Pypi (pip) bindings
* setup.py, omdclient.spec - re-worked for setuptools instead of distutils.core
* README.md - lots of updates on the path towards real distribution

### Removed

* TODO.md - currently empty
