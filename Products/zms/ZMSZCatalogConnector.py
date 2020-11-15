################################################################################
# ZMSZCatalogConnector.py
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
from Products.ZCatalog import ZCatalog
from zope.interface import implementer
import copy
import sys
import time
import zExceptions
# Product Imports.
from Products.zms import standard
from Products.zms import IZMSCatalogConnector
from Products.zms import ZMSZCatalogAdapter
from Products.zms import ZMSItem
from Products.zms import _globals


extra_column_ids = ['loc', 'index_html', 'custom']


# ------------------------------------------------------------------------------
#  ZMSZCatalogConnector.umlaut_quote:
# ------------------------------------------------------------------------------
def umlaut_quote(self, v):
  if int(self.getConfProperty('ZMSZCatalogConnector.umlaut_quote', 0)):
    return standard.umlaut_quote(v)
  return v


# ------------------------------------------------------------------------------
#  ZMSZCatalogConnector.intValue:
# ------------------------------------------------------------------------------
def intValue(v):
  try:
    i = int(v)
  except:
    i = 0
  return i


# ------------------------------------------------------------------------------
#  ZMSZCatalogConnector.Empty:
# ------------------------------------------------------------------------------
class Empty(object): 
  pass


# ------------------------------------------------------------------------------
#  ZMSZCatalogConnector.addLexicon:
# ------------------------------------------------------------------------------
def addLexicon( container, cat):
  
  # Remove Lexicon
  ids = cat.objectIds( ['ZCTextIndex Lexicon', 'ZCTextIndex Unicode Lexicon'])
  if len( ids) > 0:
    cat.manage_delObjects( ids)
  
  # Add Lexicon
  index_type = container.getConfProperty('ZCatalog.TextIndexType', 'ZCTextIndex')
  if index_type == 'ZCTextIndex':
    elements = []
    wordSplitter = Empty()
    wordSplitter.group = 'Word Splitter'
    wordSplitter.name = 'HTML aware splitter'
    elements.append(wordSplitter)
    caseNormalizer = Empty()
    caseNormalizer.group = 'Case Normalizer'
    caseNormalizer.name = 'Case Normalizer'
    elements.append(caseNormalizer)
    stopWords = Empty()
    stopWords.group = 'Stop Words'
    stopWords.name = 'Remove listed and single char words'
    elements.append(stopWords)
    try:
      cat.manage_addProduct['ZCTextIndex'].manage_addLexicon('Lexicon', 'Default lexicon', elements)
    except:
      pass


# ------------------------------------------------------------------------------
#  ZMSZCatalogConnector.getZCatalog:
# ------------------------------------------------------------------------------
def getZCatalog(self, lang):
  cat_id = 'catalog_%s'%lang
  root = self.getRootElement()
  if root != self and cat_id in self.objectIds():
    self.manage_delObjects([cat_id])
  zcatalog = getattr(root, cat_id, None)
  return zcatalog


# ------------------------------------------------------------------------------
#  ZMSZCatalogConnector.writeChangesLog:
# ------------------------------------------------------------------------------
def writeChangesLog(zcatalog, info):
  if not zcatalog.hasProperty('changes_log'):
    zcatalog.manage_addProperty('changes_log', '', 'text')
  changes_log = zcatalog.getProperty('changes_log')
  changes_log += '\n' + zcatalog.getLangFmtDate(time.time(), 'eng') + ' ' + zcatalog.writeBlock(info)
  zcatalog.manage_changeProperties({'changes_log':changes_log})


# ------------------------------------------------------------------------------
#  ZMSZCatalogConnector.recreateCatalog:
# ------------------------------------------------------------------------------
def recreateCatalog(self, zcm, lang):
  
  #-- Create catalog
  cat_id = 'catalog_%s'%lang
  if cat_id in self.objectIds():
    self.manage_delObjects([cat_id])
  cat_title = 'Default catalog'
  zcatalog = ZCatalog.ZCatalog(id=cat_id, title=cat_title, container=self)
  self._setObject(zcatalog.id, zcatalog)
  zcatalog = getZCatalog(self, lang)
  writeChangesLog(zcatalog, '[recreateCatalog]: '+self.getZMILangStr('MSG_INSERTED')%zcatalog.meta_type)
  
  #-- Add lexicon
  addLexicon( self, zcatalog)
  
  #-- Add columns
  for index_name in ['id', 'meta_id']+['zcat_column_%s'%x for x in extra_column_ids]:
    zcatalog.manage_addColumn(index_name)
  
  #-- Add Indexes (incl. Columns)
  for attr_id in zcm._getAttrIds():
    index_name = 'zcat_index_%s'%attr_id
    index_type = zcm.getConfProperty('ZCatalog.TextIndexType','ZCTextIndex')
    if attr_id == 'home_id':
      index_type = 'KeywordIndex'
    extra = None
    if index_type == 'ZCTextIndex':
      extra = Empty()
      extra.doc_attr = index_name
      extra.index_type = 'Okapi BM25 Rank'
      extra.lexicon_id = 'Lexicon'
    elif index_type != 'KeywordIndex':
      extra = {}
      extra['default_encoding'] = 'utf-8'
      extra['indexed_fields'] = index_name
      extra['fields'] = [index_name]
      extra['near_distance'] = 5
      extra['splitter_casefolding'] = 1
      extra['splitter_max_len'] = 64
      extra['splitter_separators'] = '.+-_@'
      extra['splitter_single_chars'] = 0
      if index_type == 'TextIndexNG2':
        extra['use_converters'] = 1
        extra['use_normalizer'] = ''
        # setattr(index_extra,'use_stemmer','')
        extra['use_stopwords'] = ''
      elif index_type == 'TextIndexNG3':
        extra['languages'] = (lang,)
        extra['query_parser'] = 'txng.parsers.en'
        extra['index_unknown_languages'] = True
        extra['dedicated_storage'] = True
        extra['use_stopwords'] = False
        extra['use_normalizer'] = False
        extra['use_converters'] = True
        extra['use_stemmer'] = False
    zcatalog.manage_addColumn(index_name)
    zcatalog.manage_addIndex(index_name, index_type, extra)


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
@implementer(
        IZMSCatalogConnector.IZMSCatalogConnector)
class ZMSZCatalogConnector(
        ZMSItem.ZMSItem):

    # Properties.
    # -----------
    meta_type = 'ZMSZCatalogConnector'
    icon = "++resource++zms_/img/ZCatalog.png"
    icon_clazz = "icon-search"

    # Management Interface.
    # ---------------------
    manage_input_form = PageTemplateFile('zpt/ZMSZCatalogAdapter/manage_zcatalog_connector', globals())

    # Management Permissions.
    # -----------------------
    __administratorPermissions__ = (
        'manage_changeProperties', 'manage_main',
        )
    __ac_permissions__=(
        ('ZMS Administrator', __administratorPermissions__),
        )

    ############################################################################
    #  ZMSZCatalogConnector.__init__: 
    #
    #  Constructor.
    ############################################################################
    def __init__(self):
      self.id = 'zcatalog_connector'


    # --------------------------------------------------------------------------
    #  ZMSZCatalogConnector.search_xml:
    # --------------------------------------------------------------------------
    def search_xml(self, q, page_index=0, page_size=10, REQUEST=None, RESPONSE=None):
      """ ZMSZCatalogConnector.search_xml """
      # Check constraints.
      page_index = int(page_index)
      page_size = int(page_size)
      REQUEST.set('lang', REQUEST.get('lang', self.getPrimaryLanguage()))
      RESPONSE = REQUEST.RESPONSE
      content_type = 'text/xml;charset=utf-8'
      RESPONSE.setHeader('Content-Type', content_type)
      RESPONSE.setHeader('Cache-Control', 'no-cache')
      RESPONSE.setHeader('Pragma', 'no-cache')
      RESPONSE.setHeader('Access-Control-Allow-Origin', '*')
      # Execute query.
      status = 0
      msg = ''
      results = []
      try: 
        results = self.search(q, REQUEST.get('fq[]', ''))
      except:
        standard.writeError(self, '[search_xml]')
        t, v, tb = sys.exc_info()
        status = 400
        msg = v
      # Assemble xml.
      xml = self.getXmlHeader()
      xml += '<response>'
      xml += '<lst name="responseHeader">'
      xml += '<int name="status">%i</int>'%status
      xml += '<lst name="params">'
      for key in REQUEST.form.keys():
        xml += '<str name="%s">%s</str>'%(key, standard.html_quote(REQUEST.form[key]))
      xml += '</lst>'
      xml += '</lst>'
      xmlr = ''
      if status <= 0:
        xmlr += '<result name="response" numFound="%i" start="%i">'%(len(results), page_index*page_size)
        if len(results) > page_size:
          results = results[page_index*page_size:(page_index+1)*page_size]
        for result in results:
          xmlr += '<doc>'
          for k in result.keys():
            try:
              v = result[k]
              if k == 'zcat_column_loc':
                k = 'loc'
              elif k == 'zcat_column_index_html':
                k = 'index_html'
              elif k == 'zcat_column_custom':
                k = 'custom'
              elif k == 'standard_html':
                v = ZMSZCatalogAdapter.remove_tags(self, v)
              xmlr += '<arr name="%s">'%k
              if isinstance(v,str):
                for x in range(16):
                  v = v.replace(chr(x), '')
              if k == 'custom':
                xmlr += '<str>%s</str>'%v
              else:
                xmlr += '<str><![CDATA[%s]]></str>'%v
              xmlr += '</arr>'
            except:
              standard.writeError(self, '[search_xml]: result=%s, k=%s'%(str(result), k))
              t, v, tb = sys.exc_info()
              status = 400
              msg = v
              break
          xmlr += '</doc>'
        xmlr += '</result>'
      if status > 0:
        xmlr = ''
        xmlr += '<lst name="error">'
        xmlr += '<str name="msg">%s</str>'%standard.html_quote(msg)
        xmlr += '<int name="code">%i</int>'%status
        xmlr += '</lst>'
      xml += standard.pystr(xmlr)
      xml += '</response>'
      return xml


    # --------------------------------------------------------------------------
    #  ZMSZCatalogConnector.suggest_xml:
    # --------------------------------------------------------------------------
    def suggest_xml(self, q, fq='', limit=5, REQUEST=None, RESPONSE=None):
      """ ZMSZCatalogConnector.suggest_xml """
      # Check constraints.
      REQUEST.set('lang', REQUEST.get('lang', self.getPrimaryLanguage()))
      RESPONSE = REQUEST.RESPONSE
      content_type = 'text/xml;charset=utf-8'
      RESPONSE.setHeader('Content-Type', content_type)
      RESPONSE.setHeader('Cache-Control', 'no-cache')
      RESPONSE.setHeader('Pragma', 'no-cache')
      # Execute query.
      status = 0
      msg = ''
      results = []
      try: 
        results = self.suggest(q, limit)
      except:
        standard.writeError(self, '[suggest_xml]')
        t, v, tb = sys.exc_info()
        status = 400
        msg = v
      # Assemble xml.
      xml = self.getXmlHeader()
      xml += '<response>'
      xml += '<lst name="responseHeader">'
      xml += '<int name="status">%i</int>'%status
      xml += '</lst>'
      if status > 0:
        xml += '<lst name="error">'
        xml += '<int name="msg">%s</int>'%msg
        xml += '<int name="code">%i</int>'%status
        xml += '</lst>'
      else:
        xml += '<lst>'
        xml += '<lst name="suggestions">'
        xml += '<int name="numFound">%i</int>'%len(results)
        xml += '<arr name="suggestion">'
        for result in results:
          xml += '<str>%s</str>'%result
        xml += '</arr>'
        xml += '</lst>'
        xml += '</lst>'
      xml += '</response>'
      return xml


    # --------------------------------------------------------------------------
    #  ZMSZCatalogConnector.search:
    # --------------------------------------------------------------------------
    def search(self, q, fq='', order=None):
      rtn = []
      
      # ZCatalog.
      request = self.REQUEST
      lang = request.get('lang', self.getPrimaryLanguage())
      zcatalog = getZCatalog(self, lang)
      
      # Find search-results.
      items = []
      prototype = {}
      for fqs in fq.split(','):
        attr_id = fqs[:fqs.find(':')]
        if attr_id.endswith('_s'):
          attr_id = attr_id[:-2]
        fqk = 'zcat_index_%s'%attr_id
        if fqk in zcatalog.indexes():
          fqv = fqs[fqs.find(':')+1:]
          fqv = umlaut_quote(self, fqv)
          prototype[fqk] = fqv
      for index in zcatalog.indexes():
        if index.find('zcat_index_')==0:
          query = copy.deepcopy(prototype)
          query[index] = umlaut_quote(self, q)
          qr = zcatalog(query)
          standard.writeLog( self, "[search]: %s=%i"%(str(query), len(qr)))
          for item in qr:
            if item not in items:
              items.append( item.aq_base )
      
      # Process search-results.
      results = []
      for item in items:
        data_record_id = item.data_record_id_
        path = zcatalog.getpath(data_record_id)
        # Append to valid results.
        if len([x for x in results if x[1]['path']==path]) == 0:
          result = {}
          result['path'] = path
          result['score'] = intValue(item.data_record_score_)
          result['normscore'] = intValue(item.data_record_normalized_score_)
          for column in zcatalog.schema():
            k = column
            if k.find('zcat_index_')==0:
              k = k[len('zcat_index_'):]
            result[k] = getattr(item, column, None)
          results.append((item.data_record_score_, result))
      
      # Sort search-results.
      results = sorted( results, key=lambda x: x[0])
      results.reverse()
      
      # Append search-results.
      rtn.extend([x[1] for x in results])
      
      # Return list of search-results in correct sort-order.
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSZCatalogConnector.suggest:
    # --------------------------------------------------------------------------
    def suggest(self, q, limit=5):
      rtn = []
      
      # ZCatalog.
      request = self.REQUEST
      lang = request.get('lang', self.getPrimaryLanguage())
      zcatalog = getZCatalog(self, lang)
      
      # Lexicon.
      lexicon = zcatalog.Lexicon
      for w in lexicon.words():
        if w[0] not in ['_', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] and w.lower().find(q) >= 0 and w not in rtn:
          rtn.append(w)
        if len(rtn) >= limit:
          break
      
      # Return list of suggestions.
      return rtn


    # --------------------------------------------------------------------------
    #  ZMSZCatalogConnector._update:
    # --------------------------------------------------------------------------
    def _update(self, node, d):
      zcm = self.getCatalogAdapter()
      # Prepare object.
      for attr_id in extra_column_ids:
        attr_name = 'zcat_column_%s'%attr_id
        value = d.get(attr_id)
        setattr(node, attr_name, value)
      for attr_id in zcm._getAttrIds():
        last_id = attr_id
        attr_name = 'zcat_index_%s'%attr_id
        value = umlaut_quote(self, d.get(attr_id))
        setattr(node, attr_name, value)
      # Reindex object.
      request = self.REQUEST
      lang = request.get('lang', self.getPrimaryLanguage())
      zcatalog = getZCatalog(self, lang)
      if zcatalog is not None:
        path = node.getPath()
        if zcatalog.getrid(path):
          zcatalog.uncatalog_object(path)
        zcatalog.catalog_object(node, path)
      # Unprepare object.
      for attr_id in extra_column_ids:
        attr_name = 'zcat_column_%s'%attr_id
        delattr(node, attr_name)
      for attr_id in zcm._getAttrIds():
        attr_name = 'zcat_index_%s'%attr_id
        delattr(node, attr_name)
      # premature commit
      req_key = 'ZMSZCatalogConnector._update.transaction_count'
      cfg_key = 'ZMSZCatalogConnector._update.transaction_size'
      if request.get(req_key, 0)>=int(self.getConfProperty(cfg_key, 999)):
        import transaction
        transaction.commit()
      request.set(req_key, request.get(req_key, 0)+1)



    # --------------------------------------------------------------------------
    #  ZMSZCatalogConnector.reindex_all:
    # --------------------------------------------------------------------------
    def reindex_all(self):
      result = []
      zcm = self.getCatalogAdapter()
      request = self.REQUEST
      container = self.getDocumentElement()
      for lang in container.getLangIds():
        request.set('lang', lang)
        # Recreate catalog.
        result.append(recreateCatalog(container, self.aq_parent, lang))
        # Reindex items to catalog.
        def cb(node, d):
          self._update(node, d)
        for root in [container]+self.getPortalClients():
          result.append(zcm.get_sitemap(cb, root, recursive=True))
      result = [x for x in result if x]
      return ', '.join([x for x in result])


    # --------------------------------------------------------------------------
    #  ZMSZCatalogConnector.reindex_self:
    # --------------------------------------------------------------------------
    def reindex_self(self, uid):
      result = []
      zcm = self.getCatalogAdapter()
      request = self.REQUEST
      request.set('btn', 'Reindex') # backwards-compatibility (UzK)
      container = self.getLinkObj(uid)
      home_id = container.getHome().id
      try:
        langs = request.get('langs', ';'.join(container.getLangIds())).split(';')
        for lang in langs:
          request.set('lang', lang)
          lresult = []
          lresult.append('language: %s'%lang)
          # Clear catalog.
          zcatalog = getZCatalog(self, lang)
          if zcatalog is None:
            lresult.append(recreateCatalog(container, self.aq_parent, lang))
          else:
            qr = zcatalog({'zcat_index_home_id':home_id})
            lresult.append('%i objects removed from catalog'%len(qr))
            for item in qr:
              data_record_id = item.data_record_id_
              path = zcatalog.getpath(data_record_id)
              zcatalog.uncatalog_object(path)
          # Reindex items to catalog.
          def cb(node, d):
            self._update(node, d)
          lresult.append(zcm.get_sitemap(cb, container, recursive=True))
          lresult = [x for x in lresult if x]
          result.extend(lresult)
          # Log changes.
          zcatalog = getZCatalog(self, lang)
          writeChangesLog(zcatalog, '[reindex_self]: '+'\n'.join([x for x in lresult]))
      except:
        result.append(standard.writeError(self, 'can\'t reindex_self'))
      return ', '.join([x for x in result if x])


    # --------------------------------------------------------------------------
    #  ZMSZCatalogConnector.reindex_node:
    # --------------------------------------------------------------------------
    def reindex_node(self, node):
      node.writeLog('[ZMSZCatalogConnector.reindex_node]')
      zcm = self.getCatalogAdapter()
      # Reindex item to catalog.
      def cb(node, d):
        self._update(node, d)
      zcm.get_sitemap(cb, node, recursive=False)


    def get_sitemap(self):
      """
      Returns sitemap.
      @rtype: C{str}
      """
      zcm = self.getCatalogAdapter()
      request = self.REQUEST
      RESPONSE = request.RESPONSE
      RESPONSE.setHeader('Content-Type', 'text/plain; charset=utf-8')
      l = []
      def cb(node, d):
        l.append(d)
      zcm.get_sitemap(cb, self.getDocumentElement(), recursive=True)
      return self.str_json(l)


    ############################################################################
    #  ZMSZCatalogConnector.manage_changeProperties:
    #
    #  Change properties.
    ############################################################################
    def manage_changeProperties(self, selected, btn, lang, REQUEST):
        message = ''
        
        # Remove.
        # -------
        if btn == 'Remove':
          ids = REQUEST.get('zcatalog_objectIds', [])
          if len(ids) > 0:
            self.getDocumentElement().manage_delObjects(ids)
            message += self.getZMILangStr('MSG_DELETED')%len(ids)
        
        return message

################################################################################
