################################################################################
# _zreferableitem.py
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
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
import base64
import copy
import re
# Product Imports.
from Products.zms import _confmanager
from Products.zms import _objattrs
from Products.zms import standard

# ------------------------------------------------------------------------------
#  isMailLink:
# ------------------------------------------------------------------------------
def isMailLink(url):
  rtn = isinstance(url, str) and url.lower().startswith('mailto:')
  return rtn

# ------------------------------------------------------------------------------
#  isInternalLink:
# ------------------------------------------------------------------------------
def isInternalLink(url):
  rtn = isinstance(url, str) and url.startswith('{$') and url.endswith('}')
  return rtn

# ------------------------------------------------------------------------------
#  getInternalLinkDict:
# ------------------------------------------------------------------------------
def getInternalLinkDict(self, url):
  #-- [ReqBuff]: Fetch buffered value from Http-Request.
  docelmnt = self.getDocumentElement()
  reqBuffId = 'getInternalLinkDict.%s'%url
  try: return docelmnt.fetchReqBuff(reqBuffId)
  except: pass
  d = {}
  # Params.
  ref_params = ''
  if url.find(';') > 0:
    ref_params = url[url.find(';'):-1]
    url = '{$%s}'%url[2:url.find(';')]
  ref_obj = self.getLinkObj(url)
  if ref_obj is not None:
    request = self.REQUEST
    url = '{$%s%s}'%(self.getRefObjPath( ref_obj)[2:-1], ref_params)
    d['data-id'] = url
    d['data-url'] = getInternalLinkUrl(self, url, ref_obj)
    if not ref_obj.isActive(request):
      d['data-target'] = "inactive"
    elif self.getTrashcan().isAncestor(ref_obj):
      d['data-target'] = 'trashcan'
  else:
    d['data-id'] = "{$__%s__}"%url[2:-1]
    d['data-target'] = "missing"
  #-- [ReqBuff]: Returns value and stores it in buffer of Http-Request.
  return docelmnt.storeReqBuff( reqBuffId, d)

# ------------------------------------------------------------------------------
#  getInternalLinkUrl:
# ------------------------------------------------------------------------------
def getInternalLinkUrl(self, url, ob):
  request = self.REQUEST
  if ob is None:
    index_html = './index_%s.html?error_type=NotFound&op=not_found&url=%s'%(request.get('lang', self.getPrimaryLanguage()), str(url))
  else:
    # Contextualized index_html.
    context = request.get('ZMS_THIS', self)
    index_html = ob.getHref2IndexHtmlInContext(context, REQUEST=request)
  return index_html

# ----------------------------------------------------------------------------
#  getInlineRefs:
#
#  Parses internal links.
# ----------------------------------------------------------------------------
def getInlineRefs(text):
  l = []
  p = '<a(.*?)>(.*?)<\\/a>'
  r = re.compile(p)
  for f in r.findall(text):
    d = dict(re.findall('\\s(.*?)="(.*?)"', f[0]))
    if 'data-id' in d:
      l.append(d['data-id'])
  return l

################################################################################
################################################################################
###
###   class ZReferableItem
###
################################################################################
################################################################################
class ZReferableItem(object): 

  # Management Permissions.
  # -----------------------
  __authorPermissions__ = (
    'manage_RefForm', 'manage_browse_iframe',
  )
  __ac_permissions__=(
    ('ZMS Author', __authorPermissions__),
  )

  # Management Interface.
  # ---------------------
  manage_RefForm = PageTemplateFile('zpt/ZMSLinkElement/manage_refform', globals())
  manage_browse_iframe = PageTemplateFile('zpt/ZMSLinkElement/manage_browse_iframe', globals()) 


  # ----------------------------------------------------------------------------
  #  ZReferableItem.getRelativeUrl:
  # ----------------------------------------------------------------------------
  def getRelativeUrl(self, path, url):
    import posixpath
    u_dest = standard.urllib_parse.urlsplit(url)
    u_src = standard.urllib_parse.urlsplit(path)
    _uc1 = standard.urllib_parse.urlunsplit(u_dest[:2]+tuple('' for i in range(3)))
    _uc2 = standard.urllib_parse.urlunsplit(u_src[:2]+tuple('' for i in range(3)))
    if _uc1 != _uc2:
        ## This is a different domain
        return url
    _relpath = posixpath.relpath(u_dest.path, posixpath.dirname(u_src.path))
    return './%s'%standard.urllib_parse.urlunsplit(('', '', _relpath, u_dest.query, u_dest.fragment))

  # ----------------------------------------------------------------------------
  #  ZReferableItem.getRefObjPath:
  # ----------------------------------------------------------------------------
  def getRefObjPath(self, ob, anchor=''):
    ref = ''
    if ob is not None:
      def default(*args, **kwargs):
        self = args[0]
        ob = args[1]['ob']
        anchor = args[1]['anchor']
        abs_home = self.getAbsoluteHome().getPhysicalPath()
        ob_home = ob.getPhysicalPath()[len(abs_home)-1:]
        path = '/'.join(ob_home).replace('/content/', '@')
        if path.startswith('@'):
          path = path[1:]
        return '{$' + path + anchor + '}'
      request = self.REQUEST
      key = request.get('ExtensionPoint.ZReferableItem.getRefObjPath','ExtensionPoint.ZReferableItem.getRefObjPath')
      ref = self.evalExtensionPoint(key,default,ob=ob,anchor=anchor)
    return ref


  """
  ##############################################################################
  ###  
  ###  References FROM other objects.
  ### 
  ##############################################################################
  """

  # ----------------------------------------------------------------------------
  #  ZReferableItem.getRefByObjs:
  #
  #  Returns references FROM other objects.
  # ----------------------------------------------------------------------------
  def getRefByObjs(self, REQUEST=None):
    ref_by = []
    if 'ref_by' in self.__dict__:
      ref_by = self.ref_by
      ref_by = list(set(ref_by))
    return ref_by


  # ----------------------------------------------------------------------------
  #  ZReferableItem.synchronizeRefByObjs:
  #
  #  Synchronizes references FROM other objects.
  # ----------------------------------------------------------------------------
  def synchronizeRefByObjs(self, strict=1):
    v = self.getRefByObjs()
    ref_by = []
    for i in v:
      ob = self.getLinkObj(i)
      if ob is not None:
        for ref_to in ob.getRefToObjs():
          ref_ob = self.getLinkObj(ref_to)
          if self == ref_ob:
            ref = self.getRefObjPath(ob)
            ref_by.append(ref)
            break
    ref_by = sorted(set(ref_by))
    if ref_by != v:
      self.ref_by = ref_by
    return ref_by


  # ----------------------------------------------------------------------------
  #  ZReferableItem.registerRefObj:
  #
  #  Registers reference FROM other object.
  # ----------------------------------------------------------------------------
  def registerRefObj(self, ob):
    ref = self.getRefObjPath(ob)
    standard.writeLog(self, '[registerRefObj]: ref='+ref)
    ref_by = self.synchronizeRefByObjs()
    if ref not in ref_by:
      ref_by.append(ref)
      self.ref_by = ref_by


  # ----------------------------------------------------------------------------
  #  ZReferableItem.unregisterRefObj:
  #
  #  Unregisters reference FROM other object.
  # ----------------------------------------------------------------------------
  def unregisterRefObj(self, ob):
    ref = self.getRefObjPath(ob)
    standard.writeLog(self, '[unregisterRefObj]: ref='+ref)
    ref_by = self.synchronizeRefByObjs()
    if ref in ref_by:
      ref_by = [x for x in ref_by if x!=ref]
      self.ref_by = ref_by


  """
  ##############################################################################
  ###  
  ###  References TO other objects.
  ### 
  ##############################################################################
  """

  # ----------------------------------------------------------------------------
  #  ZReferableItem.getRefToObjs:
  #
  #  Returns list of references TO other objects.
  # ----------------------------------------------------------------------------
  def getRefToObjs(self):
    d = {}
    for key in self.getObjAttrs():
      objAttr = self.getObjAttr(key)
      datatype = objAttr['datatype']
      if datatype in ['richtext', 'string', 'text', 'url']:
        lang_suffixes = ['']
        if objAttr['multilang']:
          lang_suffixes = ['_%s'%x for x in self.getLangIds()]
        for lang_suffix in lang_suffixes:
          for obj_vers in self.getObjVersions():
            v = getattr(obj_vers, '%s%s'%(key, lang_suffix), None)
            if v is not None:
              if datatype in ['richtext', 'string', 'text']:
                for iv in getInlineRefs(v):
                  ref_ob = self.getLinkObj(iv)
                  if ref_ob is not None:
                    ref = self.getRefObjPath(ref_ob)
                    d[ref] = 1
              elif datatype in ['url']:
                ref_ob = self.getLinkObj(v)
                if ref_ob is not None:
                  ref = self.getRefObjPath(ref_ob)
                  d[ref] = 1
    return list(set(d))


  # ----------------------------------------------------------------------------
  #  ZReferableItem.prepareRefreshRefToObjs:
  #
  #  Prepare refresh of references TO other objects.
  # ----------------------------------------------------------------------------
  def prepareRefreshRefToObjs(self):
    standard.writeLog( self, '[prepareRefreshRefToObjs]')
    if 'ref_to' not in self.__dict__:
      self.ref_to = self.getRefToObjs()


  # ----------------------------------------------------------------------------
  #  ZReferableItem.refreshRefToObjs:
  #
  #  Synchronizes references TO other objects.
  # ----------------------------------------------------------------------------
  def refreshRefToObjs(self):
    standard.writeLog( self, '[refreshRefToObjs]')
    if 'ref_to' in self.__dict__:
      old_ref_to = self.ref_to
      standard.writeLog( self, '[refreshRefToObjs]: old=%s'%str(old_ref_to))
      new_ref_to = self.getRefToObjs()
      standard.writeLog( self, '[refreshRefToObjs] new=%s'%str(old_ref_to))
      delattr(self, 'ref_to')
      for ref in old_ref_to:
        ref_ob = self.getLinkObj(ref)
        if ref_ob is not None:
          self_ref = ref_ob.getRefObjPath(self)
          if ref not in new_ref_to and self_ref in ref_ob.synchronizeRefByObjs():
            ref_ob.unregisterRefObj(self)
      for ref in new_ref_to:
        ref_ob = self.getLinkObj(ref)
        if ref_ob is not None:
          self_ref = ref_ob.getRefObjPath(self)
          if ref not in old_ref_to or self_ref not in ref_ob.synchronizeRefByObjs():
            ref_ob.registerRefObj(self)


  """
  ##############################################################################
  ###  
  ###  Resolve Links 
  ### 
  ##############################################################################
  """

  # ----------------------------------------------------------------------------
  #  ZReferableItem.validateInlineLinkObj:
  #
  #  Validates internal links.
  # ----------------------------------------------------------------------------
  def validateInlineLinkObj(self, text):
    if not int(self.getConfProperty('ZReferableItem.validateLinkObj', 1)): return text
    if not standard.is_str(text):
      text = standard.pystr(text)
    for pq in [('<a(.*?)>', 'href'), ('<img(.*?)>', 'src')]:
      p = pq[0]
      q = pq[1]
      r = re.compile(p)
      for f in r.findall(text):
        d = dict(re.findall('\\s(.*?)="(.*?)"', f))
        if 'data-id' in d:
          old = p.replace('(.*?)', f)
          url = d['data-id']
          ild = getInternalLinkDict(self, url)
          for k in ild:
            d[{'data-url':q}.get(k, k)] = ild[k]
          new = p.replace('(.*?)', ' '.join(['']+['%s="%s"'%(x,d[x]) for x in d]))
          if old != new:
            # @FIXME UnicodeDecodeError: 'ascii' codec can't decode byte 0x## in position ###: ordinal not in range(128)
            text = text.replace(old, new)
    return text


  # ----------------------------------------------------------------------------
  #  ZReferableItem.validateLinkObj:
  #
  #  Validates internal links.
  # ----------------------------------------------------------------------------
  def validateLinkObj(self, url):
    if not int(self.getConfProperty('ZReferableItem.validateLinkObj', 1)): return url
    if isInternalLink(url):
      if not url.startswith('{$__'):
        ild = getInternalLinkDict(self, url)
        url = ild['data-id']
    return url


  # ----------------------------------------------------------------------------
  #  ZReferableItem.getLinkObj:
  #
  #  Resolves internal/external links and returns Object.
  # ----------------------------------------------------------------------------
  def getLinkObj(self, url, REQUEST=None):
    ob = None
    if isInternalLink(url):
      def default(*args, **kwargs):
        self = args[0]
        url = args[1]['url']
        ob = None
        if not url.startswith('{$__'):
          # Find document-element.
          zmspath = url[2:-1].replace('@', '/content/')
          l = zmspath.split('/') 
          ob = self
          try:
            for id in [x for x in l if x]:
              ob = getattr(ob, id, None)
          except:
            pass
        return ob
      # Params.
      ref_params = {}
      if url.find(';') > 0:
        ref_params = dict(re.findall(';(\w*)=(\w*)', url[url.find(';'):-1]))
        url = '{$%s}'%url[2:url.find(';')]
      # Get object.
      ob = self.evalExtensionPoint('ExtensionPoint.ZReferableItem.getLinkObj', default, url=url)
      # Prepare request
      if ob is not None and ob.id not in self.getPhysicalPath():
        request = self.REQUEST
        ob.set_request_context(request, ref_params)
    return ob


  # ----------------------------------------------------------------------------
  #  ZReferableItem.getLinkUrl:
  #
  #  Resolves internal/external links and returns URL.
  # ----------------------------------------------------------------------------
  def getLinkUrl( self, url, REQUEST=None):
    request = self.REQUEST
    if isInternalLink(url):
      # Params.
      ref_params = {}
      if url.find(';') > 0:
        ref_params = dict(re.findall(';(\w*)=(\w*)', url[url.find(';'):-1]))
        url = '{$%s}'%url[2:url.find(';')]
      # Anchor.
      ref_anchor = ''
      if url.find('#') > 0:
        ref_anchor = url[url.find('#'):-1]
      # Prepare request.
      bak_params = {}
      for key in ref_params:
        bak_params[key] = request.get(key, None)
        request.set(key, ref_params[key])
      # Get index_html.
      ref_obj = self.getLinkObj(url)
      index_html = getInternalLinkUrl(self, url, ref_obj)
      # Unprepare request.
      for key in bak_params:
        request.set(key, bak_params[key])
      # Return index_html.
      url = index_html + ref_anchor
    elif isMailLink (url):
      prefix = 'mailto:'
      url = 'javascript:window.location.href=\''+prefix+'\'+atob(\''+base64.b64encode(url[len(prefix):].encode()).decode()+'\')'
    return url

  # ----------------------------------------------------------------------------
  #  ZReferableItem.tal_anchor:
  #  
  #  @param href
  #  @param target
  #  @param attrs
  #  @param content
  #  @return
  # ----------------------------------------------------------------------------
  def tal_anchor(self, href, target='', attrs={}, content=''):
    filtered_attrs_keys = [x for x in attrs if x]
    str_attrs = ' '.join(['%s=\042%s\042'%(str(x),str(attrs[x])) for x in filtered_attrs_keys])
    return '<a href="%s" %s %s>%s</a>'%(href, ['', ' target="%s"'%target][int(len(target)>0)], str_attrs, content)

################################################################################
