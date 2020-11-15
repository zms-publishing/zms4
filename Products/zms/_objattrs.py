################################################################################
# _objattrs.py
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
from DateTime.DateTime import DateTime
from OFS.Image import Image, File
import ZPublisher.HTTPRequest
import datetime
import fnmatch
import math
import string
import time
import zExceptions
# Product Imports.
from Products.zms import ZMSMetaobjManager
from Products.zms import pilutil
from Products.zms import standard
from Products.zms import zopeutil
from Products.zms import _blobfields
from Products.zms import _globals


# ------------------------------------------------------------------------------
#  getobjattrdefault
# ------------------------------------------------------------------------------
def getobjattrdefault(obj, obj_attr, lang):
    v = None
    datatype = obj_attr['datatype_key']
    default = None
    if datatype in range(len(_globals.datatype_map)):
      default = obj_attr.get('default',_globals.datatype_map[datatype][1])
    # Default inactive in untranslated languages.
    if obj_attr['id'] == 'active' and len(obj.getLangIds()) > 1 and not ( obj.isTranslated(lang,obj.REQUEST) or lang == obj.getPrimaryLanguage() ):
        default = 0
    if default is not None:
      if datatype in _globals.DT_DATETIMES and default == '{now}':
        default = time.time()
      elif type(default) is list or type(default) is tuple:
        v = standard.copy_list(default)
      elif type(default) is dict:
        v = default.copy()
      else:
        datatype = obj_attr['datatype_key']
        if default and datatype not in _globals.DT_TEXTS and standard.is_str(default):
          default = standard.dt_exec(obj,default)
        v = default
    return v


# ------------------------------------------------------------------------------
#  getobjattr
# ------------------------------------------------------------------------------
def getobjattr(self, obj, obj_attr, lang):
  # Get coverage.
  if obj_attr['id'] == 'attr_dc_coverage':
    coverage = getattr(obj, obj_attr['id'], '')
    coverages = ['', 'obligation', None]
    if coverage in coverages: 
      coverage = 'global.' + self.getPrimaryLanguage()
    return coverage
  # Get other.
  v = None
  key = self._getObjAttrName(obj_attr, lang)
  if key in obj.__dict__:
    v = getattr(obj, key)
  # Default mono-lingual attributes to primary-lang.
  if v is None:
    key = self._getObjAttrName({'id':obj_attr['id'],'multilang':not obj_attr['multilang']}, self.getPrimaryLanguage())
    if key in obj.__dict__:
      v = getattr(obj, key)
  # Default value.
  if v is None:
    v = getobjattrdefault(obj, obj_attr, lang)
  return v

# ------------------------------------------------------------------------------
#  setobjattr:
# ------------------------------------------------------------------------------
def setobjattr(self, obj, obj_attr, value, lang):
  key = self._getObjAttrName(obj_attr, lang)
  # Handle value.
  if isinstance(value, _blobfields.MyBlob):
    value.on_setobjattr()
  # Assign value.
  setattr(obj, key, value)

# ------------------------------------------------------------------------------
#  cloneobjattr:
# ------------------------------------------------------------------------------
def cloneobjattr(self, src, dst, obj_attr, lang):
  # Fetch value.
  v = getobjattr(self, src, obj_attr, lang)
  # Clone value.
  if v is not None:
    datatype = obj_attr['datatype_key']
    if datatype in _globals.DT_BLOBS:
      try:
        v = v._getCopy()
      except:
        e = "[cloneobjattr]: Can't clone object-attribute: obj_attr=%s, lang=%s, v=%s!"%(str(obj_attr), str(lang), str(v))
        standard.writeError( self, e)
        raise zExceptions.InternalError(e)
    elif isinstance(v, list) or isinstance(v, tuple):
      v = standard.copy_list(v)
    elif isinstance(v, dict):
      v = v.copy()
  # Assign value.
  setobjattr(self, dst, obj_attr, v, lang)


################################################################################
################################################################################
###
###   class ObjAttrs
###
################################################################################
################################################################################
class ObjAttrs(object):

    # --------------------------------------------------------------------------
    #  ObjAttrs.ajaxGetObjOptions:
    # --------------------------------------------------------------------------
    def ajaxGetObjOptions(self, REQUEST):
      """ ObjAttrs.ajaxGetObjOptions """
      meta_id = REQUEST['obj_id']
      key = REQUEST['attr_id']
      RESPONSE = REQUEST.RESPONSE
      content_type = 'text/plain; charset=utf-8'
      filename = 'ajaxGetObjOptions.txt'
      RESPONSE.setHeader('Content-Type', content_type)
      RESPONSE.setHeader('Content-Disposition', 'inline;filename="%s"'%filename)
      RESPONSE.setHeader('Cache-Control', 'no-cache')
      RESPONSE.setHeader('Pragma', 'no-cache')
      obj_attr = self.getObjAttr( key, meta_id)
      l = [x[1] for x in self.getObjOptions( obj_attr, REQUEST)]
      q = REQUEST.get( 'q', '').upper()
      if q:
        l = [x for x in l if x.upper().find(q) >= 0]
      limit = int(REQUEST.get('limit', self.getConfProperty('ZMS.input.autocomplete.limit', 15)))
      if len(l) > limit:
        l = l[:limit]
      if REQUEST.get('fmt') == 'json':
        return self.str_json(l)
      return '\n'.join(l)


    # --------------------------------------------------------------------------
    #  ObjAttrs.getObjAttrs:
    #
    #  Returns object-attributes and resolves meta-dictionaries.
    # --------------------------------------------------------------------------
    def getObjAttrs(self, meta_id=None):
      meta_id = standard.nvl( meta_id, self.meta_id)
      obj_attrs = getattr( self, 'dObjAttrs', {})
      return obj_attrs.get(meta_id, {})


    # --------------------------------------------------------------------------
    #  ObjAttrs.getObjAttr:
    # --------------------------------------------------------------------------
    def getObjAttr(self, key, meta_id=None):
      obj_attrs = self.getObjAttrs( meta_id)
      return obj_attrs.get(key, {'id':key,'key':key,'xml':False,'multilang':False,'name':'UNKNOWN','datatype':'string','datatype_key':_globals.DT_UNKNOWN})


    # --------------------------------------------------------------------------
    #  ObjAttrs.getObjAttrLabel:
    # --------------------------------------------------------------------------
    def getObjAttrLabel(self, obj_attr):
      lang = self.REQUEST.get('manage_lang', self.REQUEST.get('lang', self.getPrimaryLanguage()))
      for key in [ 'name', 'id']:
        if key in obj_attr:
          name = obj_attr.get( key)
          lang_key = name
          lang_str = self.getLangStr( lang_key, lang)
          if lang_key != lang_str:
            return lang_str
          lang_key = name.upper()
          lang_str = self.getLangStr( lang_key, lang)
          if lang_key != lang_str:
            return lang_str
          lang_key = ('attr_'+name).upper()
          lang_str = self.getLangStr( lang_key, lang)
          if lang_key != lang_str:
            return lang_str
      return obj_attr.get('name', obj_attr['id'].capitalize())


    # --------------------------------------------------------------------------
    #  ObjAttrs.getObjOptions:
    # --------------------------------------------------------------------------
    def getObjOptions(self, obj_attr, REQUEST):
      optpl = []
      if 'options' in obj_attr:
        opts = []
        obj_attropts = obj_attr['options']
        if isinstance(obj_attropts, list):
          v = '\n'.join([str(obj_attropts[x*2]) for x in range(len(obj_attropts)//2)])
          if len(obj_attropts)==2 and self.getLinkObj(obj_attropts[0], REQUEST):
            ob = self.getLinkObj(obj_attropts[0], REQUEST)
            metaObj = self.getMetaobj(ob.meta_id)
            res = ob.getObjProperty(metaObj['attrs'][0]['id'], REQUEST)
            res = [{'key':x['key'],'value':x.get('value', x.get('value_%s'%REQUEST['lang']))} for x in res]
            res = standard.sort_list(res, 'value', 'asc')
            opts = [[x['key'], x['value']] for x in res]
          elif v.find('<dtml-') >= 0 or v.startswith('##') or v.find('<tal:') >= 0:
            try:
              opts = standard.dt_exec(self, v)
            except:
              opts = standard.writeError(self, '[getObjOptions]: key=%s'%obj_attr['id'])
          else:
            for i in range(len(obj_attropts)//2):
              opts.append([obj_attropts[i*2], obj_attropts[i*2+1]])
        elif isinstance(obj_attropts, dict):
          for k in obj_attropts.keys():
            opts.append([k, obj_attropts[k]])
        for opt in opts:
          lang_attr = 'OPT_'
          for skey in obj_attr['id'].split('_'):
            lang_attr += skey[0]
          lang_attr += '_' + str(opt[1]).replace(' ', '')
          lang_attr = lang_attr.upper()
          lang_str = self.getZMILangStr(lang_attr)
          value = str(opt[0])
          display = str(opt[1])
          if lang_attr != lang_str:
            display = lang_str
          optpl.append([value, display])
      return optpl

    # --------------------------------------------------------------------------
    #  ObjAttrs.getObjAttrName:
    # --------------------------------------------------------------------------
    def _getObjAttrName(self, obj_attr, lang=None):
      attr = obj_attr['id']
      if obj_attr['multilang']:
        if lang is None: 
          lang = self.getPrimaryLanguage()
        attr = '%s_%s'%(attr, lang)
      return attr

    def getObjAttrName(self, obj_attr, lang=None):
      attr = self.REQUEST.get('objAttrNamePrefix', '') + self._getObjAttrName(obj_attr, lang)
      return attr

    # --------------------------------------------------------------------------
    #  ObjAttrs.isDisabledAttr:
    # --------------------------------------------------------------------------
    def isDisabledAttr(self, obj_attr, REQUEST):
      lang = REQUEST.get('lang', self.getPrimaryLanguage())
      return REQUEST.get(obj_attr['id']+'-disabled', False) or not (obj_attr['multilang'] or REQUEST.get('ZMS_INSERT', None) is not None or self.getDCCoverage(REQUEST).find('.'+lang)>0)


    ############################################################################
    #
    #  INPUT-FIELDS
    #
    ############################################################################

    # --------------------------------------------------------------------------
    #  ObjAttrs.getObjAttrInput:
    # --------------------------------------------------------------------------
    def getObjAttrInput(self, fmName, obj_attr, value, REQUEST):
    
      #-- DATATYPE
      datatype = obj_attr['datatype_key']
      
      #-- NAME
      lang = REQUEST['lang']
      elName = self.getObjAttrName(obj_attr, lang)
      
      #-- INPUTTYPE
      inputtype = obj_attr.get('type', 'string')
      
      #-- ENABLED / DISABLED
      enabled = not self.isDisabledAttr(obj_attr, REQUEST)
      disabled = obj_attr['id'].find('_')==0
      
      #-- Meta-Object
      meta_id = REQUEST.get( 'ZMS_INSERT', self.meta_id)
      metaObj = self.getMetaobj( meta_id)
      
      #-- Label
      lang_str = self.getObjAttrLabel(obj_attr)
      
      #-- Mandatory
      mandatory = obj_attr.get('mandatory', 0)
      
      #-- ID-Fields.
      if inputtype == 'identifier':
        if value == '': value = 'e%i'%self.getSequence().nextVal()
        return '<div class="form-control-static"><input type="hidden" name="%s" value="%s">%s</div>'%(elName, value, value)
      
      #-- Richtext-Fields.
      elif inputtype == 'richtext':
        REQUEST.set('data', value)
        form_fixed = False
        css = 'form-control'
        wrap = 'virtual'
        filteredMetaObjAttrs = [x for x in metaObj['attrs'] if x['id'] == 'format']
        if len(filteredMetaObjAttrs) == 1:
          if REQUEST.get('ZMS_INSERT'):
            default = standard.dt_exec(self, standard.pystr( filteredMetaObjAttrs[0].get('default', '')))
            if default:
              fmt = default
            else:
              fmt = self.getTextFormatDefault()
            data = ''
          else:
            fmt = self.getObjProperty('format', REQUEST)
            txt = self.getObjAttrValue(obj_attr, REQUEST)
            data = self.renderText(None, obj_attr['id'], txt, REQUEST)
          REQUEST.set('format', fmt)
          REQUEST.set('data', data)
          text_fmt = self.getTextFormat(fmt, REQUEST)
          form_fixed = form_fixed or ( text_fmt is not None and not text_fmt.getTag() and not text_fmt.getSubTag())
        if disabled: 
          css += '-disabled'
        return self.f_selectRichtext(self, ob=self, fmName=fmName, elName=elName, cols=50, rows=15, value=value, key=obj_attr['id'], metaObj=metaObj, enabled=enabled, lang=lang, lang_str=lang_str, REQUEST=REQUEST, css=css, wrap=wrap)
      
      #-- Image-Fields.
      elif inputtype == 'image':
        return self.f_selectImage(self, ob=self, fmName=fmName, elName=elName, value=value, key=obj_attr['id'], metaObj=metaObj, lang=lang, REQUEST=REQUEST)
      
      #-- File-Fields.
      elif inputtype == 'file':
        return self.f_selectFile(self, ob=self, fmName=fmName, elName=elName, value=value, key=obj_attr['id'], metaObj=metaObj, lang=lang, REQUEST=REQUEST)
      
      #-- Password-Fields.
      if inputtype == 'password':
        return self.getPasswordInput(fmName=fmName, elName=elName, value=value)
      
      #-- Dictionary/List-Fields.
      elif inputtype in [ 'dictionary', 'list']:
        wrap = 'virtual'
        if disabled: 
          css += '-disabled'
        cols = None
        rows = 5
        return self.getTextArea(fmName, elName, cols, rows, self.toXmlString(value), enabled, css, wrap)
      
      #-- Text-Fields.
      elif inputtype in [ 'text', 'xml']:
        css = 'form-control'
        wrap = 'virtual'
        if inputtype in ['xml']:
          wrap = 'off'
        if disabled: 
          css += '-disabled'
        cols = None
        rows = 5
        return self.getTextArea(fmName, elName, cols, rows, value, enabled, css, wrap)
      
      #-- Boolean-Fields.
      elif inputtype == 'boolean':
        return self.getCheckbox(fmName=fmName, elName=elName, elId=obj_attr['id'], value=value, enabled=enabled, hidden=False, btn=True)
      
      #-- Autocomplete-Fields.
      elif inputtype in ['autocomplete', 'multiautocomplete']:
        return self.zmi_input_autocomplete(self, name=elName, value=value, type=inputtype, ajax_url='ajaxGetObjOptions', obj_id=meta_id, attr_id=obj_attr['id'], lang_str=lang_str, enabled=enabled)
      
      #-- Select-Fields.
      elif inputtype in ['multiselect', 'select', 'color']:
        optpl = self.getObjOptions(obj_attr, REQUEST)
        return self.getSelect(fmName, elName, value, inputtype, lang_str, mandatory, optpl, enabled)
      
      #-- Input-Fields.
      else: 
        css = 'form-control'
        if disabled: css += '-disabled'
        css += ' datatype-%s'%(datatype)
        if datatype in _globals.DT_DATETIMES:
          size = 12
          fmt_str = 'DATETIME_FMT'
          if datatype == _globals.DT_DATE:
            size = 8
            fmt_str = 'DATE_FMT'
          elif datatype == _globals.DT_TIME:
            size = 8
            fmt_str = 'TIME_FMT'
          return self.getDateTimeInput(fmName, elName, size, value, enabled, fmt_str, css)
        elif datatype == _globals.DT_URL:
          return self.getUrlInput(fmName, elName, value=value, enabled=enabled, css=css)
        else:
          size = None
          extra = ''
          if 'size' in obj_attr:
            size = obj_attr['size']
          elif datatype in _globals.DT_INTS:
            size = 5
          elif datatype == _globals.DT_FLOAT:
            size = 8
          elif datatype == _globals.DT_AMOUNT:
            size = 8
            if value is not None:
              try:
                value = '%1.2f'%float(value)
              except:
                pass
          inp = []
          inp.append(self.getTextInput( fmName, elName, size, value, 'text', enabled, css, extra ))
          if datatype in [_globals.DT_AMOUNT]:
            inp.append('&nbsp;'+self.getConfProperty('ZMS.locale.amount.unit', 'EUR'))
          return ''.join(inp)

    # --------------------------------------------------------------------------
    #  ObjAttrs.getObjInput:
    # --------------------------------------------------------------------------
    def getObjInput(self, key, REQUEST):
      try:
        id = self.id
        fmName = REQUEST.get( 'fmName', REQUEST.get('fmName', 'form0_%s'%id))
        meta_id = REQUEST.get( 'ZMS_INSERT', None)
        obj_attr = self.getObjAttr( key, standard.nvl( meta_id, self.meta_id))
        if meta_id is None:
          value = self.getObjAttrValue( obj_attr, REQUEST)
        else:
          value = REQUEST.get( '%s_value'%key)
          if value is None:
            value = getobjattrdefault(self, obj_attr, REQUEST['lang'])
        return self.getObjAttrInput( fmName, obj_attr, value, REQUEST)
      except:
        return standard.writeError(self, 'can\'t getObjInput')


    """
    ############################################################################
    #
    #  Get
    #
    ############################################################################
    """

    # --------------------------------------------------------------------------
    #  ObjAttrs._getObjAttrValue:
    # --------------------------------------------------------------------------
    def _getObjAttrValue(self, obj_attr, obj_vers, lang):
      
      # Get value.
      datatype = obj_attr['datatype_key']
      value = getobjattr(self, obj_vers, obj_attr, lang)
      
      #-- Blob-Fields
      if datatype in _globals.DT_BLOBS:
        if isinstance(value,str):
          value = None
        elif value is not None:
          value = value._createCopy( self, obj_attr['id'])
          value.lang = lang
      
      #-- DateTime-Fields.
      elif datatype in _globals.DT_DATETIMES:
        if value is not None:
          if isinstance(value,str):
            fmt_str = 'DATETIME_FMT'
            if datatype == _globals.DT_DATE:
              fmt_str = 'DATE_FMT'
            elif datatype == _globals.DT_TIME:
              fmt_str = 'TIME_FMT'
            value = self.parseLangFmtDate(value)
          elif not isinstance(value, time.struct_time):
            value = standard.getDateTime(value)
      
      #-- List-Fields.
      elif datatype == _globals.DT_LIST:
        if not isinstance(value, list):
          value = [value]
      
      #-- Integer-Fields.
      elif datatype in _globals.DT_INTS:
        try:
          value = int(math.floor(float(value)))
        except:
          value = 0
      
      #-- Float-Fields.
      elif datatype == _globals.DT_FLOAT:
        try:
          value = float(value)
        except:
          value = 0.0
      
      # Return value.
      return value


    # --------------------------------------------------------------------------
    #  ObjAttrs.getObjAttrValue:
    # --------------------------------------------------------------------------
    def getObjAttrValue(self, obj_attr, REQUEST):
      datatype = obj_attr['datatype_key']
      obj_vers = self.getObjVersion(REQUEST)
      lang = self.get_request_context(REQUEST, 'lang', self.getPrimaryLanguage())
      while True:
        value = self._getObjAttrValue(obj_attr, obj_vers, lang)
        empty = False
        if obj_attr['multilang'] and \
           obj_attr['id'] not in ['active','created_uid','created_dt','change_uid','change_dt','work_uid','work_dt','internal_dict','change_history','master_version','major_version','minor_version']:
          lang = self.getParentLanguage(lang)
          if lang is not None:
            empty = empty or (value is None)
            empty = empty or (datatype in _globals.DT_NUMBERS and value==0)
            empty = empty or (datatype in _globals.DT_STRINGS and value=='')
            empty = empty or (datatype == _globals.DT_LIST and value==[])
        if not empty: break
      return value


    # --------------------------------------------------------------------------
    #  ObjAttrs.attr_is_modified:
    # --------------------------------------------------------------------------
    def attr_is_modified(self, key):
      try:
        modified = False
        request = self.REQUEST
        if 'ZMS_INSERT' not in request and not self.getAutocommit():
          obj_attr = self.getObjAttr(key, self.meta_id)
          datatype = obj_attr['datatype_key']
          lang = request['lang']
          work = self.getObjAttrValue(obj_attr, {'lang':lang,'preview':'preview'})
          live = self.getObjAttrValue(obj_attr, {'lang':lang})
          modified = modified or (datatype not in _globals.DT_BLOBS and work != live)
          modified = modified or (datatype in _globals.DT_BLOBS and (str(work) != str(live) or (work is not None and live is not None and str(work.getData()) != str(live.getData()))))
      except:
        standard.writeError(self, '[attr_is_modified]: key=%s'%key)
      return modified

    # --------------------------------------------------------------------------
    #  ObjAttrs.getObjProperty:
    #
    #  Retrieves value for specified property.
    #
    #  @deprecated: use attr(key) instead! 
    # --------------------------------------------------------------------------
    def getObjProperty(self, key, REQUEST={}, par=None):
      obj_attrs = self.getObjAttrs()
      
      # Special attributes.
      if key not in obj_attrs.keys():
        value = self.nvl(self.evalMetaobjAttr(key), '')
        if not isinstance(value, _blobfields.MyBlob) and (isinstance(value, Image) or isinstance(value, File)):
          value = _blobfields.MyBlobWrapper(value)
      
      # Standard attributes.
      elif key in obj_attrs.keys():
        obj_attr = obj_attrs[key]
        datatype = obj_attr['datatype_key']
        value = self.getObjAttrValue( obj_attr, REQUEST)
        # Text-Fields
        if datatype in _globals.DT_TEXTS:
          value = self.validateInlineLinkObj(value)
        # Url-Fields
        if datatype == _globals.DT_URL:
          value = self.validateLinkObj(value)
        # Executable fields.
        value = standard.dt_exec(self, value)
      
      # Undefined attributes.
      else:
        value = ''
      
      # Return value.
      return value


    # --------------------------------------------------------------------------
    #  ObjAttrs.attr:
    #
    #  Get one or set one or more attributes.
    #
    #  attr(key) -> getObjProperty(key,REQUEST)
    #  attr(key,value) -> setObjProperty(key,value)
    #  attr({key0:value0,...,keyN:valueN}) -> setObjProperty(key0,value0),...
    # --------------------------------------------------------------------------
    def attr(self, *args, **kwargs):
      request = kwargs.get('request',kwargs.get('REQUEST',self.REQUEST))
      if len(args) == 1 and isinstance(args[0], str):
        return self.getObjProperty( args[0], request, kwargs)
      elif len(args) == 2:
        self.setObjProperty( args[0], args[1], request.get('lang'))
      elif len(args) == 1 and isinstance(args[0], dict):
        for key in args[0].keys():
          self.setObjProperty( key, args[0][key], request.get('lang'))


    # --------------------------------------------------------------------------
    #  ObjAttrs.evalMetaobjAttr
    # --------------------------------------------------------------------------
    def evalMetaobjAttr(self, *args, **kwargs):
      root = self
      request = self.REQUEST
      id = request.get('ZMS_INSERT', self.meta_id)
      key = args[0]
      if key.find('.')>0:
        id = key[:key.find('.')]
        key = key[key.find('.')+1:]
      if id == '*':
        root = self.getRootElement()
      return root.getMetaobjManager().evalMetaobjAttr(id, key, zmscontext=self, options=kwargs)


    # --------------------------------------------------------------------------
    #  ObjAttrs.evalExtensionPoint
    # --------------------------------------------------------------------------
    def evalExtensionPoint(self, *args, **kwargs):
      key = args[0]
      default = args[1]
      root = self.getRootElement()
      ep = root.getConfProperty(key, None)
      if ep is not None:
        id = ep[:ep.find('.')]
        key = ep[ep.find('.')+1:]
        return root.getMetaobjManager().evalMetaobjAttr(id, key, zmscontext=self, options=kwargs)
      else:
        return default(self, kwargs)


    """
    ############################################################################
    ###  
    ###  Active
    ### 
    ############################################################################
    """

    # --------------------------------------------------------------------------
    #  ObjAttrs.is_active:
    #
    #  alias for isActive(request)
    # --------------------------------------------------------------------------
    def is_active(self):
      return self.isActive(self.REQUEST)

    # --------------------------------------------------------------------------
    #  ObjAttrs.isActive:
    # --------------------------------------------------------------------------
    def isActive(self, REQUEST):
      b = True
      if self.getType()=='ZMSRecordSet':
        return b
      v = self.attr('active')
      if isinstance(v, bool):
        return v
      v = self.attr('isActive')
      if isinstance(v, bool):
        b = b and v
      obj_vers = self.getObjVersion(REQUEST)
      obj_attrs = self.getObjAttrs()
      now = datetime.datetime.now()
      if 'preview_time_travel' in REQUEST.keys():
        now = datetime.datetime.strptime(REQUEST['preview_time_travel'],self.getZMILangStr('SHORTDATE_FMT'))
      for key in ['active', 'attr_active_start', 'attr_active_end']:
        if key in obj_attrs:
          obj_attr = obj_attrs[key]
          lang = self.get_request_context(REQUEST, 'lang', self.getPrimaryLanguage())
          while True:
            value = self._getObjAttrValue(obj_attr, obj_vers, lang)
            empty = False
            lang = self.getParentLanguage(lang)
            if lang is not None:
              empty = value is None
            if not empty:
              break
          # Toggle.
          if key == 'active':
            b = b and value
          # Start time.
          elif key == 'attr_active_start':
            if value is not None:
              dt = datetime.datetime.fromtimestamp(time.mktime(value))
              b = b and now > dt
          # End time.
          elif key == 'attr_active_end':
            if value is not None:
              dt = datetime.datetime.fromtimestamp(time.mktime(value))
              b = b and now < dt
          if not b: break
      return b


    """
    ############################################################################
    #
    #  Set
    #
    ############################################################################
    """
    
    # --------------------------------------------------------------------------
    #  ObjAttrs.formatObjAttrValue:
    # --------------------------------------------------------------------------
    def formatObjAttrValue(self, obj_attr, v, lang=None):
      
      #-- DATATYPE
      datatype = obj_attr.get('datatype_key', _globals.DT_UNKNOWN)
      
      #-- VALUE
      if isinstance(v, str):
        chars = ''.join([ x for x in string.whitespace if x != '\t'])
        v = v.strip(chars)
      # Retrieve v from options.
      if 'options' in obj_attr:
        options = obj_attr['options']
        try: 
          i = options.index(int(v))
          if i%2==1: v = options[i-1]
        except:
          try:
            i = options.index(str(v))
            if i%2==1: v = options[i-1]
          except:
            pass
      
      #-- Blob-Fields
      if datatype in _globals.DT_BLOBS:
        if self.getType()=='ZMSRecordSet' and isinstance(v, _blobfields.MyBlob):
          metaObj = self.getMetaobj(self.meta_id)
          metaObjAttrId = metaObj['attrs'][0]['id']
          l = self.attr(metaObjAttrId)
          r = [x for x in l if v.equals(x.get(obj_attr['id'], None))]
          if len( r) == 0:
            v = None
          else:
            v = v._getCopy()
            v.aq_parent = self
            v.key = '%s:%i'%(obj_attr['id'], l.index(r[0]))
            v.lang = lang
        if isinstance(v, ZPublisher.HTTPRequest.FileUpload):
          if len(getattr(v, 'filename', ''))==0:
            v = None
          else:
            v = _blobfields.createBlobField(self, datatype, v)
            v.filename = standard.umlaut_quote(v.filename, {':':'_','<':'_','>':'_','*':'_','?':'_','"':'_','|':'_',',':'_'})
        if isinstance(v, dict):
          if len(v.get('filename', ''))==0:
            v = None
          else:
            v = _blobfields.createBlobField(self, datatype, v)
      
      #-- DateTime-Fields.
      if datatype in _globals.DT_DATETIMES:
        if isinstance(v,str):
          v = standard.parseLangFmtDate(v)
        elif not isinstance(v, time.struct_time):
          v = standard.getDateTime(v)
      
      #-- Dictionary-Fields
      if datatype == _globals.DT_DICT:
        if v is None:
          v = {}
        if isinstance(v,str):
          try:
           v = standard.parseXmlString(self.getXmlHeader() + v)
          except:
            standard.writeError( self, "[formatObjAttrValue]: can't parse dict from xml - exception ignored!")
            pass
        if isinstance(v, dict):
          v = v.copy()
      
      #-- List-Fields
      if datatype == _globals.DT_LIST:
        if obj_attr['repetitive'] and not isinstance(v, list):
          if obj_attr['type'] in ['file', 'image']:
            l = self.getObjProperty(obj_attr['id'], self.REQUEST)
            r = [x for x in l if v is not None and v.equals(x)]
            if len( r) == 0:
              v = None
            else:
              v = v._getCopy()
              v.aq_parent = self
              v.key = '%s:%i'%(obj_attr['id'], l.index(r[0]))
              v.lang = lang
        else:
          if v is None:
            v = []
          if isinstance(v,str):
            try:
              l = standard.parseXmlString(self.getXmlHeader() + v)
            except:
              standard.writeError( self, "[formatObjAttrValue]: can't parse list from xml - exception ignored!")
              l = None
            if l is not None:
              v = l
            else:
              v = [v.strip()]
            if isinstance(v, list) or isinstance(v, tuple):
              v = standard.copy_list(v)
      
      #-- Integer-Fields
      if datatype in _globals.DT_INTS:
        if isinstance(v,str) and len(v) > 0:
          if v[-1] == '.':
            v = v[:-1]
          v = int(v)
      
      #-- Float-Fields
      if datatype == _globals.DT_FLOAT:
        if isinstance(v,str) and len(v) > 0:
          v = float(v)
      
      #-- String-Fields.
      if datatype in _globals.DT_STRINGS:
        if v is None:
          v = ''
      
      #-- Text-Fields
      if datatype in _globals.DT_TEXTS:
        v = self.validateInlineLinkObj(v)
      
      #-- Url-Fields
      if datatype == _globals.DT_URL:
        v = self.validateLinkObj(v)
      
      # Hook for custom formatting.
      name = 'formatCustomObjAttrValue'
      if hasattr(self, name):
        v = getattr(self, name)( context=self, obj_attr=obj_attr, v=v)
      
      return v


    # --------------------------------------------------------------------------
    #  ObjAttrs.setReqProperty:
    #
    #  Assigns value to specified property from Request-Object.
    # --------------------------------------------------------------------------
    def setReqProperty(self, key, REQUEST, forced=0):
      
      #-- REQUEST
      lang = REQUEST['lang']
      
      #-- DEFINTION
      obj_attr = self.getObjAttr(key)
      elName = self.getObjAttrName(obj_attr, lang)
      
      #-- ENABLED
      enabled = not self.isDisabledAttr(obj_attr, REQUEST)
      
      #-- DATATYPE
      datatype = obj_attr['datatype_key']
      
      #-- RETURN
      if ( not enabled) or \
         ( not obj_attr['xml']) or \
         ( obj_attr['id'].find('_') == 0 and elName not in REQUEST.form) or \
         ( datatype == _globals.DT_UNKNOWN): 
        if not forced: 
          return
      
      #-- VALUE
      set, value =False, REQUEST.get(elName, None)
      
      #-- Blob-Fields
      if datatype in _globals.DT_BLOBS:
        
        # Upload
        if isinstance(value, ZPublisher.HTTPRequest.FileUpload) and len(value.filename) > 0:
          set, value = True, value
        
        # Delete
        elif int(REQUEST.get('del_%s'%elName, 0)) == 1:
          set, value = True, None
        
        # Preload
        else:
          form_id = REQUEST.get('form_id', None)
          if form_id is not None:
            temp_folder = self.temp_folder
            id = form_id + '_' + key
            if id in temp_folder.objectIds():
              o = zopeutil.getObject(temp_folder,id)
              f = zopeutil.readData(o)
              filename = o.title
              mt, enc = standard.guess_content_type( filename, f)
              set, value = True, {'data':f,'filename':filename,'content_type':mt}
              if not pilutil.enabled() and datatype == _globals.DT_IMAGE and REQUEST.get('width_%s'%elName) and REQUEST.get('height_%s'%elName):
                w = REQUEST['width_%s'%elName]
                h = REQUEST['height_%s'%elName]
                width = o.getProperty('width')
                if not width:
                  width = self.getConfProperty('ZMS.image.default.width', 640)
                height = o.getProperty('height')
                if not height:
                  height = self.getConfProperty('ZMS.image.default.height', 400)
                if w != int(width) or h != int(height):
                  value = _blobfields.createBlobField( self, datatype, value)
                  value.width = w
                  value.height = h
              temp_folder.manage_delObjects([id])
      
      #-- Integer-Fields
      elif datatype in _globals.DT_INTS:
        if value is not None:
          if isinstance(value, str) and len(value) == 0:
            set, value = True, None
          else:
            set, value = True, int(value)
      
      #-- Float-Fields
      elif datatype == _globals.DT_FLOAT:
        if value is not None:
          if isinstance(value, str) and len(value) == 0:
            set, value = True, None
          else:
            set, value = True, float(value)
      
      #-- Other-Fields
      else:
        set = True
      
      #-- SET?
      if set:
        self.setObjProperty(key, value, lang)


    # --------------------------------------------------------------------------
    #  ObjAttrs.setObjProperty:
    #
    #  Assigns value to specified property.
    #
    #  @deprecated: use attr(key,value) instead! 
    # --------------------------------------------------------------------------
    def setObjProperty(self, key, value, lang=None, forced=0):
      
      #-- Get definition.
      obj_attr = self.getObjAttr(key)
      
      #-- Format value.
      value = self.formatObjAttrValue(obj_attr, value, lang)
      
      #-- Notify metaobj_manager.
      self.notifyMetaobjAttrAboutValue( self.meta_id, key, value)
      
      #-- SET!
      ob = self.getObjVersion({'preview':'preview'})
      setobjattr(self, ob, obj_attr, value, lang)
      if forced:
        ob = self.getObjVersion()
        setobjattr(self, ob, obj_attr, value, lang)


    ############################################################################
    #  ObjAttrs.preloadObjProperty:
    #
    #  Preload property.
    ############################################################################
    def preloadObjProperty(self, REQUEST, RESPONSE=None):
      """ ObjAttrs.preloadObjProperty """
      content_type = 'text/plain'
      message = {}
      message['success'] = True
      # Additional parameters.
      for qs in REQUEST['QUERY_STRING'].split('&'):
        e = qs.find('=')
        if e >= 0:
          k = qs[:e]
          v = qs[e+1:]
          REQUEST.set(k, v)
      
      # Mandatory parameters.
      lang = REQUEST['lang']
      key = REQUEST['key']
      
      dataRequestKey = REQUEST.get('dataRequestKey')
      filenameUnescape = REQUEST.get('filenameUnescape')
      if dataRequestKey:
        value = REQUEST[dataRequestKey]
        if isinstance(value, ZPublisher.HTTPRequest.FileUpload):
          filename = value.filename
        else:
          filename = value
          value = REQUEST['BODY']
          if filenameUnescape:
            filename = standard.unescape(filename)
      else:
        value = REQUEST['userfile[0]']
        filename = value.filename
      blob = self.ImageFromData(value, filename)
      filename = blob.getFilename()
      
      # Preload to temp-folder.
      form_id = REQUEST['form_id']
      temp_folder = self.temp_folder
      id = form_id + '_' + key
      if id in temp_folder.objectIds():
        temp_folder.manage_delObjects([id])
      meta_id = REQUEST.get('meta_id', self.meta_id)
      obj_attr = self.getObjAttr(key, meta_id)
      datatype = obj_attr['datatype_key']
      if datatype == _globals.DT_IMAGE:
        file = temp_folder.manage_addImage( id=id, title=filename, file=value)
      else:
        file = temp_folder.manage_addFile( id=id, title=filename, file=value)
      
      if dataRequestKey:
        message['filename'] = blob.getFilename()
        message['size_str'] = self.getDataSizeStr(blob.get_size())
        message['content_type'] = blob.getContentType()
        message['temp_url'] = '%s/%s'%(temp_folder.absolute_url(), id)
        message = self.str_json(message)
      
      if REQUEST.get('set'):
        self.setReqProperty(key, REQUEST)
        message = self.getZMILangStr( 'MSG_UPLOADED')+'('+self.getLangFmtDate(time.time())+')'
      
      # Return with success.
      RESPONSE.setHeader('Content-Type', content_type)
      return message


    def manage_changeTempBlobjProperty(self, lang, key, form_id, action, REQUEST, RESPONSE=None):
      """ ObjAttrs.manage_changeTempBlobjProperty """
      rtn = {}
      temp_folder = self.temp_folder
      id = form_id + '_' + key
      src = self.getTempBlobjPropertyUrl( format=None, REQUEST=REQUEST, RESPONSE=RESPONSE)['src']
      file = getattr( temp_folder, id)
      orig = self.ImageFromData(file.data, file.title)
      orig.lang = lang
      if action == 'preview':
        maxdim = self.getConfProperty('InstalledProducts.pil.thumbnail.max')
        blob = pilutil.thumbnail( orig, maxdim)
        thumbkey = key
        for suffix in ['hires', 'superres']:
          if thumbkey.endswith(suffix):
            thumbkey = thumbkey[:-len(suffix)]
            break
        thumbid = form_id + '_' + thumbkey
        if thumbid in temp_folder.objectIds():
          temp_folder.manage_delObjects([thumbid])
        temp_folder.manage_addImage( id=thumbid, title=blob.getFilename(), file=blob.getData())
        file = getattr( temp_folder, thumbid)
        meta_id = REQUEST.get('meta_id', self.meta_id)
        obj_attr = self.getObjAttr(thumbkey, meta_id)
        elName = self.getObjAttrName(obj_attr, lang)
        rtn['elName'] = elName
        w = file.getProperty('width')
        if not w:
          w = self.getConfProperty('ZMS.image.default.width', 640)
        rtn['width'] = int(w)
        h = file.getProperty('height')
        if not h:
          h = self.getConfProperty('ZMS.image.default.height', 400)
        rtn['height'] = int(h)
        rtn['filename'] = blob.getFilename()
        rtn['src'] = self.url_append_params(file.absolute_url(), {'ts':time.time()})
        # extra
        rtn['lang'] = thumbkey
        rtn['key'] = thumbkey
        rtn['form_id'] = form_id
      else:
        blob = orig
        if 'resize' in action.split(','):
          width = REQUEST['width']
          height = REQUEST['height']
          size = (width, height)
          blob = pilutil.resize( blob, size)
          rtn['height'] = height
          rtn['width'] = width
        if 'crop' in action.split(','):
          x0 = REQUEST['x0']
          y0 = REQUEST['y0']
          x1 = REQUEST['x1']
          y2 = REQUEST['y2']
          box = (x0, y0, x1, y2)
          blob = pilutil.crop( blob, box)
          rtn['height'] = y2-y0
          rtn['width'] = x1-x0
        file.manage_upload(blob.getData())
        rtn['filename'] = blob.getFilename()
        rtn['src'] = src
      # Return JSON.
      return self.str_json(rtn)


    def getTempBlobjPropertyUrl(self, format='json', REQUEST=None, RESPONSE=None):
      """ ObjAttrs.getTempBlobjPropertyUrl """
      rtn = {}
      # Mandatory parameters.
      lang = REQUEST['lang']
      key = REQUEST['key']
      form_id = REQUEST.get('form_id', None)
      if form_id is not None:
        temp_folder = self.temp_folder
        id = form_id + '_' + key
        if id not in temp_folder.objectIds():
          obj_attr = self.getObjAttr(key)
          datatype = obj_attr['datatype_key']
          blob = self.getObjProperty(key, REQUEST)
          filename = blob.getFilename()
          value = blob.getData()
          content_type = None
          if datatype == _globals.DT_IMAGE:
            if filename.endswith('.svg'):
              content_type = 'image/svg+xml'
            file = temp_folder.manage_addImage( id=id, title=filename, file=value, content_type=content_type)
          else:
            file = temp_folder.manage_addFile( id=id, title=filename, file=value, content_type=content_type)
        file = getattr( temp_folder, id)
        if file.meta_type == 'Image':
          w = file.getProperty('width')
          if not w:
            w = self.getConfProperty('ZMS.image.default.width', 640)
          rtn['width'] = int(w)
          h = file.getProperty('height')
          if not h:
            h = self.getConfProperty('ZMS.image.default.height', 400)
          rtn['height'] = int(h)
        rtn['content_type'] = file.content_type
        rtn['filename'] = file.title
        rtn['src'] = self.url_append_params(file.absolute_url(), {'ts':time.time()})
      # Return JSON.
      if format == 'json':
        rtn = self.str_json(rtn)
      return rtn


    def clearTempBlobjProperty(self, format='json', REQUEST=None, RESPONSE=None):
      """ ObjAttrs.clearTempBlobjProperty """
      rtn = {}
      # Mandatory parameters.
      lang = REQUEST['lang']
      key = REQUEST['key']
      form_id = REQUEST.get('form_id', None)
      if form_id is not None:
        temp_folder = self.temp_folder
        id = form_id + '_' + key
        if id in temp_folder.objectIds():
          temp_folder.manage_delObjects([id])
      # Return JSON.
      if format == 'json':
        rtn = self.str_json(rtn)
      return rtn


    """
    ############################################################################
    #
    #  C L O N E
    #
    ############################################################################
    """
    
    # --------------------------------------------------------------------------
    #  ObjAttrs.cloneObjAttrs:
    #
    #  Clone object-attributes.
    # --------------------------------------------------------------------------
    def cloneObjAttrs(self, src, dst, lang):
      standard.writeBlock( self, "[cloneObjAttrs]: Clone object-attributes from '%s' to '%s'"%(str(src), str(dst)))
      prim_lang = self.getPrimaryLanguage()
      keys = self.getObjAttrs().keys()
      if self.getType()=='ZMSRecordSet':
        keys = standard.difference_list( keys, self.getMetaobjAttrIds(self.meta_id)[1:])
      for key in keys:
        obj_attr = self.getObjAttr(key)
        # Multi-Language Attributes.
        if obj_attr['multilang']:
          for s_lang in self.getLangIds():
            if lang in ['*', prim_lang, s_lang]:
              cloneobjattr(self, src, dst, obj_attr, s_lang)
        # Others.
        else:
          coverage = getattr(src, 'attr_dc_coverage', '')
          if coverage is None or \
             coverage == '' or \
             not isinstance(coverage, str):
            coverage = 'global.%s'%prim_lang
          s_lang = coverage[coverage.find('.')+1:]
          if lang in ['*', prim_lang, s_lang]:
            cloneobjattr(self, src, dst, obj_attr, lang)


################################################################################
################################################################################
###
###   Object Attributes Manager
###
################################################################################
################################################################################
class ObjAttrsManager(object):

    # --------------------------------------------------------------------------
    #  ObjAttrsManager.synchronizeObjAttr:
    #
    #  Synchronizes object-attribute.
    # --------------------------------------------------------------------------
    def synchronizeObjAttr(self, attr):
      try:
        if attr['type'] in ZMSMetaobjManager.ZMSMetaobjManager.valid_types:
          dct = {}
          dct['id'] = attr['id']
          dct['name'] = attr.get('name', '?')
          dct['type'] = attr['type']
          dct['key'] = attr['id']
          dct['xml'] = attr['id'] not in ['created_uid','created_dt','change_uid','change_dt','work_uid','work_dt','internal_dict','change_history','master_version','major_version','minor_version']
          dct['datatype'] = attr['type']
          if attr['type'] in ['autocomplete', 'password', 'select', 'color']:
            dct['type'] = attr['type']
            dct['datatype'] = 'string'
          elif attr['type'] in ['richtext']:
            dct['type'] = attr['type']
            dct['datatype'] = 'text'
          elif attr['type'] in ['multiautocomplete', 'multiselect']:
            dct['type'] = attr['type']
            dct['datatype'] = 'list'
          elif attr.get('default', '') != '':
            dct['default'] = attr['default']
          elif attr.get('repetitive', 0):
            dct['datatype'] = 'list'
          dct['mandatory'] = attr.get('mandatory', 0)
          dct['multilang'] = attr.get('multilang', 0)
          dct['repetitive'] = attr.get('repetitive', 0)
          if len(attr.get('keys', []))>0:
            options = []
            for option in attr['keys']:
              options.append(option)
              options.append(option)
            dct['options'] = options
          dct['datatype_key'] = _globals.datatype_key(dct['datatype'])
          return dct
      except:
        standard.writeError( self, '[synchronizeObjAttr]')
      return None

    def synchronizeObjAttrs(self, sync_id=None):
      """
      Synchronizes dictionary of object-attributes.
      @param sync_id: meta-id of content-object, if None synchronize all.
      """
      rtn = []
      rtn.append('[%s.synchronizeObjAttrs]: %s'%(self.absolute_url(), str(sync_id)))
      
      # Prepare defaults.
      defaults_obj_attrs = {}
      defaults = [
        # Coverage
        { 'id':'attr_dc_coverage', 'type':'string'},
        # Changed by
        { 'id':'created_uid', 'type':'string'},
        { 'id':'created_dt', 'type':'datetime'},
        { 'id':'change_uid','type':'string', 'multilang':1},
        { 'id':'change_dt','type':'datetime', 'multilang':1},
        # Version info
        { 'id':'change_history', 'type':'list', 'default':[]},
        { 'id':'master_version', 'type':'int', 'default':0},
        { 'id':'major_version', 'type':'int', 'default':0},
        { 'id':'minor_version', 'type':'int', 'default':0},
        # Active
        { 'id':'active', 'type':'boolean', 'multilang':1, 'default':1},
        { 'id':'attr_active_start', 'type':'datetime', 'multilang':1},
        { 'id':'attr_active_end','type':'datetime', 'multilang':1},
        # Workflow
        { 'id':'work_uid','type':'string', 'multilang':1},
        { 'id':'work_dt','type':'datetime', 'multilang':1},
        # Internal dictionary
        { 'id':'internal_dict', 'type':'dictionary', 'default':{}},
      ]
      for attr in defaults:
        dct = self.synchronizeObjAttr( attr)
        if isinstance(dct, dict):
          defaults_obj_attrs[dct['id']] = dct
      
      # Process meta-model.
      if sync_id is None or sync_id == [ None]:
        self.dObjAttrs = {}
        meta_ids = list(self.dGlobalAttrs)
        for meta_id in self.getMetaobjIds():
          if meta_id not in meta_ids:
            meta_ids.append( meta_id)
      else:
        if not isinstance(sync_id, list):
          sync_id = [sync_id]
        meta_ids = sync_id
      for meta_id in meta_ids:
        if meta_id in self.dGlobalAttrs:
          obj_attrs = {}
          for key in defaults_obj_attrs.keys():
            obj_attr = defaults_obj_attrs[key]
            if obj_attr['id'].find('work_') < 0 or meta_id in ['ZMSCustom', 'ZMSLinkElement'] or self.getMetaobj(meta_id).get('type') == 'ZMSDocument':
              obj_attrs[key] = obj_attr.copy()
        else:
          obj_attrs = self.dObjAttrs['ZMSCustom'].copy()
        for key in self.getMetaobjAttrIds( meta_id):
          attr = self.getMetaobjAttr( meta_id, key)
          dct = self.synchronizeObjAttr( attr)
          if isinstance(dct, dict):
            obj_attrs[key] = dct
          elif key in obj_attrs:
            del obj_attrs[key]
        self.dObjAttrs[meta_id] = obj_attrs
      
      # Make persistent.
      self.dObjAttrs = self.dObjAttrs.copy()
      
      # Process clients.
      for portalClient in self.getPortalClients():
        try:
          b = False
          if not b:
            b = sync_id is None
          if not b:
            metaObjIds = portalClient.getMetaobjIds()
            for id in sync_id:
              if not b:
                b = id in metaObjIds and portalClient.getMetaobj(id).get('acquired', 0)==1
          if b:
            rtn.append(portalClient.synchronizeObjAttrs(sync_id))
        except:
          standard.writeError( self, '[synchronizeObjAttrs]: Can\'t process %s'%portalClient.absolute_url())
      
      return '\n'.join(rtn)

################################################################################
