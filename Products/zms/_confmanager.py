################################################################################
# _confmanager.py
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

# Imports.
from __future__ import absolute_import
from io import StringIO
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from App.Common import package_home
from DateTime.DateTime import DateTime
from OFS.Image import Image
from OFS.Folder import Folder
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.PageTemplates import ZopePageTemplate
from Products.PythonScripts import PythonScript
import OFS.misc_
import importlib
import operator
import os
import six.moves
import tempfile
import time
import xml.dom.minidom
import zExceptions
from zope.interface import implementer, providedBy
# Product imports.
from Products.zms import standard
from .IZMSConfigurationProvider import IZMSConfigurationProvider
from Products.zms import ZMSFilterManager, IZMSMetamodelProvider, IZMSFormatProvider, IZMSCatalogAdapter, ZMSZCatalogAdapter, IZMSRepositoryManager
from Products.zms import _exportable
from Products.zms import _fileutil
from Products.zms import _mediadb
from Products.zms import _multilangmanager
from Products.zms import _sequence
from Products.zms import standard
from Products.zms import zopeutil
from Products.zms import zmslog


UNINHERITED_PROPERTIES = ['ASP','Portal']

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Read system-configuration from $ZMS_HOME/etc/zms.conf
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class ConfDict(object):

    __confdict__ = None

    @classmethod
    def get(cls):
        if cls.__confdict__ is None:
            cls.__confdict__ = {'last_modified':int(DateTime().timeTime())}
            PRODUCT_HOME = os.path.dirname(os.path.abspath(__file__))
            for home in [PRODUCT_HOME, standard.getINSTANCE_HOME()]:
              fp = os.path.join(home, 'etc', 'zms.conf')
              if os.path.exists(fp):
                cfp = six.moves.configparser.ConfigParser()
                cfp.readfp(open(fp))
                for section in cfp.sections():
                    for option in cfp.options(section):
                        cls.__confdict__[section+'.'+option] = cfp.get( section, option)
        return cls.__confdict__

    @classmethod
    def forName(cls, name):
      d = name.rfind(".")
      modulname = name[:d]
      clazzname = name[d+1:len(name)]
      mod = importlib.import_module('Products.zms.'+modulname)
      clazz = getattr(mod, clazzname)
      return clazz


"""
################################################################################
###
###   Initialization
###
################################################################################
"""

# ------------------------------------------------------------------------------
#  _confmanager.initConf:
# ------------------------------------------------------------------------------
def initConf(self, profile, remote=True):
  standard.writeBlock( self, '[initConf]: profile='+profile)
  createIfNotExists = True
  files = self.getConfFiles(remote)
  for filename in files:
    label = files[filename]
    if label.startswith(profile + '.') or label.startswith(profile + '-'):
      standard.writeBlock( self, '[initConf]: filename='+filename)
      if filename.find('.zip') > 0:
        self.importConfPackage(filename, createIfNotExists)
      elif filename.find('.xml') > 0:
        self.importConf(filename, createIfNotExists=createIfNotExists)


# ------------------------------------------------------------------------------
#  _confmanager.updateConf:
# ------------------------------------------------------------------------------
def updateConf(self):
  createIfNotExists = False
  for filename in self.getConfFiles():
    try:
      self.importConf(filename)
    except:
      pass


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
@implementer(
    IZMSMetamodelProvider.IZMSMetamodelProvider,
    IZMSFormatProvider.IZMSFormatProvider)
class ConfManager(
    _multilangmanager.MultiLanguageManager,
    ):

    # Create a SecurityInfo for this class. We will use this
    # in the rest of our class definition to make security
    # assertions.
    security = ClassSecurityInfo()

    # Management Interface.
    # ---------------------
    manage_customize = PageTemplateFile('zpt/ZMS/manage_customize', globals())
    manage_customizeInstalledProducts = PageTemplateFile('zpt/ZMS/manage_customizeinstalledproducts', globals())
    manage_customizeLanguagesForm = PageTemplateFile('zpt/ZMS/manage_customizelanguagesform', globals())
    manage_customizeDesignForm = PageTemplateFile('zpt/ZMS/manage_customizedesignform', globals())


    # --------------------------------------------------------------------------
    #  ConfManager.importConfPackage:
    # --------------------------------------------------------------------------
    def importConfPackage(self, file, createIfNotExists=0):
      
      if isinstance(file, str):
        if file.startswith('http://') or file.startswith('https://'):
          file = StringIO( self.http_import(file))
        else:
          file = open(_fileutil.getOSPath(file), 'rb')
      files = _fileutil.getZipArchive( file)
      for f in files:
        if not f.get('isdir'):
          self.importConf(f, createIfNotExists=createIfNotExists)


    # --------------------------------------------------------------------------
    #  ConfManager.getConfXmlFile:
    # --------------------------------------------------------------------------
    def getConfXmlFile(self, file):
      if isinstance(file, dict):
        filename = file['filename']
        xmlfile = StringIO( file['data'])
      elif isinstance(file, str) and (file.startswith('http://') or file.startswith('https://')):
        filename = _fileutil.extractFilename(file)
        xmlfile = StringIO( self.http_import(file))
      else:
        filename = _fileutil.extractFilename(file)
        xmlfile = open(_fileutil.getOSPath(file), 'rb')
      return filename, xmlfile


    # --------------------------------------------------------------------------
    #  ConfManager.importConf:
    # --------------------------------------------------------------------------
    def importConf(self, file, createIfNotExists=0, syncIfNecessary=True):
      message = ''
      syncNecessary = False
      filename, xmlfile = self.getConfXmlFile( file)
      if not filename.startswith('._'): # ignore hidden files in ZIP created by MacOSX
        if filename.find('.charfmt.') > 0:
          self.format_manager.importCharformatXml(xmlfile, createIfNotExists)
        elif filename.find('.filter.') > 0:
          self.getFilterManager().importXml(xmlfile, createIfNotExists)
        elif filename.find('.metadict.') > 0:
          self.getMetaobjManager().importMetadictXml(xmlfile, createIfNotExists)
          syncNecessary = True
        elif filename.find('.metaobj.') > 0:
          self.getMetaobjManager().importMetaobjXml(xmlfile, createIfNotExists)
          syncNecessary = True
        elif filename.find('.workflow.') > 0:
          self.getWorkflowManager().importXml(xmlfile, createIfNotExists)
        elif filename.find('.metacmd.') > 0:
          self.getMetacmdManager().importXml(xmlfile, createIfNotExists)
        elif filename.find('.langdict.') > 0:
          _multilangmanager.importXml(self, xmlfile, createIfNotExists)
        elif filename.find('.textfmt.') > 0:
          self.format_manager.importTextformatXml(xmlfile, createIfNotExists)
        xmlfile.close()
      if syncIfNecessary and syncNecessary:
        self.synchronizeObjAttrs()
      return message


    # --------------------------------------------------------------------------
    #  ZMSTextformatManager.getPluginIds:
    # --------------------------------------------------------------------------
    def getPluginIds(self, path=[]):
      ids = []
      filepath = os.sep.join([package_home(globals()), 'plugins']+path)
      for filename in os.listdir(filepath):
        path = os.sep.join([filepath, filename])
        if os.path.isdir(path) and len(os.listdir(path)) > 0:
          ids.append(filename)
      return ids


    # --------------------------------------------------------------------------
    #  Returns configuration-files from $ZMS_HOME/import-Folder
    # --------------------------------------------------------------------------
    security.declareProtected('ZMS Administrator', 'getConfFiles')
    def getConfFiles(self, remote=True, pattern=None, REQUEST=None, RESPONSE=None):
      """
      ConfManager.getConfFiles
      """
      filenames = {}
      filepaths = [
        standard.getINSTANCE_HOME()+'/etc/zms/import/',
        package_home(globals())+'/import/',]
      for filepath in filepaths:
        filename = os.path.join(filepath, 'configure.zcml')
        if os.path.exists(filename):
          standard.writeBlock( self, "[getConfFiles]: Read from "+filename)
          xmldoc = xml.dom.minidom.parse(filename)
          for source in xmldoc.getElementsByTagName('source'):
            location = source.attributes['location'].value
            if location.startswith('http://') or location.startswith('https://'):
              if remote:
                remote_location = location+'configure.zcml'
                try:
                  remote_xml = standard.http_import(self, remote_location)
                  remote_xmldoc = xml.dom.minidom.parseString(remote_xml)
                  for remote_file in remote_xmldoc.getElementsByTagName('file'):
                    filename = remote_file.attributes['id'].value
                    if filename not in filenames:
                      filenames[location+filename] = filename+' ('+remote_file.attributes['title'].value+')'
                except:
                  standard.writeError(self, "[getConfFiles]: can't get conf-files from remote URL=%s"%remote_location)
            else:
              for filepath in filepaths:
                if os.path.exists( filepath):
                  for filename in os.listdir(filepath + location):
                    path = filepath + filename
                    if os.path.isfile(path):
                      if path not in filenames:
                        filenames[path] = filename
          break
      # Filter.
      if pattern is not None:
        lk = list(filenames)
        for k in lk:
          if k.find(pattern) < 0:
            del filenames[k]
          else:
            v = filenames[k]
            i = v.find(' ')
            if i < 0:
              i = len(v)
            v = v[:v.find(pattern)]+v[i:]
            filenames[k] = v
      # Return.
      if REQUEST is not None and \
         RESPONSE is not None:
        RESPONSE = REQUEST.RESPONSE
        content_type = 'text/xml; charset=utf-8'
        filename = 'getConfFiles.xml'
        RESPONSE.setHeader('Content-Type', content_type)
        RESPONSE.setHeader('Content-Disposition', 'inline;filename="%s"'%filename)
        RESPONSE.setHeader('Cache-Control', 'no-cache')
        RESPONSE.setHeader('Pragma', 'no-cache')
        return self.getXmlHeader() + self.toXmlString( filenames)
      else:
        return filenames


    """
    ############################################################################
    ###
    ###   Configuration-Properties Getters
    ###
    ############################################################################
    """

    # --------------------------------------------------------------------------
    #  ConfManager.getSequence:
    #
    #  Returns sequence.
    # --------------------------------------------------------------------------
    def getSequence(self):
      id = 'acl_sequence'
      exists = id in self.objectIds(['Sequence'])
      portalMaster = self.getPortalMaster()
      if portalMaster is not None:
        startvalue = 0
        if exists:
          ob = getattr(self, id)
          startvalue = ob.value
          self.manage_delObjects(ids=[id])
        ob = portalMaster.getSequence()
        if ob.value < startvalue:
          ob.value = startvalue
      else:
        if not exists:
          sequence = _sequence.Sequence()
          self._setObject(sequence.id, sequence)
        ob = getattr(self, id)
      return ob

    # --------------------------------------------------------------------------
    #  ConfManager.getMediaDb:
    #
    #  Returns mediadb.
    # --------------------------------------------------------------------------
    def getMediaDb(self):
      for ob in self.getDocumentElement().objectValues(['MediaDb']):
        return ob
      return None


    # --------------------------------------------------------------------------
    #  ConfManager.getThemes:
    #
    #  Returns list of theme-folders.
    # --------------------------------------------------------------------------
    def getThemes(self):
      obs = []
      for ob in self.getHome().objectValues():
        if isinstance(ob, Folder) and 'standard_html' in ob.objectIds():
          obs.append(ob)
      return obs


    # --------------------------------------------------------------------------
    #  ConfManager.getResourceFolders:
    #
    #  Returns list of resource-folders.
    # --------------------------------------------------------------------------
    def getResourceFolders(self):
      obs = []
      ids = self.getConfProperty('ZMS.resourceFolders', 'instance,common').split(',')
      home = self.getHome()
      if len(self.getConfProperty('ZMS.theme', '')) > 0:
        home = getattr(home, self.getConfProperty('ZMS.theme', ''))
      if '*' in ids:
        ids.extend([x.id for x in home.objectValues(['Folder', 'Filesystem Directory View']) if x.id not in ids])
      for id in ids:
        if id == '*':
          obs.append(home)
        else:
          container = getattr( home, id, None)
          if container is not None and len(container.objectValues(['ZMS']))==0:
            obs.append(container)
      return obs


    # --------------------------------------------------------------------------
    #  ConfManager.getStylesheet:
    #
    #  Returns stylesheet.
    # --------------------------------------------------------------------------
    def getStylesheet(self, id=None):
      stylesheets = self.getStylesheets()
      if id is None:
        return stylesheets[0]
      else:
        for css in stylesheets:
          if css.getId() == id:
            return css

    # --------------------------------------------------------------------------
    #  ConfManager.getStylesheets:
    #
    #  Returns list of stylesheets.
    # --------------------------------------------------------------------------
    def getStylesheets(self):
      ids = []
      obs = []
      for container in self.getResourceFolders():
        for folder in [ getattr( container, 'css', None), container]:
          if folder is not None:
            for ob in folder.objectValues(['DTML Method', 'DTML Document', 'File', 'Filesystem File','Filesystem DTML Method']):
              id = ob.getId()
              path = ob.getPhysicalPath()
              if len([x for x in path if x.endswith('css')]) > 0 and id not in ids:
                ids.append( id)
                if id == self.getConfProperty('ZMS.stylesheet', 'style.css'):
                  obs.insert( 0, ob)
                else:
                  obs.append( ob)
      return obs


    """
    ############################################################################
    ###
    ###   Configuration-Tab Options
    ###
    ############################################################################
    """

    # --------------------------------------------------------------------------
    #  ConfManager.customize_manage_options:
    # --------------------------------------------------------------------------
    customize_manage_options__roles__ = None
    def customize_manage_options(self):
      l = []
      l.append({'label':'<i class="%s"></i>'%self.zmi_icon(),'action':'manage_main'})
      l.append({'label':'TAB_USERS','action':'manage_users'})
      l.append({'label':'TAB_SYSTEM','action':'manage_customize'})
      l.append({'label':'TAB_LANGUAGES','action':'manage_customizeLanguagesForm'})
      for ob in self.objectValues():
        if IZMSConfigurationProvider in list(providedBy(ob)):
          for d in ob.manage_sub_options():
            l.append(self.operator_setitem(d.copy(), 'action', ob.id+'/'+d['action']))
      l.append({'label':'TAB_DESIGN','action':'manage_customizeDesignForm'})
      p = self.REQUEST['URL'].split('/')[-1].startswith('manage')
      if p:
        l = [x for x in l if self.restrictedTraverse(x['action'], None) is not None]
      return l


    ############################################################################
    ###
    ###   Configuration-Properties
    ###
    ############################################################################

    """
    Returns configuration-manager.
    """
    def getConfManager(self):
      return self

    """
    Returns conf-properties.
    """
    def get_conf_properties(self):
      return getattr( self, '__attr_conf_dict__', {})


    """
    Returns defaults for configuration-properties.
    @rtype: C{dict}
    """
    def getConfPropertiesDefaults(self):
      return [
        {'key':'ZMS.conf.path','title':'ZMS conf-path','desc':'ZMS conf-path','datatype':'string','default':'$INSTANCE_HOME/var/$HOME_ID'}, 
        {'key':'ZMS.debug','title':'ZMS debug','desc':'ZMS debug','datatype':'boolean','default':0}, 
        {'key':'ZMSAdministrator.email','title':'Admin e-Mail','desc':'Administrators e-mail address.','datatype':'string'},
        {'key':'ASP.protocol','title':'ASP Protocol','desc':'ASP Protocol.','datatype':'string','options':['http', 'https'],'default':'http'},
        {'key':'ASP.ip_or_domain','title':'ASP IP/Domain','desc':'ASP IP/Domain.','datatype':'string'},
        {'key':'HTTP.proxy','title':'HTTP proxy','desc':'HTTP proxy (host:port).','datatype':'string'},
        {'key':'jquery.version','title':'JQuery version','desc':'JQuery version.','datatype':'string'},
        {'key':'jquery.ui','title':'JQuery UI version','desc':'JQuery UI version.','datatype':'string'},
        {'key':'jquery.plugin.version','title':'JQuery plugin version','desc':'JQuery plugin version','datatype':'string'},
        {'key':'jquery.plugin.extensions','title':'JQuery plugin extensions','desc':'JQuery plugin extensions','datatype':'string'},
        {'key':'ZMS.blobfields.grant_public_access','title':'Grant public access to blob-fields','desc':'Blob-fields in restricted nodes are not visible. You may grant public access to blob-fields by activating this option.','datatype':'boolean'},
        {'key':'ZMS.blobfields.accept_ranges','title':'Http-Header Accept-Ranges for blob-fields','desc':'Http-Header Accept-Ranges for blob-fields.','datatype':'string','default':'bytes'},
        {'key':'ZMS.locale.amount.unit','title':'Currency unit for amount-types','desc':'The currency unit used for amount-types.','datatype':'string','default':'EUR'},
        {'key':'ZMS.password.regexp','title':'Password Regular Expression','desc':'Regular Expression for validation of new passwords.','datatype':'string','default':''},
        {'key':'ZMS.password.hint','title':'Password Hint','desc':'Hint for validation of new passwords.','datatype':'string','default':''},
        {'key':'ZMS.pathhandler','title':'Declarative URLs','desc':'ZMS can use declarative URLs based on DC.Identifier.Url.Node (or DC.Title.Alt).','datatype':'boolean'},
        {'key':'EmailMandatory','title':'Email Mandatory?','desc':'Email for users','datatype':'boolean','default':0}, 
        {'key':'ZMS.pathhandler.id_quote.mapping','title':'Declarative IDs-Mapping','desc':'ZMS can map characters in DC.Title.Alt to declarative IDs.','datatype':'string','default':' _-_/_'},
        {'key':'ZMS.preview.contentEditable','title':'Content-Editable Preview','desc':'Make content in ZMS preview editable','datatype':'boolean','default':1},
        {'key':'ZMS.pathcropping','title':'Crop URLs','desc':'ZMS can crop the SERVER_NAME from URLs.','datatype':'boolean'},
        {'key':'ZMS.manage_tabs_message','title':'Global Message','desc':'ZMS can display a global message for all users in the management interface.','datatype':'text'},
        {'key':'ZMS.http_accept_language','title':'Http Accept Language','desc':'ZMS can use the HTTP_ACCEPT_LANGUAGE request-parameter to determine initial language.','datatype':'boolean'},
        {'key':'ZMS.export.domains','title':'Export resources from external domains','desc':'ZMS can export resources from external domains in the HTML export.','datatype':'string'},
        {'key':'ZMS.export.pathhandler','title':'Export XHTML with decl. Document Ids','desc':'Please activate this option, if you would like to generate declarative document URLs for static XHTML-Export: /documentname/index_eng.html will be transformed to /documentname.html','datatype':'boolean'},
        {'key':'ZMS.export.xml.tidy','title':'Export with HTML Tidy Library','desc':'ZMS can use the HTML Tidy Library to process inline (X)HTML in the XML export to avoid CDATA-sections.','datatype':'boolean'},
        {'key':'ZMS.localfs_read','title':'LocalFS read','desc':'List of directories with permission for LocalFS read (semicolon separated).','datatype':'string','default':''},
        {'key':'ZMS.localfs_write','title':'LocalFS write','desc':'List of directories with permission for LocalFS write (semicolon separated).','datatype':'string','default':''},
        {'key':'ZMS.logout.href','title':'Logout URL','desc':'URL for logout from ZMS.','datatype':'string','default':''},
        {'key':'ZMS.richtext.plugin','title':'Richtext plugin','desc':'Select your preferred richtext plugin','datatype':'string','options':self.getPluginIds(['rte']),'default':'ckeditor'},
        {'key':'ZMS.input.file.plugin','title':'File.upload input','desc':'ZMS can use custom input-fields for file-upload.','datatype':'string','options':['input_file', 'jquery_upload'],'default':'input_file'},
        {'key':'ZMS.input.file.maxlength','title':'File.upload maxlength','desc':'ZMS can limit the maximum upload-file size to the given value (in Bytes).','datatype':'string'},
        {'key':'ZMS.input.image.maxlength','title':'Image.upload maxlength','desc':'ZMS can limit the maximum upload-image size to the given value (in Bytes).','datatype':'string'},
        {'key':'ZMSGraphic.superres','title':'Image superres-attribute','desc':'Super-resolution attribute for ZMS standard image-objects.','datatype':'boolean','default':0},
        {'key':'ZCatalog.TextIndexType','title':'Search with TextIndex-type','desc':'Use specified TextIndex-type (default: ZCTextIndex)','datatype':'string','default':'ZCTextIndex'},
        {'key':'ZMSIndexZCatalog.onImportObjEvt','title':'Resync ZMSIndex on content import','desc':'Please be aware that activating implicit ZMSIndex-resync on content import can block bigger sites for a while','datatype':'boolean','default':0},
      ]
    
    """
    Returns property from configuration.
    @rtype: C{dict}
    """
    def getConfProperties(self, prefix=None, inherited=False, REQUEST=None):
      """ ConfManager.getConfProperties """
      d = self.get_conf_properties()
      if REQUEST is not None:
        import base64
        prefix = standard.pystr(base64.b64decode(prefix),'utf-8')
        r = {}
        for x in d:
          if x.startswith(prefix+'.'):
            r[k] = d[k]
        return self.str_json(r)
      if inherited:
        d = list(d)
        portalMaster = self.getPortalMaster()
        if portalMaster is not None:
          l = portalMaster.getConfProperties(prefix,inherited,REQUEST)
          l = [x for x in l if x not in d and x[:x.find('.')] not in UNINHERITED_PROPERTIES]
          d.extend(l)
      return d


    """
    Removes property from configuration.
    
    @param key: The key.
    @type key: C{string}
    @return None
    """
    security.declareProtected('ZMS Administrator', 'delConfProperty')
    def delConfProperty(self, key):
      self.setConfProperty(key, None)


    """
    Returns property from request (used to get zope-request-properties,
    e.g. SERVER_URL oder AUTHENTICATED_USER).
    
    @param key: The key.
    @type key: C{string}
    @param default: The default-value.
    @type default: C{any}
    @rtype: C{any}
    """
    def getReqProperty(self, key, default=None, REQUEST=None):
      """ ConfManager.getReqProperty """
      authorized = REQUEST['AUTHENTICATED_USER'].has_role('Authenticated')
      if not authorized:
        raise zExceptions.Unauthorized
      return REQUEST.get(key, default)


    """
    Returns property from configuration.
    
    @param key: The key.
    @type key: C{string}
    @param default: The default-value.
    @type default: C{any}
    @var REQUEST: the triggering request
    @type REQUEST: ZPublisher.HTTPRequest
    @rtype: C{any}
    """
    def get_conf_property(self, *args, **kwargs):
      params = ('key', 'default', 'REQUEST')
      [operator.setitem(kwargs, params[x], args[x]) for x in range(len(args))]
      key = kwargs['key']
      default = kwargs.get('default')
      REQUEST = kwargs.get('REQUEST')
      if REQUEST is not None:
        import base64
        try:
          #Py3
          key = standard.pystr(base64.b64decode(key),'utf-8')
        except:
          #Py2
          key = base64.b64decode(key)
      if key in OFS.misc_.misc_.zms['confdict']:
        default = OFS.misc_.misc_.zms['confdict'].get(key)
      value = default
      confdict = self.getConfProperties()
      if key in confdict:
        value = confdict.get(key)
      elif key is not None and not key[:key.find('.')] in UNINHERITED_PROPERTIES and not key in ['UniBE.Alias', 'UniBE.Server']:
        portalMaster = self.getPortalMaster()
        if portalMaster is not None:
          value = portalMaster.getConfProperty( key)
        if value is None:
          if 'default' in kwargs:
            value = default
          else:
            for default in [x for x in self.getConfPropertiesDefaults() if x['key'] == key]:
              value = default.get('default', None)
      return value 

    def getConfProperty(self, key, default=None, REQUEST=None):
      """ ConfManager.getConfProperty """
      return self.get_conf_property(key, default, REQUEST)


    """
    Sets property into configuration.
    
    @param key: The key.
    @type key: C{string}
    @param value: The value.
    @type value: C{any}
    @return None
    """
    security.declareProtected('ZMS Administrator', 'setConfProperty')
    def setConfProperty(self, key, value):
      if key.startswith("Portal"):
        self.clearReqBuff()
      d = self.getConfProperties()
      if value is None:
        if key in d:
          del d[key]
      else:
        d[key] = value
      self.__attr_conf_dict__ = d
      self.__attr_conf_dict__ = self.__attr_conf_dict__.copy()


    """
    ############################################################################
    ###
    ###   Configuration-System
    ###
    ############################################################################
    """

    ############################################################################
    #  Customize system properties.
    ############################################################################
    def manage_customizeSystem(self, btn, key, lang, REQUEST, RESPONSE=None):
      """ ConfManager.manage_customizeSystem """
      
      message = ''
      params = []
      
      ##### Import ####
      if key == 'Import':
        if btn == 'Import':
          f = REQUEST['file']
          createIfNotExists = 1
          if f:
            filename = f.filename
            self.importConfPackage( f, createIfNotExists)
          else:
            filename = REQUEST['init']
            self.importConfPackage( filename, createIfNotExists)
          message = self.getZMILangStr('MSG_IMPORTED')%('<i>%s</i>'%filename)
      
      ##### History ####
      elif key == 'History':
        old_active = self.getConfProperty('ZMS.Version.active', 0)
        new_active = REQUEST.get('active', 0)
        old_nodes = self.getConfProperty('ZMS.Version.nodes', ['{$}'])
        new_nodes = standard.string_list(REQUEST.get('nodes', ''))
        self.setConfProperty('ZMS.Version.active', new_active)
        self.setConfProperty('ZMS.Version.nodes', new_nodes)
        nodes = []
        if old_active == 1 and new_active == 0:
          nodes = old_nodes
        if old_active == 1 and new_active == 1:
          nodes = standard.difference_list( old_nodes, self.getConfProperty('ZMS.Version.nodes', ['{$}']))
        for node in nodes:
          ob = self.getLinkObj( node)
          if ob is not None:
            message += '[%s: %i]'%(node, ob.packHistory())
        message = self.getZMILangStr('MSG_CHANGED')+message
      
      ##### Clients ####
      elif key == 'Clients':
        if btn == 'Change':
          home = self.getHome()
          s = REQUEST.get('portal_master', '').strip()
          if s != home.id:
            self.setConfProperty('Portal.Master', s)
          l = []
          portal_clients = REQUEST.get('portal_clients', [])
          if not isinstance(portal_clients, list):
            portal_clients  = [portal_clients]
          portal_clients = sorted([(int(x[:x.find(':')]), x[x.find(':')+1:]) for x in portal_clients])
          portal_clients = [x[1] for x in portal_clients]
          for id in portal_clients:
            folder = getattr(home, id, None)
            if folder is not None:
              for node in folder.objectValues('ZMS'):
                node.setConfProperty('Portal.Master', home.id)
                l.append(id)
          self.setConfProperty('Portal.Clients', l)
          message = self.getZMILangStr('MSG_CHANGED')
      
      ##### MediaDb ####
      elif key == 'MediaDb':
        if btn == 'Create':
          location = REQUEST['mediadb_location'].strip()
          _mediadb.manage_addMediaDb(self, location)
          message = self.getZMILangStr('MSG_CHANGED')
        elif btn == 'Pack':
          message = _mediadb.manage_packMediaDb(self)
        elif btn == 'Remove':
          message = _mediadb.manage_delMediaDb(self)
      
      ##### Custom ####
      elif key == 'Custom':
        k = REQUEST.get( 'conf_key', '')
        if btn == 'Change':
          v = REQUEST.get( 'conf_value', '')
          if type(v) is str:
            if (v.startswith('{') and not v.startswith('{$') and v.endswith('}')) or (v.startswith('[') and v.endswith(']')):
              try:
                from ast import literal_eval
                v = literal_eval(v)
              except:
                standard.writeError(self,'can\'t eval conf-property %s'%key)
          self.setConfProperty( k, v)
          if REQUEST.get('portal_clients'):
            for portalClient in self.getPortalClients():
              portalClient.setConfProperty( k, v)
          params.append('conf_key')
          message = self.getZMILangStr('MSG_CHANGED')
        elif btn == 'Delete':
          self.delConfProperty( k)
          if REQUEST.get('portal_clients'):
            for portalClient in self.getPortalClients():
              portalClient.delConfProperty( k)
          message = self.getZMILangStr('MSG_DELETED')%int(1)
      
      ##### InstalledProducts ####
      elif key == 'InstalledProducts':
        if btn == 'Change':
          self.setConfProperty('InstalledProducts.lesscss', REQUEST.get('lesscss', ''))
          self.setConfProperty('InstalledProducts.pil.thumbnail.max', REQUEST.get('pil_thumbnail_max', self.getConfProperty('InstalledProducts.pil.thumbnail.max')))
          self.setConfProperty('InstalledProducts.pil.hires.thumbnail.max', REQUEST.get('pil_hires_thumbnail_max', self.getConfProperty('InstalledProducts.pil.hires.thumbnail.max')))
          message = self.getZMILangStr('MSG_CHANGED')
        elif btn == 'Import':
          zmsext = REQUEST.get('zmsext', '')
          # hand over import to Deployment Library if available
          revobj = self.getMetaobjRevision('zms3.deployment')
          revreq = '0.2.0'
          if revobj >= revreq:
            target = 'manage_deployment'
            target = self.url_append_params(target, {'zmsext': zmsext})
            return RESPONSE.redirect(target)
          # otherwise import now
          target = 'manage_customize'
          isProcessed = False
          try:
            ZMSExtension  = standard.extutil()
            filesToImport = ZMSExtension.getFilesToImport(zmsext, self.getDocumentElement())
            if len(filesToImport)>0:
              for f in filesToImport:
                self.importConf(f, createIfNotExists=True, syncIfNecessary=False)
              self.synchronizeObjAttrs()
              isProcessed = True
          except:
            isProcessed = False
          if isProcessed:
            message = self.getZMILangStr('MSG_IMPORTED')%('<code class="alert-success">'+self.str_item(ZMSExtension.getFiles(zmsext))+'</code>')
            target = self.url_append_params(target, {'manage_tabs_message': message})
          else:
            message = self.getZMILangStr('MSG_EXCEPTION') 
            message += ': <code class="alert-danger">%s</code>'%('No conf files found.')
            target = self.url_append_params(target, {'manage_tabs_error_message': message})
            standard.writeError(self, "[ConfManager.manage_customizeSystem] No conf files found.")
          return RESPONSE.redirect(target + '#%s'%key)
        elif btn == 'ImportExample':
          zmsext = REQUEST.get('zmsext', '')
          target = 'manage_main'
          ZMSExtension  = standard.extutil()
          isProcessed = False
          try:
            if ZMSExtension.getExample(zmsext) is not None:
              destination = self.getLinkObj(self.getConfProperty('ZMS.Examples', {}))
              if destination is None:
                destination = self.getDocumentElement()
              ZMSExtension.importExample(zmsext, destination, REQUEST)
              isProcessed = True
          except:
            isProcessed = False
          if isProcessed:
            return True
          else:
            return False
        elif btn == 'InstallTheme':
          zmsext = REQUEST.get('zmsext', '')
          target = 'manage_main'
          ZMSExtension  = standard.extutil()
          standard.writeBlock(self, "[ConfManager.manage_customizeSystem] InstallTheme:"+standard.pystr(zmsext))
          if ZMSExtension.installTheme(self, zmsext):
            return True
          else:
            return False

      ##### Instance ####
      elif key == 'Instance':
        if btn == 'Restart':
          target = 'manage_customize'
          
          if 'ZMANAGED' in os.environ:
            from Lifetime import shutdown
            from cgi import escape
            from .standard import writeBlock
            try:
              user = '"%s"' % REQUEST['AUTHENTICATED_USER']
            except:
              user = 'unknown user'
            writeBlock(self, " Restart requested by %s" % user)
            shutdown(1)
            message = self.getZMILangStr('ZMS3 instance restarted.')
            target = self.url_append_params(target, {'manage_tabs_message': message})
            return """<html>
            <head><meta HTTP-EQUIV=REFRESH CONTENT="10; URL=%s">
            </head>
            <body>Restarting...</body></html>
            """ % escape(target + '#%s'%key, 1)
          else:       
            return "No daemon."
      
      ##### Manager ####
      elif key == 'Manager':
        if btn == 'Add':
          meta_type = REQUEST.get('meta_type', '')
          if meta_type == 'Sequence':
            obj = _sequence.Sequence()
            self._setObject(obj.id, obj)
            message = 'Added '+meta_type
          elif meta_type == 'ZMSLog':
            obj = zmslog.ZMSLog()
            self._setObject(obj.id, obj)
            message = 'Added '+meta_type
          else:
            obj = ConfDict.forName(meta_type+'.'+meta_type)()
            self._setObject(obj.id, obj)
            message = 'Added '+meta_type
        elif btn == 'Remove':
          ids = REQUEST.get('ids', [])
          if ids:
            message = 'Removed '+', '.join(ids)
            self.manage_delObjects(ids=ids)
      
      # Return with message.
      if RESPONSE:
        d = {'lang': lang,'manage_tabs_message': message}
        for param in params:
          d[param] = REQUEST.get( param, '')
        return RESPONSE.redirect( self.url_append_params( 'manage_customize', d) + '#%s'%key)
      
      return message


    ############################################################################
    #  ConfManager.manage_customizeDesign: 
    #
    #  Customize design properties.
    ############################################################################
    def manage_customizeDesign(self, btn, lang, REQUEST, RESPONSE):
      """ ConfManager.manage_customizeDesign """
      message = ''
      home = self.getHome()
      section = REQUEST.get('section','')
      
      # Save css.
      # -----
      if btn == 'BTN_SAVE' and section == 'added':
        added_id = REQUEST.get('id', '')
        fname= '%s.%s'%(added_id.split('.')[-1],added_id.split('.')[-2])
        href = self.getConfProperty(added_id,'%s/%scommon/added/%s'%(self.getHome().id,[self.getConfProperty('ZMS.theme','')+'/',''][len(self.getConfProperty('ZMS.theme',''))==0],fname))
        href = href.replace('$ZMS_HOME',self.getHome().id)
        href = href.replace('$ZMS_THEME/',[self.getConfProperty('ZMS.theme','')+'/',''][len(self.getConfProperty('ZMS.theme',''))==0])
        # Traverse to get object.
        ob = self.getHome()
        for id in href.split('/'):
          ob = getattr(ob,id,None)
          if ob is None:
            break
        # Set object
        if ob is not None:
          ob.manage_edit(title=ob.title, content_type=ob.content_type, filedata=REQUEST[added_id])
        message = self.getZMILangStr('MSG_CHANGED')
      
      # Save theme.
      # -----
      elif btn == 'BTN_SAVE':
        id = REQUEST.get('id', '')
        self.setConfProperty('ZMS.theme', id)
        message = self.getZMILangStr('MSG_CHANGED')
      
      # Delete theme.
      # -------
      elif btn == 'BTN_DELETE':
        ids = REQUEST.get('ids', [])
        home.manage_delObjects(ids)
        message = self.getZMILangStr('MSG_DELETED')%int(len(ids))
      
      # Copy theme.
      # -----
      elif btn == 'BTN_COPY':
        self.metaobj_manager.importTheme(id)
        message = self.getZMILangStr('MSG_IMPORTED')%('<code class="alert-success">'+id+'</code>')
      
      # Import theme.
      # -------
      elif btn == 'BTN_IMPORT':
        file = REQUEST['file']
        filename = _fileutil.extractFilename(file.filename)
        id = filename[:filename.rfind('.')]
        filepath = standard.getINSTANCE_HOME()+'/import/'+filename
        _fileutil.exportObj( file, filepath)
        home.manage_importObject(filename)
        _fileutil.remove( filepath)
        message = self.getZMILangStr('MSG_IMPORTED')%('<code class="alert-success">'+filename+'</code>')
      
      # Insert theme.
      # -------
      elif btn == 'BTN_INSERT':
        newId = REQUEST['newId']
        newTitle = REQUEST['newTitle']
        home.manage_addFolder(id=newId, title=newTitle)
        folder = getattr(home, newId)
        zopeutil.addPageTemplate(folder, id='standard_html', title='', data='<!DOCTYPE html>\n<html tal:define="zmscontext options/zmscontext">\n</html>')
        message = self.getZMILangStr('MSG_INSERTED')%newId
      
      # Return with message.
      message = standard.url_quote(message)
      return RESPONSE.redirect('manage_customizeDesignForm?lang=%s&manage_tabs_message=%s'%(lang, message))


    ############################################################################
    ###
    ###   Interface IZMSWorkflowProvider: delegate to workflow_manager
    ###
    ############################################################################

    def getWfActivities(self):
      workflow_manager = getattr(self, 'workflow_manager', None)
      if workflow_manager is None:
        return []
      return workflow_manager.getActivities()

    def getWfActivitiesIds(self):
      workflow_manager = getattr(self, 'workflow_manager', None)
      if workflow_manager is None:
        return []
      return workflow_manager.getActivityIds()

    def getWfActivity(self, id):
      workflow_manager = getattr(self, 'workflow_manager', None)
      if workflow_manager is None:
        return None
      return workflow_manager.getActivity(id)

    def getWfTransitions(self):
      workflow_manager = getattr(self, 'workflow_manager', None)
      if workflow_manager is None:
        return []
      return workflow_manager.getTransitions()

    def getWfTransition(self, id):
      workflow_manager = getattr(self, 'workflow_manager', None)
      if workflow_manager is None:
        return None
      return workflow_manager.getTransition(id)


    ############################################################################
    ###
    ###   Interface IZMSFilterManager: delegate
    ###
    ############################################################################

    def getFilterManager(self):
      ### updateVersion
      filters = self.getConfProperty('ZMS.filter.filters', {})
      processes = self.getConfProperty('ZMS.filter.processes', {})
      if filters or processes:
        meta_type = 'ZMSFilterManager'
        try:
          obj = ConfDict.forName(meta_type+'.'+meta_type)(filters,processes)
          self._setObject( obj.id, obj)
          self.delConfProperty('ZMS.filter.filters')
          self.delConfProperty('ZMS.filter.processes')
        except:
          standard.writeError(self, "[getFilterManager]: can't init new %s"%meta_type)
      ###
      manager = [x for x in self.getDocumentElement().objectValues() if isinstance(x,ZMSFilterManager.ZMSFilterManager)]
      if len(manager)==0:
        class DefaultManager(object):
          getFilter__roles__ = None
          def getFilter(self, id): return {}
          getFilterIds__roles__ = None
          def getFilterIds(self, sort=True): return []
          getFilterProcesses__roles__ = None
          def getFilterProcesses(self, id): return []
          getProcess__roles__ = None
          def getProcess(self, id): return {}
          getProcessIds__roles__ = None
          def getProcessIds(self, sort=True): return []
          importXml__roles__ = None
          def importXml(self, xml, createIfNotExists=True): pass
        manager = [DefaultManager()]
      return manager[0]


    ############################################################################
    ###
    ###   Interface IZMSMetamodelProvider: delegate
    ###
    ############################################################################

    def getMetaobjManager(self):
      manager = getattr(self, 'metaobj_manager', None)
      if manager is None:
        class DefaultMetaobjManager(object):
          def importXml(self, xml): pass
          def getMetaobjId(self, name): return None
          def getMetaobjIds(self, sort=None, excl_ids=[]): return []
          def getMetaobj(self, id): return None
          def getMetaobjAttrIds(self, meta_id, types=[]): return []
          def getMetaobjAttrs(self, meta_id,  types=[]): return []
          def getMetaobjAttr(self, id, attr_id): return None
          def getMetaobjAttrIdentifierId(self, meta_id): return None
          def notifyMetaobjAttrAboutValue(self, meta_id, key, value): return None
        manager = DefaultMetaobjManager()
      return manager

    def getMetaobjRevision(self, id):
      return self.getMetaobjManager().getMetaobjRevision( id)
    
    def getMetaobjId(self, name):
      return self.getMetaobjManager().getMetaobjId( name)

    def getMetaobjIds(self, sort=None, excl_ids=[]):
      return self.getMetaobjManager().getMetaobjIds( sort, excl_ids)

    def getMetaobj(self, id):
      return self.getMetaobjManager().getMetaobj( id)

    def getMetaobjAttrIds(self, meta_id, types=[]):
      return self.getMetaobjManager().getMetaobjAttrIds( meta_id, types)

    def getMetaobjAttrs(self, meta_id,  types=[]):
      return self.getMetaobjManager().getMetaobjAttrs( meta_id, types)

    def getMetaobjAttr(self, id, attr_id, sync=True):
      return self.getMetaobjManager().getMetaobjAttr( id, attr_id, sync)

    def getMetaobjAttrIdentifierId(self, meta_id):
      return self.getMetaobjManager().getMetaobjAttrIdentifierId( meta_id)

    def notifyMetaobjAttrAboutValue(self, meta_id, key, value):
      return self.getMetaobjManager().notifyMetaobjAttrAboutValue( meta_id, key, value)


    ############################################################################
    ###
    ###   Interface IZMSMetacmdProvider: delegate
    ###
    ############################################################################

    def getMetacmdManager(self):
      ### updateVersion
      commands = self.getConfProperty('ZMS.custom.commands', [])
      if len(commands)>0:
        meta_type = 'ZMSMetacmdProvider'
        obj = ConfDict.forName(meta_type+'.'+meta_type)(commands)
        self._setObject( obj.id, obj)
        self.delConfProperty('ZMS.custom.commands')
      ###
      metacmd_manager = getattr(self, 'metacmd_manager', None)
      if metacmd_manager is None:
        class DefaultManager(object):
          def importXml(self, xml): pass
          def getMetaCmdDescription(self, id): return None
          def getMetaCmd(self, id): return None
          def getMetaCmdIds(self, sort=True): return []
          def getMetaCmds(self, context=None, stereotype='', sort=True): return []
        metacmd_manager = DefaultManager()
      return metacmd_manager

    def getMetaCmdDescription(self, id):
       """ getMetaCmdDescription """
       return self.getMetacmdManager().getMetaCmdDescription(id)

    def getMetaCmd(self, id):
       return self.getMetacmdManager().getMetaCmd(id)

    def getMetaCmdIds(self, sort=1):
       return self.getMetacmdManager().getMetaCmdIds(sort)

    def getMetaCmds(self, context=None, stereotype='', sort=True):
      return self.getMetacmdManager().getMetaCmds(context, stereotype, sort)


    ############################################################################
    ###
    ###   Interface IZMSRepositoryManager: delegate
    ###
    ############################################################################

    def getRepositoryManager(self):
      manager = [x for x in self.getDocumentElement().objectValues() if IZMSRepositoryManager.IZMSRepositoryManager in list(providedBy(x))]
      if len(manager)==0:
        class DefaultManager(object):
          def exec_auto_commit(self, provider, id): return True
          def exec_auto_update(self): return True
        manager = [DefaultManager()]
      return manager[0]


    ############################################################################
    ###
    ###   Interface IZMSWorkflowProvider: delegate
    ###
    ############################################################################

    def getWorkflowManager(self):
      manager = [x for x in self.getDocumentElement().objectValues() if x.getId() == 'workflow_manager']
      if len(manager) == 0:
        class DefaultManager(object):
          def importXml(self, xml): pass
          def getAutocommit(self): return True
          def getActivities(self): return []
          def getActivityIds(self): return []
          def getActivity(self, id): return None
          def getActivityDetails(self, id): return None
          def getTransitions(self): return []
          def getTransitionIds(self): return []
        manager = [DefaultManager()]
      return manager[0]


    ############################################################################
    ###
    ###   Interface IZMSFormatProvider: delegate
    ###
    ############################################################################

    def getFormatManager(self):
      return self.format_manager

    def getTextFormatDefault(self):
      return self.getFormatManager().getTextFormatDefault()

    def getTextFormat(self, id, REQUEST):
      return self.getFormatManager().getTextFormat(id, REQUEST)

    def getTextFormats(self, REQUEST):
      return self.getFormatManager().getTextFormats(REQUEST)

    def getCharFormats(self):
      return self.getFormatManager().getCharFormats()


    ############################################################################
    ###
    ###   Interface IZMSCatalogAdapter: delegate
    ###
    ############################################################################

    def getCatalogAdapter(self):
      for ob in self.objectValues():
        if IZMSCatalogAdapter.IZMSCatalogAdapter in list(providedBy(ob)):
          return ob
      adapter = ZMSZCatalogAdapter.ZMSZCatalogAdapter()
      self._setObject( adapter.id, adapter)
      adapter = getattr(self, adapter.id)
      adapter.setIds(['ZMSFolder', 'ZMSDocument', 'ZMSFile'])
      adapter.setAttrIds(['title', 'titlealt', 'attr_dc_description', 'standard_html'])
      # FIXME ImportError: No module named 'ZMSZCatalogConnector'
      #adapter.addConnector('ZMSZCatalogConnector')
      return adapter


    ############################################################################
    ###
    ###   Interface IZMSLocale: delegate
    ###
    ############################################################################

    def getLocale(self):
      return self

    """
    def get_manage_langs(self):
      return self.getLocale().get_manage_langs()

    def get_manage_lang(self):
      return self.getLocale().get_manage_lang()

    def getZMILangStr(self, key, REQUEST=None, RESPONSE=None):
      return self.getLocale().getZMILangStr( key)

    def getLangStr(self, key, lang=None):
      return self.getLocale().getLangStr( key, lang)

    def getPrimaryLanguage(self):
      return self.getLocale().getPrimaryLanguage()
    """


# call this to initialize framework classes, which
# does the right thing with the security assertions.
InitializeClass(ConfManager)

__REGISTRY__ = None
def getRegistry():
    global __REGISTRY__
    if __REGISTRY__ is None:
        print("__REGISTRY__['confdict']",__REGISTRY__)
        __REGISTRY__ = {}
        try:
          __REGISTRY__['confdict'] = ConfDict.get()
        except:
          import sys, traceback, string
          type, val, tb = sys.exc_info()
          sys.stderr.write(string.join(traceback.format_exception(type, val, tb), ''))
    return __REGISTRY__
getRegistry()

################################################################################