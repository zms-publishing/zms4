"""
The ZMS environment consists of an application server based on pegged versions 
of depending packages (see requirements.txt).

  Use
    $ cd path/to/zms/checkout
    $ pip install -r https://raw.githubusercontent.com/zopefoundation/Zope/master/requirements-full.txt
    $ pip install -r requirements.txt
    $ pip install -e .
  to install the environment fetching the latest development snapshots from SVN/GIT-Repositories
  (currently unstable)

@see http://gpiot.com/blog/creating-a-python-package-and-publish-it-to-pypi/
@see https://caremad.io/2013/07/setup-vs-requirement/
"""
import os
import sys
from setuptools import setup

setup_path = os.path.dirname(__file__)
for path in sys.path:
  if path.endswith('site-packages'):
    site_packages = path

def read_version():
    # Remove text from version for PyPI
    raw_version = open(os.path.join(setup_path, 'Products', 'zms', 'version.txt')).read()
    cleaned_version = raw_version.replace('ZMS4-', '').replace('.REV', '')
    version_list = cleaned_version.strip().split('.')
    # Remove revision too
    if 4 == len(version_list):
        version_list.pop()
    return '.'.join(version_list)

CLASSIFIERS = [
  'Development Status :: 4 - Beta',
  'Framework :: Zope :: 4',
  'Programming Language :: Python :: 3',
  'Operating System :: OS Independent',
  'Environment :: Web Environment',
  'Topic :: Internet :: WWW/HTTP :: Site Management',
  'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
  'Intended Audience :: Education',
  'Intended Audience :: Science/Research',
  'Intended Audience :: Customer Service',
  'Intended Audience :: End Users/Desktop',
  'Intended Audience :: Healthcare Industry',
  'Intended Audience :: Information Technology',
  'Intended Audience :: Telecommunications Industry',
  'Intended Audience :: Financial and Insurance Industry',
  'License :: OSI Approved :: GNU General Public License (GPL)',
]

setup(
  name                  = 'ZMS',
  description           = 'ZMS: Simplified Content Modelling',
  long_description      = open(os.path.join(setup_path, 'README')).read(),
  version               = read_version(),
  author                = 'HOFFMANN+LIEBENBERG in association with SNTL Publishing, Berlin',
  author_email          = 'zms@sntl-publishing.com',
  url                   = 'http://www.zms-publishing.com',
  download_url          = 'https://zmslabs.org',
  install_requires      = open(os.path.join(setup_path, 'requirements.txt')).readlines(),
  namespace_packages    = ['Products'],
  packages              = ['Products.zms'],
  classifiers           = CLASSIFIERS,
  include_package_data  = True,
  zip_safe              = False,
)
