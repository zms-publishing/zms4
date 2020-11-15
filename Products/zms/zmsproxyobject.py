################################################################################
# zmsproxyobject.py
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
from zope.interface import implementer
# Product Imports.
from Products.zms import IZMSMetamodelProvider, IZMSFormatProvider
from Products.zms import zmscontainerobject
from Products.zms import  _globals


################################################################################
################################################################################
###
###  Class
###
################################################################################
################################################################################
@implementer(
      IZMSMetamodelProvider.IZMSMetamodelProvider,
      IZMSFormatProvider.IZMSFormatProvider)
class ZMSProxyObject(zmscontainerobject.ZMSContainerObject):


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.__init__: 
    # --------------------------------------------------------------------------
    def __init__(self, root, base, url_base, id, proxy, recursive=False):
      """ Constructor """
      self.__root__ = root
      self.base = base
      self.url_base = url_base
      self.meta_type = proxy.meta_type
      self.meta_id = proxy.meta_id
      self.dGlobalAttrs = proxy.dGlobalAttrs
      self.REQUEST = proxy.REQUEST
      self.id = id
      self.proxy = proxy
      self.recursive = recursive


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.__proxy__:
    # --------------------------------------------------------------------------
    def __proxy__(self):
      return self


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getProxy
    # --------------------------------------------------------------------------
    def getProxy(self):
      return self


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getPhysicalPath
    # --------------------------------------------------------------------------
    def getPhysicalPath(self):
      rtn = list( self.__root__.getPhysicalPath())
      for id in list( self.base.getPhysicalPath())+[self.id]:
        if id not in rtn:
          rtn.append( id)
      return tuple( rtn)


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.__request__ 
    # --------------------------------------------------------------------------
    def __request__(self, REQUEST):
      proxy = self.proxy
      if _globals.is_str_type(REQUEST):
        return proxy.REQUEST
      return REQUEST


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.absolute_url
    # --------------------------------------------------------------------------
    def absolute_url(self, relative=0):
      url_base = self.url_base
      rtn = url_base
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getMetaobjAttrIds:
    # --------------------------------------------------------------------------
    def getMetaobjAttrIds(self, meta_id, types=[]):
      proxy = self.proxy
      rtn = proxy.getMetaobjAttrIds( meta_id, types)
      return rtn


    # --------------------------------------------------------------------------
    #  MetaobjManager.getMetaobjAttr:
    # --------------------------------------------------------------------------
    def getMetaobjAttr(self, meta_id, key):
      proxy = self.proxy
      rtn = proxy.getMetaobjAttr( meta_id, key)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getConfProperty
    # --------------------------------------------------------------------------
    def getConfProperty(self, key, default=None):
      proxy = self.proxy
      rtn = proxy.getConfProperty( key, default)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getObjAttrs
    # --------------------------------------------------------------------------
    def getObjAttrs(self, meta_type=None):
      proxy = self.proxy
      rtn = proxy.getObjAttrs( meta_type)
      return rtn
      
      
    # --------------------------------------------------------------------------
    #  ZMSProxyObject._getObjAttrValue
    # --------------------------------------------------------------------------
    def _getObjAttrValue(self, obj_attr, obj_vers, lang):
      proxy = self.proxy
      rtn = proxy._getObjAttrValue( obj_attr, obj_vers, lang)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getObjAttrValue
    # --------------------------------------------------------------------------
    def getObjAttrValue(self, obj_attr, REQUEST):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.getObjAttrValue( obj_attr, req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getRootElement
    # --------------------------------------------------------------------------
    def getRootElement(self):
      base = self.base
      rtn = base.getRootElement( )
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getDocumentElement
    # --------------------------------------------------------------------------
    def getDocumentElement(self):
      base = self.base
      rtn = base.getDocumentElement( )
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getHome
    # --------------------------------------------------------------------------
    def getHome(self):
      base = self.base
      rtn = base.getHome( )
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getDCCoverage
    # --------------------------------------------------------------------------
    def getDCCoverage(self, REQUEST={}):
      proxy = self.proxy
      rtn = proxy.getDCCoverage( REQUEST)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getDCDescription
    # --------------------------------------------------------------------------
    def getDCDescription(self, REQUEST):
      proxy = self.proxy
      rtn = proxy.getDCDescription( REQUEST)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getUserAttr:
    #
    #  Overrides AccessManager.getUserAttr.
    # --------------------------------------------------------------------------
    def getUserAttr(self, user, name, default, flag=0):
      proxy = self.proxy
      rtn = proxy.getUserAttr( user, name, default, flag)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getPageExt
    # --------------------------------------------------------------------------
    def getPageExt(self, REQUEST):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.getPageExt( req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getTitle
    # --------------------------------------------------------------------------
    def getTitle(self, REQUEST):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.getTitle( req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getTitlealt:
    # --------------------------------------------------------------------------
    def getTitlealt(self, REQUEST):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.getTitlealt( req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getPenetrance:
    # --------------------------------------------------------------------------
    def getPenetrance(self, REQUEST):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.getPenetrance( req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getChildNodes:
    # --------------------------------------------------------------------------
    def getChildNodes(self, REQUEST={}, meta_types=None, reid=None):
      rtn = []
      recursive = self.recursive
      if recursive:
        proxy = self.proxy
        req = self.__request__( REQUEST)
        if hasattr( proxy, 'getChildNodesPROXY'):
          rtn = [ZMSProxyObject( self.__root__, self, self.absolute_url()+'/'+x.id, x.id, x, recursive) for x in proxy.getChildNodesPROXY( proxy, req, meta_types, reid)]
        else:
          rtn = [ZMSProxyObject( self.__root__, self, self.absolute_url()+'/'+x.id, x.id, x, recursive) for x in proxy.getChildNodes( req, meta_types, reid)]
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getSecNo
    # --------------------------------------------------------------------------
    def getSecNo(self):
      proxy = self.proxy
      rtn = proxy.getSecNo( )
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getLevel
    # --------------------------------------------------------------------------
    def getLevel(self):
      proxy = self.proxy
      base = self.base
      rtn = base.getLevel( ) + 1
      recursive = self.recursive
      if proxy is not None and proxy is ZMSProxyObject:
        if hasattr( proxy, 'getLevelPROXY'):
          rtn = proxy.getLevelPROXY( proxy)
        else:
          rtn = proxy.getLevel()
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getObjProperty
    # --------------------------------------------------------------------------
    def getObjProperty(self, key, REQUEST={}, default=None):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      if hasattr( proxy, 'getObjPropertyPROXY'):
        rtn = proxy.getObjPropertyPROXY( proxy, key, req, default)
      else:
        rtn = proxy.getObjProperty( key, req, default)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getParentNode
    # --------------------------------------------------------------------------
    getParentNode__roles__ = None
    def getParentNode(self):
      """
      The parent of this node. 
      All nodes except root may have a parent.
      """
      rtn = self.base
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getType
    # --------------------------------------------------------------------------
    def getType(self):
      proxy = self.proxy
      rtn = proxy.getType()
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.isActive
    # --------------------------------------------------------------------------
    def isActive(self, REQUEST):
      proxy = self.proxy
      root = self.__root__
      rtn = proxy.isActive(REQUEST) and root.isActive(REQUEST)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.isMetaType:
    # --------------------------------------------------------------------------
    def isMetaType(self, meta_type, REQUEST={'preview':'preview'}):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.isMetaType( meta_type, req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.isResource:
    # --------------------------------------------------------------------------
    def isResource(self, REQUEST):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.isResource( req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.isPage:
    # --------------------------------------------------------------------------
    def isPage(self):
      proxy = self.proxy
      rtn = proxy.isPage( )
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.isPageElement:
    # --------------------------------------------------------------------------
    def isPageElement(self):
      proxy = self.proxy
      rtn = proxy.isPageElement( )
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.isVisible:
    # --------------------------------------------------------------------------
    def isVisible(self, REQUEST):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.isVisible( req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject._getBodyContent:
    # --------------------------------------------------------------------------
    def _getBodyContent(self, REQUEST):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy._getBodyContent( req)
      return rtn

    def getBodyContent(self, REQUEST, forced=False):
      """
      HTML presentation in body-content. 
      """
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.getBodyContent( req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.display_icon:
    # --------------------------------------------------------------------------
    def display_icon(self, REQUEST, meta_type=None, key='icon', zpt=None): 
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.display_icon( req, meta_type, key, zpt)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getLangIds:
    # --------------------------------------------------------------------------
    def getLangIds(self, sort=False):
      proxy = self.proxy
      rtn = proxy.getLangIds( sort)
      return rtn


    # --------------------------------------------------------------------------
    #	ZMSProxyObject.get_manage_lang:
    # --------------------------------------------------------------------------
    def get_manage_lang(self):
      proxy = self.proxy
      rtn = proxy.get_manage_lang( )
      return rtn


    # --------------------------------------------------------------------------
    #	ZMSProxyObject.getZMILangStr:
    # --------------------------------------------------------------------------
    def getZMILangStr(self, key, REQUEST=None, RESPONSE=None):
      proxy = self.proxy
      rtn = proxy.getZMILangStr( key, REQUEST, RESPONSE)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getLangStr:
    # --------------------------------------------------------------------------
    def getLangStr(self, key, lang=None):
      proxy = self.proxy
      rtn = proxy.getLangStr( key, lang)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getPrimaryLanguage:
    # --------------------------------------------------------------------------
    def getPrimaryLanguage(self):
      proxy = self.proxy
      rtn = proxy.getPrimaryLanguage()
      return rtn
    

    # --------------------------------------------------------------------------
    #  ZMSProxyObject.hasAccess:
    # --------------------------------------------------------------------------
    def hasAccess(self, REQUEST):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.hasAccess( req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getObjVersion:
    # --------------------------------------------------------------------------
    def getObjVersion(self, REQUEST={}):
      proxy = self.proxy
      req = self.__request__( REQUEST)
      rtn = proxy.getObjVersion( req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.breadcrumbs_obj_path:
    # --------------------------------------------------------------------------
    def breadcrumbs_obj_path(self, portalMaster=True):
      proxy = self.proxy
      base = self.base
      rtn = base.breadcrumbs_obj_path( ) + [ self]
      recursive = self.recursive
      if proxy is not None and proxy is ZMSProxyObject:
        if hasattr( proxy, 'breadcrumbs_obj_pathPROXY'):
          rtn = proxy.breadcrumbs_obj_pathPROXY( proxy, portalMaster)
        else:
          rtn = proxy.breadcrumbs_obj_path(portalMaster)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getDeclUrl:
    # --------------------------------------------------------------------------
    def getDeclUrl(self, REQUEST={}):
      if self.getConfProperty('ZMS.pathhandler', 0) == 0:
        rtn = self.absolute_url()
      else:
        base = self.base
        req = self.__request__( REQUEST)
        rtn = base.getDeclUrl( req)
        rtn += '/' + self.getDeclId( req)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getHref2IndexHtml:
    # --------------------------------------------------------------------------
    def getHref2IndexHtml(self, REQUEST, deep=1): 
      proxy = self.proxy
      rtn = zmscontainerobject.ZMSContainerObject.getHref2IndexHtml( self, REQUEST, deep)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.getStylesheet:
    # --------------------------------------------------------------------------
    def getStylesheet(self, id=None):
      base = self.base
      rtn = base.getStylesheet( id)
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSProxyObject.printHtml:
    # --------------------------------------------------------------------------
    def printHtml(self, level, sectionizer, REQUEST, deep=True):
      proxy = self.proxy
      rtn = proxy.printHtml( level, sectionizer, REQUEST, deep)
      return rtn


    ############################################################################
    ###
    ###   Interface IZMSMetamodelProvider: delegate to proxy
    ###
    ############################################################################

    def getMetaobjId(self, name):
      return self.proxy.getMetaobjId( name)

    def getMetaobjIds(self, sort=None, excl_ids=[]):
      return self.proxy.getMetaobjIds( sort, excl_ids)

    def getMetaobj(self, id):
      return self.proxy.getMetaobj( id)

    def getMetaobjAttrIds(self, meta_id, types=[]):
      return self.proxy.getMetaobjAttrIds( meta_id, types)

    def getMetaobjAttr(self, meta_id, key):
      return self.proxy.getMetaobjAttr( meta_id, key)


    ############################################################################
    ###
    ###   Interface IZMSFormatProvider: delegate to proxy
    ###
    ############################################################################

    def getTextFormatDefault(self):
      return self.proxy.getTextFormatDefault()

    def getTextFormat(self, id, REQUEST):
      return self.proxy.getTextFormat(id, REQUEST)

    def getTextFormats(self, REQUEST):
      return self.proxy.getTextFormats(REQUEST)

    def getCharFormats(self):
      return self.proxy.getCharFormats()

################################################################################
