################################################################################
# _objchildren.py
#
# $Id: _objchildren.py,v 1.7 2004/11/24 21:02:52 zmsdev Exp $
# $Name:$
# $Author: zmsdev $
# $Revision: 1.7 $
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
import copy
import time
# Product Imports.
from Products.zms import _blobfields
from Products.zms import _fileutil
from Products.zms import standard


################################################################################
################################################################################
###
###   Object Children
###
################################################################################
################################################################################
class ObjChildren(object):

    # Management Permissions.
    # -----------------------
    __authorPermissions__ = (
      'manage_initObjChild',
    )
    __ac_permissions__=(
      ('ZMS Author', __authorPermissions__),
    )

    """
    ############################################################################
    ###
    ###  Constructor
    ###
    ############################################################################
    """
    # --------------------------------------------------------------------------
    #	ObjChildren.initObjChild
    # --------------------------------------------------------------------------
    def initObjChild(self, id, _sort_id, type, REQUEST):
      ##### ID ####
      metaObjAttr = self.getObjChildrenAttr(id)
      repetitive = metaObjAttr.get('repetitive', 0)==1
      if repetitive:
        id += str(self.getSequence().nextVal())
      
      ##### Create ####
      oItem = getattr(self, id, None)
      if oItem is None or id not in self.objectIds():
        globalAttr = self.dGlobalAttrs.get(type, self.dGlobalAttrs['ZMSCustom'])
        constructor = globalAttr.get('obj_class', self.dGlobalAttrs['ZMSCustom']['obj_class'])
        newNode = constructor(id, _sort_id+1, type)
        self._setObject(newNode.id, newNode)
        oItem = getattr(self, id)
      
      ##### Object State ####
      oItem.setObjStateNew(REQUEST)
      ##### Init Properties ####
      oItem.setObjStateModified(REQUEST)
      for lang in self.getLangIds():
        oItem.setObjProperty('active', 1, lang)
      ##### VersionManager ####
      oItem.onChangeObj(REQUEST)
          
      ##### Normalize Sort-IDs ####
      self.normalizeSortIds(standard.id_prefix(id))
        
      return oItem


    # --------------------------------------------------------------------------
    #  ObjChildren._initObjChildren
    # --------------------------------------------------------------------------
    def _initObjChildren(self, obj_attr, REQUEST):
      id = obj_attr['id']
      ids = [x.getId() for x in self.getChildNodes() if x.getId().startswith(id)]
      mandatory = obj_attr.get('mandatory',0)
      if mandatory:
        if len(ids) == 0:
          default  = obj_attr.get('custom')
          if default:
            _fileutil.import_zexp(self, default, obj_attr['id'], obj_attr['id'])
          else:
            if obj_attr['type'] == '*' and isinstance(obj_attr['keys'], list) and len( obj_attr['keys']) > 0:
              obj_attr['type'] = obj_attr['keys'][0]
            self.initObjChild(obj_attr['id'], 0, obj_attr['type'], REQUEST)
      repetitive = obj_attr.get('repetitive',0)
      if repetitive:
        if id in ids:
          new_id = self.getNewId(id)
          standard.writeLog( self, "[_initObjChildren]: Rename %s to %s"%(id, new_id))
          if new_id not in self.objectIds():
            try:
              self.manage_renameObject(id=id, new_id=new_id)
            except:
              ob = getattr(self, id)
              ob._setId(new_id) 
      else:
        if not id in ids and len(ids)>0:
          old_id = ids[0]
          standard.writeLog( self, "[_initObjChildren]: Rename %s to %s"%(old_id, id))
          if id not in self.objectIds():
            try:
              self.manage_renameObject(id=old_id, new_id=id)
            except:
              ob = getattr(self, old_id)
              ob._setId(id) 


    # --------------------------------------------------------------------------
    #	ObjChildren.initObjChildren
    # --------------------------------------------------------------------------
    def initObjChildren(self, REQUEST):
      standard.writeLog( self, "[initObjChildren]")
      self.getObjProperty( 'initObjChildren', REQUEST)
      metaObj = self.getMetaobj(self.meta_id)
      metaObjIds = self.getMetaobjIds()+['*']
      for metaObjAttrId in self.getMetaobjAttrIds( self.meta_id):
        metaObjAttr = self.getMetaobjAttr( self.meta_id, metaObjAttrId)
        if metaObjAttr['type'] in metaObjIds:
           self._initObjChildren( metaObjAttr, REQUEST)


    # --------------------------------------------------------------------------
    #  ObjChildren.getObjChildrenAttr:
    # --------------------------------------------------------------------------
    def getObjChildrenAttr(self, key, meta_type=None):
      meta_type = standard.nvl(meta_type, self.meta_id)
      ##### Meta-Objects ####
      if meta_type in self.getMetaobjIds() and key in self.getMetaobjAttrIds(meta_type):
        obj_attr = self.getMetaobjAttr(meta_type, key)
      ##### Default ####
      else:
        obj_attr = {'id':key,'repetitive':1,'mandatory':0}
      return obj_attr


    # --------------------------------------------------------------------------
    #  ObjChildren.getObjChildren
    # --------------------------------------------------------------------------
    def getObjChildren(self, id, REQUEST, meta_types=None):
      """
      Returns a NodeList that contains all children of this node in 
      correct order. If none, this is a empty NodeList. 
      """
      objAttr = self.getObjChildrenAttr(id)
      reid = None
      if id:
        if objAttr.get('repetitive'):
          reid = id+'$'+'|'+id+'\\d+'
        else:
          reid = id
      return self.getChildNodes(REQUEST, meta_types, reid)


    # --------------------------------------------------------------------------
    #  ObjChildren.getObjChildren
    # --------------------------------------------------------------------------
    def filteredObjChildren(self, id, REQUEST, meta_types=None):
      """
      Returns a NodeList that contains all visible children of this node in 
      correct order. If none, this is a empty NodeList. 
      """
      return [x for x in self.getObjChildren(id, REQUEST, meta_types) if x.isVisible(REQUEST)]


    ############################################################################
    #  ObjChildren.manage_initObjChild: 
    #
    #  Create object-child.
    ############################################################################
    def manage_initObjChild(self, id, type, lang, REQUEST, RESPONSE=None): 
      """ ObjChildren.manage_initObjChild """
      
      # Create.      
      obj = self.initObjChild(id, self.getNewSortId(), type, REQUEST)
      
      # Return with message.
      if RESPONSE is not None:
        message = self.getZMILangStr('MSG_INSERTED')%obj.display_type(REQUEST)
        message = standard.url_quote(message)
        target = REQUEST.get('manage_target', '%s/manage_main'%obj.id)
        RESPONSE.redirect('%s?lang=%s&manage_tabs_message=%s'%(target, lang, message))

################################################################################
