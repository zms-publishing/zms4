################################################################################
# _xmllib.py
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
from io import StringIO
from DateTime import DateTime
import collections
import copy
import os
import pyexpat
import re
import tempfile
import time
import unicodedata
import xml.dom

from App.Common import package_home
# import Globals
from OFS.Image import File

# Product Imports
from Products.zms import standard
from Products.zms import _blobfields
from Products.zms import _fileutil
from Products.zms import _globals
from Products.zms import _objattrs
from Products.zms import zopeutil


# Product Imports.
INDENTSTR = '  '


"""
################################################################################
#
#  Datatypes
#
################################################################################
"""

# ------------------------------------------------------------------------------
#  _xmllib.serialize:
# ------------------------------------------------------------------------------
def serialize(node):
  xml = ''
  if node.nodeType == node.ELEMENT_NODE:
    xml += '<' + node.nodeName
    for attribute in node.attributes:
      xml += ' ' + attribute + '="' + node.attributes[attribute].value + '"'
    xml += '>'
    for childNode in node.childNodes:
      xml += serialize(childNode)
    xml += '</' + node.nodeName
    xml += '>'
  return xml

# ------------------------------------------------------------------------------
#  _xmllib.getText:
# ------------------------------------------------------------------------------
def getText(nodelist, encoding='utf-8'):
  rc = []
  if not isinstance(nodelist, list):
    nodelist = [nodelist]
  for node in nodelist:
    for childNode in node.childNodes:
      if childNode.nodeType == childNode.TEXT_NODE:
        rc.append(childNode.data)
  return standard.pystr(''.join(rc).encode(encoding))

# ------------------------------------------------------------------------------
#  _xmllib.parseString:
# ------------------------------------------------------------------------------
def parseString(s):
  return xml.dom.minidom.parseString(s)


"""
################################################################################
#
#  Datatypes
#
################################################################################
"""

# ------------------------------------------------------------------------------
#  _xmllib.getXmlType:
# ------------------------------------------------------------------------------
def getXmlType(v):
  t = ''
  if isinstance(v, float):
    t = ' type="float"'
  elif isinstance(v, int):
    t = ' type="int"'
  elif isinstance(v, dict):
    t = ' type="dictionary"'
  elif isinstance(v, list):
    t = ' type="list"'
  elif isinstance(v, tuple) or isinstance(v, time.struct_time) or isinstance(v, DateTime):
    t = ' type="datetime"'
  elif isinstance(v, _blobfields.MyImage):
    t = ' type="image"'
  elif isinstance(v, _blobfields.MyFile):
    t = ' type="file"'
  return t


# ------------------------------------------------------------------------------
#  _xmllib.getXmlTypeSaveValue:
# ------------------------------------------------------------------------------
def getXmlTypeSaveValue(v, attrs):
  # Strip.
  if isinstance(v, str):
    while len(v) > 0 and v[0] <= ' ':
      v = v[1:]
    while len(v) > 0 and v[-1] <= ' ':
      v = v[:-1]
  # Type.
  t = attrs.get('type', '?')
  if t == 'float':
    v = float(v)
  elif t == 'int':
    if v == 'False':
      v = 0
    elif v == 'True':
      v = 1
    else:
      v = int(v)
  elif t == 'datetime':
    new = standard.parseLangFmtDate(v)
    if new is not None:
      v = new
  # Return value.
  return v


"""
################################################################################
#
#  XML-Encoding
#
################################################################################
"""

# ------------------------------------------------------------------------------
#  _xmllib.xml_header:
# ------------------------------------------------------------------------------
def xml_header(encoding='utf-8'):
  return '<?xml version="1.0" encoding="%s"?>\n' % encoding


"""
################################################################################
#
#  Import
#
################################################################################
"""

# ------------------------------------------------------------------------------
#  _xmllib.xmlInitObjProperty:
#
#  Only for internal use: init specified property with value.
# ------------------------------------------------------------------------------
def xmlInitObjProperty(self, key, value, lang=None):

  # -- DEFINITION
  obj_attr = self.getObjAttr(key)

  # -- ATTR
  attr = self.getObjAttrName(obj_attr, lang)

  # -- DATATYPE
  datatype = obj_attr['datatype_key']

  if value is not None:
    if isinstance(value, str):
      value = value.strip()
    # -- Date-Fields
    if datatype in _globals.DT_DATETIMES:
      if isinstance(value, str) and len(value) > 0:
        value = self.parseLangFmtDate(value)
    # -- Integer-Fields
    elif datatype in _globals.DT_INTS:
      if isinstance(value, str) and len(value) > 0:
        value = int(value)
    # -- Float-Fields
    elif datatype == _globals.DT_FLOAT:
      if isinstance(value, str) and len(value) > 0:
        value = float(value)
    # -- String-Fields
    elif datatype in _globals.DT_STRINGS:
      value = value

  # -- INIT
  for ob in self.objectValues(['ZMSAttributeContainer']):
    setattr(ob, attr, value)


# ------------------------------------------------------------------------------
#  _xmllib.xmlOnCharacterData:
# ------------------------------------------------------------------------------
def xmlOnCharacterData(self, sData, bInCData):
    # -- TAG-STACK
    if len(self.dTagStack) > 0:
      tag = self.dTagStack.pop()
      tag['cdata'] += sData
      self.dTagStack.append(tag)

    # -- Return
    return 1  # accept any character data


# ------------------------------------------------------------------------------
#  _xmllib.xmlOnUnknownStartTag:
# ------------------------------------------------------------------------------
def xmlOnUnknownStartTag(self, sTagName, dTagAttrs):
    # -- TAG-STACK
    tag = {}
    tag['name'] = sTagName
    tag['attrs'] = dTagAttrs
    tag['cdata'] = ''
    tag['dValueStack'] = len(self.dValueStack)
    self.dTagStack.append(tag)

    # -- VALUE-STACK

    # ITEM (DICTIONARY|LIST)
    if sTagName in ['dict', 'dictionary']:
      self.dValueStack.append({})
    elif sTagName == 'list':
      self.dValueStack.append([])
    elif sTagName == 'item':
      pass

    # DATA (IMAGE|FILE)
    elif sTagName == 'data':
      pass

    # LANGUAGE
    elif sTagName == 'lang':
      if len(self.dValueStack) == 0:
        self.dValueStack.append({})

    # PASS OBJECT-ATTRIBUTES
    elif sTagName in self.getObjAttrs():
      pass

    # SKIP OTHERS
    else:
      tag['skip'] = True

    # -- Return
    return 1  # accept any unknown tag


# ------------------------------------------------------------------------------
#  _xmllib.xmlOnUnknownEndTag:
# ------------------------------------------------------------------------------
def xmlOnUnknownEndTag(self, sTagName):
    # -- TAG-STACK
    tag = self.dTagStack.pop()
    skip = len([x for x in self.oCurrNode.dTagStack if x.get('skip')]) > 0
    name = standard.unencode(tag['name'])
    if name != sTagName: return 0  # don't accept any unknown tag
    attrs = standard.unencode(tag['attrs'])
    cdata = standard.unencode(tag['cdata'])

    # -- ITEM (DICTIONARY|LIST) --
    #----------------------------
    if sTagName in ['dict', 'dictionary']:
      pass
    elif sTagName == 'list':
      pass
    elif sTagName == 'item':
      item = cdata
      if tag['dValueStack'] < len(self.dValueStack):
        item = self.dValueStack.pop()
      else:
        item = cdata
      item = getXmlTypeSaveValue(item, attrs)
      value = self.dValueStack.pop()
      if isinstance(value, dict):
        key = attrs.get('key')
        value[key] = item
      if isinstance(value, list):
        value.append(item)
      self.dValueStack.append(value)

    # -- DATA (IMAGE|FILE) --
    #-----------------------
    elif sTagName == 'data':
      value = attrs
      if cdata is not None and len(cdata) > 0:
        filename = attrs.get('filename')
        content_type = attrs.get('content_type')
        try:
          data = standard.hex2bin(cdata)
        except:
          data = standard.pybytes(cdata,'utf-8')
        value['data'] = data
      self.dValueStack.append(value)

    # -- LANGUAGE --
    #--------------
    elif sTagName == 'lang':
      lang = attrs.get('id', self.getPrimaryLanguage())
      if len(self.dValueStack) == 1:
        item = cdata
      else:
        item = self.dValueStack.pop()
      values = self.dValueStack.pop()
      values[lang] = item
      self.dValueStack.append(values)

    # -- OBJECT-ATTRIBUTES --
    #-----------------------
    elif sTagName in self.getObjAttrs():
      if not skip:
        obj_attr = self.getObjAttr(sTagName)

        # -- DATATYPE
        datatype = obj_attr['datatype_key']

        # -- Multi-Language Attributes.
        if obj_attr['multilang']:
          item = self.dValueStack.pop()
          if item is not None:
            if not isinstance(item, dict):
              item = {self.getPrimaryLanguage():item}
            for s_lang in item:
              value = item[s_lang]
              # Data
              if datatype in _globals.DT_BLOBS:
                if isinstance(value, dict) and len(value.keys()) > 0:
                  ob = _blobfields.createBlobField(self, datatype)
                  for key in value:
                    setattr(ob, key, value[key])
                  xmlInitObjProperty(self, sTagName, ob, s_lang)
              # Others
              else:
                # -- Init Properties.
                xmlInitObjProperty(self, sTagName, value, s_lang)

        else:
          # -- Complex Attributes (Blob|Dictionary|List).
          value = None
          if len(self.dValueStack) > 0:
            value = self.dValueStack.pop()
          if value is not None and \
             (datatype in _globals.DT_BLOBS or \
               datatype == _globals.DT_LIST or \
               datatype == _globals.DT_DICT):
            # Data
            if datatype in _globals.DT_BLOBS:
              if isinstance(value, dict) and len(value.keys()) > 0:
                ob = _blobfields.createBlobField(self, datatype)
                for key in value:
                  setattr(ob, key, value[key])
                xmlInitObjProperty(self, sTagName, ob)
            # Others
            else: 
              if self.getType() == 'ZMSRecordSet':
                if isinstance(value, list):
                  for item in value:
                    if isinstance(item, dict):
                      for key in item:
                        item_obj_attr = self.getObjAttr(key)
                        item_datatype = item_obj_attr['datatype_key']
                        if item_datatype in _globals.DT_BLOBS:
                          item_data = item[ key]
                          if isinstance(item_data, dict):
                            blob = _blobfields.createBlobField(self, item_datatype, item_data)
                            item[ key] = blob
              # -- Convert multilingual to monolingual attributes.
              if obj_attr['multilang'] == 0 and \
                 isinstance(value, dict) and \
                 len(value.keys()) == 1 and \
                 value.keys()[0] == self.getPrimaryLanguage():
                value = value[value.keys()[0]]
              xmlInitObjProperty(self, sTagName, value)
            if len(self.dValueStack) > 0:
              raise "Items on self.dValueStack=%s" % self.dValueStack

          # -- Simple Attributes (String, Integer, etc.)
          else:
            if value is not None:
              standard.writeBlock(self, "[xmlOnUnknownEndTag]: WARNING - Skip %s" % sTagName)
            value = cdata
            # -- OPTIONS
            if 'options' in obj_attr:
              options = obj_attr['options']
              if isinstance(options, list):
                try:
                  i = options.index(int(value))
                  if i % 2 == 1: value = options[i - 1]
                except:
                  try:
                    i = options.index(value)
                    if i % 2 == 1: value = options[i - 1]
                  except:
                    pass
            xmlInitObjProperty(self, sTagName, value)

        # Clear value stack.
        self.dValueStack.clear()

    # -- OTHERS --
    #------------                            
    else:
      value = None
      if len(self.dTagStack): value = self.dTagStack.pop()
      if value is None: value = {'cdata':''}
      cdata = value.get('cdata', '')
      cdata += '<' + tag['name']
      for attr_name in attrs:
        attr_value = attrs.get(attr_name)
        cdata += ' ' + attr_name + '="' + attr_value + '"'
      cdata += '>' + tag['cdata']
      cdata += '</' + tag['name'] + '>'
      value['cdata'] = cdata
      self.dTagStack.append(value)

    return 1  # accept matching end tag


"""
################################################################################
#
#  Export
#
################################################################################
"""

# ------------------------------------------------------------------------------
#  _xmllib.toCdata
# ------------------------------------------------------------------------------
def toCdata(self, s, xhtml=False):
  rtn = ''

  # Return Text (HTML) in CDATA as XHTML.
  from Products.zms import _filtermanager
  processId = 'tidy'
  if not xhtml \
     and self.getConfProperty('ZMS.export.xml.tidy', 0) \
     and processId in self.getProcessIds():

    # Create temporary folder.
    folder = tempfile.mktemp()
    os.mkdir(folder)

    # Save <HTML> to file.
    filename = _fileutil.getOSPath('%s/xhtml.html' % folder)
    _fileutil.exportObj(s, filename)

    # Call <HTML>Tidy
    processOb = self.getProcess(processId)
    command = processOb.get('command')
    if command.find('{trans}') >= 0:
      trans = _fileutil.getOSPath(package_home(globals()) + '/conf/xsl/tidy.html2xhtml.conf')
      command = command.replace('{trans}', trans)
    filename = _filtermanager.processCommand(self, filename, command)

    # Read <XHTML> from file.
    f = open(htmfilename, 'rb')
    rtn = f.read().strip()
    f.close()

    # Read Error-Log from file.
    f = open(logfilename, 'rb')
    log = f.read().strip()
    f.close()

    # Remove temporary files.
    _fileutil.remove(folder, deep=1)

    # Process <XHTML>.
    prefix = '<p>'
    if s[:len(prefix)] != prefix and rtn[:len(prefix)] == prefix:
      rtn = rtn[len(prefix):]
      suffix = '</p>'
      if s[-len(suffix):] != suffix and rtn[-len(suffix):] == suffix:
        rtn = rtn[:-len(suffix)]
    f.close()

    # Process Error-Log.
    if log.find('0 errors') < 0:
      rtn += '<!-- ' + log + '-->'

  # Return Text.
  elif standard.is_str(s) and s.find(' ') < 0 and s.find('<') < 0 and s.find('&') < 0:
    rtn = s

  # Return Text in CDATA.
  elif s is not None:
    if standard.is_bytes(s):
      s = standard.pystr(s)
    # Hack for invalid characters
    s = s.replace(chr(30), '')
    # Hack for nested CDATA
    s = re.compile(r'\<\!\[CDATA\[(.*?)\]\]\>').sub(r'<!{CDATA{\1}}>', s)
    # Wrap with CDATA
    rtn = '<![CDATA[%s]]>' % s

  # Return.
  return rtn


# ------------------------------------------------------------------------------
#  _xmllib.toXml:
# ------------------------------------------------------------------------------
def toXml(self, value, indentlevel=0, xhtml=False, encoding='utf-8'):
  xml = []
  if value is not None:

    # Image
    if isinstance(value, _blobfields.MyImage):
      xml.append('\n' + indentlevel * INDENTSTR + value.toXml(self))

    # File
    elif isinstance(value, _blobfields.MyFile):
      xml.append('\n' + indentlevel * INDENTSTR + value.toXml(self))

    # File (Zope-native)
    elif isinstance(value, File):
      tagname = 'data'
      content_type = value.content_type
      xml.append('\n' + indentlevel * INDENTSTR)
      xml.append('<%s' % tagname)
      xml.append(' content_type="%s"' % content_type)
      xml.append(' filename="%s"' % value.title)
      xml.append(' type="file"')
      xml.append('>')
      data = zopeutil.readData(value)
      if content_type.startswith('text/') or content_type in ['application/css','application/javascript','image/svg']:
        data = standard.pystr(data,'utf-8')
      cdata = None
      # Ensure CDATA is valid.
      try:
        cdata = '<![CDATA[%s]]>'%data
        p = pyexpat.ParserCreate()
        rv = p.Parse('<?xml version="1.0" encoding="utf-8"?><%s>%s</%s>'%(tagname,cdata,tagname), 1)
      # Otherwise use binary encoding.
      except:
        cdata = standard.bin2hex(standard.pybytes(data))
      xml.append(cdata)
      xml.append('</%s>' % tagname)

    # Dictionaries
    elif isinstance(value, dict):
      keys = sorted(value)
      xml.append('\n' + indentlevel * INDENTSTR)
      xml.append('<dictionary>')
      indentstr = '\n' + (indentlevel + 1) * INDENTSTR
      for x in keys:
        k = ' key="%s"' % x
        xv = value[x]
        tv = getXmlType(xv)
        sv = toXml(self, xv, indentlevel + 2, xhtml, encoding)
        xml.append(indentstr)
        xml.append('<item%s%s>' % (k, tv))
        xml.append(sv)
        if sv.find('\n') >= 0:
          xml.append(indentstr)
        xml.append('</item>')
      xml.append('\n' + indentlevel * INDENTSTR)
      xml.append('</dictionary>')

    # Lists
    elif isinstance(value, list):
      xml.append('\n' + indentlevel * INDENTSTR)
      xml.append('<list>')
      indentstr = '\n' + (indentlevel + 1) * INDENTSTR
      for xv in value:
        k = ''
        tv = getXmlType(xv)
        sv = toXml(self, xv, indentlevel + 2, xhtml, encoding)
        xml.append(indentstr)
        xml.append('<item%s%s>' % (k, tv))
        xml.append(sv)
        if sv.startswith('\n'):
          xml.append(indentstr)
        xml.append('</item>')
      xml.append('\n' + indentlevel * INDENTSTR)
      xml.append('</list>')

    # Tuples (DateTime)
    elif isinstance(value, tuple) or isinstance(value, time.struct_time) or isinstance(value, DateTime):
      try:
        s_value = self.getLangFmtDate(value, 'eng', 'DATETIME_FMT')
        if len(s_value) > 0:
          xml.append('\n' + indentlevel * INDENTSTR)
          xml.append(toCdata(self, s_value, -1))
      except:
        pass

    # Numbers
    elif isinstance(value, int) or isinstance(value, float):
      xml.append(value)

    else:
      # Zope-Objects
      try: meta_type = value.meta_type
      except: meta_type = None
      if meta_type is not None:
        value = zopeutil.readData(value)
      if value:
        xml.append(toCdata(self, value, xhtml))

  # Return xml.
  return ''.join([standard.pystr(x) for x in xml])


# ------------------------------------------------------------------------------
#  _xmllib.getAttrToXml:
# ------------------------------------------------------------------------------
def getAttrToXml(self, base_path, data2hex, obj_attr, REQUEST):
  xml = ''

  # -- DATATYPE
  datatype = obj_attr['datatype_key']

  # -- VALUE
  obj_vers = self.getObjVersion(REQUEST)
  value = self._getObjAttrValue(obj_attr, obj_vers, REQUEST.get('lang', self.getPrimaryLanguage()))

  if value is not None:

    # Retrieve value from options.
    if 'options' in obj_attr:
      options = obj_attr['options']
      try:
        i = options.index(int(value))
        if i % 2 == 0: value = options[i + 1]
      except:
        try:
          i = options.index(str(value))
          if i % 2 == 0: value = options[i + 1]
        except:
          pass

    #-- Blob-Fields
    if datatype in _globals.DT_BLOBS:
      xml += value.toXml(self, base_path, data2hex)

    #-- Text-Fields
    elif datatype in _globals.DT_TEXTS:
      request = self.REQUEST
      request.set('ExtensionPoint.ZReferableItem.getRefObjPath','disabled')
      value = self.validateInlineLinkObj(value)
      xml += toXml(self, value)
      
    #-- Url-Fields
    elif datatype == _globals.DT_URL:
      request = self.REQUEST
      request.set('ExtensionPoint.ZReferableItem.getRefObjPath','disabled')
      value = self.validateLinkObj(value)
      xml += toXml(self, value)
    
    # XML.
    elif datatype == _globals.DT_XML or \
         datatype == _globals.DT_BOOLEAN or \
         datatype in _globals.DT_NUMBERS:
      xml += toXml(self, value, -1)

    # Others.
    else:
      xml += toXml(self, value)

  # Return xml.
  return xml


# ------------------------------------------------------------------------------
#  _xmllib.getObjPropertyToXml:
# ------------------------------------------------------------------------------
def getObjPropertyToXml(self, base_path, data2hex, obj_attr, REQUEST):
  xml = ''
  # Multi-Language Attributes.
  indentlevel = len(base_path.split('/'))
  if obj_attr['multilang']:
    lang = REQUEST.get('lang')
    langIds = self.getLangIds()
    for langId in langIds:
      REQUEST.set('lang', langId)
      s_attr_xml = getAttrToXml(self, base_path, data2hex, obj_attr, REQUEST)
      if len(s_attr_xml) > 0:
        xml += '<lang%s>%s</lang>' % ( [ '' , ' id="%s"'%langId ][ int(len(langIds)>1) ] , s_attr_xml )
    REQUEST.set('lang', lang)
  # Simple Attributes.
  else:
    xml += getAttrToXml(self, base_path, data2hex, obj_attr, REQUEST)
  # Return xml.
  return xml


# ------------------------------------------------------------------------------
#  _xmllib.getObjToXml:
# ------------------------------------------------------------------------------
def getObjToXml(self, REQUEST, deep=True, base_path='', data2hex=False):
  # Check Constraints.
  root = getattr(self, '__root__', None)
  if root is not None:
    return ''
  xml = []
  # Start tag.
  indentlevel = len(base_path.split('/'))
  xml.append('%s<%s' % ( indentlevel * INDENTSTR, self.meta_id ) )
  xml.append(' uid="%s"' % self.get_uid() )
  id = self.id 
  prefix = standard.id_prefix(id)
  if id == prefix:
    xml.append(' id_fix="%s"' % id)
  else:
    xml.append(' id="%s"' % id)
    xml.append(' id_prefix="%s"' % standard.id_prefix(id))
  xml.append('>\n')
  # Attributes.
  keys = self.getObjAttrs().keys()
  if self.getType() == 'ZMSRecordSet':
    keys = ['active', self.getMetaobjAttrIds(self.meta_id,types=['list'])[0]]
  for key in keys:
    obj_attr = self.getObjAttr(key)
    if obj_attr['xml'] or key in ['change_dt','change_uid','created_dt','created_uid']:
      ob_prop = getObjPropertyToXml(self, base_path, data2hex, obj_attr, REQUEST)
      if len(ob_prop) > 0:
        xml.append('%s<%s>%s</%s>\n' % ( (indentlevel+1) * INDENTSTR, key, ob_prop, key ) )
  # Process children.
  if deep:
    xml.extend([getObjToXml(x, REQUEST, deep, base_path + x.id + '/', data2hex) for x in self.getChildNodes()])
  # End tag.
  xml.append('%s</%s>\n' % ( indentlevel * INDENTSTR, self.meta_id ) )
  # Return xml.
  return ''.join(xml)


"""
################################################################################
# class ParseError(Exception):
#
# General exception class to indicate parsing errors.
################################################################################
"""
class ParseError(Exception): pass



"""
################################################################################
# class XmlAttrBuilder:
#
# Parser for complex Python-Attributes (dictionaries, lists).
################################################################################
"""
class XmlAttrBuilder(object):
    "class XmlAttrBuilder"

    ######## class variables ########
    iBufferSize = 1028 * 32  # buffer size for XML file parsing

    ############################################################################
    # XmlAttrBuilder.__init__(self):
    #
    # Constructor.
    ############################################################################
    def __init__(self):
      """ XmlAttrBuilder.__init__ """
      pass


    ############################################################################
    # XmlAttrBuilder.parse(self, input):
    #
    # Parse a given XML document.
    #
    # IN:  input = XML document as string
    #            = XML document as file object
    # OUT: value or None, if nothing was parsed
    ############################################################################
    def parse(self, input):
      """ XmlAttrBuilder.parse """

      # prepare builder
      self.dValueStack = collections.deque()
      self.dTagStack = collections.deque()

      # create parser object
      p = pyexpat.ParserCreate()

      # connect parser object with handler methods
      p.StartElementHandler = self.OnStartElement
      p.EndElementHandler = self.OnEndElement
      p.CharacterDataHandler = self.OnCharacterData
      p.StartCdataSectionHandler = self.OnStartCData
      p.EndCdataSectionHandler = self.OnEndCData
      p.ProcessingInstructionHandler = self.OnProcessingInstruction
      p.CommentHandler = self.OnComment
      p.StartNamespaceDeclHandler = self.OnStartNamespaceDecl
      p.EndNamespaceDeclHandler = self.OnEndNamespaceDecl

      #### parsing ####
      if standard.is_bytes(input):
        # input is a string!
        rv = p.Parse(input, 1)
      else:
        # input is a file object!
        while True:

          v = input.read(self.iBufferSize)
          if len(v) == 0:
            rv = 1
            break

          rv = p.Parse(v, 0)
          if not rv:
            break

      # raise parser exception
      if not rv:
        raise ParseError('%s at line %s' % (pyexpat.ErrorString(p.ErrorCode), p.ErrorLineNumber))

      return self.dValueStack.pop()


    ############################################################################
    # XmlAttrBuilder.OnStartElement(self, name, attrs):
    #
    # Handler of XML-Parser:
    # Called at the start of a XML element (resp. on occurence of a XML start tag).
    # Usually, the occurence of a XML tag induces the instanciation of a new node object. Therefore,
    # XmlAttrBuilder contains a mapping table ("dGlobalAttrs"), that maps XML tags to python classes. The
    # newly created node object is then made current. If no matching class is found for a XML tag,
    # the event handler "xmlOnUnknownStart()" is called on the current object.
    #
    # IN: name  = element name (=tag name)
    #     attrs = dictionary of element attributes
    ############################################################################
    def OnStartElement(self, sTagName, dTagAttrs):
      """ XmlAttrBuilder.OnStartElement """

      # -- TAG-STACK
      tag = {'name':sTagName, 'attrs':dTagAttrs, 'cdata':''}
      tag['dValueStack'] = len(self.dValueStack)
      self.dTagStack.append(tag)

      # -- VALUE-STACK
      if sTagName == 'data':
        self.dValueStack.append(None)
      elif sTagName == 'dictionary':
        self.dValueStack.append({})
      elif sTagName == 'list':
        self.dValueStack.append([])


    ############################################################################
    # XmlAttrBuilder.OnEndElement(self, name):
    #
    # Handler of XML-Parser:
    # Called at the end of a XML element (resp. on occurence of a XML end tag).
    #
    # IN: name  = element name (=tag name)
    ############################################################################
    def OnEndElement(self, sTagName):
      """ XmlAttrBuilder.OnEndElement """

      # -- TAG-STACK
      tag = self.dTagStack.pop()
      name = standard.unencode(tag['name'])
      attrs = standard.unencode(tag['attrs'])
      cdata = standard.unencode(tag['cdata'])
      # Hack for nested CDATA
      cdata = re.compile(r'\<\!\{CDATA\{(.*?)\}\}\>').sub(r'<![CDATA[\1]]>',cdata)

      if name != sTagName:
        raise ParseError("Unmatching end tag (" + str(sTagName) + ") expected (" + str(name) + ")")

      # -- DATA
      if sTagName in ['data']:
        filename = attrs.get('filename')
        content_type = attrs.get('content_type')
        try:
          data = standard.hex2bin(cdata)
        except:
          data = standard.pybytes(cdata,'utf-8')
        file = {'data':data, 'filename':filename, 'content_type':content_type}
        objtype = attrs.get('type')
        item = _blobfields.createBlobField(None, objtype, file)
        for key in attrs:
          value = attrs.get(key)
          setattr(item, key, value)
        self.dValueStack.pop()
        self.dValueStack.append(item)

      # -- ITEM
      elif sTagName in ['item']:
        if tag['dValueStack'] < len(self.dValueStack):
          item = self.dValueStack.pop()
        else:
          item = cdata
        item = getXmlTypeSaveValue(item, attrs)
        value = self.dValueStack.pop()
        if isinstance(value, dict):
          key = attrs.get('key')
          value[key] = item
        if isinstance(value, list):
          value.append(item)
        self.dValueStack.append(value)


    ############################################################################
    # XmlAttrBuilder.OnCharacterData(self, data):
    #
    # Handler of XML-Parser:
    # Called after plain character data was parsed. Forwards the character data to the current
    # node. The class attribute "bInCData" determines, wether the character data is nested in a
    # CDATA block.
    #
    # IN: data = character data string
    ############################################################################
    def OnCharacterData(self, sData):
      """ XmlAttrBuilder.OnCharacterData """

      # -- TAG-STACK
      if len(self.dTagStack) > 0:
        tag = self.dTagStack.pop()
        tag['cdata'] += sData
        self.dTagStack.append(tag)


    ############################################################################
    # XmlAttrBuilder.OnStartCData(self):
    #
    # Handler of XML-Parser:
    # Called at the start of a CDATA block (resp. on occurence of the "CDATA[" tag).
    ############################################################################
    def OnStartCData(self):
      """ XmlAttrBuilder.OnStartCData """
      self.bInCData = 1


    ############################################################################
    # XmlAttrBuilder.OnEndCData(self):
    #
    # Handler of XML-Parser:
    # Called at the end of a CDATA block (resp. on occurence of the "]" tag).
    ############################################################################
    def OnEndCData(self):
      """ XmlAttrBuilder.OnEndCData """
      self.bInCData = 0


    ############################################################################
    # XmlAttrBuilder.OnProcessingInstruction(self, target, data):
    #
    # Handler of XML-Parser:
    # Called on occurence of a processing instruction.
    #
    # IN: target = target (processing instruction)
    #     data   = dictionary of data
    ############################################################################
    def OnProcessingInstruction(self, target, data):
      """ XmlAttrBuilder.OnProcessingInstruction """
      pass  # ignored


    ############################################################################
    # XmlAttrBuilder.OnComment(self, data):
    #
    # Handler of XML-Parser:
    # Called on occurence of a comment.
    #
    # IN: data = comment string
    ############################################################################
    def OnComment(self, data):
      """ XmlAttrBuilder.OnComment """
      pass  # ignored


    ############################################################################
    # XmlAttrBuilder.OnStartNamespaceDecl(self, prefix, uri):
    #
    # Handler of XML-Parser:
    # Called at the start of a namespace declaration.
    #
    # IN: prefix = prefix of namespace
    #     uri    = namespace identifier
    ############################################################################
    def OnStartNamespaceDecl(self, prefix, uri):
      """ XmlAttrBuilder.OnStartNamespaceDecl """
      pass  # ignored


    ############################################################################
    # XmlAttrBuilder.OnEndNamespaceDecl(self, prefix):
    #
    # Handler of XML-Parser:
    # Called at the end of a namespace declaration.
    #
    # IN: prefix = prefix of namespace
    ############################################################################
    def OnEndNamespaceDecl(self, prefix):
      """ XmlAttrBuilder.OnEndNamespaceDecl """
      pass  # ignored


def xmlNodeSet(mNode, sTagName='', iDeep=0):
  """
  Retrieve node-set for given tag-name from dictionary of XML-Node-Structure.
  @return: List of dictionaries of XML-Structure.
  @rtype: C{list}
  """
  lNodeSet = []
  lNode = mNode
  if isinstance(mNode, list) and len(mNode) == 2:
    lNode = mNode[1]
  lTags = lNode.get('tags', [])
  for i in range(0, len(lTags) // 2):
    lTagName = lTags[i * 2]
    lNode = lTags[i * 2 + 1]
    if sTagName in [lTagName, '']:
      lNodeSet.append(lNode)
    if iDeep == 1:
      lNodeSet.extend(xmlNodeSet(lNode, sTagName, iDeep))
  return lNodeSet


"""
################################################################################
# class XmlBuilder:
#
# Parser for custom xml.
################################################################################
"""

def xmlParse(xml):
  """
  Parse arbitrary XML-Structure into dictionary.
  @param data: the xml
  @type data: C{str} or C{StringIO}
  @return: Dictionary of XML-Structure.
  @rtype: C{dict}
  """
  builder = XmlBuilder()
  if isinstance(xml, str):
    xml = StringIO(xml)
  v = builder.parse(xml)
  return v


class XmlBuilder(object):
    "class XmlBuilder"

    ######## class variables ########
    iBufferSize = 1028 * 32  # buffer size for XML file parsing

    ############################################################################
    # XmlBuilder.__init__(self):
    #
    # Constructor.
    ############################################################################
    def __init__(self):
      """ XmlBuilder.__init__ """
      pass


    ############################################################################
    # XmlBuilder.parse(self, input):
    #
    # Parse a given XML document.
    #
    # IN:  input = XML document as string
    #            = XML document as file object
    # OUT: value or None, if nothing was parsed
    ############################################################################
    def parse(self, input):
        """ XmlBuilder.parse """

        # prepare builder
        self.dTagStack = collections.deque()
        self.dTagStack.append({'tags':[]})

        # create parser object
        p = pyexpat.ParserCreate()

        # connect parser object with handler methods
        p.StartElementHandler = self.OnStartElement
        p.EndElementHandler = self.OnEndElement
        p.CharacterDataHandler = self.OnCharacterData
        p.StartCdataSectionHandler = self.OnStartCData
        p.EndCdataSectionHandler = self.OnEndCData
        p.ProcessingInstructionHandler = self.OnProcessingInstruction
        p.CommentHandler = self.OnComment
        p.StartNamespaceDeclHandler = self.OnStartNamespaceDecl
        p.EndNamespaceDeclHandler = self.OnEndNamespaceDecl

        #### parsing ####
        if isinstance(input, bytes):
          # input is a string!
          rv = p.Parse(input, 1)
        else:
          # input is a file object!
          while True:

            v = input.read(self.iBufferSize)
            if len(v) == 0:
              rv = 1
              break

            rv = p.Parse(v, 0)
            if not rv:
              break

        # raise parser exception
        if not rv:
          raise ParseError('%s at line %s' % (pyexpat.ErrorString(p.ErrorCode), p.ErrorLineNumber))

        return self.dTagStack.pop()['tags']


    ############################################################################
    # XmlBuilder.OnStartElement(self, name, attrs):
    #
    # Handler of XML-Parser:
    # Called at the start of a XML element (resp. on occurence of a XML start tag).
    # Usually, the occurence of a XML tag induces the instanciation of a new node object. Therefore,
    # XmlBuilder contains a mapping table ("dGlobalAttrs"), that maps XML tags to python classes. The
    # newly created node object is then made current. If no matching class is found for a XML tag,
    # the event handler "xmlOnUnknownStart()" is called on the current object.
    #
    # IN: name  = element name (=tag name)
    #     attrs = dictionary of element attributes
    ############################################################################
    def OnStartElement(self, sTagName, dTagAttrs):
      """ XmlBuilder.OnStartElement """
      tag = {'name':sTagName, 'attrs':dTagAttrs, 'cdata':'', 'tags':[]}
      self.dTagStack.append(tag)


    ############################################################################
    # XmlBuilder.OnEndElement(self, name):
    #
    # Handler of XML-Parser:
    # Called at the end of a XML element (resp. on occurence of a XML end tag).
    #
    # IN: name  = element name (=tag name)
    ############################################################################
    def OnEndElement(self, sTagName):
      """ XmlBuilder.OnEndElement """
      
      lTag = self.dTagStack.pop()
      name = standard.unencode(lTag['name'])
      attrs = standard.unencode(lTag['attrs'])
      lCdata = standard.unencode(lTag['cdata'])
      lTags = standard.unencode(lTag['tags'])

      if name != sTagName:
        raise ParseError("Unmatching end tag (" + sTagName + ")")

      lTag = {}
      lTag['level'] = len(self.dTagStack)
      lTag['name'] = name
      lTag['attrs'] = attrs
      lCdata = lCdata.strip()
      if len(lCdata) > 0:
        lTag['cdata'] = lCdata
      if len(lTags) > 0:
        lTag['tags'] = lTags
      parent = self.dTagStack.pop()
      parent['tags'].append(name)
      parent['tags'].append(lTag)
      self.dTagStack.append(parent)


    ############################################################################
    # XmlBuilder.OnCharacterData(self, data):
    #
    # Handler of XML-Parser:
    # Called after plain character data was parsed. Forwards the character data to the current
    # node. The class attribute "bInCData" determines, wether the character data is nested in a
    # CDATA block.
    #
    # IN: data = character data string
    ############################################################################
    def OnCharacterData(self, sData):
      """ XmlBuilder.OnCharacterData """
      tag = self.dTagStack.pop()
      tag['cdata'] = tag['cdata'] + sData
      self.dTagStack.append(tag)


    ############################################################################
    # XmlBuilder.OnStartCData(self):
    #
    # Handler of XML-Parser:
    # Called at the start of a CDATA block (resp. on occurence of the "CDATA[" tag).
    ############################################################################
    def OnStartCData(self):
      """ XmlBuilder.OnStartCData """
      self.bInCData = 1


    ############################################################################
    # XmlBuilder.OnEndCData(self):
    #
    # Handler of XML-Parser:
    # Called at the end of a CDATA block (resp. on occurence of the "]" tag).
    ############################################################################
    def OnEndCData(self):
      """ XmlBuilder.OnEndCData """
      self.bInCData = 0


    ############################################################################
    # XmlBuilder.OnProcessingInstruction(self, target, data):
    #
    # Handler of XML-Parser:
    # Called on occurence of a processing instruction.
    #
    # IN: target = target (processing instruction)
    #     data   = dictionary of data
    ############################################################################
    def OnProcessingInstruction(self, target, data):
      """ XmlBuilder.OnProcessingInstruction """
      pass  # ignored


    ############################################################################
    # XmlBuilder.OnComment(self, data):
    #
    # Handler of XML-Parser:
    # Called on occurence of a comment.
    #
    # IN: data = comment string
    ############################################################################
    def OnComment(self, data):
      """ XmlBuilder.OnComment """
      pass  # ignored


    ############################################################################
    # XmlBuilder.OnStartNamespaceDecl(self, prefix, uri):
    #
    # Handler of XML-Parser:
    # Called at the start of a namespace declaration.
    #
    # IN: prefix = prefix of namespace
    #     uri    = namespace identifier
    ############################################################################
    def OnStartNamespaceDecl(self, prefix, uri):
      """ XmlBuilder.OnStartNamespaceDecl """
      pass  # ignored


    ############################################################################
    # XmlBuilder.OnEndNamespaceDecl(self, prefix):
    #
    # Handler of XML-Parser:
    # Called at the end of a namespace declaration.
    #
    # IN: prefix = prefix of namespace
    ############################################################################
    def OnEndNamespaceDecl(self, prefix):
      """ XmlBuilder.OnEndNamespaceDecl """
      pass  # ignored

###############################################################################################
