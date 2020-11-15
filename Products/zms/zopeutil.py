################################################################################
# zopeutil.py
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
from AccessControl.SecurityInfo import ModuleSecurityInfo
from Products.ExternalMethod import ExternalMethod
from Products.PageTemplates import ZopePageTemplate
from Products.PythonScripts import PythonScript
import os
import re
# Product Imports.
from Products.zms import standard
from Products.zms import _fileutil

security = ModuleSecurityInfo('Products.zms.zopeutil')

class MissingArtefactProxy(object):
  def __init__(self, id, meta_type, data=None):
    self.id=id
    self.meta_type=meta_type
    self.data = data
  icon__roles__=None
  def zmi_icon(self):
    return 'fas fa-skull-crossbones text-danger'
  def zmi_icon(self):
    return icon_clazz(self)
  getId__roles__=None
  def getId(self):
    return self.id
  getData__roles__=None
  def getData(self):
    return self.data
  absolute_url__roles__=None
  def absolute_url(self):
    return '#'

def nextObject(container, meta_type):
  """
  Get next parent Zope-object with given meta_type.
  """
  while hasattr(container,'meta_type') and not getattr(container,'meta_type') == meta_type and hasattr(container,'aq_parent'):
    container = container.aq_parent
  return container

def getExternalMethodModuleName(container, id):
  """
  Add context-folder-id to module-name (to prevent deleting artefacts from other clients).
  """
  m = id
  next = nextObject(container,'Folder')
  if hasattr(next,"id"):
    m = '%s.%s'%(next.getId(),id)
  return m

security.declarePublic('addObject')
def addObject(container, meta_type, id, title, data, permissions={}):
  """
  Add Zope-object to container.
  """
  if meta_type == 'DTML Document':
    addDTMLDocument( container, id, title, data)
  elif meta_type == 'DTML Method':
    addDTMLMethod( container, id, title, data)
  elif meta_type == 'External Method':
    addExternalMethod( container, id, title, data)
  elif meta_type == 'File':
    addFile( container, id, title, data)
  elif meta_type == 'Image':
    addImage( container, id, title, data)
  elif meta_type == 'Page Template':
    addPageTemplate( container, id, title, data)
  elif meta_type == 'Script (Python)':
    addPythonScript( container, id, title, data)
  elif meta_type == 'Folder':
    addFolder( container, id, title, data)
  elif meta_type == 'Z SQL Method':
    addZSqlMethod( container, id, title, data)
  initPermissions(container, id, permissions)
  return getObject(container, id)

security.declarePublic('getObject')
def getObject(container, id, meta_type=None, default=None):
  """
  Get Zope-object from container.
  """
  ob = getattr(container, id, None)
  if ob is None and meta_type in ['External Method']:
    ob = MissingArtefactProxy(id, meta_type, default)
  return ob

security.declarePublic('callObject')
def callObject(ob, zmscontext=None, options={}):
  """
  Call Zope-object.
  """
  v = None
  if ob.meta_type in [ 'DTML Method', 'DTML Document']:
    v = ob(zmscontext, zmscontext.REQUEST)
  elif options:
    v = ob(zmscontext=zmscontext, options=options)
  elif ob.meta_type in [ 'External Method' ]:
    v = ob()
  elif ob.meta_type in [ 'Script (Python)'] and readData(ob).find('##parameters=zmscontext')<0:
    v = ob()
  else:
    v = ob(zmscontext=zmscontext)
  return v

security.declarePublic('readData')
def readData(ob, default=None):
  """
  Read data of Zope-object.
  """
  data = default
  if ob is None and default is not None:
    return default
  if ob.meta_type in [ 'DTML Document', 'DTML Method', 'Filesystem DTML Document', 'Filesystem DTML Method']:
    data = ob.raw
  elif ob.meta_type in [ 'File', 'Filesystem File', 'Filesystem Image', 'Image']:
    data = ob.data
    if not standard.is_bytes(data):
      b = b''
      while data is not None:
        b += data.data
        data = data.next
      data = b
  elif ob.meta_type in [ 'Filesystem Page Template', 'Filesystem Script (Python)', 'Page Template', 'Script (Python)']:
    data = ob.read()
  elif ob.meta_type in [ 'External Method']:
    if isinstance(ob,MissingArtefactProxy):
      return ob.getData()
    else:
      context = ob
      id = ob.getId()
      while context is not None:
        m = getExternalMethodModuleName(context, id)
        filepath = standard.getINSTANCE_HOME()+'/Extensions/'+m+'.py'
        if os.path.exists(filepath):
          break
        try:
          context = context.getParentNode()
        except:
          context = None
      if context is None:
        m = id
      filepath = standard.getINSTANCE_HOME()+'/Extensions/'+m+'.py'
      if os.path.exists(filepath):
        f = open(filepath, 'rb')
        data = standard.pystr(f.read(),encoding='utf-8')
        f.close()
  elif ob.meta_type == 'Z SQL Method':
    lines = []
    lines.append('<connection>%s</connection>'%ob.connection_id)
    lines.append('<params>%s</params>'%ob.arguments_src)
    lines.append('<max_rows>%i</max_rows>'%ob.max_rows_)
    lines.append('<max_cache>%i</max_cache>'%ob.max_cache_)
    lines.append('<cache_time>%i</cache_time>'%ob.cache_time_)
    lines.append(ob.src)
    data = '\n'.join(lines)
  return data

security.declarePublic('readObject')
def readObject(container, id, default=None):
  """
  Read Zope-object from container.
  """
  ob = getObject(container, id)
  return readData(ob, default)

security.declarePublic('removeObject')
def removeObject(container, id, removeFile=True):
  """
  Remove Zope-object from container.
  """
  #try: container.writeBlock("[zopeutil.removeObject]: %s@%s -%s"%(container.meta_type,container.absolute_url(),id))
  #except: pass
  if id in container.objectIds():
    ob = getattr(container, id)
    if ob.meta_type == 'External Method' and removeFile:
      m = getExternalMethodModuleName(container, id)
      filepath = standard.getINSTANCE_HOME()+'/Extensions/'+m+'.py'
      if os.path.exists(filepath):
        os.remove(filepath)
    container.manage_delObjects(ids=[id])

security.declarePublic('initPermissions')
def initPermissions(container, id, permissions={}):
  """
  Init permissions for Zope-object:
  - set Proxy-role 'Manager'
  - set View-permissions to 'Authenticated' and remove acquired permissions for manage-objects.
  """
  ob = getattr( container, id, None)
  if ob is None: return
  
  # apply proxy-roles
  ob._proxy_roles=('Authenticated','Manager')
  # manage-artefacts need at least view permission
  if id.find( 'manage_') >= 0:
    permissions['Authenticated'] = list(set(permissions.get('Authenticated',[]) + ['View']))
  # apply permissions for roles
  role_permissions = []
  for role in permissions:
    permission = permissions[role]
    ob.manage_role(role_to_manage=role,permissions=permission)
    role_permissions = list(set(role_permissions+permission))
  # activate all acquired permissions
  manager_permissions = [x['name'] for x in ob.permissionsOfRole('Manager') if x['selected']=='SELECTED']
  acquired_permissions = [x for x in manager_permissions if x not in role_permissions]
  ob.manage_acquiredPermissions(acquired_permissions)

def addDTMLMethod(container, id, title, data):
  """
  Add DTML-Method to container.
  @deprecated
  """
  container.manage_addDTMLMethod( id, title, data)
  initPermissions(container, id)

def addDTMLDocument(container, id, title, data):
  """
  Add DTML-Document to container.
  @deprecated
  """
  container.manage_addDTMLDocument( id, title, data)
  initPermissions(container, id)

def addExternalMethod(container, id, title, data):
  """
  Add External Method to container.
  """
  m = id
  filepath = standard.getINSTANCE_HOME()+'/Extensions/'+m+'.py'
  # Acquired external methods.
  if m.find('.') > 0 and os.path.exists(filepath):
    id = m[m.find('.')+1:]
    f = id
  # Other.
  else:
    m = getExternalMethodModuleName(container, id)
    f = id
    # If data is given then save to file in Extensions-folder.
    if data:
      filepath = standard.getINSTANCE_HOME()+'/Extensions/'+m+'.py'
      _fileutil.exportObj( data, filepath)
    elif m != f:
      context = container
      while context is not None:
        m = getExternalMethodModuleName(context, id)
        filepath = standard.getINSTANCE_HOME()+'/Extensions/'+m+'.py'
        if os.path.exists(filepath):
          break
        context = context.getParentNode()
  ExternalMethod.manage_addExternalMethod( container, id, title, m, f)

def addPageTemplate(container, id, title, data):
  """
  Add Page Template to container.
  """
  ZopePageTemplate.manage_addPageTemplate( container, id, title=title, text=data)
  ob = getattr( container, id)
  ob.output_encoding = 'utf-8'

def addPythonScript(container, id, title, data):
  """
  Add Script (Python) to container.
  """
  PythonScript.manage_addPythonScript( container, id)
  ob = getattr( container, id)
  ob.ZPythonScript_setTitle( title)
  ob.write( data)
  initPermissions(container, id)

def addFolder(container, id, title, data):
  """
  Add Folder to container.
  """
  container.manage_addFolder(id, title)
  ob = getattr( container, id)
  return ob

def addZSqlMethod(container, id, title, data):
  """
  Add Z Sql Method to container.
  """
  try:
    from Products.ZSQLMethods import SQL
    connection_id = container.SQLConnectionIDs()[0][1]
    arguments = ''
    template = ''
    SQL.manage_addZSQLMethod( container, id, title, connection_id, arguments, template)
  except:
    pass
  if data:
    ob = getattr( container, id)
    d = {}
    d['connection'] = ob.connection_id
    d['params'] = ob.arguments_src
    d['max_rows'] = ob.max_rows_
    d['max_cache'] = ob.max_cache_
    d['cache_time'] = ob.cache_time_
    for key in d:
      f = re.findall('<%s>((.|\s)*?)</%s>\n'%(key,key),data)
      if f:
        value = f[0][0]
        d[key] = value
        data = data.replace('<%s>%s</%s>'%(key,value,key),'').strip()
    ob.manage_edit(title=title,connection_id=d['connection'],arguments=d['params'],template=data) 
    ob.max_rows_ = int(d['max_rows'])
    ob.max_cache_ = int(d['max_cache'])
    ob.cache_time_ = int(d['cache_time'])

def addFile(container, id, title, data, content_type=None):
  """
  Add File to container.
  """
  if content_type is None:
    if type(data) is str:
      data = standard.pybytes(data,'utf-8')
    content_type, enc = standard.guess_content_type(id, data)
  container.manage_addFile(id=id, title=title, file=data, content_type=content_type)
  ob = getattr( container, id)
  return ob

def addImage(container, id, title, data, content_type=None):
  """
  Add Image to container.
  """
  if content_type is None:
    content_type, enc = standard.guess_content_type(id, data)
  container.manage_addImage(id=id, title=title, file=data, content_type=content_type)
  ob = getattr( container, id)
  return ob

security.apply(globals())