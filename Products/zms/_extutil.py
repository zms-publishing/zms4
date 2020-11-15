# -*- coding: utf-8 -*-
################################################################################
# _extutil.py
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
################################################################################

from pkg_resources import WorkingSet, Requirement, ResourceManager

EXTENSIONS = {
  'zms3.behave': ['0.1.0',
                    'Manage tests based on feature/scenario/step descriptions using Behavior-driven development (BDD) practices',
                    'https://github.com/zms-publishing/zms3.behave',
                    'developed by Christian Meier'],
  'zms3.formulator': ['3.4.11',
                    'Submit JSON-based HTML-Forms into a SQL-Storage with protection by reCAPTCHA',
                    'https://github.com/zms-publishing/zms3.formulator',
                    'developed by SNTL Publishing'],
  'zms3.mindmap': ['0.1.5',
                    'Manage and browse mind maps',
                    'https://github.com/zms-publishing/zms3.mindmap',
                    'developed by Christian Meier'],
  'zms3.deployment': ['0.2.5',
                    'Handle continuous delivery by automation of deployment and installation tasks',
                    'https://pypi.python.org/pypi/zms3.deployment',
                    'developed by SNTL Publishing'],
  'zms3.themes': ['0.2.1',
                    'Additional Themes based on Start Bootstrap',
                    'https://bitbucket.org/zms3/themes',
                    'developed by SNTL Publishing'],
  'zms3.photodb': ['0.2.1',
                    'Handle EXIF/XMP/IPTC metadata',
                    'https://github.com/zms-publishing/zms3.photodb',
                    'developed by Christian Meier'],
  'zms3.qrcode': ['0.1.1',
                    'Generate Quick Response Codes (QR codes)',
                    'https://github.com/zms-publishing/zms3.qrcode',
                    'developed by Christian Meier'],
  'Pillow': ['6.1.0',
                    'The friendly PIL (Python Imaging Library) fork',
                    'https://pypi.python.org/pypi/Pillow',
                    'developed by Alex Clark'],
  'python-ldap': ['3.2.0',
                    'Object-oriented API to access LDAP servers',
                    'https://pypi.python.org/pypi/python-ldap',
                    'developed by python-ldap.org'],
  'MySQL-python': ['1.2.5',
                    'Python Interface to MySQL',
                    'https://pypi.python.org/pypi/MySQL-python',
                    'developed by Andy Dustman'],
  'SQLAlchemy': ['1.3.8',
                    'Python SQL Toolkit and Object Relational Mapper',
                    'https://pypi.python.org/pypi/SQLAlchemy',
                    'developed by Mike Bayer'],
  'Products.ZCatalog': ['5.0.1',
                    'Built in search engine of Zope',
                    'https://pypi.python.org/pypi/Products.ZCatalog',
                    'developed by Zope Foundation and Contributors'],
  'Products.ZMySQLDA': ['4.4.0',
                    'MySQL Database Adapter',
                    'https://pypi.python.org/pypi/Products.ZMySQLDA',
                    'developed by John Eikenberry'],
  'Products.ZSQLiteDA': ['0.6.1',
                    'SQLite Database Adapter',
                    'https://pypi.python.org/pypi/Products.ZSQLiteDA',
                    'developed by Hajime Nakagami'],
  'Products.ZSQLMethods': ['3.0.8',
                    'SQL Method Support',
                    'https://pypi.python.org/pypi/Products.ZSQLMethods',
                    'developed by Zope Foundation and Contributors'],
  'Products.CMFCore': ['2.4.0',
                    'File System Directory Views',
                    'https://pypi.python.org/pypi/Products.CMFCore',
                    'developed by Zope Foundation and Contributors'],
  'Products.PluggableAuthService': ['2.1.0',
                    'Pluggable authentication / authorization framework',
                    'https://pypi.python.org/pypi/Products.PluggableAuthService',
                    'developed by Zope Foundation and Contributors'],
  'lesscpy': ['0.13.0',
                    'Python LESS Compiler',
                    'https://pypi.python.org/pypi/lesscpy',
                    'developed by Jóhann T Maríusson'],
  'behave': ['1.2.6',
                    'Library to write tests in a Domain Specific Language (DSL) automated by Python code',
                    'https://pypi.python.org/pypi/behave',
                    'developed by Benno Rice, Richard Jones and Jens Engel'],
  'mock': ['3.0.5',
                    'Library for testing in Python to replace parts of the system under test with mock objects and make assertions',
                    'https://pypi.python.org/pypi/mock',
                    'developed by Testing Cabal'],
  'beautifulsoup4': ['4.5.1',
                    'Library to provide Pythonic idioms for iterating, searching, and modifying an HTML/XML parse tree',
                    'https://pypi.python.org/pypi/beautifulsoup4',
                    'developed by Leonard Richardson'],
  'ftfy': ['4.8.0',
                    'Library for fixing Unicode that is broken in various ways',
                    'https://pypi.python.org/pypi/ftfy',
                    'developed by Rob Speer'],
  'PyQRCode': ['1.2.1',
                    'A QR code generator written purely in Python with SVG, EPS, PNG and terminal output',
                    'https://pypi.python.org/pypi/PyQRCode',
                    'developed by Michael Nooner'],
  'Zope2': ['4.0.0',
                    'Open-source web application server',
                    'https://github.com/zopefoundation/Zope',
                    'developed by Zope Foundation and Contributors'],
  'ZODB': ['5.5.1',
                    'Set of tools for using the Zope Object Database',
                    'https://github.com/zopefoundation/ZODB',
                    'developed by Zope Foundation and Contributors'],
  'ZopeUndo': ['4.3.0',
                    'Support the undo log (Prefix object) in a ZEO server, without pulling in all of Zope',
                    'https://github.com/zopefoundation/ZopeUndo',
                    'developed by Zope Foundation and Contributors'],
  'zope.publisher': ['5.1.1',
                    'Map requests from HTTP/WebDAV/FTP clients, web browsers and XML-RPC onto Python objects',
                    'https://github.com/zopefoundation/zope.publisher',
                    'developed by Zope Foundation and Contributors'],
  'zope.pagetemplate': ['4.4.1',
                    'Templating mechanism that achieves a clean separation of presentation and application logic',
                    'https://github.com/zopefoundation/zope.pagetemplate',
                    'developed by Zope Foundation and Contributors'],
  'zope.sendmail': ['5.0.0',
                    'Send mails using transaction mechanism and queuing',
                    'https://github.com/zopefoundation/zope.sendmail',
                    'developed by Zope Foundation and Contributors']
}

class ZMSExtensions(object):
  """
    Utility to handle zms3.extensions
  
    Management interface is at ZMS > Configuration > System > Installed Libraries
    @see zpt/ZMS/manage_customize.zpt
    @see _confmanager.py
  """
  getAll__roles__ = None
  getAllExtensions__roles__ = None
  getAllThemes__roles__ = None
  getAllProducts__roles__ = None
  getAllOthers__roles__ = None
  getAllProjspecs__roles__ = None
  getAllFramework__roles__ = None
  isEnabled__roles__ = None  
  isThemeInstalled__roles__ = None
  installTheme__roles__ = None
  getHint__roles__ = None  
  getInfo__roles__ = None  
  getVersionAvailable__roles__ = None  
  getVersionInstalled__roles__ = None  
  getFiles__roles__ = None  
  getFilesToImport__roles__ = None
  getExample__roles__ = None  
  getExampleToImport__roles__ = None
  importExample__roles__ = None
  getUrl__roles__ = None
  getUrlPackage__roles__ = None

  def __init__(self):
    self.pkg = {}
    self.pkg_names = []
    self.pkg_available = []
    self.pkg_hints = []
    self.pkg_infos = []
    self.pkg_ready = []
    self.pkg_confs = []
    self.pkg_installed = []
    self.pkg_urls = []
        
    for name, info in sorted(EXTENSIONS.iteritems()):
      self.pkg_names.append(name)
      self.pkg_available.append(info[0])
      self.pkg_hints.append(info[1])
      self.pkg_infos.append(info[3])
      self.pkg_urls.append(info[2])
      package = str(WorkingSet().find(Requirement.parse(name))).split()
      if ((name in package) and (len(package) == 2)):
        # TODO: **Normalize Versions** acc. to `PEP 440`: http://legacy.python.org/dev/peps/pep-0440/
        # The version specified requires normalization, consider using '3.2.0.dev3' instead of '3.2.0dev3' etc. + 
        # pip v6.0.6 does not append svn revision specified in `setup.cfg` as v1.5.6 before
        # => `zms.zms_version()` have to be adjusted too...
        self.pkg_installed.append(package[1].replace('.dev', 'dev').replace('dev0', 'dev'))
        self.pkg_ready.append(True)
        try:
          confres = ResourceManager().resource_listdir(name, 'conf')
        except:
          confres = None
        if confres:
          confxml = [ob for ob in confres if ob.endswith('.xml') or ob.endswith('.zip')]
          if len(confxml) > 0:
            self.pkg_confs.append(confxml)
          else:
            self.pkg_confs.append(None)
        else:
          self.pkg_confs.append(None)
      else:
        self.pkg_installed.append(None)
        self.pkg_confs.append(None)
        self.pkg_ready.append(False)

    
  def getAll(self):
    """
      Return all defined extensions
    """
    return self.pkg_names

  def getAllExtensions(self, prj=None):
    """
      Return all zms3.* extensions
    """
    pkg = [x for x in self.pkg_names if x.startswith('zms3.')]
    if prj is not None:
      pkg = [x for x in pkg if x not in self.getAllProjspecs(prj)]
    return pkg

  def getAllThemes(self, prj=None):
    """
      Return all themes identified by an entry in configure.zcml representing a subfolder of /skins
    """
    pkg = []
    try:
      import Products.CMFCore.DirectoryView
      for directory in Products.CMFCore.DirectoryView.manage_listAvailableDirectories():
        if 'Products.zms:skins' in directory or 'zms3.themes:skins' in directory:
          d = directory.split('/', 1)[1]
          if '/' not in d:
            pkg.append(d)
    except:
      pass
    if prj is not None:
      pkg = [x for x in pkg if x not in self.getAllProjspecs(prj)]    
    return pkg

  def isThemeInstalled(self, context, ext=None):
    """
      Return TRUE if given theme is available as Filesystem Directory View in root folder of ZMS
      otherwise FALSE
    """
    if ext in [x.getId() for x in context.getHome().objectValues('Filesystem Directory View')]:
      return True
    else:
      return False

  def installTheme(self, context, ext=None):
    """
      Create Filesystem Directory View of given theme in root folder of ZMS
    """
    try:
      import Products.CMFCore.DirectoryView
      for directory in Products.CMFCore.DirectoryView.manage_listAvailableDirectories():
        if 'Products.zms:skins' in directory or 'zms3.themes:skins' in directory:
          d = directory.split('/', 1)[1]
          if '/' not in d:
            if ext in directory:
              Products.CMFCore.DirectoryView.manage_addDirectoryView(context.getHome(), directory)
              break
      return True
    except:
      return False    

  def getAllProducts(self):
    """
      Return all Products.* extensions
    """
    pkg = [x for x in self.pkg_names if x.startswith('Products.')]
    return pkg
  
  def getAllOthers(self):
    """
      Return all other extensions
    """
    pkg = [x for x in self.pkg_names if not x.startswith('zms3.') and not x.startswith('Products.') and x not in self.getAllFramework()]
    return pkg

  def getAllProjspecs(self, prj=None):
    """
      Return all project specific extensions (define parameter ZMS.Project at ZMS > System > Miscelleanous)
    """
    if prj is not None:
      pkg = [x for x in self.pkg_names if x.startswith('zms3.%s' % prj.lower())]
      return pkg
    return []

  def getAllFramework(self):
    """
      Return all framework specific packages
    """
    pkg = [x for x in self.pkg_names if x.startswith('Zope') or x.startswith('ZODB') or x.find('zope') >= 0]
    return pkg

  def isEnabled(self, ext=None):
    """
      Return TRUE if given extension is available as python package in environment
      otherwise FALSE
    """
    if ext in self.pkg_names:
      return self.pkg_ready[self.pkg_names.index(ext)]
    else:
      return False
  
  def getHint(self, ext=None):
    """
      Return short description of given extension
    """
    if ext in self.pkg_names:
      return self.pkg_hints[self.pkg_names.index(ext)]
    else:
      return None

  def getInfo(self, ext=None):
    """
      Return info about given extension to display as hover-link-title
    """
    if ext in self.pkg_names:
      return self.pkg_infos[self.pkg_names.index(ext)]
    else:
      return None

  def getVersionAvailable(self, ext=None):
    """
      Return python package version of given extension configured above
    """
    if ext in self.pkg_names:
      return self.pkg_available[self.pkg_names.index(ext)]
    else:
      return None
  
  def getVersionInstalled(self, ext=None):
    """
      Return python package version of given extension installed in environment
    """
    if ext in self.pkg_names:
      return self.pkg_installed[self.pkg_names.index(ext)]
    else:
      return None

  def getFiles(self, ext=None):
    """
      Return configuration files found at $LIBS/zms3/{ext}/conf/*.xml
    """
    if ext in self.pkg_names:
      files = self.pkg_confs[self.pkg_names.index(ext)]
      files = [filename for filename in files if not filename.endswith('.example.xml') and not filename.endswith('.example.zip')]
      return files
    else:
      return None
      
  def getFilesToImport(self, ext=None, context=None):
    """
      Return list of configuration files of given extension with full pathnames
    """
    if ext in self.pkg_names:
      files = self.pkg_confs[self.pkg_names.index(ext)]
      if files:
        filenames = []
        for f in files:
          filename = ResourceManager().resource_filename(ext, 'conf/' + f)
          filenames.append(filename)
          # if ZMSActions are included but no Provider available - create it
          if context is not None:
            if ('.metacmd.' in f) \
              and ( 'ZMSMetacmdProvider' not in [ x.meta_type for x in context.objectValues() ] ) \
              and ( 'ZMSMetacmdProviderAcquired' not in [ x.meta_type for x in context.objectValues() ] ):
              context.REQUEST.set('meta_type', 'ZMSMetacmdProvider')
              context.manage_customizeSystem('Add', 'Manager', context.REQUEST['lang'], context.REQUEST)
        return filenames
    return []
  
  def getExample(self, ext=None):
    """
      Return an available *.example.xml or *.example.zip file of given extension
    """
    if ext in self.pkg_names:
      files = self.pkg_confs[self.pkg_names.index(ext)]
      if files:
        for filename in files:
          if filename.endswith('.example.xml') or filename.endswith('.example.zip'):
            return filename
    return None
  
  def getExampleToImport(self, ext=None):
    """
      Return an available example file of given extension with full pathname
    """
    example = self.getExample(ext)
    if example is not None:
      files = self.getFilesToImport(ext)
      for filename in files:
        if filename.endswith(example):
          return filename
    return None
  
  def importExample(self, ext=None, context=None, request=None):
    """
      Import example file of given extension at given context
    """
    import _fileutil
    import _importable
    example = self.getExample(ext)
    if example is not None:
      filename = self.getExampleToImport(ext)
      contents = open(_fileutil.getOSPath(filename), 'rb')
      _importable.importFile(context, contents, request, _importable.importContent)
      contents.close()
      
  def getUrl(self, ext=None):
    """
      Return url to package website of given extension if available
    """    
    if ext in self.pkg_names:
      str_url = self.pkg_urls[self.pkg_names.index(ext)]
      if str_url.startswith('https://bitbucket.org'):
        str_url += '/downloads'
      return str_url
    else:
      return None 
  
  def getUrlPackage(self, ext=None, mode='install'):
    """
      Return url to package download of given extension for install/update
    """
    if ext in self.pkg_names:
      str_ins = str_upd = str_url = self.getUrl(ext)
      if str_url.startswith('https://bitbucket.org') and str_url.endswith('/downloads'):
        str_ins = '%s/get/%s.zip'%(str_url[:-10], self.getVersionAvailable(ext))
        str_upd = '%s/get/HEAD.zip'%(str_url[:-10])
      if ext=='zms3.deployment':
        str_ins = str_upd = 'zms3.deployment==0.2.5'
      
      if mode=='install':
        return str_ins
      elif mode=='update':
        return str_upd
      else:
        return 'n/a'
    else:
      return None 
