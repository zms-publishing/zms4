################################################################################
# zmslinkelement.py
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
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
import sys
# Product Imports.
from Products.zms import zmscontainerobject
from Products.zms import zmscustom
from Products.zms import zmsobject
from Products.zms import zmsproxyobject
from Products.zms import standard
from Products.zms import _confmanager
from Products.zms import _xmllib
from Products.zms import _zreferableitem


"""
################################################################################
# class ConstraintViolation(Exception):
#
# General exception class to indicate constraint violations.
################################################################################
"""
class ConstraintViolation(Exception): pass


################################################################################
################################################################################
###
###  Class
###
################################################################################
################################################################################
class ZMSLinkElement(zmscustom.ZMSCustom):

    # Create a SecurityInfo for this class. We will use this
    # in the rest of our class definition to make security
    # assertions.
    security = ClassSecurityInfo()

    # Properties.
    # -----------
    meta_type = meta_id = "ZMSLinkElement"

    # Management Options.
    # -------------------
    def manage_options(self):
      return ( 
        {'label': 'TAB_EDIT',    'action': 'manage_main'},
        {'label': 'TAB_HISTORY', 'action': 'manage_UndoVersionForm'},
        )

    # Management Permissions.
    # -----------------------
    __authorPermissions__ = (
        'manage', 'manage_main', 'manage_main_iframe', 'manage_workspace',
        'manage_changeProperties', 'manage_changeTempBlobjProperty',
        'manage_moveObjUp', 'manage_moveObjDown', 'manage_moveObjToPos',
        'manage_cutObjects', 'manage_copyObjects', 'manage_pasteObjs',
        'manage_ajaxDragDrop', 'manage_ajaxZMIActions',
        'manage_userForm', 'manage_user',
        )
    __viewPermissions__ = (
        'manage_ajaxGetChildNodes',
        )
    __ac_permissions__=(
        ('ZMS Author', __authorPermissions__),
        ('View', __viewPermissions__),
        )


    ############################################################################
    #
    #   Constructor
    #
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getSelf:
    # --------------------------------------------------------------------------
    def getSelfPROXY(self, proxy, meta_type=None):
      return zmsobject.ZMSObject.getSelf( proxy, meta_type)

    def getSelf(self, meta_type=None):
      proxy = self.getProxy()
      rtn = self.getSelfPROXY( proxy, meta_type)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getEmbedType: 
    # --------------------------------------------------------------------------
    def getEmbedType(self):
      embed_type = self.getObjAttrValue( self.getObjAttr( 'attr_type'), self.REQUEST)
      if embed_type in [ 'embed', 'recursive', 'remote']:
        ref_obj = self.getRefObj()
        if ref_obj is not None and ref_obj.isAncestor( self):
          embed_type = 'cyclic' # Error!
      return embed_type


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.isEmbedded: 
    # --------------------------------------------------------------------------
    def isEmbedded(self, REQUEST):
      rtn = self.getEmbedType() in [ 'embed', 'recursive', 'remote']
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.isEmbeddedRecursive: 
    # --------------------------------------------------------------------------
    def isEmbeddedRecursive(self, REQUEST):
      rtn = self.getEmbedType() in [ 'recursive']
      return rtn


    ############################################################################
    ###
    ###   Properties
    ###
    ############################################################################

    ############################################################################
    #  ZMSLinkElement.manage_changeProperties: 
    #
    #  Change Linkelement properties.
    ############################################################################
    def manage_changeProperties(self, lang, REQUEST, RESPONSE): 
      """ ZMSLinkElement.manage_changeProperties """

      target_ob = self.getParentNode()
      if REQUEST.get('menulock',0) == 1:
        # Remain in Current Menu
        target_ob = self
      target = REQUEST.get( 'manage_target', '%s/manage_main'%target_ob.absolute_url())
      message = ''
      if REQUEST.get('btn', '') not in  [ 'BTN_CANCEL', 'BTN_BACK']:
        try:
          
          ##### Object State ####
          self.setObjStateModified(REQUEST)
          
          ##### Properties ####
          for key in self.getObjAttrs():
            obj_attr = self.getObjAttr(key)
            if obj_attr['xml']:
              self.setReqProperty(key, REQUEST)
          
          ##### VersionManager ####
          self.onChangeObj(REQUEST)
          
          ##### Success Message ####
          message = self.getZMILangStr('MSG_CHANGED')
        
        ##### Failure Message ####
        except ConstraintViolation:
          target = REQUEST.get( 'manage_target', '%s/manage_main'%self.absolute_url())
          message = "[ConstraintViolation]: " + standard.pystr( sys.exc_info()[1])
      
      # Return with message.
      target = self.url_append_params( target, { 'lang': lang, 'manage_tabs_message': message})
      target = '%s#zmi_item_%s'%( target, self.id)
      return RESPONSE.redirect( target)


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getRef:
    # --------------------------------------------------------------------------
    def getRef(self):
      coverage = self.getDCCoverage()
      req = {'preview':'preview','lang':coverage[coverage.find('.')+1:]}
      ref = self.getObjAttrValue( self.getObjAttr( 'attr_ref'), req) 
      return ref


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getRefObj:
    # --------------------------------------------------------------------------
    def getRefObj(self):
      ref_obj = self.getLinkObj(self.getRef())
      if ref_obj == self:
        ref_obj = None
      if ref_obj is not None and ref_obj.meta_type == 'ZMSLinkElement':
        ref_obj = ref_obj.getRefObj()
      return ref_obj


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getRemoteObj:
    # --------------------------------------------------------------------------
    def getRemoteObj(self):
      value = None
      ref = self.getRef()
      try:
        value = self.http_import( ref + '/ajaxGetNode?lang=%s'%lang)
        value = _xmllib.xmlParse( value)
      except:
        standard.writeError(self, '[getRemoteObj]: can\'t embed from remote: ref=%s'%ref)
      return value


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.isMetaType:
    # --------------------------------------------------------------------------
    def isMetaTypePROXY(self, proxy, meta_type, REQUEST={'preview':'preview'}):
      if proxy != self and proxy is not None and self.isEmbeddedRecursive( self.REQUEST):
        b = proxy.isMetaType( meta_type, REQUEST)
      else:
        b = False
        if not (self.NOREF == meta_type or (isinstance(meta_type, list) and self.NOREF in meta_type)):
          b = b or zmsobject.ZMSObject.isMetaType(self, meta_type, REQUEST)
          ref_obj = self.getRefObj()
          if ref_obj is not None and self.isEmbedded(REQUEST):
            if not (self.NORESOLVEREF == meta_type or (isinstance(meta_type, list) and self.NORESOLVEREF in meta_type)):
              b = b or ref_obj.isMetaType(meta_type, REQUEST)
      return b

    def isMetaType(self, meta_type, REQUEST={'preview':'preview'}):
      proxy = self.getProxy()
      rtn = self.isMetaTypePROXY( proxy, meta_type, REQUEST)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getLevel:
    # --------------------------------------------------------------------------
    def getLevelPROXY(self, proxy):
      if proxy != self and proxy is not None and self.isEmbeddedRecursive( self.REQUEST):
        rtn = proxy.getLevel()
      else:
        rtn = self.getParentNode().getLevel() + 1
      return rtn

    def getLevel(self):
      proxy = self.getProxy()
      rtn = self.getLevelPROXY( proxy)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getParentNode:
    # --------------------------------------------------------------------------
    def getParentNodePROXY(self, proxy):
      if proxy != self and proxy is not None and self.isEmbeddedRecursive( self.REQUEST):
        rtn = proxy.getParentNode()
      else:
        rtn = getattr( self, 'aq_parent', getattr( self, 'base', None))
      return rtn

    getParentNode__roles__ = None
    def getParentNode(self):
      """
      The parent of this node. 
      All nodes except root may have a parent.
      """
      proxy = self.getProxy()
      rtn = self.getParentNodePROXY( proxy)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getTitlealt:
    # --------------------------------------------------------------------------
    def getTitlealtPROXY(self, proxy, REQUEST):
      if proxy != self and proxy is not None and self.isEmbeddedRecursive( REQUEST):
        rtn = proxy.getTitlealt( REQUEST)
      else:
        rtn = self.getObjProperty('titlealt', REQUEST)
        if len(rtn) == 0:
          ref_obj = self.getRefObj()
          if ref_obj is None:
            rtn = super(ZMSLinkElement, self).getTitlealt(REQUEST)
          else:
            rtn = ref_obj.getTitlealt(REQUEST)
      return rtn

    def getTitlealt(self, REQUEST):
      rtn = ''
      if self.getEmbedType() == 'remote':
        remote_obj = self.getRemoteObj()
        if isinstance(remote_obj, list):
          for node in _xmllib.xmlNodeSet( remote_obj, 'titlealt'):
            rtn = node['cdata']
      else:
        proxy = self.getProxy()
        rtn = self.getTitlealtPROXY( proxy, REQUEST)
      if len(rtn) == 0:
        rtn = self.display_type(REQUEST)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getTitle:
    # --------------------------------------------------------------------------
    def getTitlePROXY(self, proxy, REQUEST):
      if proxy != self and proxy is not None and self.isEmbeddedRecursive( REQUEST):
        rtn = proxy.getTitle( REQUEST)
      else:
        rtn = self.getObjProperty('title', REQUEST)
        if len(rtn) == 0:
          ref_obj = self.getRefObj()
          if ref_obj is None:
            rtn = super(ZMSLinkElement, self).getTitle(REQUEST)
          else:
            rtn = ref_obj.getTitle(REQUEST)
      return rtn

    def getTitle(self, REQUEST):
      rtn = ''
      if self.getEmbedType() == 'remote':
        remote_obj = self.getRemoteObj()
        if isinstance(remote_obj, list):
          for node in _xmllib.xmlNodeSet( remote_obj, 'title'):
            rtn = node['cdata']
      else:
        proxy = self.getProxy()
        rtn = self.getTitlePROXY( proxy, REQUEST)
      if len(rtn) == 0:
        rtn = self.display_type(REQUEST)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.display_icon:
    # --------------------------------------------------------------------------
    def display_icon(self, REQUEST, meta_type=None, key='icon', zpt=True): 
      context = self
      if self.isEmbedded(REQUEST):
        ref_obj = self.getRefObj()
        if ref_obj is not None:
          context = ref_obj
      return zmsobject.ZMSObject.display_icon(context, REQUEST=REQUEST, meta_type=meta_type, key=key, zpt=zpt)


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.isActive:
    # --------------------------------------------------------------------------
    def isActive(self, REQUEST):
      active = super(ZMSLinkElement, self).isActive(REQUEST) 
      if self.getEmbedType() == 'remote':
        remote_obj = self.getRemoteObj()
        if isinstance(remote_obj, list):
          rtnVal = remote_obj[1]['attrs']['active'] in ['1', 'True']
      else:
        ref_obj = self.getRefObj()
        if ref_obj is not None:
            active = active and ref_obj.isActive(REQUEST)
      return active


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.isPageContainer:
    # --------------------------------------------------------------------------
    def isPageContainer(self):
      return False


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.isPage
    # --------------------------------------------------------------------------
    def isPage(self):
      rtnVal = False
      if self.getEmbedType() == 'remote':
        remote_obj = self.getRemoteObj()
        if isinstance(remote_obj, list):
          rtnVal = remote_obj[1]['attrs']['is_page'] in ['1', 'True']
      else:
        if self.isEmbedded( self.REQUEST):
          ref_obj = self.getRefObj()
          if ref_obj is not None:
            rtnVal = rtnVal or ref_obj.isPage()
      return rtnVal


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.isPageElement
    # --------------------------------------------------------------------------
    def isPageElement(self): 
      rtnVal = False
      if self.getEmbedType() == 'remote':
        remote_obj = self.getRemoteObj()
        if isinstance(remote_obj, list):
          rtnVal = remote_obj[1]['attrs']['is_pageelement'] in ['1', 'True']
      else:
        if self.isEmbedded( self.REQUEST):
          ref_obj = self.getRefObj()
          if ref_obj is not None:
            rtnVal = rtnVal or ref_obj.isPageElement()
          else:
            rtnVal = rtnVal or True
        elif self.getObjProperty('align', self.REQUEST) not in ['', 'NONE']:
          rtnVal = rtnVal or True
      return rtnVal


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getType
    #
    #  Overrides getType of zmscustom.ZMSCustom. 
    # --------------------------------------------------------------------------
    def getTypePROXY(self, proxy): 
      rtn = 'ZMSObject'
      if proxy != self and proxy is not None and self.isEmbeddedRecursive( self.REQUEST):
        rtn = proxy.getType()
      else:
        ref_obj = self.getRefObj()
        if ref_obj is not None:
           rtn = ref_obj.getType()
      return rtn
    
    def getType(self): 
      proxy = self.getProxy()
      rtn = self.getTypePROXY( proxy)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getObjProperty
    #
    #  Overrides getObjProperty of _objattrs.ObjAttrs. 
    # --------------------------------------------------------------------------
    def getObjPropertyPROXY(self, proxy, key, REQUEST={}, default=None):
      obj_attr = proxy.getObjAttr( key)
      value = proxy.getObjAttrValue( obj_attr, REQUEST) 
      return value

    def getObjProperty(self, key, REQUEST={}, default=None):
      value = None
      value = self.getObjPropertyPROXY( self, key, REQUEST, default)
      # First exit...
      if (value is None or value=='' or (value==0 and not isinstance(value, bool))) and \
        key in self.getMetaobjAttrIds( self.meta_id):
        value = zmsobject.ZMSObject.getObjProperty( self, key, REQUEST, default)
      # Second exit...
      if (value is None or value=='' or (value == 0 and not isinstance(value, bool))) and \
          key not in ['active', 'change_uid', 'change_dt', 'work_uid', 'work_dt', 'internal_dict', 'attr_ref', 'attr_dc_coverage']:
        recursive = self.isEmbeddedRecursive( REQUEST)
        if recursive:
          proxy = self.getProxy()
          if proxy != self and proxy is not None:
            value = self.getObjPropertyPROXY( proxy, key, REQUEST, default)
        else:
          ref_obj = self.getRefObj()
          if ref_obj != self and ref_obj is not None:
            value = self.getObjPropertyPROXY( ref_obj, key, REQUEST, default)
          # Last exit...
          if (value is None or len(str(value)) == 0 or (value == 0 and not isinstance(value, bool))):
            value = zmsobject.ZMSObject.getObjProperty( self, key, REQUEST, default)
      return value


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getNavItems:
    #
    #  Overrides getNavItems of zmscontainerobject.ZMSContainerObject.
    # --------------------------------------------------------------------------
    def getNavItemsPROXY(self, proxy, current, REQUEST, opt={}, depth=0):
      rtn = []
      recursive = self.isEmbeddedRecursive( REQUEST)
      if proxy != self and proxy is not None and recursive:
        rtn = proxy.getNavItems( current, REQUEST, opt, depth)
      else:
        ref_obj = self.getRefObj()
        if isinstance(ref_obj, zmscontainerobject.ZMSContainerObject):
          rtn = super(zmslinkelement.ZMSLinkElement, self).getNavItems( current, REQUEST, opt, depth)
      return rtn

    def getNavItems(self, current, REQUEST, opt={}, depth=0):
      proxy = self.getProxy()
      rtn = self.getNavItemsPROXY( proxy, current, REQUEST, opt, depth)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getNavElements:
    #
    #  Overrides getNavElements of zmscontainerobject.ZMSContainerObject.
    # --------------------------------------------------------------------------
    def getNavElementsPROXY(self, proxy, REQUEST, expand_tree=1, current_child=None, subElements=[]):
      rtn = []
      recursive = self.isEmbeddedRecursive( REQUEST)
      if proxy != self and proxy is not None and recursive:
        rtn = proxy.getNavElements( REQUEST, expand_tree, current_child, subElements)
      else:
        ref_obj = self.getRefObj()
        if isinstance(ref_obj, zmscontainerobject.ZMSContainerObject):
          rtn = super(zmslinkelement.ZMSLinkElement, zself).getNavElements( REQUEST, expand_tree, current_child, subElements)
      return rtn

    def getNavElements(self, REQUEST, expand_tree=1, current_child=None, subElements=[]):
      proxy = self.getProxy()
      rtn = self.getNavElementsPROXY( proxy, REQUEST, expand_tree, current_child, subElements)
      return rtn


    ############################################################################
    ###
    ###  HTML-Presentation
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getHref2IndexHtml:
    # --------------------------------------------------------------------------
    def getHref2IndexHtmlPROXY(self, proxy, REQUEST, deep=1): 
      if proxy != self and proxy is not None and self.isEmbeddedRecursive( self.REQUEST):
        rtn = proxy.getHref2IndexHtml( REQUEST, deep)
      else:
        rtn = zmsobject.ZMSObject.getHref2IndexHtml( proxy, REQUEST, deep)
      return rtn
    
    def getHref2IndexHtml(self, REQUEST, deep=1): 
      proxy = self.getProxy()
      rtn = self.getHref2IndexHtmlPROXY( proxy, REQUEST, deep)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement._getBodyContent:
    #
    #  HTML presentation of link-element.
    # --------------------------------------------------------------------------
    def _getBodyContent(self, REQUEST):
      rtn = ''
      if self.getEmbedType() == 'remote':
        ref = self.getObjProperty('attr_ref', REQUEST)
        try:
          rtn += self.http_import( ref+'/ajaxGetBodyContent')
        except:
          rtn += standard.writeError(self, '[_getBodyContent]: can\'t embed from remote: ref=%s'%ref)
      else:
        if self.isEmbedded(REQUEST):
          REQUEST.set('ZMS_RELATIVATE_URL', False)
        proxy = self.getProxy()
        if proxy != self and proxy is not None and self.isEmbeddedRecursive( self.REQUEST):
          rtn += proxy._getBodyContent(REQUEST)
        elif proxy == self and proxy is not None and self.isEmbedded( REQUEST):
          ref_obj = self.getRefObj()
          if ref_obj is None:
            ref = self.getObjProperty('attr_ref', REQUEST)
            ref_obj = self.getLinkObj(ref)
          if ref_obj is not None and ref_obj != self:
            rtn += ref_obj._getBodyContent( REQUEST)
        else:
          rtn = self._getBodyContentContentEditable(self.metaobj_manager.renderTemplate( self))
        if self.isEmbedded(REQUEST):
          REQUEST.set('ZMS_RELATIVATE_URL', True)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.renderShort:
    #
    #  Renders short presentation of link-element.
    # --------------------------------------------------------------------------
    def renderShort(self, REQUEST):
      rtn = ''
      ref_obj = self.getRefObj()
      ref = self.getObjProperty('attr_ref', REQUEST) 
       
      if self.getEmbedType() == 'remote': 
        try: 
          rtn += self.http_import( ref+'/renderShort') 
        except: 
          rtn += standard.writeError(self, '[renderShort]: can\'t embed from remote: ref=%s'%ref) 
       
      elif self.isEmbedded(REQUEST): 
        REQUEST.set('ZMS_RELATIVATE_URL', False)
        if ref_obj is None: 
          ref_obj = self.getLinkObj(ref) 
        if ref_obj is None or ref_obj.isPage(): 
          rtn += super(ZMSLinkElement, self).renderShort(REQUEST) 
        elif ref_obj != self: 
          rtn += ref_obj.renderShort(REQUEST) 
        REQUEST.set('ZMS_RELATIVATE_URL', True)
      else: 
          rtn += self._getBodyContent( REQUEST) 
      return rtn


    ############################################################################
    ###
    ###  DOM-Methods
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSLinkElement.breadcrumbs_obj_path:
    # --------------------------------------------------------------------------
    def breadcrumbs_obj_pathPROXY(self, proxy, portalMaster=True):
      if proxy != self and proxy is not None and self.isEmbeddedRecursive( self.REQUEST):
        rtn = proxy.breadcrumbs_obj_path()
      else:
        rtn = zmsobject.ZMSObject.breadcrumbs_obj_path( proxy, portalMaster)
      return rtn
    
    def breadcrumbs_obj_path(self, portalMaster=True):
      proxy = self.getProxy()
      rtn = self.breadcrumbs_obj_pathPROXY( proxy, portalMaster)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getTreeNodes:
    #
    #  Returns an empty NodeList that contains all children of this subtree in 
    #  correct order. If none, this is a empty NodeList. 
    # --------------------------------------------------------------------------
    def getTreeNodes(self, REQUEST={}, meta_types=None):
      return []


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.initProxy: 
    # --------------------------------------------------------------------------
    def initProxy(self, base, url_base, proxy, recursive=False):
      return zmsproxyobject.ZMSProxyObject( self, base, url_base, proxy.id, proxy, recursive)


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.__proxy__:
    #
    #  Returns self or referenced object (if embedded) as ZMSProxyObject
    # --------------------------------------------------------------------------
    def __proxy__(self):
      rtn = self
      req = self.REQUEST
      if req.get( 'ZMS_PROXY', True):
        if req.get( 'URL', '').find( '/manage') < 0 or req.get( 'ZMS_PATH_HANDLER', False):
          if self.isEmbeddedRecursive( req):
            ref_obj = self.getRefObj()
            if ref_obj is not None:
              recursive = True
              rtn = zmsproxyobject.ZMSProxyObject( self, self.aq_parent, self.absolute_url(), self.id, ref_obj, recursive)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getProxy:
    #
    #  Returns self or proxy-object from Path-Handler (if embedded) as 
    #  ZMSProxyObject.
    # --------------------------------------------------------------------------
    def getProxy(self):
      rtn = self
      req = self.REQUEST
      if req.get( 'ZMS_PROXY', True):
        rtn = req.get( 'ZMS_PROXY_%s'%self.id, self.__proxy__())
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSLinkElement.getChildNodes:
    #
    #  Overrides original method of zmscontainerobject.ZMSContainerObject. 
    # --------------------------------------------------------------------------
    def getChildNodesPROXY(self, proxy, REQUEST={}, meta_types=None, reid=None):
      rtn = []
      if proxy != self and proxy is not None and self.isEmbeddedRecursive( REQUEST):
        recursive = True
        rtn = [self.initProxy( proxy, proxy.absolute_url()+'/'+x.id, x, recursive) for x in proxy.getChildNodes( REQUEST, meta_types, reid)]
      elif proxy == self and proxy is not None and self.isEmbedded( REQUEST):
        ref_obj = self.getRefObj()
        if ref_obj is not None:
          for ob in ref_obj.getChildNodes( REQUEST, meta_types, reid):
            if not ob.isPage():
              rtn.append( ob)
      return rtn

    def getChildNodes(self, REQUEST={}, meta_types=None, reid=None):
      proxy = self.getProxy()
      rtn = self.getChildNodesPROXY( proxy, REQUEST, meta_types, reid)
      return rtn


    ############################################################################
    ###
    ###  Printable
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSLinkElement.printHtml:
    #
    #  Renders printable presentation of a ContainerObject.
    # --------------------------------------------------------------------------
    def printHtmlPROXY(self, proxy, level, sectionizer, REQUEST, deep=True):
      rtn = ''
      recursive = self.isEmbeddedRecursive( REQUEST)
      if proxy != self and proxy is not None and recursive:
        rtn = proxy.printHtml( level, sectionizer, REQUEST, deep)
      else:
        ref_obj = self.getRefObj()
        if ref_obj is not None:
          rtn = ref_obj.printHtml( level, sectionizer, REQUEST, deep)
      return rtn

    def printHtml(self, level, sectionizer, REQUEST, deep=True):
      proxy = self.getProxy()
      rtn = self.printHtmlPROXY( proxy, level, sectionizer, REQUEST, deep)
      return rtn


# call this to initialize framework classes, which
# does the right thing with the security assertions.
InitializeClass(ZMSLinkElement)

################################################################################