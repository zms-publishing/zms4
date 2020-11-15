################################################################################
# ZMSWorkflowProviderAcquired.py
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
from Products.zms import IZMSConfigurationProvider
from Products.zms import IZMSWorkflowProvider, ZMSWorkflowProvider
from Products.zms import ZMSItem


@implementer(
        IZMSConfigurationProvider.IZMSConfigurationProvider,
        IZMSWorkflowProvider.IZMSWorkflowProvider)
class ZMSWorkflowProviderAcquired(
        ZMSItem.ZMSItem):

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Properties
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    meta_type = 'ZMSWorkflowProviderAcquired'
    icon = "fas fa-random"
    icon_clazz = icon

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Options
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    manage_options_default_action = '../manage_customize'
    def manage_options(self):
      return [self.operator_setitem( x, 'action', '../'+x['action']) for x in copy.deepcopy(self.aq_parent.manage_options())]

    manage_sub_options__roles__ = None
    def manage_sub_options(self):
      return (
        {'label': 'TAB_WORKFLOW','action': 'manage_main'},
        )

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    Management Interface
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    manage = PageTemplateFile('zpt/ZMSWorkflowProvider/manage_main_acquired', globals())
    manage_main = PageTemplateFile('zpt/ZMSWorkflowProvider/manage_main_acquired', globals())


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProviderAcquired.__init__: 
    
    Constructor.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __init__(self, autocommit=1, nodes=['{$}']):
      self.id = 'workflow_manager'
      self.autocommit = autocommit
      self.nodes = nodes


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProviderAcquired.getAutocommit
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getAutocommit(self):
      return getattr(self, 'autocommit', 1)


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProviderAcquired.getNodes
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getNodes(self):
      return getattr(self, 'nodes', ['{$}'])


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProviderAcquired.doAutocommit:
    
    Auto-Commit ZMS-tree.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def doAutocommit(self, lang, REQUEST):
      ZMSWorkflowProvider.doAutocommit(self, REQUEST)

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    @see IZMSWorkflowProvider.getActivities()
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getActivities(self):
      return self.getPortalMaster().getWorkflowManager().getActivities()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    @see IZMSWorkflowProvider.getActitiesIds()
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getActivityIds(self):
      return self.getPortalMaster().getWorkflowManager().getActivityIds()
  
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    @see IZMSWorkflowProvider.getActivity()
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getActivity(self, id):
      return self.getPortalMaster().getWorkflowManager().getActivity(id)

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    @see IZMSWorkflowProvider.getActivityDetails()
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getActivityDetails(self, id):
      return self.getPortalMaster().getWorkflowManager().getActivityDetails(id)

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    @see IZMSWorkflowProvider.getTransitions()
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getTransitions(self):
      return self.getPortalMaster().getWorkflowManager().getTransitions()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    @see IZMSWorkflowProvider.getTransitionIds()
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getTransitionIds(self):
      return self.getPortalMaster().getWorkflowManager().getTransitionIds()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    @see IZMSWorkflowProvider.getTransition()
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def getTransition(self, id, for_export=False):
      return self.getPortalMaster().getWorkflowManager().getTransition(id, for_export)

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    ZMSWorkflowProviderAcquired.manage_changeWorkflow:
    
    Chang workflow.
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def manage_changeWorkflow(self, lang, key='', btn='', REQUEST=None, RESPONSE=None):
      """ ZMSWorkflowProvider.manage_changeWorkflow """
      message = ''
      
      # Active.
      # -------
      if key == 'custom' and btn == 'BTN_SAVE':
        # Autocommit & Nodes.
        old_autocommit = getattr(self, 'autocommit', 1)
        new_autocommit = REQUEST.get('workflow', 0) == 0
        self.autocommit = new_autocommit
        self.nodes = standard.string_list(REQUEST.get('nodes', ''))
        if old_autocommit == 0 and new_autocommit == 1:
          self.doAutocommit(lang, REQUEST)
        message = self.getZMILangStr('MSG_CHANGED')
      
      # Return with message.
      message = standard.url_quote(message)
      return RESPONSE.redirect('manage_main?lang=%s&manage_tabs_message=%s#_%s'%(lang, message, key))

################################################################################