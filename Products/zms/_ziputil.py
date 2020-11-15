################################################################################
# _ziputil.py
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
from io import BytesIO
import zipfile
# Product Imports.
# import standard
from Products.zms import _globals

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_ziputil.exportZodb2Zip:

Extracts and imports zip-file to zodb.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def _exportZodb2Zip(zf, root, container):
  for ob in container.objectValues():
    if ob.meta_type in ['Folder']:
      _exportZodb2Zip(zf, root, ob)
    elif ob.meta_type in ['Image', 'File']:
      arcname = ob.absolute_url()[len(root.absolute_url())+1:]
      try:
        bytes = ob.data
        if len(bytes) == 0:
          bytes = ob.getData()
        try:
          bytes = bytes.read()
        except:
          bytes = str(bytes)
        zf.writestr(arcname, bytes)
      except:
        standard.writeError(root.content, "_exportZodb2Zip")

def exportZodb2Zip(root):
  zip_buffer = zipfile.ZipFile( zipfilename, 'w')
  _exportZodb2Zip(zip_buffer, root, root)
  return zip_buffer.getvalue()


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_ziputil.importZip2Zodb:

Extracts and imports zip-file to zodb.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def importZip2Zodb(root, data):
  if _globals.is_str_type(data):
    data = BytesIO( data)
  zf = zipfile.ZipFile( data, 'r')
  for name in zf.namelist():
    container = root
    ids = name.split('/')
    if len(ids) > 1:
      for id in ids[:-1]:
        if id not in container.objectIds():
          container.manage_addFolder(id=id)
        container = getattr(container, id)
    id = ids[-1]
    if id:
      file = zf.read( name)
      mt, enc  = standard.guess_content_type( id, file)
      if id in container.objectIds():
        container.manage_delObjects( [id])
      if mt.startswith('image'):
        file = container.manage_addImage(id=id, file=file)
      else:
        file = container.manage_addFile(id=id, file=file)

################################################################################