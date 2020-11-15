################################################################################
# _importable.py
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
from App.Common import package_home
from io import StringIO
import ZPublisher.HTTPRequest
import collections
import os
import sys
import tempfile
import time
import transaction
import zExceptions
# Product Imports.
from Products.zms import standard
from Products.zms import _blobfields
from Products.zms import _fileutil
from Products.zms import _filtermanager
from Products.zms import _globals


# ------------------------------------------------------------------------------
#  _importable.recurse_importContent:
#
#  Process objects after import.
# ------------------------------------------------------------------------------
def recurse_importContent(self, folder):
  # Cleanup.
  for key in ['oRootTag', 'oCurrNode', 'oParent', 'dTagStack', 'dValueStack']:
    try: delattr(self, key)
    except: pass
  
  # Upload ressources.
  langs = self.getLangIds()
  prim_lang = self.getPrimaryLanguage()
  obj_attrs = self.getObjAttrs()
  for key in obj_attrs:
    obj_attr = self.getObjAttr(key)
    datatype = obj_attr['datatype_key']
    if datatype in _globals.DT_BLOBS:
      for lang in langs:
        try:
          if obj_attr['multilang'] or lang==prim_lang:
            req = {'lang':lang,'preview':'preview'}
            obj_vers = self.getObjVersion(req)
            blob = self._getObjAttrValue(obj_attr, obj_vers, lang)
            if blob is not None:
              filename = _fileutil.getOSPath('%s/%s'%(folder, blob.filename))
              standard.writeBlock( self, '[recurse_importContent]: filename=%s'%filename)
              # Backup properties (otherwise manage_upload sets it).
              bk = {}
              for __xml_attr__ in blob.__xml_attrs__:
                bk[__xml_attr__] = getattr(blob, __xml_attr__, '')
              # Read file to ZODB.
              f = open( filename, 'rb')
              try:
                blob = _blobfields.createBlobField( self, datatype, file={'data':f,'filename':filename})
              finally:
                f.close()
              # Restore properties.
              for __xml_attr__ in blob.__xml_attrs__:
                if bk.get(__xml_attr__, '') not in ['', 'text/x-unknown-content-type']:
                  setattr(blob, __xml_attr__, bk[__xml_attr__])
              blob.getFilename() # Normalize filename
              self.setObjProperty(key, blob, lang)
        except:
          standard.writeError(self, "[recurse_importContent]")
  
  # Commit object.
  self.onChangeObj( self.REQUEST, forced=1)
  transaction.commit()
  
  # Process children.
  for ob in self.getChildNodes():
    recurse_importContent(ob, folder)


# ------------------------------------------------------------------------------
#  _importable.importContent
# ------------------------------------------------------------------------------
def importContent(self, file):
  
  # Setup.
  catalog_awareness = self.getConfProperty('ZMS.CatalogAwareness.active', 1)
  self.setConfProperty('ZMS.CatalogAwareness.active', 0)

  self.dTagStack = collections.deque()
  self.dValueStack = collections.deque()
  self.oParent = self.getParentNode()
  
  # Parse XML-file.
  ob = self.parse(file, self, 1)
  
  # Process objects after import
  recurse_importContent(ob, _fileutil.getFilePath(file.name))
  
  # Cleanup.
  self.setConfProperty('ZMS.CatalogAwareness.active', catalog_awareness)
  standard.triggerEvent( self, '*.onImportObjEvt')
  
  # Return imported object.
  return ob


# ------------------------------------------------------------------------------
#  _importable.importFile
# ------------------------------------------------------------------------------
def importFile(self, file, REQUEST, handler):
  
  # Get filename.
  if isinstance(file, ZPublisher.HTTPRequest.FileUpload):
    filename = file.filename
  else: 
    filename = file.name
  standard.writeBlock( self, '[importFile]: filename='+filename)
  
  # Create temporary folder.
  folder = tempfile.mktemp()
  os.mkdir(folder)
  
  # Save to temporary file.
  filename = _fileutil.getOSPath('%s/%s'%(folder, _fileutil.extractFilename(filename)))
  _fileutil.exportObj(file, filename)
  
  # Find XML-file.
  if _fileutil.extractFileExt(filename) == 'zip':
    _fileutil.extractZipArchive(filename)
    filename = None
    for deep in [0, 1]:
      for ext in ['xml', 'htm', 'html' ]:
        if filename is None:
          filename = _fileutil.findExtension(ext, folder, deep)
      break
    if filename is None:
      raise zExceptions.InternalError('XML-File not found!')
  
  # Import Filter.
  if REQUEST.get('filter', '') in self.getFilterManager().getFilterIds():
    filename = _filtermanager.importFilter(self, filename, REQUEST.get('filter', ''), REQUEST)
  
  # Import XML-file.
  standard.writeBlock( self, '[importFile]: filename='+filename)
  f = standard.pyopen(filename, 'r', encoding='utf-8')
  ob = handler(self, f)
  f.close()
  
  # Remove temporary files.
  _fileutil.remove(folder, deep=1)
  
  # Return imported object.
  return ob

################################################################################
