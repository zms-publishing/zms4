# -*- coding: utf-8 -*- 
################################################################################
# ZMSWorkflowProvider.py
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
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
import copy
from zope.interface import implementer
# Product Imports.
from Products.zms import standard
from Products.zms import IZMSConfigurationProvider, IZMSRepositoryProvider
from Products.zms import IZMSWorkflowProvider, ZMSWorkflowActivitiesManager, ZMSWorkflowTransitionsManager
from Products.zms import ZMSItem
from Products.zms import zopeutil
from Products.zms import _accessmanager
from Products.zms import _fileutil


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ZMSWorkflowProvider.doAutocommit:
Commit pending changes of all objects.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def doAutocommit(self, REQUEST): 
  
  ##### Auto-Commit ####
  if len( self.getObjStates()) > 0:
    
    if self.inObjStates(['STATE_DELETED'], REQUEST):
       parent = self.getParentNode()
       parent.moveObjsToTrashcan([self.id], REQUEST)
       return
    
    if self.version_work_id is not None:
      if self.version_live_id is not None and \
         self.version_live_id in self.objectIds(list(self.dGlobalAttrs)):
        ids = [ self.version_live_id]
        self.manage_delObjects( ids=ids)
      self.version_live_id = self.version_work_id
      self.version_work_id = None
    self.initializeWorkVersion()
  
  ##### Process child-objects ####
  for ob in self.getChildNodes():
    doAutocommit( ob, REQUEST)


"""
################################################################################
#
#   XML IM/EXPORT
#
################################################################################
"""

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
ZMSWorkflowProvider.exportXml
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def exportXml(self, REQUEST, RESPONSE):
  value = {}
  value['activities'] = []
  for x in self.getActivityIds():
    value['activities'].extend([x, self.getActivity(x, for_export=True)])
  value['transitions'] = []
  for x in self.getTransitionIds():
    value['transitions'].extend([x, self.getTransition(x, for_export=True)])
  export = self.getXmlHeader() + self.toXmlString(value, 1)
  content_type = 'text/xml; charset=utf-8'
  filename = 'workflow.xml'
  RESPONSE.setHeader('Content-Type', content_type)
  RESPONSE.setHeader('Content-Disposition', 'attachment;filename="%s"'%filename)
  return export


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
@implementer(
        IZMSConfigurationProvider.IZMSConfigurationProvider,
        IZMSWorkflowProvider.IZMSWorkflowProvider,
        IZMSRepositoryProvider.IZMSRepositoryProvider,)
class ZMSWorkflowProvider(
        ZMSItem.ZMSItem,
        ZMSWorkflowActivitiesManager.ZMSWorkflowActivitiesManager,
        ZMSWorkflowTransitionsManager.ZMSWorkflowTransitionsManager):

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Properties
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    meta_type = 'ZMSWorkflowProvider'
    zmi_icon = "fas fa-random"
    icon_clazz = zmi_icon

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Options
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    manage_options_default_action = '../manage_customize'
    def manage_options(self):
      return [self.operator_setitem( x, 'action', '../'+x['action']) for x in copy.deepcopy(self.aq_parent.manage_options())]

    def manage_sub_options(self):
      return (
        {'label': 'TAB_WORKFLOW','action': 'manage_main'},
        )

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Interface
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    manage = PageTemplateFile('zpt/ZMSWorkflowProvider/manage_main', globals())
    manage_main = PageTemplateFile('zpt/ZMSWorkflowProvider/manage_main', globals())

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Permissions
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    __administratorPermissions__ = (
        'manage_main',
        'manage_changeWorkflow',
        'manage_changeActivities',
        'manage_changeTransitions',
        )
    __ac_permissions__=(
        ('ZMS Administrator', __administratorPermissions__),
        )


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.__init__: 
    
    Constructor.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __init__(self, autocommit=1, nodes=['{$}'], activities=[], transitions=[]):
      self.id = 'workflow_manager'
      self.autocommit = autocommit
      self.nodes = nodes
      self.activities = []
      self.transitions = []
      l = activities
      for li in range(len(l)//2):
        id = l[li*2]
        i = l[li*2+1]
        self.setActivity(id=None, newId=id, newName=i['name'], newIcon=i.get('icon'))
      l = transitions
      for li in range(len(l)//2):
        id = l[li*2]
        i = l[li*2+1]
        newData = i.get('ob',i.get('dtml',''))
        newType = i.get('type',['','DTML Method'][int(len(newData)>0)])
        self.setTransition(id=None, newId=id, newName=i['name'], newType=newType, newIconClass=i.get('icon_clazz', ''), newFrom=i.get('from', []), newTo=i.get('to', []), newPerformer=i.get('performer', []), newData=newData)


    ############################################################################
    #
    #  IRepositoryProvider
    #
    ############################################################################

    """
    @see IRepositoryProvider
    """
    def provideRepository(self, r, ids=None):
      self.writeBlock("[provideRepository]: ids=%s"%str(ids))
      r = {}
      id = 'workflow'
      d = {'id':id,'revision':self.getRevision(),'__filename__':['__init__.py']}
      r[id] = d
      self.provideRepositoryActivities(r, ids)
      self.provideRepositoryTransitions(r, ids)
      return r

    """
    @see IRepositoryProvider
    """
    def updateRepository(self, r):
      id = r['id']
      self.setRevision(r['revision'])
      self.updateRepositoryActivities(r)
      self.updateRepositoryTransitions(r)
      return id


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.importXml
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def importXml(self, xml, createIfNotExists=1):
      ids = [self.activities[x*2] for x in range(len(self.activities)//2)]
      for id in ids:
        self.delItem(id, 'activities')
      ids = [self.transitions[x*2] for x in range(len(self.transitions)//2)]
      for id in ids:
        self.delItem(id, 'transitions')
      v = standard.parseXmlString(xml)
      l = v.get('activities', [])
      for li in range(len(l)//2):
        id = l[li*2]
        i = l[li*2+1]
        self.setActivity(id=None, newId=id, newName=i['name'], newIconClazz=i.get('icon_clazz', ''), newIcon=i.get('icon'))
      l = v.get('transitions', [])
      for li in range(len(l)//2):
        id = l[li*2]
        i = l[li*2+1]
        newData = i.get('ob',i.get('dtml',''))
        newType = i.get('type', ['', 'DTML Method'][int(len(newData)>0)])
        self.setTransition(id=None, newId=id, newName=i['name'], newType=newType, newIconClass=i.get('icon_clazz', ''), newFrom=i.get('from', []), newTo=i.get('to', []), newPerformer=i.get('performer', []), newData=newData)
      # Create non existant roles.
      roles = []
      for transition in self.getTransitions():
        roles = standard.concat_list(roles, transition.get('performer', []))
      for newRole in roles:
        if newRole not in self.userdefined_roles():
          _accessmanager.addRole(self, newRole)


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.revision
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getRevision(self):
      return getattr(self, 'revision', '0.0.0')

    def setRevision(self, revision):
      self.revision = revision


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.getAutocommit
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getAutocommit(self):
      return self.autocommit


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.getNodes
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getNodes(self):
      return self.nodes


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.delItem
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def delItem(self, id, key):
      obs = getattr(self, key, [])
      # Update attribute.
      if id in obs:
        i = obs.index(id)
        ob = obs[i+1]
        for obj_id in [id, '%s.icon'%id]:
          if obj_id in self.objectIds():
            self.manage_delObjects([obj_id])
        del obs[i] 
        del obs[i] 
      # Update attribute.
      setattr(self, key, copy.copy(obs))
      # Return with empty id.
      return ''


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.moveItem
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def moveItem(self, id, pos, key):
      obs = getattr(self, key, [])
      # Move.
      i = obs.index(id)
      id = obs[i] 
      values = obs[i+1]
      del obs[i] 
      del obs[i] 
      obs.insert(pos*2, values)
      obs.insert(pos*2, id)
      # Update attribute.
      setattr(self, key, copy.copy(obs))


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.doAutocommit:
    
    Auto-Commit ZMS-tree.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def doAutocommit(self, lang, REQUEST):
      doAutocommit(self, REQUEST)


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProvider.manage_changeWorkflow:
    
    Change workflow.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def manage_changeWorkflow(self, lang, btn='', key='properties', REQUEST=None, RESPONSE=None):
      """ ZMSWorkflowProvider.manage_changeWorkflow """
      message = ''

      # Version Control.
      # -----------
      if key == 'history':
        old_active = self.getConfProperty('ZMS.Version.active',0)
        new_active = REQUEST.get('active',0)
        old_nodes = self.getConfProperty('ZMS.Version.nodes',['{$}'])
        new_nodes = standard.string_list(REQUEST.get('nodes',''))
        self.setConfProperty('ZMS.Version.active',new_active)
        self.setConfProperty('ZMS.Version.nodes',new_nodes)
        nodes = []
        if old_active == 1 and new_active == 0:
          nodes = old_nodes
        if old_active == 1 and new_active == 1:
          nodes = standard.difference_list( old_nodes, self.getConfProperty('ZMS.Version.nodes',['{$}']))
        for node in nodes:
          ob = self.getLinkObj(node)
          if ob is not None:
            try:
              message += '[%s: %i]'%(node,ob.packHistory())
            except:
              message += '[%s: %s]'%(node,'No history to pack')
        message = self.getZMILangStr('MSG_CHANGED')+message
      
      # Properties.
      # -----------
      elif key == 'properties':
        # Save.
        # ------
        if btn == 'BTN_SAVE':
          # Autocommit & Nodes.
          old_autocommit = self.autocommit
          new_autocommit = REQUEST.get('workflow', 0) == 0
          self.revision = REQUEST.get('revision', '0.0.0')
          self.autocommit = new_autocommit
          self.nodes = standard.string_list(REQUEST.get('nodes', ''))
          if old_autocommit == 0 and new_autocommit == 1:
            self.doAutocommit(lang, REQUEST)
          message = self.getZMILangStr('MSG_CHANGED')
      
        # Clear.
        # ------
        elif btn == 'BTN_CLEAR':
          self.doAutocommit(lang, REQUEST)
          self.autocommit = 1
          self.activities = []
          self.transitions = []
          message = self.getZMILangStr('MSG_CHANGED')
     
        # Export.
        # -------
        elif btn == 'BTN_EXPORT':
          return exportXml(self, REQUEST, RESPONSE)
      
        # Import.
        # -------
        elif btn == 'BTN_IMPORT':
          f = REQUEST['file']
          if f:
            filename = f.filename
            xml = f
          else:
            filename = REQUEST.get('init')
            xml = open(_fileutil.getOSPath(filename), 'rb')
          self.importXml(xml)
          message = self.getZMILangStr('MSG_IMPORTED')%('<i>%s</i>'%filename)
      
      # Return with message.
      message = standard.url_quote(message)
      return RESPONSE.redirect('manage_main?lang=%s&key=%s&manage_tabs_message=%s#_properties'%(lang, key, message))

################################################################################
