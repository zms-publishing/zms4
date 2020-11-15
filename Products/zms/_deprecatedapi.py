################################################################################
# _deprecated.py
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
import tempfile
# Product Imports.
from Products.zms import _fileutil
from Products.zms import _xmllib
from Products.zms import standard


def warn(self,old,new=None):
  import warnings
  warnings.warn('Using <%s@%s>.%s() is deprecated.'
               ' Use %s() instead.'%(self.meta_id, self.absolute_url(), old, [old, new][new is not None]),
                 DeprecationWarning, 
                 stacklevel=2)

################################################################################
################################################################################
###
###   class DeprecatedAPI:
###
################################################################################
################################################################################
class DeprecatedAPI(object):

  f_bo_area = '' 
  f_eo_area = '' 
  f_submitBtn = '' 

  def f_bodyContent(self, *args, **kwargs):
    warn(self, 'f_bodyContent', 'None')
    request = self.REQUEST 
    response = request.RESPONSE
    return self.getBodyContent(request)

  def zmi_form_section_begin(self, *args, **kwargs):
    warn(self, 'zmi_form_section_begin', 'None')
    return ''

  def zmi_form_section_end(self, *args, **kwargs):
    warn(self, 'zmi_form_section_end', 'None')
    return ''

  def f_selectInput(self, *args, **kwargs):
    warn(self, 'f_selectInput', 'getSelect')
    return here.getSelect(fmName=kwargs['fmName'], elName=kwargs['elName'], value=kwargs['value'], inputtype=kwargs['inputtype'], lang_str=kwargs['lang_str'], required=kwargs['required'], optpl=kwargs['optpl'], enabled=kwargs['enabled'])

  def f_headline(self, *args, **kwargs):
    warn(self, 'f_headline', 'None')
    return '<h2>%s</h2><div>%s</div>'%(kwargs.get('headline', ''), kwargs.get('extra', '')) 

  def getTitleimage( self, REQUEST): 
    warn(self, 'getTitleimage(REQUEST)', 'attr(\'titleimage\')')
    return self.getObjProperty('titleimage', REQUEST) 

  def getImage(self, REQUEST):
    warn(self, 'getImage(REQUEST)', 'attr(\'img\')')
    return self.getObjProperty('img', REQUEST)

  def getFile(self, REQUEST):
    warn(self, 'getFile(REQUEST)', 'attr(\'file\')')
    return self.getObjProperty('file', REQUEST)

  def getFormat(self, REQUEST):
    warnings.warn("[getFormat]: @deprecated: returns \"getObjProperty('format',REQUEST)\" for compatibility reasons!")
    return self.getObjProperty('format', REQUEST)

  def meta_id_or_type(self):
    warn(self, 'meta_id_or_type', 'meta_id')
    return self.meta_id

  def absolute_obj_path(self):
    warn(self, 'absolute_obj_path', 'None')
    ob = self.getDocumentElement()
    return '%s/%s/'%(ob.aq_parent.id, self.absolute_url()[len(ob.aq_parent.absolute_url())+1:])

  """
  Resolves internal/external links and returns Html. 
  """
  def getLinkHtml( self, url, html='<a href="%s">&raquo;</a>', REQUEST=None): 
    warn(self, 'getLinkHtml', '@deprecated: use own implementation!')
    REQUEST = standard.nvl( REQUEST, self.REQUEST) 
    s = '' 
    ob = self 
    while ob is not None: 
      if html in ob.getMetaobjIds() and 'getLinkHtml' in ob.getMetaobjAttrIds(html):
        REQUEST.set( 'ref_id', url) 
        return ob.evalMetaobjAttr('%s.getLinkHtml'%html,ref_id=url)
      ob = ob.getPortalMaster() 
    ob = self.getLinkObj(url) 
    if ob is not None: 
      if ob.isVisible(REQUEST): 
        url = ob.getHref2IndexHtml(REQUEST) 
        s = html%url 
    return s 


  # --------------------------------------------------------------------------
  #  DeprecatedAPI.ZCatalogItem:
  # --------------------------------------------------------------------------
  def search_quote(self, s, maxlen=255, tag='&middot;'):
    warn(self, 'search_quote', 'Products.zms.standard.string_maxlen')
    return standard.string_maxlen(s, maxlen, etc=tag*3)

  def search_encode(self, s):
    warn(self, 'search_encode', 'Products.zms.standard.umlaut_quote')
    return standard.umlaut_quote(s)

  def getCatalogNavUrl(self, REQUEST):
    warn(self, 'getCatalogNavUrl', 'None')
    return self.url_inherit_params(REQUEST['URL'], REQUEST, ['qs'])


  # --------------------------------------------------------------------------
  #  DeprecatedAPI.ZMSGlobals:
  # --------------------------------------------------------------------------
  """
  Replace special characters in string for javascript.
  """
  def js_quote(self, text, charset=None):
    warn(self, 'js_quote', 'None')
    if isinstance(text, str):
      text= text.encode([charset, 'utf-8'][charset==None])
    text = text.replace("\r", "\\r").replace("\n", "\\n")
    text = text.replace('"', '\\"').replace("'", "\\'")
    return text

  def zmi_manage_css(self, *args, **kwargs):
    """ ZMSItem.zmi_manage_css """
    warn(self, 'zmi_manage_css', 'None')
    request = self.REQUEST
    response = request.RESPONSE
    response.setHeader('Content-Type', 'text/css')
    css = []
    for stylesheet in self.getStylesheets():
      try:
        s = stylesheet(self)
      except:
        s = bytes(stylesheet).decode()
      css.append("/* ######################################################################")
      css.append("   ### %s"%stylesheet.absolute_url())
      css.append("   ###################################################################### */")
      css.append(s)
    return '\n'.join(css)

  """
  Parses default-stylesheet and returns elements.
  @deprecated
  @return: Elements
  @rtype: C{dict}
  """
  def parse_stylesheet(self):
    warn(self, 'parse_stylesheet', 'None')
    stylesheet = self.getStylesheet()
    if stylesheet.meta_type in ['DTML Document', 'DTML Method']:
      data = stylesheet.raw
    elif stylesheet.meta_type in ['File']:
      data = stylesheet.data
    data = re.sub( '/\*(.*?)\*/', '', data)
    value = {}
    for elmnt in data.split('}'):
      i = elmnt.find('{')
      keys = elmnt[:i].strip()
      v = elmnt[i+1:].strip()
      for key in keys.split(','):
        key = key.strip()
        if len(key) > 0:
          value[key] = value.get(key, '') + v
    colormap = {}
    for key in value:
      if key.startswith('.') and \
         key.find('Color') > 0 and \
         key.find('.cms') < 0 and \
         key.find('.zmi') < 0:
        for elmnt in value[key].split(';'):
          i = elmnt.find(':')
          if i > 0:
            elmntKey = elmnt[:i].strip().lower()
            elmntValue = elmnt[i+1:].strip().lower()
            if elmntKey == 'color' or elmntKey == 'background-color':
              colormap[key[1:]] = elmntValue
    self.setConfProperty('ZMS.colormap', colormap)
    return colormap

  def get_colormap(self):
    warn(self, 'get_colormap', 'None')
    colormap = self.getConfProperty('ZMS.colormap', None)
    if colormap is None:
      try:
        colormap = self.parse_stylesheet()
      except:
        # Destroy Colormap on Error
        colormap = {}
        self.setConfProperty('ZMS.colormap', colormap)
    return colormap

  """
  Returns parents for linked list.
  @rtype: C{list}
  """
  def tree_parents(self, l, i='id', r='idId', v='', deep=1, reverse=1):
    warn(self, 'tree_parents', 'None')
    k = []
    for x in l:
      if x.get(i)==v:
        k.append(x)
        if deep:
          k.extend(self.tree_parents(l, i, r, x[r], deep, 0))
    if reverse:
      k.reverse()
    return k

  """
  Returns children for linked list.
  @rtype: C{list}
  """
  def tree_list(self, l, i='id', r='idId', v='', deep=0):
    warn(self, 'tree_list', 'None')
    k = []
    for x in l:
      if x.get(r)==v:
        k.append(x)
        if deep:
          k.extend(self.tree_list(l, i, r, x[i], deep))
    return k

  def string_maxlen(self, s, maxlen=20, etc='...', encoding=None):
    warn(self, 'string_maxlen', 'Products.zms.standard.string_maxlen')
    return standard.string_maxlen(s, maxlen, etc, encoding)

  def get_id_prefix(self, s):
    warn(self, 'get_id_prefix', 'Products.zms.standard.id_prefix')
    return standard.id_prefix(s)

  def id_quote(self, s, mapping={'\x20': '_', '-': '_', '/': '_',}):
    warn(self, 'id_quote', 'Products.zms.standard.id_quote')
    return standard.id_quote(s, mapping)

  def parseLangFmtDate(self, s, lang=None, fmt_str=None, recflag=None):
    warn(self, 'parseLangFmtDate', 'Products.zms.standard.parseLangFmtDate')
    return standard.parseLangFmtDate(s)

  def compareDate(self, t0, t1):
    warn(self, 'compareDate', 'Products.zms.standard.compareDate')
    return standard.compareDate(t0, t1) 

  def daysBetween(self, t0, t1):
    warn(self, 'daysBetween', 'Products.zms.standard.daysBetween')
    return standard.daysBetween(t0, t1) 

  def encrypt_ordtype(self, s):
    warn(self, 'encrypt_ordtype', 'Products.zms.standard.encrypt_ordtype')
    return standard.encrypt_ordtype(s)

  def encrypt_password(self, pw, algorithm='md5', hex=False):
    warn(self, 'encrypt_password', 'Products.zms.encrypt_password')
    return standard.encrypt_password(pw, algorithm, hex)

  def encrypt_schemes(self):
    warn(self, 'encrypt_schemes', 'Products.zms.encrypt_schemes')
    return standard.encrypt_schemes()

  def nvl(self, a1, a2, n=None):
    warn(self, 'nvl', 'Products.zms.standard.nvl')
    return standard.nvl( a1, a2, n)

  def rand_int(self, n):
    warn(self, 'rand_int', 'Products.zms.standard.rand_int')
    return standard.rand_int(n)

  def re_findall( self, pattern, text, ignorecase=False):
    warn(self, 're_findall', 'Products.zms.standard.re_findall')
    return standard.re_findall(pattern, text, ignorecase)

  def re_search( self, pattern, subject, ignorecase=False):
    warn(self, 're_search', 'Products.zms.standard.re_search')
    return standard.re_search(pattern, subject, ignorecase)

  def re_sub( self, pattern, replacement, subject, ignorecase=False):
    warn(self, 're_sub', 'Products.zms.standard.re_sub')
    return standard.re_sub(pattern, replacement, subject, ignorecase)

  def operator_gettype(self, v):
    warn(self, 'operator_gettype', 'Products.zms.standard.operator_gettype')
    return standard.operator_gettype(v)
  
  def operator_setitem(self, a, b, c):
    warn(self, 'operator_setitem', 'Products.zms.standard.operator_setitem')
    return standard.operator_setitem(a, b, c)
  
  def operator_getitem(self, a, b, c=None, ignorecase=True):
    warn(self, 'operator_getitem', 'Products.zms.standard.operator_getitem')
    return standard.operator_getitem(a, b, c, ignorecase)
  
  def operator_delitem(self, a, b):
    warn(self, 'operator_delitem', 'Products.zms.standard.operator_delitem')
    return standard.operator_delitem(a, b)
  
  def operator_setattr(self, a, b, c):
    warn(self, 'operator_setattr', 'Products.zms.standard.operator_setattr')
    return standard.operator_setattr(a, b, c)
  
  def operator_getattr(self, a, b, c=None):
    warn(self, 'operator_getattr', 'Products.zms.standard.operator_getattr')
    return standard.operator_getattr(a, b, c)
  
  def operator_delattr(self, a, b):
    warn(self, 'operator_delattr', 'Products.zms.standard.operator_delattr')
    return standard.operator_delattr(a, b)
  
  def intersection_list(self, l1, l2):
    warn(self, 'intersection_list', 'Products.zms.standard.intersection_list')
    return standard.intersection_list(l1, l2)

  def difference_list(self, l1, l2):
    warn(self, 'difference_list', 'Products.zms.standard.difference_list')
    return standard.difference_list(l1, l2)

  def concat_list(self, l1, l2):
    warn(self, 'concat_list', 'Products.zms.standard.concat_list')
    return standard.concat_list(l1, l2)

  def dict_list(self, l):
    warn(self, 'dict_list', 'Products.zms.standard.dict_list')
    return standard.dict_list(l)

  def distinct_list(self, l, i=None):
    warn(self, 'distinct_list', 'Products.zms.standard.distinct_list')
    return standard.distinct_list(l, i)

  def sort_list(self, l, qorder=None, qorderdir='asc', ignorecase=1): 
    warn(self, 'sort_list', 'Products.zms.standard.sort_list')
    return standard.sort_list(l, qorder, qorderdir, ignorecase)

  def string_list(self, s, sep='\n', trim=True):
    warn(self, 'string_list', 'Products.zms.standard.string_list')
    return standard.string_list(s, sep, trim)

  def str_json(self, i, encoding='ascii', errors='xmlcharrefreplace', formatted=False, level=0):
    warn(self,'str_json','Products.zms.standard.str_json')
    import json
    return json.dumps(i)

  def str_item(self, i):
    warn(self, 'str_item', 'Products.zms.standard.str_item')
    return standard.str_item(i)

  def filter_list(self, l, i, v, o='%'):
    warn(self, 'filter_list', 'Products.zms.standard.filter_list')
    return standard.filter_list(l, i, v, o)

  def copy_list(self, l):
    warn(self, 'copy_list', 'Products.zms.standard.copy_list')
    return standard.copy_list(l)

  def sync_list(self, l, nl, i):
    warn(self, 'sync_list', 'Products.zms.standard.sync_list')
    return standard.sync_list(l, nl, i)

  def aggregate_list(self, l, i):
    warn(self, 'aggregate_list', 'Products.zms.standard.aggregate_list')
    return standard.aggregate_list(l, i)

  def url_append_params(self, url, dict, sep='&amp;'):
    warn(self, 'url_append_params', 'Products.zms.standard.url_append_params')
    return standard.url_append_params(url, dict, sep)

  def url_inherit_params(self, url, REQUEST, exclude=[], sep='&amp;'):
    warn(self, 'url_inherit_params', 'Products.zms.standard.url_inherit_params')
    return standard.url_inherit_params(url, REQUEST, exclude, sep)

  def getZipArchive(self, f):
    warn(self, 'getZipArchive', 'None')
    return _fileutil.getZipArchive(f)

  def extractZipArchive(self, f):
    warn(self, 'extractZipArchive', 'None')
    return _fileutil.extractZipArchive(f)

  def buildZipArchive( self, files, get_data=True):
    warn(self, 'buildZipArchive', 'None')
    return _fileutil.buildZipArchive( files, get_data)

  def getXmlHeader(self, encoding='utf-8'):
    warn(self, 'getXmlHeader', 'Products.zms.standard.getXmlHeader')
    return standard.getXmlHeader(encoding)

  def toXmlString(self, v, xhtml=False, encoding='utf-8'):
    warn(self, 'toXmlString', 'Products.zms.standard.toXmlString')
    return standard.toXmlString(self, v, xhtml, encoding)

  def parseXmlString(self, xml):
    warn(self, 'parseXmlString', 'Products.zms.standard.parseXmlString')
    return standard.parseXmlString(xml)

  def xslProcess(self, xsl, xml):
    warn(self, 'xslProcess', 'None')
    return self.processData('xslt', xml, xsl)

  def processData(self, processId, data, trans=None):
    warn(self, 'processData', 'Products.zms.standard.processData')
    return standard.processData(self, processId, data, trans)

  def xmlParse(self, xml):
    warn(self, 'xmlParse', 'None')
    return _xmllib.xmlParse(xml)

  def xmlNodeSet(self, mNode, sTagName='', iDeep=0):
    warn(self, 'xmlNodeSet', 'Products.zms.standard.xmlNodeSet')
    return _xmllib.xmlNodeSet( mNode, sTagName, iDeep)

  def dt_executable(self, v):
    warn(self, 'dt_executable', 'Products.zms.standard.dt_executable')
    return standard.dt_executable(self, v)

  def dt_exec(self, v, o={}):
    warn(self, 'dt_exec', 'Products.zms.standard.dt_exec')
    return standard.dt_exec(self, v, o)

  def sendMail(self, mto, msubject, mbody, REQUEST=None, mattach=None):
    warn(self, 'sendMail', 'Products.zms.standard.sendMail')
    return standard.sendMail(self, mto, msubject, mbody, REQUEST, mattach)

  def getPRODUCT_HOME(self):
    warn(self, 'getPRODUCT_HOME', 'Products.zms.standard.getPRODUCT_HOME')
    return standard.getPRODUCT_HOME()

  def getPACKAGE_HOME(self):
    warn(self, 'getPACKAGE_HOME', 'Products.zms.standard.getPACKAGE_HOME')
    return standard.getPACKAGE_HOME()

  def getINSTANCE_HOME(self):
    warn(self, 'getINSTANCE_HOME', 'Products.zms.standard.getINSTANCE_HOME')
    return standard.getINSTANCE_HOME()

  def writeLog(self, info):
    warn(self, 'writeLog', 'Products.zms.standard.writeLog')
    return standard.writeLog( self, info)

  def writeBlock(self, info):
    warn(self, 'writeBlock', 'Products.zms.standard.writeBlock')
    return standard.writeBlock( self, info)

  def writeError(self, info):
    warn(self, 'writeError', 'Products.zms.standard.writeError')
    return standard.writeError( self, info)

  def getDataSizeStr(self, len):
    warn(self, 'getDataSizeStr', 'Products.zms.standard.getDataSizeStr')
    return standard.getDataSizeStr(len)

  def getMimeTypeIconSrc(self, mt):
    warn(self, 'getMimeTypeIconSrc', 'Products.zms.standard.getMimeTypeIconSrc')
    return standard.getMimeTypeIconSrc(mt)
    
  def http_import(self, url, method='GET', auth=None, parse_qs=0, timeout=10, headers={'Accept':'*/*'}):
    warn(self, 'http_import', 'Products.zms.standard.http_import')
    return standard.http_import( self, url, method=method, auth=auth, parse_qs=parse_qs, timeout=timeout, headers=headers)

  def getLangFmtDate(self, t, lang=None, fmt_str='SHORTDATETIME_FMT'):
    warn(self, 'getLangFmtDate', 'Products.zms.standard.getLangFmtDate')
    return standard.getLangFmtDate(self, t, lang, fmt_str)
