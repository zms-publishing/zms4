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
from Products.PageTemplates.Expressions import SecureModuleImporter
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
import six
import sys

# MD5
import AccessControl
import hashlib

class MD5DigestScheme(object):

  def encrypt(self, pw):
    enc = hashlib.md5(pw)
    enc = enc.hexdigest()
    return enc

  def validate(self, reference, attempt):
    compare = self.encrypt(attempt)[:-1]
    return (compare == reference)

import AccessControl.AuthEncoding
AccessControl.AuthEncoding.registerScheme('MD5', MD5DigestScheme())


# Umlauts
umlaut_map = {
        # German
        u'ä': 'ae',
        u'ö': 'oe',
        u'ü': 'ue',
        u'Ä': 'Ae',
        u'Ö': 'Oe',
        u'Ü': 'Ue',
        u'ß': 'ss',
        # Cyrillic
        u'а': 'a',
        u'б': 'b',
        u'в': 'v',
        u'г': 'g',
        u'д': 'd',
        u'е': 'e',
        u'ё': 'e',
        u'ж': 'zh',
        u'з': 'z',
        u'и': 'i',
        u'й': 'j',
        u'к': 'k',
        u'л': 'l',
        u'м': 'm',
        u'н': 'n',
        u'о': 'o',
        u'п': 'p',
        u'р': 'r',
        u'с': 's',
        u'т': 't',
        u'у': 'u',
        u'ф': 'f',
        u'х': 'h',
        u'ц': 'c',
        u'ч': 'ch',
        u'ш': 'sh',
        u'щ': 'sch',
        u'ь': "'",
        u'ы': 'y',
        u'ь': "'",
        u'э': 'e',
        u'ю': 'ju',
        u'я': 'ja',
        u'А': 'A',
        u'Б': 'B',
        u'В': 'V',
        u'Г': 'G',
        u'Д': 'D',
        u'Е': 'E',
        u'Ё': 'E',
        u'Ж': 'ZH',
        u'З': 'Z',
        u'И': 'I',
        u'Й': 'J',
        u'К': 'K',
        u'Л': 'L',
        u'М': 'M',
        u'Н': 'N',
        u'О': 'O',
        u'П': 'P',
        u'Р': 'R',
        u'С': 'S',
        u'Т': 'T',
        u'У': 'U',
        u'Ф': 'F',
        u'Х': 'H',
        u'Ц': 'C',
        u'Ч': 'CH',
        u'Ш': 'SH',
        u'Щ': 'SCH',
        u'Ъ': "'",
        u'Ы': 'Y',
        u'Ь': "'",
        u'Э': 'E',
        u'Ю': 'JU',
        u'Я': 'JA',}

def sort_item( i):
  if isinstance(i, bytes):
    i = i.decode('utf-8')
  if isinstance(i, str):
    mapping = umlaut_map
    for key in mapping.keys():
      try: i = i.replace(key, mapping[key])
      except: pass
  return i


# Datatypes.
DT_UNKNOWN = 0
DT_BOOLEAN = 1
DT_DATE = 2
DT_DATETIME = 3
DT_DICT = 4
DT_FILE = 5
DT_FLOAT = 6
DT_IMAGE = 7
DT_INT = 8
DT_LIST = 9
DT_PASSWORD = 10
DT_STRING = 11
DT_TEXT = 12
DT_TIME = 13
DT_URL = 14
DT_ID = 15
DT_XML = 16
DT_AMOUNT = 17
DT_TEXTS = [ DT_STRING, DT_TEXT ]
DT_STRINGS = [ DT_STRING, DT_TEXT, DT_URL, DT_PASSWORD, DT_XML ]
DT_BLOBS = [ DT_IMAGE, DT_FILE ]
DT_INTS = [ DT_INT, DT_BOOLEAN ]
DT_NUMBERS = [ DT_INT, DT_FLOAT, DT_AMOUNT ]
DT_DATETIMES = [ DT_DATE, DT_TIME, DT_DATETIME ]

datatype_map = [
  [ 'unknown', ''],
  [ 'boolean', 0],
  [ 'date', None],
  [ 'datetime', None],
  [ 'dictionary', {}],
  [ 'file', None],
  [ 'float', 0.0],
  [ 'image', None],
  [ 'int', 0],
  [ 'list', []],
  [ 'password', ''],
  [ 'string', ''],
  [ 'text', ''],
  [ 'time', None],
  [ 'url', ''],
  [ 'identifier', ''],
  [ 'xml', ''],
  [ 'amount', 0.0],
]

def datatype_key(datatype):
  for dt_index in range(len(datatype_map)):
    if datatype_map[dt_index][0] == datatype:
      return dt_index
  else:
    return DT_UNKNOWN


def is_str_type(v):
  """
  Is str type.
  @param
  @return
  @rtype: C(Boolean)
  """
  return isinstance(v, bytes) or isinstance(v, str)


def get_size(v):
  """
  Returns size of given object v in bytes.
  @return: Size in bytes
  @rtype: C{int}
  """
  if hasattr(v, 'get_real_size') and callable(getattr(v, 'get_real_size')):
      return v.get_real_size()
  elif hasattr(v, 'get_size') and callable(getattr(v, 'get_size')):
      return v.get_size()
  return sys.getsizeof(v)


################################################################################
# Define StaticPageTemplateFile.
################################################################################
class StaticPageTemplateFile(PageTemplateFile):
  def setEnv(self, context, options):
    self.context = context
    self.options = options
  def pt_getContext(self):
    root = self.context.getPhysicalRoot()
    context = self.context
    options = self.options
    c = {'template': self,
         'here': context,
         'context': context,
         'options': options,
         'root': root,
         'request': getattr(root, 'REQUEST', None),
         'modules': SecureModuleImporter,
         }
    return c


################################################################################
# Define MyClass.
################################################################################
if six.PY2:
  # class MyClass:
  # class MyClass(object):
  class MyClass:

    # ----------------------------------------------------------------------------
    #  MyClass.keys:
    # ----------------------------------------------------------------------------
    def keys(self):
      return self.__dict__.keys()

if six.PY3:
  class MyClass(object):
  
    # ----------------------------------------------------------------------------
    #  MyClass.keys:
    # ----------------------------------------------------------------------------
    def keys(self):
      return self.__dict__.keys()


################################################################################
# Define MySectionizer.
################################################################################
class MySectionizer(object):

    # --------------------------------------------------------------------------
    #  MySectionizer.__init__:
    #
    #  Constructor.
    # --------------------------------------------------------------------------
    def __init__(self, levelnfc='0'):
      self.levelnfc = levelnfc
      self.sections = []

    # --------------------------------------------------------------------------
    #  MySectionizer.__str__:
    #
    #  Returns a string representation of the object.
    # --------------------------------------------------------------------------
    def __str__(self):
      s = ''
      for i in range(len(self.sections)):
        if self.levelnfc == '0':
          s += str(self.sections[i]) + '.'
        elif self.levelnfc == '1':
          s += chr(self.sections[i] - 1 + ord('A')) + '.'
        elif self.levelnfc == '2':
          s += chr(self.sections[i] - 1 + ord('a')) + '.'
      return s

    # --------------------------------------------------------------------------
    #  MySectionizer.clone:
    #
    #  Creates and returns a copy of this object.
    # --------------------------------------------------------------------------
    def clone(self):
      ob = MySectionizer(self.levelnfc)
      ob.sections = copy.deepcopy(self.sections)
      return ob

    # --------------------------------------------------------------------------
    #  MySectionizer.getLevel:
    # --------------------------------------------------------------------------
    def getLevel(self):
      return len(self.sections)

    # --------------------------------------------------------------------------
    #  MySectionizer.processLevel:
    # --------------------------------------------------------------------------
    def processLevel(self, level):
      # Increase section counter on this level.
      if level > 0:
        if level == len(self.sections):
          self.sections[level-1] = self.sections[level-1] + 1
        elif level > len(self.sections):
          for i in range(len(self.sections), level):
            self.sections.append(1)
        elif level < len(self.sections):
          for i in range(level, len(self.sections)):
            del self.sections[len(self.sections)-1]
          self.sections[level-1] = self.sections[level-1] + 1

################################################################################
