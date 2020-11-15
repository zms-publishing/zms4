################################################################################
# ZMSMetacmdProvider.py
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
from Products.PageTemplates import ZopePageTemplate
import copy
import os
from zope.interface import implementer
# Product Imports.
from Products.zms import _fileutil
from Products.zms import standard
from Products.zms import zopeutil
from Products.zms import IZMSMetacmdProvider, IZMSConfigurationProvider, IZMSRepositoryProvider
from Products.zms import ZMSItem


# Example code.
# -------------

dtmlExampleCode = '<!-- @deprecated -->'

pageTemplateExampleCode = \
  '<!DOCTYPE html>\n' + \
  '<html lang="en">\n' + \
  '<tal:block tal:content="structure python:here.zmi_html_head(here,request)">zmi_html_head</tal:block>\n' + \
  '<body class="zmi">\n' + \
  '<tal:block tal:content="structure python:here.zmi_body_header(here,request)">zmi_body_header</tal:block>\n' + \
  '<div id="zmi-tab">\n' + \
  '<tal:block tal:content="structure python:here.zmi_breadcrumbs(here,request)">zmi_breadcrumbs</tal:block>\n' + \
  '</div><!-- #zmi-tab -->\n' + \
  '<script>\n' + \
  '</script>\n' + \
  '<tal:block tal:content="structure python:here.zmi_body_footer(here,request)">zmi_body_footer</tal:block>\n' + \
  '</body>\n' + \
  '</html>\n'

pyScriptExampleCode = \
  '# Example code:\n' + \
  '\n' + \
  '# Import a standard function, and get the HTML request and response objects.\n' + \
  'from Products.PythonScripts.standard import html_quote\n' + \
  'request = container.REQUEST\n' + \
  'RESPONSE =  request.RESPONSE\n' + \
  '\n' + \
  '# Return a string identifying this script.\n' + \
  'p = []\n' + \
  'p.append("This is the Python Script %s" % script.getId())\n' + \
  'p.append("in %s" % container.absolute_url())\n' + \
  'return "\\n".join(p)\n' + \
  ''


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
@implementer(
        IZMSConfigurationProvider.IZMSConfigurationProvider,
        IZMSMetacmdProvider.IZMSMetacmdProvider,
        IZMSRepositoryProvider.IZMSRepositoryProvider)
class ZMSMetacmdProvider(
        ZMSItem.ZMSItem):

    # Properties.
    # -----------
    meta_type = 'ZMSMetacmdProvider'
    zmi_icon = "fas fa-wrench"
    icon_clazz = zmi_icon

    # Management Options.
    # -------------------
    manage_options_default_action = '../manage_customize'
    def manage_options(self):
      return [self.operator_setitem( x, 'action', '../'+x['action']) for x in  copy.deepcopy(self.aq_parent.manage_options())]

    manage_sub_options__roles__ = None
    def manage_sub_options(self):
      return (
        {'label': 'TAB_METACMD','action': 'manage_main'},
        )

    # Management Interface.
    # ---------------------
    manage = PageTemplateFile('zpt/ZMSMetacmdProvider/manage_main', globals()) 
    manage_main = PageTemplateFile('zpt/ZMSMetacmdProvider/manage_main', globals()) 
    manage_main_acquire = PageTemplateFile('zpt/ZMSMetacmdProvider/manage_main_acquire', globals()) 

    # Management Permissions.
    # -----------------------
    __administratorPermissions__ = (
      'manage_changeMetacmds', 'manage_main', 'manage_main_acquire'
    )
    __ac_permissions__=(
      ('ZMS Administrator', __administratorPermissions__),
    )

    ############################################################################
    #  ZMSMetacmdProvider.__init__: 
    #
    #  Constructor.
    ############################################################################
    def __init__(self, commands=[]):
      self.id = 'metacmd_manager'
      self.commands = copy.deepcopy(commands)


    ############################################################################
    #
    #  IRepositoryProvider
    #
    ############################################################################

    """
    @see IRepositoryProvider
    """
    def provideRepository(self, ids=None):
      r = {}
      if ids is None:
        ids = self.getMetaCmdIds()
      for id in ids:
        o = self.getMetaCmd(id)
        if o and not o.get('acquired', 0):
          d = {}
          for k in [x for x in o if x not in ['bobobase_modification_time', 'data', 'home', 'meta_type']]:
            d[k] = o[k]
          ob = getattr(self, id)
          if ob:
            d['__icon__'] = ob.zmi_icon() if 'zmi_icon' in ob.__dict__ else 'fas fa-cog'
            d['__description__'] = ob.meta_type
            attr = {}
            attr['id'] = id
            attr['ob'] = ob
            attr['type'] = ob.meta_type
            d['Impl'] = [attr]
          r[id] = d
      return r

    """
    @see IRepositoryProvider
    """
    def updateRepository(self, r):
      id = r['id']
      impl = r['Impl'][0]
      newId = id
      newAcquired = 0
      newRevision = r.get('revision', '0.0.0')
      newName = r['name']
      newTitle = r.get('title', '')
      newMethod = impl['type']
      newData = impl['data']
      newExecution = 'execution' in r and r['execution']
      newDescription = r.get('description', '')
      newIconClazz = r.get('icon_clazz', '')
      newMetaTypes = r.get('meta_types',[])
      newRoles = r.get('roles',[])
      newNodes = r.get('nodes', '{$}')
      self.delMetacmd(id)
      return self.setMetacmd(None, newId, newAcquired, newRevision, newName, newTitle, newMethod, \
        newData, newExecution, newDescription, newIconClazz, newMetaTypes, newRoles, \
        newNodes)


    ############################################################################
    #
    #  XML IM/EXPORT
    #
    ############################################################################

    # ------------------------------------------------------------------------------
    #  ZMSMetacmdProvider.importXml
    # ------------------------------------------------------------------------------
    def _importXml(self, item, createIfNotExists=1):
      id = item['id']
      if createIfNotExists == 1:
        
        # Delete existing object.
        try: self.delMetacmd(id)
        except: pass
        
        # Initialize attributes of new object.
        newId = id
        newAcquired = 0
        newRevision = item.get('revision', '0.0.0')
        newName = item['name']
        newTitle = item.get('title', '')
        newMethod = item['meta_type']
        newExecution = ('execution' in item and item['execution']) or ('exec' in item and item['exec'])
        newDescription = item.get('description', '')
        newIconClazz = item.get('icon_clazz', '')
        newMetaTypes = item.get('meta_types',[])
        newRoles = item.get('roles',[])
        newNodes = item.get('nodes', '{$}')
        newData = item['data']
        
        # Return with new id.
        return self.setMetacmd(None, newId, newAcquired, newRevision, newName, newTitle, newMethod, \
          newData, newExecution, newDescription, newIconClazz, newMetaTypes, newRoles, \
          newNodes)

    def importXml(self, xml, createIfNotExists=1):
      v = standard.parseXmlString(xml)
      if isinstance(v, list):
        for item in v:
          id = self._importXml(item, createIfNotExists)
      else:
        id = self._importXml(v, createIfNotExists)


    # ------------------------------------------------------------------------------
    #  ZMSMetacmdProvider.__get_metacmd__
    # ------------------------------------------------------------------------------
    def __get_metacmd__(self, id):
      return ([x for x in self.commands if x['id']==id]+[None])[0]


    # ------------------------------------------------------------------------------
    #  ZMSMetacmdProvider.delMetacmd:
    # 
    #  Delete Action specified by given Id.
    # ------------------------------------------------------------------------------
    def delMetacmd(self, id):
      
      # Catalog.
      obs = self.commands
      old = [x for x in obs if x['id'] == id]
      if len(old) > 0:
        obs.remove(old[0])
      self.commands = obs
      self.commands = copy.deepcopy(self.commands) # Make persistent.
      
      # Remove Template.
      container = self.aq_parent
      zopeutil.removeObject(container, id)
      
      # Return with empty id.
      return ''

    # ------------------------------------------------------------------------------
    #  ZMSMetacmdProvider.setMetacmd:
    #
    #  Set/add Action specified by given Id.
    # ------------------------------------------------------------------------------
    def setMetacmd(self, id, newId, newAcquired, newRevision='0.0.0', newName='', newTitle='', newMethod=None, \
          newData=None, newExecution=0, newDescription='', newIconClazz='', newMetaTypes=[], \
          newRoles=['ZMSAdministrator'], newNodes='{$}'):
      
      # Catalog.
      obs = self.commands
      old = [x for x in obs if x['id'] in [id, newId]]
      if len(old) > 0:
        obs.remove(old[0])
      
      # Values.
      new = {}
      new['id'] = newId
      new['acquired'] = newAcquired
      new['revision'] = newRevision
      new['name'] = newName
      new['title'] = newTitle
      new['description'] = newDescription
      new['icon_clazz'] = newIconClazz
      new['meta_types'] = newMetaTypes
      new['roles'] = newRoles
      new['nodes'] = newNodes
      new['execution'] = newExecution
      obs.append(new)
      self.commands = copy.deepcopy(self.commands) # Make persistent.
      
      # Insert Object.
      if not newAcquired:
        container = self.getDocumentElement()
        if newMethod is None:
          newMethod = getattr(container, id).meta_type
        if id is None and newData is None:
          if newMethod in ['DTML Document', 'DTML Method']:
            newData = dtmlExampleCode
          elif newMethod == 'Page Template':
            newData = pageTemplateExampleCode 
          elif newMethod == 'Script (Python)':
            newData = pyScriptExampleCode
          elif newMethod == 'External Method':
            newData = ''
            newData += '# Example code:\n'
            newData += '\n'
            newData += 'def ' + newId + '( self):\n'
            newData += '  return "This is the external method ' + newId + '"\n'
        zopeutil.removeObject(container, id)
        zopeutil.removeObject(container, newId)
        object = zopeutil.addObject(container, newMethod, newId, newTitle, newData, permissions={'Authenticated':['View']})
      
      # Return with new id.
      return newId


    # --------------------------------------------------------------------------
    #  ZMSMetacmdProvider.getMetaCmdDescription
    # --------------------------------------------------------------------------
    def getMetaCmdDescription(self, id):
      """
      Returns description of meta-command specified by ID.
      """
      metaCmd = self.getMetaCmd(id)
      return metaCmd.get('description', '')


    # --------------------------------------------------------------------------
    #  ZMSMetacmdProvider.getMetaCmd
    # 
    # Returns action.
    # --------------------------------------------------------------------------
    def getMetaCmd(self, id):
      obs = self.getMetaCmds(sort=False)
      # Filter by id.
      obs = [x for x in obs if x['id'] == id]
      # Not found!
      if len(obs) == 0:
        return None
      # Refresh Object.
      metaCmd = obs[0]
      if metaCmd.get('home',None)==None:
        return None
      if 'exec' in metaCmd:
        metaCmd['execution'] = metaCmd['exec']
        del metaCmd['exec']
      container = self.aq_parent
      src = zopeutil.getObject(metaCmd['home'], metaCmd['id'])
      newData = zopeutil.readObject(metaCmd['home'], metaCmd['id'], '')
      data = zopeutil.readObject(container, metaCmd['id'], '')
      acquiredExternalMethod = metaCmd.get('acquired',0) and src.meta_type=='External Method'
      if src is not None and (newData != data or acquiredExternalMethod):
        newId = metaCmd['id']
        newMethod = src.meta_type
        newTitle = '*** DO NOT DELETE OR MODIFY ***'
        zopeutil.removeObject(container, newId, removeFile=False)
        zopeutil.addObject(container, newMethod, ['',metaCmd['home'].getHome().getId()+'.'][acquiredExternalMethod]+newId, newTitle, newData)
      ob = zopeutil.getObject(container, metaCmd['id'])
      if ob is not None:
        metaCmd['meta_type'] = ob.meta_type
        metaCmd['data'] = zopeutil.readObject(container, metaCmd['id'], '')
        metaCmd['bobobase_modification_time'] = DateTime(ob._p_mtime)
      return metaCmd


    # --------------------------------------------------------------------------
    #  ZMSMetacmdProvider.getMetaCmdIds
    #
    #  Returns list of action-ids.
    # --------------------------------------------------------------------------
    def getMetaCmdIds(self, sort=True):
      obs = self.commands
      if sort:
        obs = [self.getMetaCmd(x['id']) for x in obs]
        obs = [(x['name'], x) for x in obs if x is not None]
        obs = sorted(obs)
        obs = [x[1] for x in obs]
      ids = [x['id'] for x in obs]
      return ids


    # --------------------------------------------------------------------------
    #  ZMSMetacmdProvider.getMetaCmds
    #
    #  Returns list of actions.
    # --------------------------------------------------------------------------
    def getMetaCmds(self, context=None, stereotype='', sort=True):
      stereotypes = {'insert':'manage_add','tab':'manage_tab','repository':'manage_repository'}
      metaCmds = []
      portalMasterMetaCmds = None
      for metaCmd in [x for x in self.commands if x['id'].startswith(stereotypes.get(stereotype, ''))]:
        # Acquire from parent.
        if metaCmd.get('acquired', 0)==1:
          if portalMasterMetaCmds is None:
            portalMaster = self.getPortalMaster()
            portalMasterMetaCmds = portalMaster.getMetaCmds(stereotype=stereotype)
          l = [x for x in portalMasterMetaCmds if x['id']==metaCmd['id']]
          if len(l) > 0:
            metaCmd = l[0]
            metaCmd['acquired'] = 1
        else:
          metaCmd = metaCmd.copy()
          metaCmd['home'] = self.aq_parent
          metaCmd['stereotype'] = ' '.join([x for x in stereotypes if metaCmd['id'].startswith(stereotypes[x])])
          metaCmd['action'] = '%smanage_executeMetacmd?id='+metaCmd['id']
          if metaCmd.get('execution') == 2:
            metaCmd['action'] = 'javascript:%%s'+metaCmd['id']
            
        metaCmds.append(metaCmd)
      if context is not None:
        request = context.REQUEST
        auth_user = request['AUTHENTICATED_USER']
        user_roles = context.getUserRoles(auth_user)
        absolute_url = '/'.join(list(context.getPhysicalPath())+[''])
        l = []
        for metaCmd in metaCmds:
          canExecute = True
          if canExecute:
            meta_types = metaCmd.get('meta_types',[])
            hasMetaType = False
            hasMetaType = hasMetaType or '*' in meta_types
            hasMetaType = hasMetaType or context.meta_id in meta_types
            hasMetaType = hasMetaType or 'type(%s)'%context.getType() in meta_types
            canExecute = canExecute and hasMetaType
          if canExecute:
            roles = metaCmd.get('roles',[])
            hasRole = False
            hasRole = hasRole or '*' in roles
            hasRole = hasRole or len(standard.intersection_list(user_roles,roles)) > 0
            hasRole = hasRole or auth_user.has_role('Manager')
            canExecute = canExecute and hasRole
          if canExecute:
            nodes = standard.string_list(metaCmd.get('nodes', '{$}'))
            sl = []
            sl.extend([(context.getHome().id+'/content/'+x[2:-1]+'/').replace('//', '/') for x in [x for x in nodes if x.find('@')<0]])
            sl.extend([(x[2:-1].replace('@', '/content/')+'/').replace('//', '/') for x in [x for x in nodes if x.find('@')>0]])
            hasNode = len([x for x in sl if absolute_url.find(x)>=0]) > 0
            canExecute = canExecute and hasNode
          if canExecute:
            l.append(metaCmd)
        metaCmds = l
      return metaCmds


    ############################################################################
    #  ZMSMetacmdProvider.manage_changeMetacmds:
    #
    #  Change Meta-Commands.
    ############################################################################
    def manage_changeMetacmds(self, btn, lang, REQUEST, RESPONSE):
        """ ZMSMetacmdProvider.manage_changeMetacmds """
        message = ''
        id = REQUEST.get('id', '')
        
        # Acquire.
        # --------
        if btn == 'BTN_ACQUIRE':
          aq_ids = REQUEST.get('aq_ids', [])
          for newId in aq_ids:
            newAcquired = 1
            self.setMetacmd(None, newId, newAcquired)
          message = self.getZMILangStr('MSG_INSERTED')%str(len(aq_ids))
        
        # Change.
        # -------
        elif btn == 'BTN_SAVE':
          id = REQUEST['id']
          newId = REQUEST['el_id'].strip()
          newAcquired = 0
          newRevision = REQUEST.get('el_revision', '').strip()
          newName = REQUEST.get('el_name', '').strip()
          newTitle = REQUEST.get('el_title', '').strip()
          newMethod = REQUEST.get('el_method')
          newData = REQUEST.get('el_data', '').strip()
          newExecution = REQUEST.get('el_execution', 0)
          newDescription = REQUEST.get('el_description', '').strip()
          newIconClazz = REQUEST.get('el_icon_clazz', '')
          newMetaTypes = REQUEST.get('el_meta_types', [])
          newRoles = REQUEST.get('el_roles', [])
          newNodes = REQUEST.get('el_nodes', '')
          id = self.setMetacmd(id, newId, newAcquired, newRevision, newName, newTitle, \
            newMethod, newData, newExecution, newDescription, newIconClazz, \
            newMetaTypes, newRoles, newNodes)
          message = self.getZMILangStr('MSG_CHANGED')
        
        # Copy.
        # -----
        elif btn == 'BTN_COPY':
          metaOb = self.getMetaCmd(id)
          if metaOb.get('acquired', 0) == 1:
            portalMaster = self.getPortalMaster()
            if portalMaster is not None:
              REQUEST.set('ids', [id])
              xml =  portalMaster.manage_changeMetacmds('BTN_EXPORT', lang, REQUEST, RESPONSE)
              self.importXml(xml=xml)
              message = self.getZMILangStr('MSG_IMPORTED')%('<i>%s</i>'%id)
        
        # Delete.
        # -------
        elif btn == 'BTN_DELETE':
          if id:
            ids = [id]
          else:
            ids = REQUEST.get('ids', [])
          for id in ids:
            self.delMetacmd(id)
          id = ''
          message = self.getZMILangStr('MSG_DELETED')%len(ids)
        
        # Export.
        # -------
        elif btn == 'BTN_EXPORT':
          revision = '0.0.0'
          value = []
          ids = REQUEST.get('ids', [])
          for id in self.getMetaCmdIds():
            if id in ids or len(ids) == 0:
              metaCmd = self.getMetaCmd(id)
              revision = metaCmd.get('revision', '0.0.0')
              el_id = metaCmd['id']
              el_name = metaCmd['name']
              el_title = metaCmd.get('title', '')
              el_meta_type = metaCmd['meta_type']
              el_description = metaCmd['description']
              el_icon_clazz = metaCmd.get('icon_clazz', '')
              el_meta_types = metaCmd['meta_types']
              el_roles = metaCmd['roles']
              el_execution = metaCmd['execution']
              el_data = zopeutil.readObject(metaCmd['home'], metaCmd['id'])
              # Value.
              value.append({'id':el_id,'revision':revision,'name':el_name,'title':el_title,'description':el_description,'meta_types':el_meta_types,'roles':el_roles,'execution':el_execution,'icon_clazz':el_icon_clazz,'meta_type':el_meta_type,'data':el_data})
          # XML.
          if len(ids)==1:
            filename = '%s-%s.metacmd.xml'%(ids[0], revision)
          else:
            filename = 'export.metacmd.xml'
          content_type = 'text/xml; charset=utf-8'
          export = self.getXmlHeader() + self.toXmlString(value, 1)
          RESPONSE.setHeader('Content-Type', content_type)
          RESPONSE.setHeader('Content-Disposition', 'attachment;filename="%s"'%filename)
          return export
        
        # Import.
        # -------
        elif btn == 'BTN_IMPORT':
          f = REQUEST['file']
          if f:
            filename = f.filename
            self.importXml(xml=f)
          else:
            filename = REQUEST['init']
            self.importConf(filename, createIfNotExists=1)
          message = self.getZMILangStr('MSG_IMPORTED')%('<i>%s</i>'%f.filename)
        
        # Insert.
        # -------
        elif btn == 'BTN_INSERT':
          newId = REQUEST.get('_id').strip()
          newAcquired = 0
          newRevision = REQUEST.get('_revision', '0.0.0').strip()
          newName = REQUEST.get('_name').strip()
          newTitle = REQUEST.get('_title').strip()
          newMethod = REQUEST.get('_type', 'DTML Method')
          newData = None
          newExecution = REQUEST.get('_execution', 0)
          newIconClazz = REQUEST.get('_icon_clazz', '')
          id = self.setMetacmd(None, newId, newAcquired, newRevision, newName, newTitle, newMethod, newData, newExecution, newIconClazz=newIconClazz)
          message = self.getZMILangStr('MSG_INSERTED')%id
        
        # Sync with repository.
        self.getRepositoryManager().exec_auto_commit(self, id)
        
        # Return with message.
        message = standard.url_quote(message)
        return RESPONSE.redirect('manage_main?lang=%s&manage_tabs_message=%s&id=%s'%(lang, message, id))

################################################################################
