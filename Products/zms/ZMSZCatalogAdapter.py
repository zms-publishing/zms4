#!/usr/bin/python
# -*- coding: utf-8 -*-

################################################################################
# _globals.py
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
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
import copy
import time
import zope.interface
# Product Imports.
from Products.zms import standard
from Products.zms import IZMSCatalogAdapter, IZMSConfigurationProvider
from Products.zms import ZMSItem


# ------------------------------------------------------------------------------
#  updateVersion:
# ------------------------------------------------------------------------------
def updateVersion(root):
  if not root.REQUEST.get('ZMSCatalogAdapter_updateVersion', False):
    root.REQUEST.set('ZMSCatalogAdapter_updateVersion', True)
    if root.getConfProperty('ZMS.catalog.build', 0) == 0:
      if len(root.getConnectors()) == 0:
        root.addConnector('ZMSZCatalogConnector')
      root.setConfProperty('ZMS.catalog.build', 1)
    elif root.getConfProperty('ZMS.catalog.build', 0) == 1:
      if not hasattr(root, '_attrs'):
        root._attrs = {}
        for attr_id in getattr(root, '_attr_ids', []):
          root._attrs[attr_id] = {'boost':1.0,'type':'text'}
        if hasattr(root, '_attr_ids'):
          delattr(root, '_attr_ids')
      root.setConfProperty('ZMS.catalog.build', 2)


# ------------------------------------------------------------------------------
#  remove_tags:
# ------------------------------------------------------------------------------
def remove_tags(self, s):
  d = {
    '&ndash;':'-',
    '&middot;': '.',
    '&nbsp;': ' ',
    '&ldquo;': '',
    '&sect;': '',
    '&Auml;': u'Ä',
    '&Ouml;': u'Ö',
    '&Uuml;': u'Ü',
    '&auml;': u'ä',
    '&ouml;': u'ö',
    '&uuml;': u'ü',
    '&szlig;': u'ß'}
  s = standard.pystr(s)
  for x in d:
    s = s.replace(x,d[x])
  s = standard.re_sub('<script(.*?)>(.|\\n|\\r|\\t)*?</script>', ' ', s)
  s = standard.re_sub('<style(.*?)>(.|\\n|\\r|\\t)*?</style>', ' ', s)
  s = standard.re_sub('<[^>]*>', ' ', s)
  while s.find('\t') >= 0:
    s = s.replace('\t', ' ')
  while s.find('\n') >= 0:
    s = s.replace('\n', ' ')
  while s.find('\r') >= 0:
    s = s.replace('\r', ' ')
  while s.find('  ') >= 0:
    s = s.replace('  ', ' ')
  s = s.strip()
  return s


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################

@zope.interface.implementer(
    IZMSConfigurationProvider.IZMSConfigurationProvider,
    IZMSCatalogAdapter.IZMSCatalogAdapter
)

class ZMSZCatalogAdapter(ZMSItem.ZMSItem):

    # Properties.
    # -----------
    meta_type = 'ZMSZCatalogAdapter'
    zmi_icon = "fas fa-search"
    icon_clazz = zmi_icon

    # Management Options.
    # -------------------
    manage_options_default_action = '../manage_customize'
    def manage_options(self):
      return [self.operator_setitem( x, 'action', '../'+x['action']) for x in copy.deepcopy(self.aq_parent.manage_options())]

    def manage_sub_options(self):
      return (
        {'label': 'TAB_SEARCH','action': 'manage_main'},
        )

    # Management Interface.
    # ---------------------
    manage = PageTemplateFile('zpt/ZMSZCatalogAdapter/manage_main', globals())
    manage_main = PageTemplateFile('zpt/ZMSZCatalogAdapter/manage_main', globals())

    # Management Permissions.
    # -----------------------
    __administratorPermissions__ = (
        'manage_changeProperties', 'manage_main', 'manage_reindex',
        )
    __ac_permissions__=(
        ('ZMS Administrator', __administratorPermissions__),
        )


    ############################################################################
    #  ZMSZCatalogAdapter.__init__:
    #
    #  Constructor.
    ############################################################################
    def __init__(self):
      self.id = 'zcatalog_adapter'


    # --------------------------------------------------------------------------
    #  ZMSZCatalogAdapter.search:
    # --------------------------------------------------------------------------
    def search(self, qs, order=None):
      rtn = []
      if len(qs) > 0:
        for connector in self.getConnectors():
          f = getattr(connector, 'search', None)
          if f is not None:
            rtn.extend(f(qs, order))
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSZCatalogAdapter.reindex_all:
    # --------------------------------------------------------------------------
    def reindex_all(self):
      try:
        for connector in self.getConnectors():
          connector.reindex_all()
        return True
      except:
        standard.writeError( self, "can't reindex_all")
        return False


    # --------------------------------------------------------------------------
    #  ZMSZCatalogAdapter.reindex_node:
    # --------------------------------------------------------------------------
    def reindex_node(self, node, forced=False):
      try:
        if self.getConfProperty('ZMS.CatalogAwareness.active', 1) or forced:
          for connector in self.getConnectors():
            # Check meta-id.
            nodes = node.breadcrumbs_obj_path()
            nodes.reverse()
            for node in nodes:
              if node.meta_id in self.getIds():
                connector.reindex_node(node)
                break
        return True
      except:
        standard.writeError( self, "can't reindex_node")
        return False



    # --------------------------------------------------------------------------
    #  ZMSZCatalogAdapter.ids: getter and setter
    # --------------------------------------------------------------------------
    def getIds(self):
      return getattr(self, '_ids', [])

    def setIds(self, ids):
      setattr(self, '_ids', ids)


    # --------------------------------------------------------------------------
    #  ZMSZCatalogAdapter.attr_ids: getter and setter
    # --------------------------------------------------------------------------
    def _getAttrIds(self):
      return ['home_id']+self.getAttrIds()

    def getAttrIds(self):
      return list(self.getAttrs())

    def setAttrIds(self, attr_ids):
      attrs = self.getAttrs()
      for attr_id in attr_ids:
        attrs[attr_id] = {'boost':1.0,'type':'text'}
      self.setAttrs(attrs)

    def getAttrs(self):
      return getattr(self, '_attrs', {})

    def setAttrs(self, attrs):
      setattr(self, '_attrs', attrs)


    # --------------------------------------------------------------------------
    #  ZMSZCatalogAdapter.getConnectorMetaTypes
    # --------------------------------------------------------------------------
    def getConnectorMetaTypes(self):
      return ['ZMSZCatalogConnector', 'ZMSZCatalogSolrConnector']


    # --------------------------------------------------------------------------
    #  ZMSZCatalogAdapter.getConnectors
    # --------------------------------------------------------------------------
    def getConnectors(self):
      updateVersion(self)
      return sorted(self.objectValues(self.getConnectorMetaTypes()),key=lambda x:x.id)


    # --------------------------------------------------------------------------
    #  ZMSZCatalogAdapter.addConnector
    # --------------------------------------------------------------------------
    def addConnector(self, meta_type):
      from Products.zms import _confmanager
      connector = _confmanager.ConfDict.forName(meta_type+'.'+meta_type)()
      self._setObject(connector.id, connector)
      return getattr(self, connector.id)


    # --------------------------------------------------------------------------
    #  ZMSZCatalogAdapter.get_sitemap
    #
    #  @param self
    #  @param  cb  callback
    # --------------------------------------------------------------------------
    def get_sitemap(self, cb, root, recursive):
      result = []
      request = self.REQUEST

      # Add node.
      def get_catalog_index(node):
        request.set('ZMS_CONTEXT_URL', True)
        d = {}
        d['id'] = node.id
        d['home_id'] = node.getHome().id
        d['loc'] = '/'.join(node.getPhysicalPath())
        d['index_html'] = node.getHref2IndexHtmlInContext(node.getRootElement(), REQUEST=request)
        d['meta_id'] = node.meta_id
        d['custom'] = d.get('custom', {})
        d['custom']['breadcrumbs'] = []
        for obj in [x for x in node.breadcrumbs_obj_path()[1:-1] if x.isPage()]:
          d['custom']['breadcrumbs'].append({
              '__nodeName__': 'breadcrumb',
              'loc': '/'.join(obj.getPhysicalPath()),
              'index_html': obj.getHref2IndexHtmlInContext(obj.getRootElement(), REQUEST=request),
              'title': obj.getTitlealt(request),
            })
        return d

      # Add node.
      def add_catalog_index(node, d):
        for k in d:
          v = d[k]
          if isinstance(v, dict):
            def to_xml(o):
              xml = ''
              if isinstance(o, list):
                for i in o:
                  xml += '<%s>'%i['__nodeName__']
                  xml += to_xml(i)
                  xml += '</%s>'%i['__nodeName__']
              elif isinstance(o, dict):
                for k in [x for x in o if x != '__nodeName__']:
                  xml += '<%s>'%k
                  xml += to_xml(o[k])
                  xml += '</%s>'%k
              else:
                xml = str(o)
              return xml
            d[k] = '<![CDATA[<%s>%s</%s>]]>'%(k, to_xml(v), k)
        lang = node.REQUEST.get('lang')
        d['id'] = '%s_%s'%(d['id'], lang)
        d['lang'] = lang
        for attr_id in self.getAttrIds():
          attr_type = self.getAttrs().get(attr_id, {}).get('type', 'string')
          value = ''
          try:
            value = node.attr(attr_id)
          except:
            msg = '[@%s.get_sitemap]: can\'t get attr \'%s.%s\' - see error-log for details'%(node.getHome().id, node.meta_id, attr_id)
            standard.writeError(self, msg)
            if msg not in result:
              result.append(msg)
          if attr_type in ['date', 'datetime']:
            value = self.getLangFmtDate(value, 'eng', 'ISO8601')
          if type(value) in [str, str]:
            value = str(value)
          d[attr_id] = remove_tags(self, value)
        cb(node, d)

      # Traverse tree.
      def traverse(node, recursive):
        l = []
        can_add = True
        if 'catalog_indexable' in self.getMetaobjAttrIds(node.meta_id):
          can_add = node.attr('catalog_indexable')
        if can_add:
          # Hook
          if 'catalog_index' in self.getMetaobjAttrIds(node.meta_id):
            for d in node.attr('catalog_index'):
              add_catalog_index(node, d)
              l.append(1)
          # Check meta-id.
          if node.meta_id in self.getIds():
            d = get_catalog_index(node)
            add_catalog_index(node, d)
            l.append(1)
        # Handle child-nodes.
        if recursive:
          for childNode in node.filteredChildNodes(request):
            l.extend(traverse(childNode, recursive))
        return l

      self.REQUEST.set('lang', self.REQUEST.get('lang', self.getPrimaryLanguage()))
      result.append('%i objects cataloged'%len(traverse(root, recursive)))
      return ', '.join([x for x in result if x])


    ############################################################################
    #  ZMSZCatalogAdapter.manage_reindex:
    #
    #  Reindex.
    ############################################################################
    def manage_reindex(self, uid, REQUEST, RESPONSE):
        """ ZMSZCatalogAdapter.manage_reindex """
        result = []
        t0 = time.time()
        for connector in self.getConnectors():
          result.append(connector.reindex_self(uid))
        result.append('done!')
        return ', '.join([x for x in result if x])+' (in '+str(int((time.time()-t0)*100.0)/100.0)+' secs.)'


    ############################################################################
    #  ZMSZCatalogAdapter.manage_changeProperties:
    #
    #  Change properties.
    ############################################################################
    def manage_changeProperties(self, btn, lang, REQUEST, RESPONSE):
        """ ZMSZCatalogAdapter.manage_changeProperties """
        message = ''
        ids = REQUEST.get('objectIds', [])

        # Delegate to connectors.
        # -----------------------
        for connector in self.getConnectors():
          if self.getConfProperty('zms.search.adapter.id', self.id)==self.id:
            self.setConfProperty('zms.search.connector.id', connector.id)
          message += connector.manage_changeProperties(connector.id in ids, btn, lang, REQUEST)

        # Add.
        # ----
        if btn == 'Add':
          meta_type = REQUEST['meta_type']
          connector = self.addConnector(meta_type)
          message += 'Added '+meta_type

        # Save.
        # -----
        elif btn == 'Save':
          self.setConfProperty('ZMS.CatalogAwareness.active', REQUEST.get('catalog_awareness_active')==1)
          self._ids = REQUEST.get('ids', [])
          attrs = {}
          for attr_id in REQUEST.get('attr_ids', []):
            attrs[attr_id] = {'boost':float(REQUEST.get('boost_%s'%attr_id, '1.0')),'type':REQUEST.get('type_%s'%attr_id, 'text')}
          self.setAttrs(attrs)
          message += self.getZMILangStr('MSG_CHANGED')

        # Remove.
        # -------
        elif btn == 'Remove':
          if len(ids) > 0:
            self.manage_delObjects(ids)
            message += self.getZMILangStr('MSG_DELETED')%len(ids)

        # Return with message.
        message = standard.url_quote(message)
        return RESPONSE.redirect('manage_main?lang=%s&manage_tabs_message=%s#%s'%(lang, message, REQUEST.get('tab')))

################################################################################

