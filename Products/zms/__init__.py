################################################################################
# Initialisation file for the ZMS Product for Zope
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
#
################################################################################

# Imports.
from __future__ import absolute_import
from App.Common import package_home
import OFS.misc_
import codecs
import fnmatch
import os
import re
import six
# Product Imports.
from Products.zms import _confmanager
from Products.zms import _multilangmanager
from Products.zms import _mediadb
from Products.zms import _sequence
from Products.zms import _zmsattributecontainer
from Products.zms import standard
from Products.zms import zms
from Products.zms import zmscustom
from Products.zms import zmssqldb
from Products.zms import zmslinkcontainer
from Products.zms import zmslinkelement
from Products.zms import ZMSZCatalogAdapter
from Products.zms import ZMSFilterManager
from Products.zms import ZMSFormatProvider, ZMSFormatProviderAcquired
from Products.zms import ZMSMetacmdProvider, ZMSMetacmdProviderAcquired
from Products.zms import ZMSWorkflowProvider, ZMSWorkflowProviderAcquired
from Products.zms import ZMSRepositoryManager

"""ZMS Product"""
# Documentation string.
__doc__ = """initialization module."""
# Version string.
__version__ = '0.1'

try:
  from Products.CMFCore.DirectoryView import registerFileExtension
  from Products.CMFCore.FSFile import FSFile
  registerFileExtension('xlsx', FSFile)
  registerFileExtension('xls', FSFile)
  registerFileExtension('doc', FSFile)
  registerFileExtension('docx', FSFile)
  registerFileExtension('ppt', FSFile)
  registerFileExtension('pptx', FSFile)
  registerFileExtension('map', FSFile)
  registerFileExtension('svg', FSFile)
  registerFileExtension('ttf', FSFile)
  registerFileExtension('eot', FSFile)
  registerFileExtension('woff', FSFile)
  registerFileExtension('woff2', FSFile)
  registerFileExtension('mp3', FSFile)
  registerFileExtension('mp4', FSFile)
  registerFileExtension('json', FSFile)
except:
  pass

################################################################################
# Define the initialize() function.
################################################################################

def initialize(context): 
    """Initialize the product."""
    
    try: 
        """Try to register the product."""
        
        context.registerClass(
            zms.ZMS,
            permission = 'Add ZMSs',
            constructors = ( zms.manage_addZMSForm, zms.manage_addZMS),
            container_filter = zms.containerFilter,
            )
        context.registerClass(
            zmscustom.ZMSCustom,
            permission = 'Add ZMSs',
            constructors = (zmscustom.manage_addZMSCustomForm, zmscustom.manage_addZMSCustom),
            container_filter = zmscustom.containerFilter,
            )
        context.registerClass(
            zmssqldb.ZMSSqlDb,
            permission = 'Add ZMSs',
            constructors = (zmssqldb.manage_addZMSSqlDbForm, zmssqldb.manage_addZMSSqlDb),
            container_filter = zmscustom.containerFilter,
            )
        context.registerClass(
            zmslinkcontainer.ZMSLinkContainer,
            permission = 'Add ZMSs',
            constructors = (zmscustom.manage_addZMSCustomForm, zmscustom.manage_addZMSCustom),
            container_filter = zmscustom.containerFilter,
            )
        context.registerClass(
            zmslinkelement.ZMSLinkElement,
            permission = 'Add ZMSs',
            constructors = (zmscustom.manage_addZMSCustomForm, zmscustom.manage_addZMSCustom),
            container_filter = zmscustom.containerFilter,
            )
        context.registerClass(
            _mediadb.MediaDb,
            permission = 'Add ZMSs',
            constructors = (_mediadb.manage_addMediaDb, _mediadb.manage_addMediaDb),
            container_filter = _mediadb.containerFilter,
            )
        context.registerClass(
            _zmsattributecontainer.ZMSAttributeContainer,
            permission = 'Add ZMSs',
            constructors = (_zmsattributecontainer.manage_addZMSAttributeContainer, _zmsattributecontainer.manage_addZMSAttributeContainer),
            container_filter = _zmsattributecontainer.containerFilter,
            )
        
        # register deprecated classes
        dummy_constructors = (zmscustom.manage_addZMSCustomForm, zmscustom.manage_addZMSCustom,)
        dummy_permission = 'Add ZMSs'
        zms.NoETagAdapter.register()
        
        # automated registration of language-dictionary
        if not hasattr(OFS.misc_.misc_,'zms'):
          OFS.misc_.misc_.zms = {}
        OFS.misc_.misc_.zms['langdict']=_multilangmanager.langdict()
        
        # automated registration of configuration
        confdict = _confmanager.ConfDict.get()
        OFS.misc_.misc_.zms['confdict']=confdict
        
        # automated minification
        confkeys = confdict.keys()
        for confkey in [x for x in confkeys if x.startswith('gen.') and x+'.include' in confkeys]:
          gen = confdict.get(confkey+'.include').split(',')
          if gen[0] != '':
            standard.writeStdout(context, "automated minification: %s=%s"%(confkey, str(confdict.get(confkey))))
            fileobj = open(translate_path(confdict.get(confkey)), 'w')
            for key in gen:
              fn = translate_path(confdict.get(key))
              fh = open(fn, 'r')
              fc = fh.read()
              fh.close()
              l0 = len(fc)
              if fn.find('.min.') > 0 or fn.find('-min.') > 0:
                standard.writeStdout(context, "add %s (%i Bytes)"%(fn, l0))
              else:
                # Pack
                s0 = []
                s1 = []
                s2 = []
                s3 = []
                if fn.endswith('.js'):
                  s0 = [ \
                      '\$ZMI\.writeDebug\((.*?)\);', \
                      '/\*(\!|\*|\s)((.|\n|\r|\t)*?)\*/', \
                      '//( |-|\$)((.|\r|\t)*?)\n', \
                    ]
                  s1 = ['=', '+', '-', '(', ')', ';', ',', ':', '&', '|']
                  s2 = []
                  s3 = ['\t', ' ', '{ ', '{', '{\n', '{', ' }', '}', ';}', '}', ',\n', ',', ';\n', ';', '\n ', '\n', '  ', ' ', '\n\n', '\n', '}\n}\n', '}}\n']
                elif fn.endswith('.css'):
                  s0 = [ \
                      '/\*((.|\n|\r|\t)*?)\*/', \
                    ]
                  s1 = ['=', '+', '{', '}', '(', ';', ',', ':']
                  s2 = [') ', '}\n']
                  s3 = ['\t', ' ', '  ', ' ', '\n\n', '\n', ';}', '}']
                fc = fc.strip()
                for s in s0:
                  l1 = len(fc)
                  fc = re.sub(s, '', fc)
                while True:
                  done = False
                  for k in s1:
                    for sk in [' ', '\n']:
                      while fc.find(sk+k)>=0:
                        fc=fc.replace(sk+k, k)
                        done = True
                      while k+sk not in s2 and fc.find(k+sk)>=0:
                        fc=fc.replace(k+sk, k)
                        done = True
                  d = s3
                  for i in range(len(d)//2):
                    k = d[i*2]
                    v = d[i*2+1]
                    while fc.find(k) >= 0:
                      l1 = len(fc)
                      fc = fc.replace(k, v)
                      done = True
                  if not done:
                    break
                l1 = len(fc)
                standard.writeStdout(context, "add %s (Packed: %i -> %i Bytes)"%(fn, l0, l1))
              fileobj.write(fc)
            fileobj.close()
        
        # automated generation of language JavaScript
        from xml.dom import minidom
        filename = os.sep.join([package_home(globals())]+['import', '_language.xml'])
        standard.writeStdout(context, "automated generation of language JavaScript: %s"%filename)
        xmldoc = minidom.parse(filename)
        langs = None
        d = {}
        for row in xmldoc.getElementsByTagName('Row'):
          cells = row.getElementsByTagName('Cell')
          if langs is None:
            langs = []
            for cell in cells:
              data = getData(cell)
              if data is not None:
                langs.append(data)
          else:
            l = []
            for cell in cells:
              data = getData(cell)
              if cell.attributes.get('ss:Index') is not None:
                while len(l) < int(cell.attributes['ss:Index'].value) - 1:
                  l.append(None)
              l.append(data)
            if len(l) > 1:
              k = l[0]
              d[k] = {}
              for i in range(len(l)-1):
                d[k][langs[i]] = l[i+1]

        # populate language-strings to i18n-js
        path = os.sep.join([package_home(globals())]+['plugins', 'www', 'i18n'])
        if not os.path.exists(path):
          os.mkdir(path)
        for lang in langs:
          filename = os.sep.join([path, '%s.js'%lang])
          standard.writeStdout(context, "generate: %s"%filename)
          fileobj = codecs.open(filename, mode='w', encoding='utf-8')
          fileobj.write('var zmiLangStr={\'lang\':\'%s\''%lang)
          for k in d.keys():
            v = d[k].get(lang)
            if v is not None:
              v = v.replace('\'', '\\\'').replace('\n', '\\n')
              fileobj.write(',\'%s\':\''%k)
              fileobj.write(v)
              fileobj.write('\'')
          fileobj.write('};')
          fileobj.close()
    
    except:
        """If you can't register the product, dump error. 
        
        Zope will sometimes provide you with access to "broken product" and
        a backtrace of what went wrong, but not always; I think that only 
        works for errors caught in your main product module. 
        
        This code provides traceback for anything that happened in 
        registerClass(), assuming you're running Zope in debug mode."""
        
        import sys, traceback, string
        type, val, tb = sys.exc_info()
        sys.stderr.write(''.join(traceback.format_exception(type, val, tb)))
        del type, val, tb

def getData(cell):
    rc = None
    datas = cell.getElementsByTagName('Data')
    if len(datas) > 0:
        data = datas[0]
        rc = getText(data.childNodes)
    return rc

def getText(nodelist):
    rc = []
    for node in nodelist:
        if node.nodeType == node.TEXT_NODE:
            rc.append(node.data)
    return ''.join(rc)

def translate_path(s):
  """
  translate path
  """
  ZMS_HOME = package_home(globals())
  if s.startswith('/++resource++zms_/'):
    l = ['plugins', 'www']+s.split('/')[2:]
  return os.sep.join([ZMS_HOME]+l)

################################################################################
# Dynamic Modification of the Zope Skin
################################################################################
confdict = _confmanager.ConfDict.get()
if six.PY2 and confdict.get('zmi.console') in ['light','dark']:
  from App.special_dtml import DTMLFile
  from App.Management import Navigation
  from App.Management import Tabs
  from App.ApplicationManager import DebugManager
  from OFS.ObjectManager import ObjectManager
  Navigation.manage = DTMLFile('skins/zope2/manage', globals())
  setattr(Navigation, 'manage_page_style.css', DTMLFile('skins/zope2/manage_page_style_%s.css'%(confdict['zmi.console']), globals()))
  Navigation.manage_page_header = DTMLFile('skins/zope2/manage_page_header', globals())
  Navigation.manage_page_footer = DTMLFile('skins/zope2/manage_page_footer', globals())
  Navigation.manage_menu = DTMLFile('skins/zope2/menu', globals())
  Tabs.manage_tabs = DTMLFile('skins/zope2/manage_tabs', globals())
  ObjectManager.manage_main = DTMLFile('skins/zope2/main', globals())
  DebugManager.manage_main = DTMLFile('skins/zope2/debug', globals())
