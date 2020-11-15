################################################################################
# _mediadb.py
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
from AccessControl import ClassSecurityInfo
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Persistence import Persistent
from ZPublisher.Iterators import filestream_iterator
from platform import python_version
from zExceptions import NotFound
import OFS.SimpleItem
import Acquisition
import os
import shutil
import time
import tempfile
# Product Imports.
from Products.zms import standard
from Products.zms import _blobfields
from Products.zms import _fileutil
from Products.zms import _globals
from Products.zms import _objattrs


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Constructor
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def manage_addMediaDb(self, location, REQUEST=None, RESPONSE=None):
  """ manage_addMediaDb """
  obj = MediaDb(location)
  self._setObject(obj.id, obj)
  recurse_addMediaDb(self,self.getMediaDb())
  if RESPONSE is not None:
    RESPONSE.redirect('%s/manage_main'%self.absolute_url())


def containerFilter(container):
  return container.meta_type == 'ZMS'


################################################################################
###   
###   Create
###   
################################################################################
def recurse_addMediaDb(self, mediadb):

  # Process recordset.
  if self.getType()=='ZMSRecordSet':
    key = self.getMetaobjAttrIds(self.meta_id,types=['list'])[0]
    obj_attr = self.getObjAttr(key)
    lang = self.getPrimaryLanguage()
    for obj_vers in self.getObjVersions():
      v = _objattrs.getobjattr(self,obj_vers,obj_attr,lang)
      c = 0
      for r in v:
        for k in r:
          u = r[k]
          if isinstance(u,_blobfields.MyBlob):
            mediadbfile = mediadb.storeFile(u)
            u.mediadbfile = mediadbfile
            u.data = ''
        c += 1
  
  # Process object. 
  else:
    for key in self.getObjAttrs():
      obj_attr = self.getObjAttr(key)
      datatype = obj_attr['datatype_key']
      if datatype in _globals.DT_BLOBS:
        for lang in self.getLangIds():
          for obj_vers in self.getObjVersions():
            v = _objattrs.getobjattr(self,obj_vers,obj_attr,lang)
            if isinstance(v,_blobfields.MyBlob):
              mediadbfile = mediadb.storeFile(v)
              v.aq_parent = None
              v.mediadbfile = mediadbfile
              v.data = ''
              _objattrs.setobjattr(self,obj_vers,obj_attr,v,lang)
  
  # Process children.
  for ob in self.objectValues( self.dGlobalAttrs):
    recurse_addMediaDb(ob,mediadb)


################################################################################
###   
###   Compress
###   
################################################################################
def getFilenamesFromValue( v):
  rtn = []
  if type( v) is list:
    for i in v:
      rtn.extend( getFilenamesFromValue( i))
  elif type( v) is dict:
    for k in v:
      rtn.extend( getFilenamesFromValue( v[k]))
  elif isinstance(v,_blobfields.MyBlob):
    filename = v.getMediadbfile()
    if filename is not None:
      rtn.append(filename.split(os.sep)[-1])
  return rtn


def manage_structureMediaDb(self, structure, REQUEST=None, RESPONSE=None):
  """ manage_structureMediaDb """
  message = ''
  mediadb = self.getMediaDb()
  mediadb.structure = structure
  
  # Temp location.
  path = mediadb.getLocation()
  location = mediadb.location
  mediadb.location = location + "_tmp"
  temp = mediadb.getLocation()
  
  # Traverse existing structure.
  def traverse(path, p):
    standard.writeBlock( self, "[manage_structureMediaDb]: traverse %s"%path)
    for filename in os.listdir(path):
      filepath = os.path.join(path,filename)
      if os.path.isdir(filepath):
        traverse(filepath,p)
      elif os.path.isfile(filepath):
        targetpath = mediadb.targetFile(filepath)
        standard.writeBlock( self, "[manage_structureMediaDb]: %s -> %s"%(filepath,targetpath))
        targetdir = os.sep.join(targetpath.split(os.sep)[:-1])
        if not os.path.exists(targetdir):
          standard.writeBlock( self, "[manage_structureMediaDb]: makedirs %s"%targetdir)
          os.makedirs(targetdir)
        shutil.move(filepath,targetpath)
        p['t'] += 1
  standard.writeBlock( self, "[manage_structureMediaDb]: makedirs %s"%temp)
  os.makedirs(temp)
  p = {'t':0}
  traverse(path,p)
  standard.writeBlock( self, "[manage_structureMediaDb]: remove %s"%path)
  shutil.rmtree(path)  
  standard.writeBlock( self, "[manage_structureMediaDb]: rename %s -> %s"%(temp,path))
  os.rename(temp,path)
  
  # Restore location.
  mediadb.location = location
  
  # Return with message.
  message = "Restructured Media-Folder %s: %i files proecessed."%(str(structure),p['t'])
  standard.writeBlock( self, "[manage_structureMediaDb]: "+message)
  return message


def manage_packMediaDb(self, REQUEST=None, RESPONSE=None):
  """ manage_packMediaDb """
  message = ''
  mediadb = self.getMediaDb()
  path = mediadb.getLocation()
  
  # Get filenames.
  filenames = mediadb.valid_filenames()
  standard.writeLog( self, "[manage_packMediaDb]: filenames %s"%str(filenames))
  tempfolder = tempfile.mktemp()
  os.makedirs(tempfolder)
  standard.writeLog( self, "[manage_packMediaDb]: tempfolder %s"%tempfolder)
  
  # Traverse existing structure.
  def traverse(path, p):
    for filename in os.listdir(path):
      filepath = os.path.join(path,filename)
      if os.path.isdir(filepath):
        traverse(filepath,p)
      elif os.path.isfile(filepath):
        if filename not in p['filenames']:
          standard.writeBlock( self, "[manage_packMediaDb]: filename %s"%str(filename))
          shutil.move(filepath,p['tempfolder']+os.sep+filename)
          p['c'] += 1
        p['t'] += 1
  p = {'t':0,'c':0,'filenames':filenames,'tempfolder':tempfolder}
  traverse(path,p)
  
  # Return with message.
  message = "%i files (total %i) moved to %s."%(p['c'],p['t'],p['tempfolder'])
  standard.writeBlock( self, "[manage_packMediaDb]: "+message)
  return message


################################################################################
###   
###   Destroy
###   
################################################################################
def recurse_delMediaDb(self, mediadb):

  # Process recordset.
  if self.getType()=='ZMSRecordSet':
    key = self.getMetaobjAttrIds(self.meta_id,types=['list'])[0]
    obj_attr = self.getObjAttr(key)
    lang = self.getPrimaryLanguage()
    for obj_vers in self.getObjVersions():
      v = _objattrs.getobjattr(self,obj_vers,obj_attr,lang)
      for r in v:
        for k in r:
          u = r[k]
          mediadbfile = getattr(u,'mediadbfile',None)
          if mediadbfile is not None:
            u.mediadbfile = None
            u.data = mediadb.retrieveFile(mediadbfile)
  # Process object. 
  else:
    for key in self.getObjAttrs():
      obj_attr = self.getObjAttr(key)
      datatype = obj_attr['datatype_key']
      if datatype in _globals.DT_BLOBS:
        for lang in self.getLangIds():
          for obj_vers in self.getObjVersions():
            v = _objattrs.getobjattr(self,obj_vers,obj_attr,lang)
            if v is not None:
              mediadbfile = getattr(v,'mediadbfile',None)
              if mediadbfile is not None:
                v.aq_parent = None
                v.mediadbfile = None
                v.data = mediadb.retrieveFile(mediadbfile)
                _objattrs.setobjattr(self,obj_vers,obj_attr,v,lang)
  
  # Process children.
  if self.meta_id != 'ZMSLinkElement':
    for ob in self.getChildNodes():
      recurse_delMediaDb(ob,mediadb)


def manage_delMediaDb(self, REQUEST=None, RESPONSE=None):
  """ manage_delMediaDb """
  message = ''
  recurse_delMediaDb(self,self.getMediaDb())
  self.manage_delObjects(ids=['acl_mediadb'])
  return message


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Class
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class MediaDb(
      OFS.SimpleItem.Item,
      Persistent,
      Acquisition.Implicit):

    # Create a SecurityInfo for this class. We will use this
    # in the rest of our class definition to make security
    # assertions.
    security = ClassSecurityInfo()

    # Properties.
    # -----------
    meta_type = 'MediaDb'
    if python_version().startswith("3."): # py3
      zmi_icon = "fas fa-images"
      icon_clazz = zmi_icon
    else: # py2
      zmi_icon = "icon-folder-close"
      icon_clazz = zmi_icon

    # Management Options.
    # -------------------
    manage_options = (
      {'label': 'Properties','action': 'acl_mediadb/manage_properties'},
      {'label': 'Edit','action': 'acl_mediadb/manage_browse'},
      )

    # Management Interface.
    # ---------------------
    manage_browse = PageTemplateFile('zpt/MediaDb/manage_browse', globals())
    manage_main = PageTemplateFile('zpt/MediaDb/manage_properties', globals())
    manage_properties = PageTemplateFile('zpt/MediaDb/manage_properties', globals())


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Constructor
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __init__(self, location, structure=0):
      self.id = 'acl_mediadb'
      self.setLocation(location)
      self.structure = structure
      _fileutil.mkDir(self.getLocation())

    # --------------------------------------------------------------------------
    # MediaDb.setLocation
    # --------------------------------------------------------------------------
    def setLocation(self, location):
      if location.endswith('/'):
        location = location[:-1]
      self.location = location

    # --------------------------------------------------------------------------
    # MediaDb.getLocation
    # --------------------------------------------------------------------------
    def getLocation(self):
      return self.location.replace('$INSTANCE_HOME', standard.getINSTANCE_HOME())

    # --------------------------------------------------------------------------
    # MediaDb.getStructure
    # --------------------------------------------------------------------------
    def getStructure(self):
      return getattr(self,'structure',0)

    # --------------------------------------------------------------------------
    #  MediaDb.urlQuote
    # --------------------------------------------------------------------------
    def urlQuote(self, s): 
      return standard.url_quote(s)

    # --------------------------------------------------------------------------
    #  MediaDb.getPath
    # --------------------------------------------------------------------------
    def getPath(self, REQUEST): 
      path = REQUEST.get('path','')
      if len(path) < len(self.getLocation()):
        path = self.getLocation()
      return path

    # --------------------------------------------------------------------------
    #	MediaDb.readDir
    # --------------------------------------------------------------------------
    def readDir(self, path):
      return _fileutil.readDir(path)

    # --------------------------------------------------------------------------
    #  MediaDb.getParentDir
    # --------------------------------------------------------------------------
    def getParentDir(self, path):
      return _fileutil.getFilePath(path)

    # --------------------------------------------------------------------------
    #  MediaDb.getFile
    # --------------------------------------------------------------------------
    def getFile(self, REQUEST,RESPONSE): 
      filename = _fileutil.extractFilename( self.getPath( REQUEST))
      return self.retrieveFileStreamIterator( filename, REQUEST)

    # --------------------------------------------------------------------------
    #  MediaDb.targetFile
    #
    #  Get target filename in flat or hierarchical structure.
    # --------------------------------------------------------------------------
    def targetFile(self, filename):
      filepath = ''
      filename = _fileutil.extractFilename(filename)
      filename = filename.replace('..','')
      if len(filename) > 0:
        fileext = filename[filename.rfind('.'):]
        filename = filename[:filename.rfind('.')]
        location = [self.getLocation()]
        for i in reversed(range(self.getStructure())):
          location.append(filename[-(i+1)])
        location.append(filename+fileext)
        filepath = os.sep.join(location)
      return filepath

    # --------------------------------------------------------------------------
    #  MediaDb.storeFile
    # --------------------------------------------------------------------------
    def storeFile(self, file):
      filepath = ''
      filename = _fileutil.extractFilename(file.filename)
      if len(filename) > 0:
        filename, fileext = os.path.splitext(filename)
        filename = filename + '_'+str(time.time()).replace('.','') + fileext
        filepath = self.targetFile(filename)
        _fileutil.exportObj(file,filepath)
      return filename

    # --------------------------------------------------------------------------
    #  MediaDb.manage_index_html
    # --------------------------------------------------------------------------
    security.declareProtected('ZMS Administrator', 'manage_index_html')
    def manage_index_html(self, filename, REQUEST=None):
      """ MediaDb.manage_index_html """
      return self.retrieveFileStreamIterator(filename,REQUEST)

    # --------------------------------------------------------------------------
    #  MediaDb.retrieveFileStreamIterator
    # --------------------------------------------------------------------------
    def retrieveFileStreamIterator(self, filename, REQUEST=None):
      threshold = 2 << 16 # 128 kb
      local_filename = self.targetFile(filename)
      try:
        fsize = os.path.getsize( local_filename)
      except:
        fsize = 0
        raise NotFound
      if fsize < threshold or REQUEST.RESPONSE is None:
        try:
          f = open( local_filename, 'rb')
          data = f.read()
        finally:
          f.close()
      else:
        data = filestream_iterator( local_filename, 'rb')
      try:
        mt, enc = standard.guess_content_type( local_filename, data)
      except:
        mt, enc = 'content/unknown', ''
      # Remove timestamp from filename.
      filename = filename[:filename.rfind('_')]+filename[filename.rfind('.'):]
      standard.set_response_headers(filename,mt,fsize,REQUEST)
      return data

    # --------------------------------------------------------------------------
    #  MediaDb.retrieveFile
    # --------------------------------------------------------------------------
    def retrieveFile(self, filename):
      filename = filename.replace('..','')
      try:
        location = self.getLocation()
        if not filename.startswith(location):
          filename = os.path.join(location,filename)
        f = open( filename, 'rb')
        data = f.read()
        f.close()
      except:
        standard.writeError( self, "can't retrieveFile")
        data = ''
      return data

    # --------------------------------------------------------------------------
    #	MediaDb.getFileSize
    # --------------------------------------------------------------------------
    def getFileSize(self, filename):
      location = self.getLocation()
      if not filename.startswith(location):
        filename = os.path.join(location,filename)
      fsize = os.path.getsize( filename)
      return fsize

    # --------------------------------------------------------------------------
    #  MediaDb.valid_filenames
    # --------------------------------------------------------------------------
    def valid_filenames(self):
      filenames = []
      objs = [self.getSelf()]
      objs.extend(objs[0].getTreeNodes())
      objs.extend(objs[0].getTrashcan().getTreeNodes())
      for obj in objs:
        # Process recordset.
        if obj.getType()=='ZMSRecordSet':
          si = obj.getMetaobjAttrIds(obj.meta_id)[0]
          obj_attr = obj.getObjAttr(si)
          for lang in obj.getLangIds():
            for obj_vers in obj.getObjVersions():
              v = _objattrs.getobjattr(obj,obj_vers,obj_attr,lang)
              for r in v:
                for k in r:
                  u = r[k]
                  mediadbfile = getattr(u,'mediadbfile',None)
                  if mediadbfile is not None:
                    filenamesFromValue = getFilenamesFromValue( u)
                    for filename in filenamesFromValue:
                      if filename not in filenames:
                        filenames.append( filename)
        # Process object. 
        else:
          obj_attrs = obj.getObjAttrs()
          for si in obj_attrs:
            obj_attr = obj_attrs[si]
            datatype = obj_attr['datatype'] 
            multilang = obj_attr['multilang']
            if datatype in [ 'file', 'image', 'list', 'dictionary']:
              for obj_vers in obj.getObjVersions():
                obj_attr_names = []
                if multilang:
                  for lang in self.getLangIds():
                    obj_attr_names.append('%s_%s'%(si,lang))
                else:
                  obj_attr_names.append(si)
                for obj_attr_name in obj_attr_names:
                  v = getattr(obj_vers,obj_attr_name,None)
                  filenamesFromValue = getFilenamesFromValue( v)
                  for filename in filenamesFromValue:
                    if filename not in filenames:
                      filenames.append( filename)
      return filenames


    """
    ############################################################################
    ###
    ###   P r o p e r t i e s
    ###
    ############################################################################
    """

    ############################################################################
    #  MediaDb.manage_changeProperties: 
    #
    #  Change MediaDb properties.
    ############################################################################
    def manage_changeProperties(self, submit, REQUEST, RESPONSE): 
      """ MediaDb.manage_changeProperties """
      
      message = ''
      
      # Change.
      if submit == 'Change':
        location = REQUEST.get('location',self.location)
        self.setLocation(location)

      # Return.
      if RESPONSE is not None:
        RESPONSE.redirect('manage_properties?manage_tabs_message=%s'%standard.url_quote(message))

################################################################################
