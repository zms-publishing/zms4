################################################################################
# ZMSFilterManager.py
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
from DateTime import DateTime
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
import ZPublisher.HTTPRequest
import copy
import time
from zope.interface import implementer, providedBy
# Product Imports.
from Products.zms import _blobfields
from Products.zms import IZMSConfigurationProvider, IZMSRepositoryProvider
from Products.zms import ZMSItem
from Products.zms import standard
from Products.zms import zopeutil


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
@implementer(
        IZMSConfigurationProvider.IZMSConfigurationProvider,
        IZMSRepositoryProvider.IZMSRepositoryProvider,)
class ZMSFilterManager(
        ZMSItem.ZMSItem):

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Properties
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    meta_type = 'ZMSFilterManager'
    zmi_icon = "fas fa-filter"
    icon_clazz = zmi_icon

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Options
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    manage_options_default_action = '../manage_customize'
    def manage_options(self):
      return [self.operator_setitem( x, 'action', '../'+x['action']) for x in copy.deepcopy(self.aq_parent.manage_options())]

    manage_sub_options__roles__ = None
    def manage_sub_options(self):
      return (
        {'label': 'TAB_FILTER','action': 'manage_main'},
        )

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Interface
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    manage = PageTemplateFile('zpt/ZMSFilterManager/manage_main', globals())
    manage_main = PageTemplateFile('zpt/ZMSFilterManager/manage_main', globals())

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Permissions
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    __administratorPermissions__ = (
        'manage_main',
        'manage_change',
        )
    __ac_permissions__=(
        ('ZMS Administrator', __administratorPermissions__),
        )


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSFilterManager.__init__: 
    
    Constructor.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __init__(self, filters={}, processes={}):
      self.id = 'filter_manager'
      self.filters = {}
      for x in filters:
        try:
          self.setFilter(None, x['id'], x['acquired'], x['name'], x['format'], x['content_type'], x['description'], x['roles'], x['meta_types'])
          index = 0
          for p in x.get('processes', []):
            self.setFilterProcess(x['id'], index, p['id'], p['file'])
            index += 1
        except:
          standard.writeError(self,'can\'t __init__ filter: %s'%standard.pystr(x))
      self.processes = {}
      for x in processes:
        try:
          self.setProcess(None, x['id'], x['acquired'], x['name'], x['type'], x['command'])
        except:
          standard.writeError(self,'can\'t __init__ process: %s'%standard.pystr(x))


    ############################################################################
    #
    #  IRepositoryProvider
    #
    ############################################################################

    """
    @see IRepositoryProvider
    """
    def provideRepository(self, r, ids=None):
      r = {}
      for id in self.getFilterIds():
        d = self.getFilter(id)
        d['meta_type'] = 'filter'
        d['__icon__'] = 'fas fa-filter'
        d['__description__'] = self.getZMILangStr('ATTR_FILTER')
        d['__filename__'] = ['filters',id,'__init__.py']
        if 'processes' in d:
          del d['processes']
        d['Processes'] = []
        for fp in self.getFilterProcesses(id):
          p = {}
          p['id'] = fp['id']
          if 'file' in fp:
            p['id'] = '%s/%i.%s'%(fp['id'],len(d['Processes']),fp['file_filename'])
            p['ob'] = fp['file']
          d['Processes'].append(p)
        r[id] = d
      for id in self.getProcessIds():
        d = self.getProcess(id)
        d['meta_type'] = 'process'
        d['__icon__'] = 'fas fa-cog'
        d['__description__'] = self.getZMILangStr('ATTR_PROCESS')
        d['__filename__'] = ['processes',id,'__init__.py']
        ob = zopeutil.getObject(self,id)
        if ob:
          command = {}
          command['id'] = id
          command['ob'] = ob
          command['type'] = ob.meta_type
          if 'command' in d:
            del d['command']
          d['Command'] = [command]
        r[id] = d
      return r

    """
    @see IRepositoryProvider
    """
    def updateRepository(self, r):
      id = r['id']
      if not id.startswith('__') and not id.endswith('__'):
        standard.writeBlock(self,"[updateRepository]: id=%s"%id)
        oldId = id
        newId = id
        if r.get('meta_type') == 'filter':
          newName = r['name']
          newFormat = r['format']
          newContentType = r['content_type']
          newDescription = r.get('description','')
          newRoles = r.get('roles',[])
          newMetaTypes = r.get('meta_types',[])
          self.setFilter(oldId, newId, newAcquired=0, newName=newName, newFormat=newFormat, newContentType=newContentType, newDescription=newDescription, newRoles=newRoles, newMetaTypes=newMetaTypes)
          index = 0
          for process in r.get('Processes', []):
            newProcessId = process.get('id')
            newProcessFile = None
            if newProcessId.find('/') >= 0:
              data = process.get('data')
              filename = process.get('id')
              filename = filename[filename.find('/')+1:]
              filename = filename[filename.find('.')+1:]
              newProcessId = newProcessId[:newProcessId.find('/')]
              newProcessFile = standard.FileFromData(self,data,filename)
            self.setFilterProcess(newId, index, newProcessId, newProcessFile)
            index += 1
        elif r.get('meta_type') == 'process':
          newName = r['name']
          newType = r['type']
          newCommand = r.get('command',None)
          for command in r.get('Command',[]):
            newCommand = command['data']
            break
          self.setProcess(oldId, newId, newName=newName, newType=newType, newCommand=newCommand)
      return id


    ################################################################################
    #
    #  XML IM/EXPORT
    #
    ################################################################################
    
    # ------------------------------------------------------------------------------
    #  importXml
    # ------------------------------------------------------------------------------
    
    def _importXml(self, item, createIfNotExists=True):
      itemType = item.get('type')
      itemOb = item.get('value')
      if itemType == 'filter':
        newId = itemOb.get('id')
        newAcquired = 0
        newName = itemOb.get('name')
        newFormat = itemOb.get('format')
        newContentType = itemOb.get('content_type')
        newDescription = itemOb.get('description', '')
        newRoles = itemOb.get('roles', [])
        newMetaTypes = itemOb.get('meta_types', [])
        if createIfNotExists:
          self.setFilter(None, newId, newAcquired, newName, newFormat, newContentType, newDescription, newRoles, newMetaTypes)
          index = 0
          for process in itemOb.get('processes', []):
            newProcessId = process.get('id')
            newProcessFile = process.get('file')
            self.setFilterProcess(newId, index, newProcessId, newProcessFile)
            index += 1
      elif itemType == 'process':
        newId = itemOb.get('id')
        newAcquired = 0
        newName = itemOb.get('name')
        newType = itemOb.get('type', 'process')
        newCommand = itemOb.get('command')
        if createIfNotExists:
          self.setProcess(None, newId, newAcquired, newName, newType, newCommand)
      else:
        standard.writeError(self, "[_importXml]: Unknown type >%s<"%itemType)
    
    def importXml(self, xml, createIfNotExists=True):
      v = standard.parseXmlString(xml)
      if isinstance(v, list):
        for item in v:
          id = self._importXml(item, createIfNotExists)
      else:
        id = self._importXml(v, createIfNotExists)
    
    # ------------------------------------------------------------------------------
    #  exportXml
    # ------------------------------------------------------------------------------
    def exportXml(self, REQUEST, RESPONSE):
      value = []
      ids = REQUEST.get('ids', [])
      filterIds = []
      for id in self.getFilterIds():
        if id in ids or len(ids) == 0:
          ob = self.getFilter(id).copy()
          value.append({'type':'filter','value':ob})
          filterIds.append(id)
      for id in self.getProcessIds():
        if id in ids or len(ids) == 0:
          ob = self.getProcess(id).copy()
          value.append({'type':'process','value':ob})
      # Filename.
      filename = 'export'
      if len(filterIds)==1:
        filename = filterIds[0]
      elif len(ids)==1:
        filename = ids[0]
      # XML.
      if len(value)==1:
        value = value[0]
      content_type = 'text/xml; charset=utf-8'
      filename = '%s.filter.xml'%filename
      export = self.getXmlHeader() + self.toXmlString(value, 1)
      RESPONSE.setHeader('Content-Type', content_type)
      RESPONSE.setHeader('Content-Disposition', 'attachment;filename="%s"'%filename)
      return export
    
    
    # --------------------------------------------------------------------------
    #  FilterManager.getProcessIds:
    # 
    #  Returns list of process-Ids.
    # --------------------------------------------------------------------------
    def getProcessIds(self, sort=True):
      obs = self.processes
      ids = list(obs)
      portalMaster = self.getPortalMaster()
      if portalMaster is not None:
        ids = list(set(ids+portalMaster.getProcessIds()))
      if sort:
        ids = sorted(ids,key=lambda x:self.getProcess(x)['name'])
      return ids

    # --------------------------------------------------------------------------
    #  FilterManager.getProcess:
    # 
    #  Returns process specified by Id.
    # --------------------------------------------------------------------------
    def getProcess(self, id):
      processes = self.processes
      process = {}
      if id in processes:
        process = processes.get( id).copy()
      else:
        # Acquire from parent.
        portalMaster = self.getPortalMaster()
        if portalMaster is not None:
          if id in portalMaster.getProcessIds():
            process = portalMaster.getProcess(id)
            process['acquired'] = 1
      process['id'] = id
      process['name'] = process.get('name',process['id'])
      # Synchronize type.
      try:
        container = self.getHome()
        ob = zopeutil.getObject( container, process['id'])
        process['command'] = zopeutil.readData( ob)
      except:
        pass
      return process


    # --------------------------------------------------------------------------
    #  FilterManager.getFilterIds:
    # 
    #  Returns list of filter-Ids.
    # --------------------------------------------------------------------------
    def getFilterIds(self, sort=True):
      obs = self.filters
      ids = list(obs)
      if sort:
        ids = sorted(ids,key=lambda x:self.getProcess(x)['name'])
      return ids


    # --------------------------------------------------------------------------
    #  FilterManager.getFilter:
    # 
    #  Returns filter specified by Id.
    # --------------------------------------------------------------------------
    def getFilter(self, id):
      obs = self.filters
      ob = {}
      if id in obs:
        ob = obs.get( id).copy()
      # Acquire from parent.
      if ob.get('acquired', 0) == 1:
        portalMaster = self.getPortalMaster()
        if portalMaster is not None:
          ob = portalMaster.getFilter(id)
          ob['acquired'] = 1
      ob['id'] = id
      return ob


    """
    ################################################################################
    #
    #   F I L T E R S
    #
    ################################################################################
    """

    # ------------------------------------------------------------------------------
    #  _filtermanager.setFilter:
    # 
    #  Set/add filter specified by given Id.
    # ------------------------------------------------------------------------------
    def setFilter(self, oldId, newId, newAcquired=0, newName='', newFormat='', newContentType='', newDescription='', newRoles=[], newMetaTypes=[]):
      # Set.
      obs = self.filters
      ob = {}
      ob['acquired'] = newAcquired
      ob['name'] = newName
      ob['format'] = newFormat
      ob['content_type'] = newContentType
      ob['description'] = newDescription
      ob['roles'] = newRoles
      ob['meta_types'] = newMetaTypes
      obs[newId] = ob
      # Rename assets.
      if oldId != newId:
        oldprefix = '%s.'%(oldId)
        ids = [x for x in self.objectIds('File') if x.startswith(oldprefix)]
        for id in ids:
          suffix = '.'.join(id.split('.')[1:])
          self.manage_renameObject(id=id, new_id='%s%s'%('%s.'%newId,suffix))
      # Set attribute.
      self.filters = obs.copy()
      # Return with new id.
      return newId

    # ------------------------------------------------------------------------------
    #  _filtermanager.delFilter:
    # 
    #  Delete filter specified by given Id.
    # ------------------------------------------------------------------------------
    def delFilter(self, id):
      # Delete.
      cp = self.filters
      obs = {}
      for key in cp:
        if key != id:
          obs[key] = cp[key]
      # Delete assets.
      prefix = '%s.'%(id)
      ids = [x for x in self.objectIds('File') if x.startswith(prefix)]
      if ids:
        self.manage_delObjects(ids=ids)
      # Set attribute.
      self.filters = obs.copy()
      # Return with empty id.
      return ''


    """
    ################################################################################
    #
    #   F I L T E R - P R O C E S S E S
    #
    ################################################################################
    """

    # --------------------------------------------------------------------------
    #  FilterManager.getFilterProcesses:
    # 
    #  Returns list of processes for filter specified by Id.
    # --------------------------------------------------------------------------
    def getFilterProcesses(self, id):
      obs = []
      index = 0
      for process in self.getFilter( id).get( 'processes', []):
        ob = process.copy()
        ob[ 'type'] = ob.get( 'type', 'process')
        prefix = '%s.%i.'%(id,index)
        ids = [x for x in self.objectIds('File') if x.startswith(prefix)]
        if ids:
          f = zopeutil.getObject(self,ids[0])
          ob['file'] = f
          ob['file_href'] = f.absolute_url()
          ob['file_filename'] = '.'.join(f.getId().split('.')[2:])
          ob['file_content_type'] = f.getContentType()
          ob['file_size'] = f.get_size()
        p = self.getProcess(ob['id'])
        if p is not None:
          obs.append( ob)
        index += 1
      return obs

    # ------------------------------------------------------------------------------
    #  _filtermanager.setFilterProcess:
    # 
    #  Set/add filter-process specified by given id.
    # ------------------------------------------------------------------------------
    def setFilterProcess(self, id, index, newProcessId, newProcessFile=None):
      # Set.
      obs = self.filters
      ob = {}
      ob['id'] = newProcessId
      pobs = obs[id].get('processes', [])
      pobs.append(ob)
      obs[id]['processes'] = pobs
      # Asset.
      if isinstance(newProcessFile, _blobfields.MyBlob):
        prefix = '%s.%i.'%(id,index)
        # Delete asset with prefix.
        ids = [x for x in self.objectIds('File') if x.startswith(prefix)]
        if ids:
          self.manage_delObjects(ids=ids)
        # Add asset with prefix.
        fn = newProcessFile.getFilename()
        data = newProcessFile.getData()
        zopeutil.addFile(self, '%s%s'%(prefix,fn), fn, data)
      # Set attribute.
      self.filters = obs.copy()
      # Return with new id.
      return len(pobs)-1

    # ------------------------------------------------------------------------------
    #  _filtermanager.delFilterProcess:
    # 
    #  Delete filter-process specified by given Ids.
    # ------------------------------------------------------------------------------
    def delFilterProcess(self, id, index):
      # Delete.
      obs = self.filters
      p = obs[ id].get('processes', [])
      p.remove( p[index])
      obs[id]['processes'] = p
      # Asset.
      prefix = '%s.%i.'%(id,index)
      # Delete asset with prefix.
      ids = [x for x in self.objectIds('File') if x.startswith(prefix)]
      if ids:
        self.manage_delObjects(ids=ids)
      # Rename assets.
      for i in range(len(p)-index):
        oldprefix = '%s.%i.'%(id,i+index+1)
        newprefix = '%s.%i.'%(id,i+index)
        old = [x for x in self.objectIds('File') if x.startswith(oldprefix)]
        if old:
          old_id = old[0]
          fn = '.'.join(old_id.split('.')[2:])
          new_id = '%s%s'%(newprefix,fn)
          self.manage_renameObject(id=old_id, new_id=new_id)
      # Set attribute.
      self.filters = obs.copy()
      # Return with empty id.
      return -1

    # ------------------------------------------------------------------------------
    #  _filtermanager.moveFilterProcess:
    # 
    #  Move filter-process by given id and index to specified position.
    # ------------------------------------------------------------------------------
    def moveFilterProcess(self, id, index, pos):
      # Set.
      obs = self.filters
      p = obs[id].get('processes', [])
      ob = p[index]
      p.remove(ob)
      p.insert(pos, ob)
      obs[id]['processes'] = p
      # Asset.
      prefix = '%s.%i.'%(id,index)
      # Rename asset with prefix.
      ids = [x for x in self.objectIds('File') if x.startswith(prefix)]
      if ids:
        old_id = ids[0]
        fn = '.'.join(old_id.split('.')[2:])
        new_id='%s.%i.%s'%(id,pos,fn)
        self.manage_renameObject(id=old_id,new_id=new_id)
      # Rename assets after move.
      for i in range(abs(index-pos)):
        oldprefix = '%s.%i.'%(id,i+min(index,pos)+1)
        newprefix = '%s.%i.'%(id,i+min(index,pos))
        old = [x for x in self.objectIds('File') if x.startswith(oldprefix)]
        if old:
          old_id = old[0]
          fn = '.'.join(old_id.split('.')[2:])
          new_id='%s%s'%(newprefix,fn)
          self.manage_renameObject(id=old_id, new_id=new_id)
      # Set attribute.
      self.filters = obs.copy()
      # Return with new id.
      return pos


    ############################################################################
    #  FilterManager.manage_changeFilter:
    #
    #  Customize filter.
    ############################################################################
    def manage_changeFilter(self, lang, btn='', key='', REQUEST=None, RESPONSE=None):
      """ FilterManager.manage_changeFilter """
      message = ''
      id = REQUEST.get('id', '')
      index = REQUEST.get('index', -1)
      
      # Change.
      # -------
      if btn == 'BTN_SAVE':
        cp = self.getFilter(id)
        # Filter.
        newId = REQUEST.get('inpId').strip()
        newAcquired = 0
        newName = REQUEST.get('inpName').strip()
        newFormat = REQUEST.get('inpFormat').strip()
        newContentType = REQUEST.get('inpContentType').strip()
        newDescription = REQUEST.get('inpDescription').strip()
        newRoles = REQUEST.get('inpRoles', [])
        newMetaTypes = REQUEST.get('inpMetaTypes', [])
        id = self.setFilter(id, newId, newAcquired, newName, newFormat, newContentType, newDescription, newRoles, newMetaTypes)
        # Filter Processes.
        index = 0
        for filterProcess in cp.get('processes', []):
          newProcessId = REQUEST.get('newFilterProcessId_%i'%index, '').strip()
          newProcessFile = REQUEST.get('newFilterProcessFile_%i'%index)
          if isinstance(newProcessFile, ZPublisher.HTTPRequest.FileUpload):
            if len(getattr(newProcessFile, 'filename', ''))==0:
              newProcessFile = filterProcess.get('file', None)
            else:
              newProcessFile = _blobfields.createBlobField(self, _blobfields.MyFile, newProcessFile)
          self.setFilterProcess(id, index, newProcessId, newProcessFile)
          index += 1
        # New Filter Process?
        newProcessId = REQUEST.get('newFilterProcessId_%i'%index, '').strip()
        newProcessFile = REQUEST.get('newFilterProcessFile_%i'%index)
        if newProcessId:
          self.setFilterProcess(id, newProcessId, newProcessFile)
        # Return with message.
        message = self.getZMILangStr('MSG_CHANGED')
      
      # Delete.
      # -------
      elif btn == 'BTN_DELETE':
        if key == 'obj':
          ids = REQUEST.get('ids', [])
          for id in ids:
            self.delFilter(id)
          message = self.getZMILangStr('MSG_DELETED')%len(ids)
        elif key == 'attr':
          ids = [REQUEST.get('id')]
          for id in ids:
            if id is not None:
              self.delFilterProcess(id, index)
          message = self.getZMILangStr('MSG_DELETED')%len(ids)
      
      # Export.
      # -------
      elif btn == 'BTN_EXPORT':
        return self.exportXml(REQUEST, RESPONSE)
      
      # Import.
      # -------
      elif btn == 'BTN_IMPORT':
        f = REQUEST['file']
        if f:
          filename = f.filename
          self.importXml(xml=f)
        else:
          filename = REQUEST['init']
          self.importConf(filename, createIfNotExists=True)
        message = self.getZMILangStr('MSG_IMPORTED')%('<em>%s</em>'%filename)
      
      # Insert.
      # -------
      elif btn == 'BTN_INSERT':
        newId = REQUEST.get('newId').strip()
        newAcquired = 0
        newName = REQUEST.get('newName').strip()
        newFormat = REQUEST.get('newFormat').strip()
        newContentType = REQUEST.get('newContentType').strip()
        id = self.setFilter(None, newId, newAcquired, newName, newFormat, newContentType)
        message = self.getZMILangStr('MSG_INSERTED')%id
      
      # Move to.
      # --------
      elif btn == 'move_to':
        pos = REQUEST['pos']
        self.moveFilterProcess(id, index, pos)
        message = self.getZMILangStr('MSG_MOVEDOBJTOPOS')%(("<em>%s</em>"%index), (pos+1))
      
      # Return with message.
      message = standard.url_quote(message)
      return RESPONSE.redirect('manage_main?id=%s&index:int=%i&lang=%s&manage_tabs_message=%s'%(id, index, lang, message))


    """
    ################################################################################
    #
    #   P R O C E S S E S
    #
    ################################################################################
    """
    
    # ------------------------------------------------------------------------------
    #  _filtermanager.setProcess:
    # 
    #  Set/add process specified by given Id.
    # ------------------------------------------------------------------------------
    def setProcess(self, oldId, newId, newAcquired=0, newName='', newType='process', newCommand=None):
      if newCommand is None:
        newCommand = ''
        if newType in [ 'Script (Python)']:
          newCommand += '# --// BO '+ newId + ' //--\n'
          newCommand += '# Example code:\n'
          newCommand += '\n'
          newCommand += '# Import a standard function, and get the HTML request and response objects.\n'
          newCommand += 'from Products.PythonScripts.standard import html_quote\n'
          newCommand += 'request = container.REQUEST\n'
          newCommand += 'RESPONSE =  request.RESPONSE\n'
          newCommand += '\n'
          newCommand += '# Return a string identifying this script.\n'
          newCommand += 'p = []\n'
          newCommand += 'p.append("This is the Python Script %s" % script.getId())\n'
          newCommand += 'p.append("in %s" % container.absolute_url())\n'
          newCommand += 'return "\\n".join(p)\n'
          newCommand += '\n'
          newCommand += '# --// EO '+ newId + ' //--\n'
        elif newType in [ 'External Method']:
          newCommand = ''
          newCommand += '# Example code:\n'
          newCommand += '\n'
          newCommand += 'def ' + newId + '( self, request):\n'
          newCommand += '  return "This is the external method ' + newId + '"\n'
      # Remove Zope-Object (if exists)
      zopeutil.removeObject(self, oldId)
      zopeutil.removeObject(self, newId)
      # Insert Zope-Object.
      if isinstance(newCommand,_blobfields.MyBlob): newCommand = newCommand.getData()
      if standard.is_str(newCommand): newCommand = newCommand.replace('\r', '')
      zopeutil.addObject(self, newType, newId, newName, newCommand)
      # Set.
      obs = self.processes
      ob = {}
      ob['acquired'] = newAcquired
      ob['name'] = newName
      ob['type'] = newType
      ob['command'] = newCommand
      obs[newId] = ob
      # Set attribute.
      self.processes = obs.copy()
      # Return with new id.
      return newId


    # ------------------------------------------------------------------------------
    #  _filtermanager.delProcess:
    # 
    #  Delete process specified by given Id.
    # ------------------------------------------------------------------------------
    def delProcess(self, id):
      # Delete.
      obs = self.processes
      del obs[id]
      zopeutil.removeObject(self, id)
      # Set attribute.
      self.processes = obs.copy()
      # Return with empty id.
      return ''


    ############################################################################
    #  FilterManager.manage_changeProcess:
    #
    #  Customize process.
    ############################################################################
    def manage_changeProcess(self, lang, btn='', key='', REQUEST=None, RESPONSE=None):
      """ FilterManager.manage_changeProcess """
      message = ''
      id = REQUEST.get('id', '')

      # Change.
      # -------
      if btn == 'BTN_SAVE':
        newId = REQUEST.get('inindex').strip()
        newAcquired = 0
        newName = REQUEST.get('inpName').strip()
        newType = REQUEST.get('inpType').strip()
        newCommand = REQUEST.get('inpCommand').strip()
        id = self.setProcess(id, newId, newAcquired, newName, newType, newCommand)
        message = self.getZMILangStr('MSG_CHANGED')

      # Delete.
      # -------
      elif btn == 'BTN_DELETE':
        ids = REQUEST.get('ids', [])
        for id in ids:
          self.delProcess(id)
        message = self.getZMILangStr('MSG_DELETED')%len(ids)

      # Export.
      # -------
      elif btn == 'BTN_EXPORT':
        return self.exportXml(REQUEST, RESPONSE)

      # Import.
      # -------
      elif btn == 'BTN_IMPORT':
        f = REQUEST['file']
        if f:
          filename = f.filename
          self.importXml(xml=f)
        else:
          filename = REQUEST['init']
          self.importConf(filename, createIfNotExists=True)
        message = self.getZMILangStr('MSG_IMPORTED')%('<em>%s</em>'%filename)

      # Insert.
      # -------
      elif btn == 'BTN_INSERT':
        newId = REQUEST.get('newId').strip()
        newAcquired = 0
        newName = REQUEST.get('newName').strip()
        newType = REQUEST.get('newType').strip()
        id = self.setProcess(None, newId, newAcquired, newName, newType)
        message = self.getZMILangStr('MSG_INSERTED')%id

      # Return with message.
      message = standard.url_quote(message)
      return RESPONSE.redirect('manage_main?id=%s&lang=%s&manage_tabs_message=%s'%(id, lang, message))

################################################################################
