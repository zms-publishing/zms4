################################################################################
# zms.py
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
from App.Common import package_home
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
from sys import *
import collections
import copy
import os
import shutil
import sys
import time
import transaction
import zExceptions
# Product imports.
from Products.zms import standard
from Products.zms import _accessmanager
from Products.zms import _builder
from Products.zms import _confmanager
from Products.zms import _enummanager
from Products.zms import _fileutil
from Products.zms import _importable
from Products.zms import _mediadb
from Products.zms import _objattrs
from Products.zms import _xmllib
from Products.zms import _zcatalogmanager
from Products.zms import _zmsattributecontainer
from Products.zms import ZMSMetacmdProvider, ZMSMetamodelProvider, ZMSFormatProvider, ZMSWorkflowProvider
from Products.zms.zmscustom import ZMSCustom
from Products.zms.zmslinkcontainer import ZMSLinkContainer
from Products.zms.zmslinkelement import ZMSLinkElement
from Products.zms.zmslog import ZMSLog
from Products.zms.zmsobject import ZMSObject
from Products.zms.zmssqldb import ZMSSqlDb
from Products.zms.zmstrashcan import ZMSTrashcan

__all__= ['ZMS']


################################################################################
#
# ZMS Object Index
#
################################################################################

import zope.event
from zope.container.contained import ObjectAddedEvent
from zope.container.contained import ObjectMovedEvent
from zope.container.contained import ObjectRemovedEvent

def subscriber(event):
  if isinstance(event, ObjectAddedEvent):
    if isinstance(event.object, ZMSObject):
      if isinstance(event.newParent, ZMSObject):
        # trigger object-added event
        standard.triggerEvent(event.object, "*.ObjectAdded")
  elif isinstance(event, ObjectMovedEvent):
    if isinstance(event.object, ZMSObject):
      if isinstance(event.newParent, ZMSObject):
        # trigger object-moved event
        standard.triggerEvent(event.object, "*.ObjectMoved")
      elif event.newParent is None:
        standard.triggerEvent(event.object, "*.ObjectRemoved")
  elif isinstance(event, ObjectRemovedEvent):
    if isinstance(event.object, ZMSObject):
        # trigger object-removed event
      standard.triggerEvent(event.object, "*.ObjectRemoved")
zope.event.subscribers.append(subscriber)


################################################################################
#
# Common Function(s)
#
################################################################################

# ------------------------------------------------------------------------------
#  importTheme:
# ------------------------------------------------------------------------------
def importTheme(folder, theme):
  
  filename = _fileutil.extractFilename(theme)
  id = filename[:filename.rfind('.')]
  
  if filename.endswith('.zexp'):
    ### Store copy of ZEXP in INSTANCE_HOME/import-folder.
    filepath = standard.getINSTANCE_HOME() + '/import/' + filename
    if theme.startswith('http://'):
      initutil = standard.initutil()
      initutil.setConfProperty('HTTP.proxy',REQUEST.get('http_proxy',''))
      zexp = standard.http_import( initutil, theme)
      _fileutil.exportObj( zexp, filepath)
    else:
      packagepath = package_home(globals()) + '/import/' + filename
      try:
        os.stat(_fileutil.getOSPath(filepath))
      except OSError:
        shutil.copy( packagepath, filepath)
    
    ### Import theme from ZEXP.
    _fileutil.importZexp( folder, filename)
  
  else:
    id = filename[:filename.find('-')]
    _confmanager.initConf(folder.content, id, remote=False)
  
  return id


# ------------------------------------------------------------------------------
#  initZMS:
# ------------------------------------------------------------------------------
def initZMS(self, id, titlealt, title, lang, manage_lang, REQUEST):

  ### Constructor.
  obj = ZMS()
  obj.id = id
  self._setObject(obj.id, obj)
  obj = getattr(self, obj.id)

  ### Trashcan.
  trashcan = ZMSTrashcan()
  obj._setObject(trashcan.id, trashcan)

  ### Manager.
  manager = ZMSMetamodelProvider.ZMSMetamodelProvider()
  obj._setObject( manager.id, manager)
  manager = ZMSMetacmdProvider.ZMSMetacmdProvider()
  obj._setObject( manager.id, manager)
  manager = ZMSFormatProvider.ZMSFormatProvider()
  obj._setObject( manager.id, manager)

  ### Init languages.
  obj.setLanguage(lang, REQUEST['lang_label'], '', manage_lang)

  ### Log.
  if REQUEST.get('zmslog'):
    zmslog = ZMSLog( copy_to_stdout=True, logged_entries=[ 'ERROR', 'INFO'])
    obj._setObject(zmslog.id, zmslog)

  ### Init Configuration.
  obj.setConfProperty('HTTP.proxy', REQUEST.get('http_proxy', ''))
  obj.setConfProperty('ZMS.autocommit', 1)

  ### Init ZMS object-model.
  _confmanager.initConf(obj, 'com.zms.foundation', remote=False)
  _confmanager.initConf(obj, 'com.zms.foundation.bootstrap', remote=False)
  _confmanager.initConf(obj, 'com.zms.foundation.theme', remote=False)
  _confmanager.initConf(obj, 'com.zms.index', remote=False)

  ### Init default-configuration.
  _confmanager.initConf(obj, 'default', remote=False)

  ### Init Role-Definitions and Permission Settings.
  obj.initRoleDefs()

  ### Init Properties: active, titlealt, title.
  obj.setObjStateNew(REQUEST)
  obj.setObjProperty('active', 1, lang)
  obj.setObjProperty('titlealt', titlealt, lang)
  obj.setObjProperty('title', title, lang)
  obj.onChangeObj(REQUEST, forced=1)
  
  # Init Object-Children
  obj.initObjChildren(REQUEST)
  
  ### Return new ZMS instance.
  return obj


# ------------------------------------------------------------------------------
#  initContent:
# ------------------------------------------------------------------------------
def initContent(self, filename, REQUEST):
  file = open(_fileutil.getOSPath(package_home(globals())+'/import/'+filename), 'rb')
  _importable.importFile( self, file, REQUEST, _importable.importContent)
  file.close()


################################################################################
#
# Constructor
#
################################################################################
manage_addZMSForm = PageTemplateFile('manage_addzmsform', globals())
def manage_addZMS(self, lang, manage_lang, REQUEST, RESPONSE):
  """ manage_addZMS """
  message = ''
  t0 = time.time()

  if REQUEST['btn'] == 'Add':

    ##### Add Home ####
    homeElmnt = Folder(REQUEST['folder_id'])
    self._setObject(homeElmnt.id, homeElmnt)
    homeElmnt = [x for x in self.objectValues() if x.id == homeElmnt.id][0]
    
    ##### Add ZMS ####
    titlealt = 'ZMS home'
    title = 'ZMS - Python-based Content Management System for Science, Technology and Medicine'
    obj = initZMS(homeElmnt, 'content', titlealt, title, lang, manage_lang, REQUEST)
    
    ##### Add Theme ####
    themeId = importTheme(homeElmnt,REQUEST['theme'])
    obj.setConfProperty('ZMS.theme',themeId)

    ##### Default content ####
    if REQUEST.get('initialization', 0)==1:
      initContent(obj, 'content.default.zip', REQUEST)

    ##### Configuration ####

    #-- Search
    initContent(obj, 'com.zms.search.content.xml', REQUEST)

    # Initialize catalogs.
    obj.getCatalogAdapter().reindex_all()

    # Initialize access.
    obj.synchronizePublicAccess()

    # Return with message.
    message = obj.getLangStr('MSG_INSERTED', manage_lang)%obj.meta_type
    message += ' (in '+str(int((time.time()-t0)*100.0)/100.0)+' secs.)'
    RESPONSE.redirect('%s/%s/manage?manage_tabs_message=%s'%(homeElmnt.absolute_url(), obj.id, standard.url_quote(message)))

  else:
    RESPONSE.redirect('%s/manage_main'%self.absolute_url())


def containerFilter(container):
  return container.meta_type == 'Folder'


################################################################################
#
#  Class
#
################################################################################
class ZMS(
        ZMSCustom,
        _accessmanager.AccessManager,
        _builder.Builder,
        _confmanager.ConfManager,
        _objattrs.ObjAttrsManager,
        _zcatalogmanager.ZCatalogManager,
        ):

    # Version-Info.
    # -------------
    zms_build = '134'        # Internal use only, designates object model!
    zms_patch = 'c'          # Internal use only!

    # Properties.
    # -----------
    meta_type = meta_id = 'ZMS'

    # Management Permissions.
    # -----------------------
    __administratorPermissions__ = (
        'manage_customize',
        'manage_customizeInstalledProducts',
        'manage_customizeSystem',
        'manage_changeLanguages', 'manage_customizeLanguagesForm',
        'manage_customizeDesign', 'manage_customizeDesignForm',
        )
    __authorPermissions__ = (
        'manage', 'manage_main', 'manage_main_iframe', 'manage_workspace',
        'manage_addZMSModule',
        'manage_deleteObjs', 'manage_undoObjs',
        'manage_moveObjUp', 'manage_moveObjDown', 'manage_moveObjToPos',
        'manage_cutObjects', 'manage_copyObjects', 'manage_pasteObjs',
        'manage_ajaxDragDrop', 'manage_ajaxZMIActions',
        'manage_properties', 'manage_changeProperties', 'manage_changeTempBlobjProperty',
        'manage_wfTransition', 'manage_wfTransitionFinalize',
        'manage_userForm', 'manage_user',
        'manage_importexport', 'manage_import', 'manage_export',
        'manage_executeMetacmd',
        )
    __userAdministratorPermissions__ = (
        'manage_users', 'manage_users_sitemap', 'manage_userProperties', 'manage_roleProperties', 'userdefined_roles',
        )
    __ac_permissions__=(
        ('ZMS Administrator', __administratorPermissions__),
        ('ZMS Author', __authorPermissions__),
        ('ZMS UserAdministrator', __userAdministratorPermissions__),
        )

    # Globals.
    # --------
    dGlobalAttrs = {
    'ZMS': {
                'obj_class':None},
    'ZMSCustom': {
                'obj_class':ZMSCustom},
    'ZMSLinkContainer': {
                },
    'ZMSLinkElement': {
                'obj_class':ZMSLinkElement},
    'ZMSSqlDb': {
                'obj_class':ZMSSqlDb,
                'constructor':'manage_addzmssqldbform'},
    }

    # Interface.
    # ----------
    index_html = PageTemplateFile('zpt/ZMS/index', globals()) # index_html
    f_index_html = PageTemplateFile('zpt/ZMS/index', globals()) # index_html
    f_headDoctype = PageTemplateFile('zpt/ZMS/f_headdoctype', globals()) # Head.DOCTYPE
    f_headTitle = PageTemplateFile('zpt/ZMS/f_headtitle', globals()) # Head.Title
    f_headMeta_DC = PageTemplateFile('zpt/ZMS/f_headmeta_dc', globals()) # Head.Meta.DC (Dublic-Core))
    f_headMeta_Locale = PageTemplateFile('zpt/ZMS/f_headmeta_locale', globals()) # Head.Locale (Content-Type & Charset)
    f_standard_html_header = PageTemplateFile('zpt/ZMS/f_standard_html_header', globals())
    f_standard_html_footer = PageTemplateFile('zpt/ZMS/f_standard_html_footer', globals())
    headScript = PageTemplateFile('zpt/ZMS/headscript', globals()) # Head.Script
    headMeta = PageTemplateFile('zpt/ZMS/headmeta', globals()) # Head.Meta
    headCStyleSheet = PageTemplateFile('zpt/ZMS/headcstylesheet', globals()) # Head.CStyleSheet
    headCSS = PageTemplateFile('zpt/ZMS/headcstylesheet', globals()) # Head.CSS

    # Enumerations.
    # -------------
    enumManager = _enummanager.EnumManager()


    """
    ############################################################################
    ###
    ###   Constructor
    ###
    ############################################################################
    """

    # --------------------------------------------------------------------------
    #  ZMS.__init__:
    # --------------------------------------------------------------------------
    """
    Constructor.
    """
    def __init__(self):
      self.id = 'content'


    # --------------------------------------------------------------------------
    #  ZMS.initZMS:
    # --------------------------------------------------------------------------
    def initZMS(self, container, id, titlealt, title, lang, manage_lang, REQUEST):
      return initZMS(container, id, titlealt, title, lang, manage_lang, REQUEST)


    # --------------------------------------------------------------------------
    #  ZMS.manage_addMediaDb:
    # --------------------------------------------------------------------------
    def manage_addMediaDb(self, location, REQUEST=None, RESPONSE=None):
      _mediadb.manage_addMediaDb(self, location, REQUEST, RESPONSE)


    # --------------------------------------------------------------------------
    #  ZMS.zms_version:
    #
    #  Get version.
    # --------------------------------------------------------------------------
    def zms_version(self):
      """
      Try to obtain the version from package info if installed by pip
      otherwise read from version.txt and from svnversion
        
        1. installed by pip from PyPI
          (revision 'XXXX' in version.txt - package info of official releases does not contain revision)
        2. installed by pip from ZMSLabs w/ info by svn
          (revision 'svn-rXXXX' in package info due to setup.cfg)
        3. installed by pip from TAR-Ball w/o info by svn
          (revision 'XXXX' in version.txt due to nightly build - 'svn0' in package info due to setup.cfg)
        4. deployed to instance/Products
          (revision 'XXXX' in version.txt, maybe installed but unused package)
        5. checked out to instance/Products as working copy from svn 
          (revision 'REV' in version.txt, maybe installed but unused package)
      """
      from pkg_resources import WorkingSet, Requirement
      zms = WorkingSet().find(Requirement.parse('ZMS3'))
      pth = _fileutil.getOSPath(package_home(globals()))
      
      file = open(_fileutil.getOSPath(pth+'/version.txt'), 'r')
      version_txt = file.read()
      version     = version_txt.strip().split('.')
      file.close()
      
      # return plain version info if it is a deployment specific format like 
      # ZMS3-3.Y.Z.XXXX.prj-ABCD
      if len(version)!=4:
        return version_txt
      
      # obtain revision and return formatted version info
      # ZMS3-3.Y.Z.XXXX
      else:
        revision = version.pop()
        # get revision from pip if running as package
        if (zms is not None) and ('site-packages' in pth):
          version_pip = str(zms.version)
          if ('.svn-r' in version_pip):
            # leave -r in revision to recognize as snapshot below
            revision = version_pip.strip().split('.svn', 1)[1]        
        # get revision from svnversion
        elif (revision == 'REV'):
          import subprocess
          version_svn = subprocess.Popen("svnversion",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, cwd=pth, universal_newlines=True)
          revision = version_svn.communicate()[0].strip()
        # format revision info
        if (revision.startswith('export')):
          revision = ' (unknown build/snapshot)'
        # at moment there are 4-digits for builds 
        elif len(revision)==4:
          revision = ' (build #%s)'%revision
        # otherwise it is a development snapshot
        else:
          revision = ' (snapshot #%s)'%revision.replace('-r', '')
      
      return '.'.join(version)+revision

    # --------------------------------------------------------------------------
    #  ZMS.getDocumentElement
    # --------------------------------------------------------------------------
    """
    The document-element of the site.
    """
    def getDocumentElement(self):
      return self

    # --------------------------------------------------------------------------
    #  ZMS.getRootElement
    # --------------------------------------------------------------------------
    """
    The root element of the site.
    """
    def getRootElement(self):
      return self.breadcrumbs_obj_path()[0]

    # --------------------------------------------------------------------------
    #  ZMS.getAbsoluteHome
    # --------------------------------------------------------------------------
    def getAbsoluteHome(self):
      portalMaster = self.getPortalMaster()
      if portalMaster:
        return portalMaster.getAbsoluteHome()
      return self.getHome()

    """
    Returns the home-folder of the site.
    """
    def getHome(self):
      docElmnt = self.getDocumentElement()
      ob = docElmnt
      try:
        depth = 0
        while ob.meta_type != 'Folder':
          if depth > sys.getrecursionlimit():
            raise zExceptions.InternalError('Maximum recursion depth exceeded')
          depth = depth + 1
          ob = ob.aq_parent
      except:
        try:
          ob = getattr( docElmnt, docElmnt.absolute_url().split( '/')[-2])
        except:
          ob = docElmnt.aq_parent
      return ob

    """
    Returns the trashcan of the site.
    """
    def getTrashcan(self):
      return self.objectValues(['ZMSTrashcan'])[0]

    """
    Returns new (unique) Object-ID.
    """
    def getNewId(self, id_prefix='e'):
      return '%s%i'%(id_prefix, self.getSequence().nextVal())

    """
    Returns Dublin-Core Meta-Attribute Coverage.
    """
    def getDCCoverage(self, REQUEST={}):
      return 'global.'+self.getPrimaryLanguage()



    ############################################################################
    #
    #   ZMS - Portals
    #
    ############################################################################

    """
    Returns portal-master, none if it does not exist.
    """
    def getPortalMaster(self):
      v = self.get_conf_properties().get('Portal.Master', '')
      if len(v) > 0:
        try:
          return getattr( self, v).content
        except:
          standard.writeError(self, '[getPortalMaster]: %s not found!'%str(v))
      return None

    """
    Returns portal-clients, empty list if none exist.
    """
    def getPortalClients(self):
      docElmnts = []
      v = self.get_conf_properties().get('Portal.Clients', [])
      if len(v) > 0:
        thisHome = self.getHome()
        for id in v:
          try:
            docElmnts.append(getattr(thisHome, id).content)
          except:
            standard.writeError(self, '[getPortalClients]: %s not found!'%str(id))
      return docElmnts


    ############################################################################
    ###
    ###   DOM-Methods
    ###
    ############################################################################

    """
    The parent of this node.
    All nodes except root may have a parent.
    """
    def getParentNode(self):
      return None

    ############################################################################
    ###
    ###   XML-Builder
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    # Handler for XML-Builder (_builder.py)
    # --------------------------------------------------------------------------
    def xmlOnStartElement(self, sTagName, dTagAttrs, oParentNode):
      standard.writeLog( self, "[xmlOnStartElement]: sTagName=%s"%sTagName)

      # remove all ZMS-objects.
      ids = self.objectIds(list(self.dGlobalAttrs))
      if ids:
        self.manage_delObjects(ids=ids)

      # initialize stacks.
      self.dTagStack = collections.deque()
      self.dValueStack  = collections.deque()

      # WORKAROUND! The member variable "aq_parent" does not contain the right
      # parent object at this stage of the creation process (it will later on!).
      # Therefore, we introduce a special attribute containing the parent
      # object, which will be used by xmlGetParent() (see below).
      self.oParent = None

################################################################################


# Workaround for an incompatibility with zope.browserresource 3.11.0 and newer
# which requires an ETagAdapter to be provided by the application.
# Sent a patch upstream to lift this requirement, at which point this
# workaround could be removed:
#  https://github.com/zopefoundation/zope.browserresource/pull/1
try:
    from zope.browserresource.interfaces import IFileResource, IETag
    from zope.publisher.interfaces.browser import IBrowserRequest
    from zope.interface import implementer

    from zope.component import adapter, provideAdapter

    @adapter(IFileResource, IBrowserRequest)
    @implementer(IETag)
    class NoETagAdapter(object):

        def __init__(self, context, request):
            pass

        def __call__(self, mtime, content):
            return None

        @classmethod
        def register(cls):
            provideAdapter(cls)

except ImportError:
    # zope.browserresource before 3.11.0
    class NoETagAdapter(object):
        @classmethod
        def register(cls):
            pass
