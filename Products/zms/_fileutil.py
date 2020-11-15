################################################################################
# _fileutil.py
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
from ZPublisher.Iterators import filestream_iterator
from App.config import getConfiguration
import fnmatch
import io
import os
import shutil
import six
import sys
import tempfile
import zipfile
import zope.contenttype


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.import_zexp:

Import zexp.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def import_zexp(self, zexp, new_id, id_prefix, _sort_id=0):
  INSTANCE_HOME = getConfiguration().instancehome
  # Import
  filename = zexp.title_or_id()
  fileid = filename[:filename.find('.')]
  filepath = INSTANCE_HOME + '/import/' + filename
  exportObj( zexp, filepath)
  importZexp( self, filename)
  
  # Rename
  if new_id != fileid:
    self.manage_renameObject(fileid, new_id)
  
  ## Normalize Sort-IDs
  obj = getattr( self, new_id)
  obj.sort_id = _sort_id
  self.normalizeSortIds( id_prefix)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.importZexp:

Import file from specified path.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def importZexp(self, filename):
  ### Store copy of ZEXP in INSTANCE_HOME/import-folder.
  INSTANCE_HOME = getConfiguration().instancehome
  filepath = INSTANCE_HOME + '/import/' + filename
  self.manage_importObject(filename)
  remove(filepath)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.extractFilename:

Extract filename from path.
IN:  path
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def extractFilename(path, sep=None, undoable=False):
  if sep is None:
    path = getOSPath(path, undoable=undoable)
  items = path.split( os.sep)
  lastitem = items[len(items)-1]
  return lastitem


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.extractFileExt:

Extract fileextension from path.
IN:  path
OUT: extension
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def extractFileExt(path):
  items = path.split('.')
  lastitem = items[len(items)-1]
  return lastitem


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.getOSPath:

Return path with OS separators.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def getOSPath(path, chs=list(range(32))+[34, 39, 60, 62, 63, 127], undoable=False):
  if type(path) is bytes:
    path = path.decode('utf-8')
  path = path.replace('\\', os.sep)
  path = path.replace('/', os.sep)
  # if isinstance(path, str):
  #   path = path.encode('ascii', 'replace')
  # if undoable or os.name != "nt":
  #   path = path.encode('ascii', 'replace') # replace uncodable characters by ? (63)
  # if len( chs) > 0:
  #   for ch in chs:
  #     path = path.replace(chr(ch), '')
  return path


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.absoluteOSPath:

Return absolute-path with OS separators.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def absoluteOSPath(path):
  path = getOSPath(path)
  l0 = path.split(os.sep)
  l1 = []
  for i in l0:
    if i == '..':
      l1 = l1[:-1]
    else:
      l1 = l1 + [i]
  path = os.sep.join(l1)
  return path


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.getFilePath:

Extract filepath from path (cut-off filename).
IN:  path
OUT: filepath
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def getFilePath(path):
  items = getOSPath(path).split(os.sep)
  filepath = ''
  for i in range(len(items)-1):
    filepath = filepath + items[i] + os.sep
  if len(filepath) > 0:
    if filepath[-1] == os.sep:
      filepath = filepath[:-1]
  return filepath


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
 _fileutil.findExtension:

Searches path and all subdirectories for file with extension and returns 
complete filepath. Returns None if no file with specified extension exists.
IN:  extension
     path
OUT: filepath
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def findExtension(extension, path, deep=1):
  rtn = None
  path = getOSPath(path)
  for file in os.listdir(path):
    filepath = path + os.sep + file 
    if extractFileExt(file).lower() == extension:
      return filepath
    elif deep:
      if os.path.isdir(filepath):
        rtn = findExtension(extension, filepath, deep)
        if rtn is not None:
          return rtn
  return rtn


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.readPath:

Reads path.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def readPath(path, data=True, recursive=True):
  l = []
  path = path.replace('\\', os.sep)
  path = path.replace('/', os.sep)
  filter = extractFilename(path, os.sep)
  if filter.find('*') >= 0 and filter.find('.') >= 0:
    path = getFilePath( path)
  else:
    filter = None
  if os.path.isdir(path):
    for filename in os.listdir(path):
      local_filename = os.path.join(path,filename)
      if filter is None or fnmatch.fnmatch(filename, filter):
        d = {}
        d['local_filename']=local_filename
        d['filename']=extractFilename(local_filename)
        if os.path.isdir(local_filename):
          mtime = os.path.getmtime( local_filename)
          d['mtime']=mtime
          d['isdir']=True
          l.append(d)
        else:
          fdata = None
          if data:
            fdata, mt, enc, fsize = readFile( local_filename, 'b', -1)
            d['data']=fdata
            d['content_type']=mt
            d['encoding']=enc
          else:
            try:
              mt, enc = zope.contenttype.guess_content_type( local_filename)
            except:
              mt, enc = 'content/unknown', ''
            d['content_type']=mt
            d['encoding']=enc
          fsize = os.path.getsize( local_filename)
          d['size']=fsize
          mtime = os.path.getmtime( local_filename)
          d['mtime']=mtime
          d['isdir']=False
          l.append(d)
      if os.path.isdir(local_filename) and recursive:
        if filter is not None:
          local_filename = local_filename + '/' + filter
        l.extend(readPath(local_filename, data, recursive))
  return l


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.readFile:

Reads file (threshold for filesteam_iterator is 128 kb).
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def readFile(filename, mode='b', threshold=2 << 16):
  size = os.path.getsize( filename)
  if size < threshold or -1 == threshold:
    f = None
    try:
      f = open( filename, 'r'+mode)
      data = f.read()
    finally:
      if f is not None:
        f.close()
  else:
    data = filestream_iterator( filename, 'r'+mode)
  try:
    mt, enc  = zope.contenttype.guess_content_type( filename, data)
  except:
    mt, enc = 'content/unknown', ''
  return data, mt, enc, size


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.remove:

Removes path.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def remove(path, deep=0):
  path = getOSPath(path)
  if os.path.isdir(path):
    shutil.rmtree(path)
  else:
    os.remove(path)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.getDataSizeStr: 

Display string for file-size.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def getDataSizeStr(len):
  s = ''
  try:
    mod = 0
    while len > 1024.0 and mod < 3:
      len = len / 1024.0
      mod = mod + 1
    s = str(int(len))
    n = str(int(10*(len - int(len))))
    if mod == 0:
      s = "%sBytes"%s
    elif mod == 1:
      s = "%sKB"%s
    elif mod == 2:
      s = "%s.%s MB"%(s, n)
    elif mod == 3:
      s = "%s.%s GB"%(s, n)
  except:
    pass
  return s


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.executeCommand:
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def executeCommand(path, command):
  os.chdir(path)
  os.system(command)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.exportObj:
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def exportObj(obj, filename, filetype='b'):
  
  #-- Try to create directory-tree.
  filename = getOSPath(filename)
  filepath = getFilePath(filename)
  mkDir(filepath)
  
  #-- Get object data.
  data = None
  try: # ImageFile
    f = open(obj.path,'r%s'%filetype)
    data = f.read()
    f.close()
  except:
    try: # Image / File
      data = obj.data
      if len(data) == 0:
        data = obj.getData()
    except: 
      try:
        data = obj.raw # DTML Method
      except:
        try:
          data = obj.read() # REQUEST.enctype multipart/form-data
        except:
          data = str(obj)
    
  #-- Save to file.
  if data is not None:
    objfile = open(filename, 'w%s'%filetype)
    if isinstance(data, six.string_types):
      from Products.zms import standard
      objfile.write(standard.six_ensure_binary(data))
    elif isinstance(data, six.binary_type):
      objfile.write(data)
    elif isinstance(data,io.RawIOBase):
      objfile.write(data.read())
    else:
      while data is not None:
        objfile.write(data.data)
        data=data.next
    objfile.close()


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.mkDir:

Make directory.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def mkDir(path):
  try:
    os.makedirs( path)
  except:
    pass


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.readDir
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def readDir(path):
  obs = []
  path = getOSPath(path)
  for file in os.listdir(path):
    ob = {}
    ob['path'] = path + os.sep
    ob['file'] = file
    filepath = path + os.sep + file 
    ob['mtime'] = os.path.getmtime(filepath)
    ob['size'] = os.path.getsize(filepath)
    if os.path.isdir(filepath): 
      ob['type'] = 'd'
    else:
      ob['type'] = 'f'
    obs.append(ob)
  return sorted(obs, key=lambda x:x['type'])


################################################################################
###
###  ZIP
###
################################################################################

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.getZipArchive:

Extract files from zip-archive and return list of extracted files.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def getZipArchive(f):
  l = []
  
  # Saved zip-file in temp-folder.
  tempfolder = tempfile.mktemp()
  filename = tempfolder + os.sep + extractFilename(tempfolder) + '.zip'
  exportObj(f, filename)
  
  # Unzip zip-file.
  extractZipArchive(filename)
  
  # Remove zip-file.
  remove(filename)
  
  # Read extracted files.
  l = readPath(tempfolder, data=True)
  
  # Remove temp-folder.
  remove(tempfolder, deep=1)
  
  # Return list of files.
  return l


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.extractZipArchive:

Unpack ZIP-Archive.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def extractZipArchive(file):
  l = []
  
  zf = zipfile.ZipFile( file, 'r')
  for name in zf.namelist():
    dir = getOSPath( name)
    i = dir.rfind( os.sep) 
    if i > 0:
      dir = getFilePath(file) + os.sep + dir[ :i]
      mkDir( dir)
    localname = getOSPath( getFilePath(file) + os.sep + name)
    if localname[-1] != os.sep:
      l.append( localname)
      f = open( localname, 'wb')
      f.write( zf.read( name))
      f.close()
  zf.close()
  
  # Return list of files.
  return l


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.writeZipFile:
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def writeZipFile( zf, basepath, path, filter):
  for file in os.listdir( path):
    filepath = path+os.sep+file
    if os.path.isdir(filepath): 
      writeZipFile( zf, basepath, filepath, filter)
    else:
      arcname = filepath[len( basepath)+1:]
      match = False
      for pattern in filter.split(';'):
        match = match or fnmatch.fnmatch( arcname, pattern)
      if match:
        zf.write( filepath, str(arcname))

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.buildZipArchive:

Pack ZIP-Archive and return data.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def buildZipArchive( files, get_data=True):
  
  # Create temporary zip-file.
  zipfilename = tempfile.mktemp() + '.zip'
  
  # Write filtered files to zip-file.
  files = getOSPath( files)
  path = getFilePath( files)
  filter = extractFilename( files)
  zf = zipfile.ZipFile( zipfilename, 'w')
  writeZipFile( zf, path, path, filter)
  zf.close()
  
  # Read data from zip-file as return value.
  data = zipfilename
  if get_data:
    f = open( zipfilename, 'rb')
    data = f.read()
    f.close()
  
    # Remove temporary zip-file.
    os.remove( zipfilename)
  
  # Returns filename or data of zip-file.
  return data


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_fileutil.tail_lines:

Does what "tail -10 filename" would have done
@param filename   file to read
@param linesback  Number of lines to read from end of file
@param returnlist Return a list containing the lines instead of a string
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def tail_lines(filename,linesback=10,returnlist=0):
    avgcharsperline=75
    
    file = open(filename, 'r')
    while True:
        try: file.seek(-1 * avgcharsperline * linesback, 2)
        except IOError: file.seek(0)
        if file.tell() == 0: atstart=1
        else: atstart=0
        
        lines=file.read().split("\n")
        if (len(lines) > (linesback+1)) or atstart: break
        # The lines are bigger than we thought
        avgcharsperline=avgcharsperline * 1.3 #Inc avg for retry
    file.close()
    
    if len(lines) > linesback: start=len(lines)-linesback -1
    else: start=0
    if returnlist: return lines[start:len(lines)-1]
    
    out=""
    for l in lines[start:len(lines)-1]: out=out + l + "\n"
    return out

################################################################################