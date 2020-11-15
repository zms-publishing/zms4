################################################################################
# zmscontainerobject.py
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
from OFS.role import RoleManager
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.CopySupport import _cb_decode, _cb_encode, CopyError # TODO , eNoData, eNotFound, eInvalid
import copy
import re
import sys
import time
# Product Imports.
from Products.zms import zmsobject
from Products.zms import standard
from Products.zms import _accessmanager
from Products.zms import _confmanager
from Products.zms import _fileutil
from Products.zms import _objattrs
from Products.zms import _versionmanager
from Products.zms import _zmi_actions_util

__all__= ['ZMSContainerObject']


# ------------------------------------------------------------------------------
#  zmscontainerobject.isPageWithElements:
# ------------------------------------------------------------------------------
def isPageWithElements(obs):
  for ob in obs:
    if ob.isPageElement():
      return True
  return False


# ------------------------------------------------------------------------------
#  zmscontainerobject.getPrevSibling: 
#
#  The node immediately preceding this node, otherwise returns None. 
# ------------------------------------------------------------------------------
def getPrevSibling(self, REQUEST, incResource=False):
  parent = self.getParentNode()
  if parent is not None:
    siblings = parent.getChildNodes(REQUEST, [self.PAGES, self.NORESOLVEREF]) 
    if self in siblings:
      i = siblings.index(self) - 1
      while i >= 0:
        ob = siblings[i]
        if ob.isVisible(REQUEST) and (incResource or not ob.isResource(REQUEST)):
          return ob
        i = i - 1
  return None

# ------------------------------------------------------------------------------
#  zmscontainerobject.getNextSibling: 
#
#  The node immediately following this node, otherwise returns None. 
# ------------------------------------------------------------------------------
def getNextSibling(self, REQUEST, incResource=False):
  parent = self.getParentNode()
  if parent is not None:
    siblings = parent.getChildNodes(REQUEST, [self.PAGES, self.NORESOLVEREF]) 
    siblingIds = [x.id for x in siblings]
    if self.id in siblingIds:
      i = siblingIds.index( self.id) + 1
      while i < len(siblings):
        ob = siblings[i]
        if ob.isVisible(REQUEST) and (incResource or not ob.isResource(REQUEST)):
          return ob
        i = i + 1
  return None



################################################################################
################################################################################
###
###   Abstract Class ZMSContainerObject
###
################################################################################
################################################################################
class ZMSContainerObject(
    zmsobject.ZMSObject,
    RoleManager,
    _accessmanager.AccessableContainer,
    _versionmanager.VersionManagerContainer
    ):

    # Management Permissions.
    # -----------------------
    __administratorPermissions__ = (
        'manage_system',
        )
    __ac_permissions__=(
        ('ZMS Administrator', __administratorPermissions__),
        )

    # Management Interface.
    # ---------------------
    manage_main = PageTemplateFile('zpt/ZMSObject/manage_main', globals())
    zmi_manage_main_change = PageTemplateFile('zpt/ZMSContainerObject/zmi_manage_main_change', globals())
    zmi_manage_main_grid = PageTemplateFile('zpt/ZMSContainerObject/main_grid', globals())
    manage_container = PageTemplateFile('zpt/ZMSContainerObject/manage_main', globals())
    manage_properties = PageTemplateFile('zpt/ZMSObject/manage_main', globals())
    manage_system = PageTemplateFile('zpt/ZMSContainerObject/manage_system', globals())
    manage_importexport = PageTemplateFile('zpt/ZMSContainerObject/manage_importexport', globals())
    manage_importexportDebugFilter = PageTemplateFile('zpt/ZMSContainerObject/manage_importexportdebugfilter', globals())


    # Role Manager.
    # -------------
    def manage_addZMSCustom(self, meta_id, values={}, REQUEST=None):
      """
      Add a custom node of the type designated by meta_id in current context.
      @param meta_id: the meta-id / type of the new ZMSObject
      @type meta_id: C{str}
      @param values: the dictionary of initial attribut-values assigned to the new ZMSObject 
      @type values: C{dict}
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @return: the new node
      @rtype: C{zmsobject.ZMSObject}
      """
      values['meta_id'] = meta_id
      return self.manage_addZMSObject('ZMSCustom', values, REQUEST)


    # --------------------------------------------------------------------------
    #  ZMSContainerObject.manage_addZMSObject:
    # --------------------------------------------------------------------------
    def manage_addZMSObject(self, meta_id, values, REQUEST):
      """
      Add a node of type designated by meta_id in current context.
      @param meta_id: the meta-id / type of the new ZMSObject
      @type meta_id: C{str}
      @param values: the dictionary of initial attribut-values assigned to the new ZMSObject 
          - I{id_prefix} (C{str=''}) the id-prefix used to generate the new id
          - I{id} (C{str=''}) the new id (fixed)
          - I{sort_id} (C{str=''}) the sort-id
          - I{meta_id} (C{str=''}) the meta-id
          - I{active} (C{str=''}) is active
          - I{attr_dc_coverage} (C{str=''}) the coverage
      @type values: C{dict}
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @return: the new node
      @rtype: C{zmsobject.ZMSObject}
      """
      prim_lang = self.getPrimaryLanguage()
      lang = REQUEST.get('lang', prim_lang)
      
      attrs = []
      for key in values:
        attrs.extend([key, values[key]])
      
      # Get new id.
      if 'id_prefix' in attrs:
        i = attrs.index('id_prefix')
        id_prefix = attrs[i+1]
        new_id = self.getNewId(id_prefix)
        del attrs[i] # Key.
        del attrs[i] # Value.
      elif 'id' in attrs:
        i = attrs.index('id')
        new_id = attrs[i+1]
        del attrs[i] # Key.
        del attrs[i] # Value.
      else:
        new_id = self.getNewId()
      
      # Get sort id.
      key = 'sort_id'
      if key in attrs and attrs.index(key)%2 == 0:
        i = attrs.index(key)
        _sort_id = attrs[i+1]
        del attrs[i] # Key.
        del attrs[i] # Value.
      else:
        _sort_id = 99999
      
      # Type of new object.
      key = 'meta_id'
      if meta_id == 'ZMSCustom' and key in attrs and attrs.index(key)%2 == 0:
        i = attrs.index(key)
        meta_id = attrs[i+1]
        del attrs[i] # Key.
        del attrs[i] # Value.
      
      # Create new object.
      globalAttr = self.dGlobalAttrs.get(meta_id, self.dGlobalAttrs['ZMSCustom'])
      constructor = globalAttr.get('obj_class', self.dGlobalAttrs['ZMSCustom']['obj_class'])
      obj = constructor(new_id, _sort_id+1, meta_id)
      self._setObject(obj.id, obj)
      node = getattr(self, obj.id)
      
      # Object state.
      node.setObjStateNew(REQUEST)
      
      # Init properties.
      key = 'active'
      if not (key in attrs and attrs.index(key)%2 == 0):
        attrs.extend([key, 1])
      key = 'attr_dc_coverage'
      if not (key in attrs and attrs.index(key)%2 == 0):
        attrs.extend([key, 'global.%s'%lang])
      for i in range(len(attrs)//2):
        key = attrs[i*2]
        value = attrs[i*2+1]
        node.setObjProperty(key, value, REQUEST['lang'])
      
      # Version manager.
      node.onChangeObj(REQUEST)
      
      # Normalize sort-ids.
      if values.get('normalize_sort_ids', True):
        self.normalizeSortIds(standard.id_prefix(node.id))
      
      # Return object.
      return node


    ############################################################################
    ###
    ###   Trashcan
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    # Move objects to trashcan.
    #
    # @param ids: List of object-ids.
    # @type ids: C{list}
    # @rtype: C{None}
    # --------------------------------------------------------------------------
    def moveObjsToTrashcan(self, ids, REQUEST):
      if self.meta_id == 'ZMSTrashcan':
        return
      trashcan = self.getTrashcan()
      # Set deletion-date.
      ids_copy = []
      for id in ids:
        try:
          context = getattr(self, id)
          context.del_uid = str(REQUEST.get('AUTHENTICATED_USER', None))
          context.del_dt = standard.getDateTime( time.time())
          ids_copy.append(id)
        except:
          standard.writeBlock( self, "[moveObjsToTrashcan]: Attribute Error %s"%(id))
      # Use only successfully tried ids
      ids = ids_copy
      # Move (Cut & Paste).
      children = [getattr(self,x) for x in ids]
      [standard.triggerEvent(child,'beforeDeleteObjsEvt') for child in children]
      cb_copy_data = _cb_decode(self.manage_cutObjects(ids))
      trashcan.manage_pasteObjects(cb_copy_data=_cb_encode(cb_copy_data))
      trashcan.normalizeSortIds()
      trashcan.run_garbage_collection(forced=1)
      # Sort-IDs.
      self.normalizeSortIds()
      [standard.triggerEvent(child,'afterDeleteObjsEvt') for child in children]


    ############################################################################
    #  ZMSContainerObject.manage_eraseObjs:
    ############################################################################
    def manage_eraseObjs(self, lang, ids, REQUEST, RESPONSE=None):
      """ 
      Delete a subordinate object physically:
      The objects specified in 'ids' get deleted.
      @param lang: the language-id.
      @type lang: C{str}
      @param ids: the list of object-ids.
      @type ids: C{list}
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @param RESPONSE: the triggering request
      @type RESPONSE: C{ZPublisher.HTTPResponse}
      """ 
      
      message = ''
      t0 = time.time()
      
      ##### Delete objects ####
      count = len(ids)
      self.manage_delObjects(ids=ids)
      
      # Return with message.
      if RESPONSE is not None:
        message += self.getZMILangStr('MSG_DELETED')%count
        message += ' (in '+str(int((time.time()-t0)*100.0)/100.0)+' secs.)'
        target = REQUEST.get('manage_target', 'manage_main')
        return RESPONSE.redirect('%s?lang=%s&manage_tabs_message=%s'%(target, lang, standard.url_quote(message)))


    ############################################################################
    #  ZMSContainerObject.manage_undoObjs:
    ############################################################################
    def manage_undoObjs(self, lang, ids, REQUEST, RESPONSE=None):
      """
      Undo a subordinate object:
      The objects specified in 'ids' get undone (changes are rolled-back).
      @param lang: the language-id.
      @type lang: C{str}
      @param ids: the list of object-ids.
      @type ids: C{list}
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @param RESPONSE: the triggering request
      @type RESPONSE: C{ZPublisher.HTTPResponse}
      """ 
      
      message = ''
      t0 = time.time()
      
      ##### Delete objects ####
      c = 0
      for child in self.getChildNodes():
        if child.id in ids:
          if child.inObjStates( [ 'STATE_NEW', 'STATE_MODIFIED', 'STATE_DELETED'], REQUEST):
            child.rollbackObjChanges( self, REQUEST)
            c += 1
      
      # Return with message.
      if RESPONSE is not None:
        message += self.getZMILangStr('MSG_UNDONE')%c
        message += ' (in '+str(int((time.time()-t0)*100.0)/100.0)+' secs.)'
        target = REQUEST.get('manage_target', 'manage_main')
        return RESPONSE.redirect('%s?preview=preview&lang=%s&manage_tabs_message=%s'%(target, lang, standard.url_quote(message)))


    ############################################################################
    #  ZMSContainerObject.manage_deleteObjs:
    ############################################################################
    def manage_deleteObjs(self, lang, ids, REQUEST, RESPONSE=None):
      """
      Delete a subordinate object logically:
      The objects specified in 'ids' get deleted (moved to trashcan).
      @param lang: the language-id.
      @type lang: C{str}
      @param ids: the list of object-ids.
      @type ids: C{list}
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @param RESPONSE: the triggering request
      @type RESPONSE: C{ZPublisher.HTTPResponse}
      """
      message = ''
      t0 = time.time()
      
      ##### Delete objects ####
      versionMgrCntnrs = []
      for child in self.getChildNodes():
        if child.id in ids:
          if child.getAutocommit() or child.inObjStates(['STATE_NEW'], REQUEST):
            self.moveObjsToTrashcan([child.id], REQUEST)
          else:
            child.setObjStateDeleted(REQUEST)
            versionCntnr = child.getVersionContainer()
            if versionCntnr not in versionMgrCntnrs:
              versionMgrCntnrs.append( versionCntnr)
      
      ##### VersionManager ####
      for versionCntnr in versionMgrCntnrs:
        versionCntnr.onChangeObj(REQUEST)
      
      # Return with message.
      if RESPONSE is not None:
        message += self.getZMILangStr('MSG_TRASHED')%len(ids)
        message += ' (in '+str(int((time.time()-t0)*100.0)/100.0)+' secs.)'
        target = REQUEST.get('manage_target', 'manage_main')
        return RESPONSE.redirect('%s?preview=preview&lang=%s&manage_tabs_message=%s'%(target, lang, standard.url_quote(message)))


    # --------------------------------------------------------------------------
    #  ZMSContainerObject.getContentType
    # --------------------------------------------------------------------------
    def getContentType( self, REQUEST):
      """
      Returns MIME-type (text/html).
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @return: always returns 'text/html'
      @rtype: C{str}
      """
      return 'text/html'


    ############################################################################
    ###
    ###  Drag'n Drop
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSContainerObject.manage_ajaxDragDrop:
    # --------------------------------------------------------------------------
    def manage_ajaxDragDrop( self, lang, target, REQUEST, RESPONSE):
      """ 
      ZMSContainerObject.manage_ajaxDragDrop
      internal use only
      """
      rc = 0
      message = self.getZMILangStr('MSG_PASTED')
      try:
        before = False
        into = False
        if target.startswith('-'):
          before = True
          target = target[1:]
        elif target.endswith('-'):
          target = target[:-1]
        else:
          into = True
        ob = self.getLinkObj( target)
        sort_id = ob.getSortId()
        if into:
          sort_id = 0
        else:
          ob = ob.getParentNode()
          if before:
            sort_id = sort_id - 1
          else:
            sort_id = sort_id + 1
        self.setSortId(sort_id)
        cb_copy_data = self.getParentNode().manage_cutObjects([self.id])
        ob.manage_pasteObjects(cb_copy_data)
        ob.normalizeSortIds()
      except:
        tp, vl, tb = sys.exc_info()
        rc = -1
        message = str(tp)+': '+str(vl)
        standard.writeError(self, '[manage_ajaxDragDrop]')
      #-- Build xml.
      RESPONSE = REQUEST.RESPONSE
      content_type = 'text/xml; charset=utf-8'
      filename = 'manage_ajaxDragDrop.xml'
      RESPONSE.setHeader('Content-Type', content_type)
      RESPONSE.setHeader('Content-Disposition', 'inline;filename="%s"'%filename)
      RESPONSE.setHeader('Cache-Control', 'no-cache')
      RESPONSE.setHeader('Pragma', 'no-cache')
      self.f_standard_html_request( self, REQUEST)
      xml = self.getXmlHeader()
      xml += '<result code="%i" message="%s">\n'%(rc, message)
      xml += "</result>\n"
      return xml


    ############################################################################
    ###
    ###  Page-Navigation
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSContainerObject.getFirstPage:
    # --------------------------------------------------------------------------
    def getFirstPage(self, REQUEST, incResource=False, root=None):
      """
      Returns the first page of the tree from root (or document-element if root
      is not given).
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @return: the first page
      @rtype: C{zmsobject.ZMSObject}
      """
      root = standard.nvl(root, self.getDocumentElement())
      return root
    
    # --------------------------------------------------------------------------
    #  ZMSContainerObject.getPrevPage:
    # --------------------------------------------------------------------------
    def getPrevPage(self, REQUEST, incResource=False, root=None):
      """
      Returns the previous page of this node from root (or document-element if root
      is not given).
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @return: the previous page
      @rtype: C{zmsobject.ZMSObject}
      """
      ob = None
      root = standard.nvl(root, self.getDocumentElement())
      while True:
        ob = getPrevSibling(self, REQUEST, incResource)
        if ob is None:
          parent = self.getParentNode()
          if parent is not None:
            if self.getHref2IndexHtml(REQUEST) == parent.getHref2IndexHtml(REQUEST):
              ob = parent.getPrevPage(REQUEST, incResource, parent)
            else:
              ob = parent
        else:
          ob = ob.getLastPage(REQUEST, incResource, ob)
        if not ob is None and not ob.isMetaType(self.PAGES, REQUEST):
          ob = ob.getPrevPage(REQUEST, incResource, root)
        if ob is None or ob.isMetaType(self.PAGES, REQUEST):
          break
      return ob

    # --------------------------------------------------------------------------
    #  ZMSContainerObject.getNextPage:
    # --------------------------------------------------------------------------
    def getNextPage(self, REQUEST, incResource=False, root=None): 
      """
      Returns the next page of this node from root (or document-element if root
      is not given).
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @return: the next page
      @rtype: C{zmsobject.ZMSObject}
      """
      ob = None
      root = standard.nvl(root, self.getDocumentElement())
      while True:
        children = self.filteredChildNodes(REQUEST, self.PAGES)
        if len(children) > 0:
          ob = children[0]
        else:
          current = self
          while ob is None and current is not None:
            ob = getNextSibling(current, REQUEST, incResource)
            current = current.getParentNode()
        if not ob is None and not ob.isMetaType(self.PAGES, REQUEST):
          ob = ob.getNextPage(REQUEST, incResource, root)
        if ob is None or ob.isMetaType(self.PAGES, REQUEST):
          break
      return ob

    # --------------------------------------------------------------------------
    #  ZMSContainerObject.getLastPage:
    # --------------------------------------------------------------------------
    def getLastPage(self, REQUEST, incResource=False, root=None):
      """
      Returns the last page of the tree from root (or document-element if root
      is not given).
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @return: the last page
      @rtype: C{zmsobject.ZMSObject}
      """
      ob = None
      root = standard.nvl(root, self.getDocumentElement())
      children = [root]
      while len( children) > 0:
        i = len( children)-1
        while i >= 0:
          if (incResource or not children[i].isResource(REQUEST)):
            ob = children[i]
            i = 0
          i = i - 1
        if ob == self:
          break
        children = ob.filteredChildNodes(REQUEST, self.PAGES)
      return ob


    ############################################################################
    ###  
    ###  Object-actions of management interface
    ### 
    ############################################################################

    def manage_ajaxZMIActions(self, context_id, REQUEST, RESPONSE):
      """
      Returns ZMI actions.
      internal use only
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @param RESPONSE: the response
      @type RESPONSE: C{ZPublisher.HTTPResponse}
      """
      
      #-- Get actions.
      actions = []
      container = self
      objPath = ''
      context = None 
      if context_id == '':
        context = container
        actions.extend( _zmi_actions_util.zmi_actions(self, self))
      else:
        attr_id = standard.id_prefix(context_id)
        if context_id in container.objectIds():
            context = getattr(container, context_id, None)
        actions.extend( _zmi_actions_util.zmi_actions(container, context, attr_id))
        if context is not None:
          objPath = context.id+'/'
      if context is not None:
        actions.extend( context.filtered_workflow_actions(objPath))
      
      #-- Build json.
      RESPONSE.setHeader('Content-Type', 'text/plain; charset=utf-8')
      RESPONSE.setHeader('Cache-Control', 'no-cache')
      RESPONSE.setHeader('Pragma', 'no-cache')
      rtn = self.str_json({'id':context_id,'actions':actions})
      return rtn


    ############################################################################
    ###
    ###  HTML-Presentation
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSContainerObject.getNavItems:
    # --------------------------------------------------------------------------
    def getNavItems(self, current, REQUEST, opt={}, depth=0):
      """
      Returns html-formatted (unordered) list of navigation-items.
      Uses the following classes
        - I{current} item is current-element
        - I{(in-)active} items is parent of current-element or current-element
        - I{restricted} item has restricted access
      @param current: the currently displayed page
      @type current: C{zmsobject.ZMSObject}
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @param opt: the dictionary of options
          - I{id} (C{str=''}) id of base ul-element
          - I{cssclass} (C{str=''}) css class of base ul-element
          - I{add_self} (C{boolean=False}) add self to list
          - I{deep} (C{boolean=True}) process child nodes
          - I{complete} (C{boolean=False}) process complete subtree
          - I{maxdepth} (C{int=100}) limits node list to a given depth
          - I{getrestricted} (C{boolean=True}) get is restricted
          - I{getchildpages} (C{boolean=True}) get has child-pages
      @return: the Html
      @rtype: C{str}
      """
      items = []
      obs = []
      if opt.get('add_self', False):
        obs.append( self)
        opt['add_self'] = False
      obs.extend( self.filteredChildNodes(REQUEST, self.PAGES))
      for ob in obs:
        if not ob.isResource(REQUEST):
          if len( items) == 0:
            items.append( '<ul')
            if opt.get('id', ''):
              items.append( ' id="%s"'%opt.get('id', ''))
              opt['id'] = ''
            if opt.get('cssclass', ''):
              items.append( ' class="%s"'%opt.get('cssclass', ''))
              opt['cssclass'] = ''
            items.append('>\n')
          css = []
          css.append( ob.id)
          if ob.id == current.id:
            css.append( 'current')
            css.append( 'active')
            css.append( ob.meta_id + '1') 
          elif ob.id != self.id and ob.id in current.getPhysicalPath():
            css.append( 'active')
            css.append( ob.meta_id + '1') 
          else: 
            css.append( 'inactive')
            css.append( ob.meta_id + '0')
          if opt.get('getrestricted', True) and ob.attr( 'attr_dc_accessrights_restricted'):
            css.append( 'restricted')
          if opt.get('getchildpages', True) and len(ob.filteredChildNodes(REQUEST, self.PAGES))>0:
            css.append( 'childpages')
          items.append('<li')
          items.append(' class="%s"'%(' '.join(css)))
          items.append('>')
          items.append('<a ')
          items.append(' href="%s"'%ob.getHref2IndexHtml(REQUEST))
          items.append(' title="%s"'%ob.getTitle(REQUEST))
          if len(css) > 0:
            items.append(' class="%s"'%(' '.join(css)))
          items.append('>')
          items.append('<span>%s</span>'%ob.getTitlealt(REQUEST))
          items.append('</a>')
          if (max(depth, ob.getLevel()) < opt.get('maxdepth', 100)) and \
             ((opt.get('complete', False)) or \
              (opt.get('deep', True) and ob.id != self.id and \
                (ob.id in current.getPhysicalPath() or \
                 ob.id in REQUEST['URL'].split('/')))):
            items.append( ob.getNavItems( current, REQUEST, opt, depth+1))
          items.append('</li>\n')
      if len( items) > 0:
        items.append( '</ul>\n')
      return ''.join(items)


    # --------------------------------------------------------------------------
    #  ZMSContainerObject.getNavElements: 
    #
    #  Elements of main-navigation in content-area.
    # --------------------------------------------------------------------------
    def getNavElements(self, REQUEST, expand_tree=1, current_child=None, subElements=[]):
      elmnts = []
      # Child navigation.
      obs = self.filteredChildNodes(REQUEST)
      if not expand_tree and \
         current_child is not None and \
         current_child.meta_id in ['ZMS', 'ZMSFolder'] and \
         isPageWithElements(obs) and \
         self.getLevel() > 0:
        obs = [current_child]
      for ob in obs:
        if ob.isPage() and not ob.isResource(REQUEST): 
          elmnts.append(ob)
        if current_child is not None and \
           current_child.id == ob.id:
          elmnts.extend(subElements)
      # Parent navigation.
      parent = self.getParentNode()
      if parent is not None:
        elmnts = parent.getNavElements(REQUEST, expand_tree, self, elmnts)
      # Return elements.
      return elmnts


    # --------------------------------------------------------------------------
    #  ZMSContainerObject.getIndexNavElements: 
    #
    #  Elements of index-navigation in content-area.
    # --------------------------------------------------------------------------
    def getIndexNavElements(self, REQUEST):
      indexNavElmnts = []
      # Retrieve elements.
      if REQUEST.get('op', '')=='':
        indexNavElmnts = [x for x in self.filteredChildNodes(REQUEST, self.PAGES) if ob.isPage() and ob.isMetaType(['ZMSDocument', 'ZMSCustom']) and not ob.isResource(REQUEST)]
      # Return elements.
      return indexNavElmnts


    ############################################################################
    ###
    ###   DOM-Methods
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSContainerObject.filteredTreeNodes:
    #
    # --------------------------------------------------------------------------
    def filteredTreeNodes(self, REQUEST, meta_types, order_by=None, order_dir=None, max_len=None, recursive=True):
      """
      Returns a node-list that contains all visible children of this subtree 
      in correct order. If none, this is a empty node-list. 
      @param meta_types: the meta_type(s) (single or list), may also be C{ZMSContainerObject.PAGES} or C{ZMSContainerObject.PAGEELEMENTS}
      @type meta_types: C{str|list}
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest=None}
      @return: the list of ZMSObjects
      @rtype: C{list<ZMSObject>}
      """
      rtn = []
      
      #-- Process tree.
      if not self.meta_type == 'ZMSLinkElement':
        obs = self.getChildNodes(REQUEST)
        for ob in obs:
          append = True
          append = append and ob.isMetaType(meta_types)
          append = append and ob.isVisible(REQUEST)
          if append: 
            rtn.append(ob)
          if not append or (append and recursive):
            if ob.isPage():
              rtn.extend(ob.filteredTreeNodes(REQUEST, meta_types, None, order_dir, None, recursive))
      
      #-- Order.
      if order_by is not None:
      
        # order by select-options of special object
        options = []
        if isinstance(meta_types, str) and meta_types in self.getMetaobjIds():
          metaObj = self.getMetaobj(meta_types)
          attrs = metaObj['attrs']
          for attr in attrs:
            if attr['id'] == order_by:
              options = attr.get('keys', [])
      
        # collect object-items
        tmp = []
        for ob in rtn:
          value = ob.getObjProperty(order_by, REQUEST)
          if value in options:
            value = options.index(value)
          tmp.append((value, ob))
        
        # sort object-items
        tmp.sort()
        
        # truncate sort-id from sorted object-items
        rtn = [x[1] for x in tmp]
        if order_dir == 'desc': 
          rtn.reverse()
      
      #-- Size.
      if max_len is not None:
        if len(rtn) > max_len:
          rtn = rtn[:max_len]
      
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSContainerObject.firstFilteredChildNode:
    # --------------------------------------------------------------------------
    def firstFilteredChildNode(self, REQUEST=None, meta_types=None):
      """
      Returns the first visible child of this node.
      @param meta_types: the meta_type(s) (single or list), may also be C{ZMSContainerObject.PAGES} or C{ZMSContainerObject.PAGEELEMENTS}
      @type meta_types: C{str|list}
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest=None}
      @return: the first ZMSObject
      @rtype: C{ZMSObject}
      """
      for node in self.getChildNodes(REQUEST, meta_types):
        if node.isVisible(REQUEST):
          return node
      return None


    # --------------------------------------------------------------------------
    #  ZMSContainerObject.filteredChildNodes:
    # --------------------------------------------------------------------------
    def filteredChildNodes(self, REQUEST=None, meta_types=None):
      """
      Returns a node-list that contains all visible children of this node in 
      correct order. If none, this is a empty node-list. 
      @param meta_types: the meta_type(s) (single or list), may also be C{ZMSContainerObject.PAGES} or C{ZMSContainerObject.PAGEELEMENTS}
      @type meta_types: C{str|list}
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest=None}
      @return: the list of ZMSObjects
      @rtype: C{list<ZMSObject>}
      """
      return [x for x in self.getChildNodes(REQUEST, meta_types) if x.isVisible(REQUEST)]


    # --------------------------------------------------------------------------
    #  ZMSContainerObject.getChildNodes:
    # --------------------------------------------------------------------------
    PAGES        = 0 # virtual meta_type for all Pages (Containers)
    PAGEELEMENTS = 1 # virtual meta_type for all Page-Elements
    NOREF        = 4 # virtual meta_type for resolving meta-type of ZMSLinkElement-target-object.
    NORESOLVEREF = 5 # virtual meta_type for not resolving meta-type of ZMSLinkElement-target-object.
    def getChildNodes(self, REQUEST=None, meta_types=None, reid=None):
      """
      Returns a node-list that contains all children of this node in correct 
      order. If none, this is a empty node-list. 
      """
      childNodes = []
      obs = self.objectValues(list(self.dGlobalAttrs))
      # Filter ids.
      if reid:
        pattern = re.compile( reid)
        obs = [x for x in obs if pattern.match( x.id)]
      # Get all object-items.
      if REQUEST is None:
        childNodes = [( getattr( x, 'sort_id', ''), x) for x in obs]
      # Get selected object-items.
      else:
        prim_lang = self.getPrimaryLanguage()
        lang = REQUEST.get('lang', None)
        # Get coverages.
        coverages = [ '', 'obligation', None]
        if lang is not None:
          coverages.extend( [ 'global.'+lang, 'local.'+lang])
          coverages.extend( ['global.'+x for x in self.getParentLanguages( lang)])
        for ob in [x for x in obs if x.isMetaType( meta_types, REQUEST)]:
          coverage = None
          if lang is not None:
            obj_vers = ob.getObjVersion( REQUEST)
            coverage = getattr( obj_vers, 'attr_dc_coverage', '')
          if coverage in coverages:
            proxy = ob.__proxy__()
            if proxy is not None:
              sort_id = getattr( ob, 'sort_id', '')
              if ob.isPage():
                sort_id = 's' + sort_id
              childNodes.append( ( sort_id, proxy))
      # Sort child-nodes.
      childNodes.sort()
      # Return child-nodes in correct sort-order.
      return [x[1] for x in childNodes]


    ############################################################################
    ###  
    ###  Sort-Order
    ### 
    ############################################################################

    def normalizeSortIds(self, id_prefix='e'):
      """
      Normalizes sort-ids for all children with given prefix of this node.
      Always called on container after new node was added.
      E.g.: sort_ids:before=[10,15,20,30,40] => sort_ids:after=[10,20,30,40,50]
      @param id_prefix: the id-prefix.
      @type id_prefix: C{str='e'}
      """
      obs = [x for x in self.objectValues(list(self.dGlobalAttrs)) if standard.id_prefix(x.id)==id_prefix and x.__proxy__() is not None]
      obs = sorted(obs,key=lambda x:[1,1000][x.isPage()]*x.getSortId())
      [obs[x].setSortId((x+1)*10) for x in range(len(obs))]


    def getNewSortId(self):
      """
      Get new sort-id.
      @return: the new sort-id.
      @rtype: C{int}
      """
      new_sort_id = 0
      childNodes = self.getChildNodes()
      for ob in childNodes:
        sort_id = ob.getSortId()
        if sort_id > new_sort_id:
          new_sort_id = sort_id
        new_sort_id = new_sort_id + 10
      return new_sort_id


    ############################################################################
    #
    #   Module
    #
    ############################################################################

    def manage_addZMSCustomDefault(self, lang, id_prefix, _sort_id, REQUEST, RESPONSE):
      """
      Add default node.
      internal use only
      @param lang: the language-id.
      @type lang: C{str}
      @param id_prefix: the id-prefix.
      @type id_prefix: C{str}
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @param RESPONSE: the triggering request
      @type RESPONSE: C{ZPublisher.HTTPResponse}
      """
      attr = self.getMetaobjAttr( self.meta_id, id_prefix)
      zexp = attr[ 'custom']
      new_id = self.getNewId(id_prefix)
      _fileutil.import_zexp(self, zexp, new_id, id_prefix, _sort_id)
      
      # Return with message.
      message = self.getZMILangStr('MSG_INSERTED')%attr['name']
      RESPONSE.redirect('%s/%s/manage_main?lang=%s&manage_tabs_message=%s'%(self.absolute_url(), new_id, lang, standard.url_quote(message)))

    def manage_addZMSModule(self, lang, _sort_id, custom, REQUEST, RESPONSE):
      """
      Add module-node.
      internal use only
      @param lang: the language-id.
      @type lang: C{str}
      @param id_prefix: the id-prefix.
      @type id_prefix: C{str}
      @param REQUEST: the triggering request
      @type REQUEST: C{ZPublisher.HTTPRequest}
      @param RESPONSE: the triggering request
      @type RESPONSE: C{ZPublisher.HTTPResponse}
      """
      meta_id = self.getMetaobjId( custom)
      metaObj = self.getMetaobj( meta_id)
      key = self.getMetaobjAttrIds( meta_id)[0]
      attr = self.getMetaobjAttr( meta_id, key)
      zexp = attr[ 'custom']
      id_prefix = standard.id_prefix(REQUEST.get('id_prefix', 'e'))
      new_id = self.getNewId(id_prefix)
      _fileutil.import_zexp(self, zexp, new_id, id_prefix, _sort_id)
      
      # Return with message.
      message = self.getZMILangStr('MSG_INSERTED')%custom
      RESPONSE.redirect('%s/%s/manage_main?lang=%s&manage_tabs_message=%s'%(self.absolute_url(), new_id, lang, standard.url_quote(message)))

################################################################################
