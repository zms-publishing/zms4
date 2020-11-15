################################################################################
# ZMSWorkflowTransitionsManager.py
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
from Products.PageTemplates import ZopePageTemplate
from Products.PythonScripts import PythonScript
import copy
import sys
import time
# Product Imports.
from Products.zms import IZMSRepositoryProvider
from Products.zms import standard
from Products.zms import zopeutil


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
class ZMSWorkflowTransitionsManager(object):

  ############################################################################
  #
  #  IRepositoryProvider
  #
  ############################################################################

  """
  @see IRepositoryProvider
  """
  def provideRepositoryTransitions(self, r, ids=None):
    self.writeBlock("[provideRepositoryTransitions]: ids=%s"%str(ids))
    r['workflow']['Transitions'] = []
    for id in self.getTransitionIds():
      d = self.getTransition(id)
      d['id'] = id
      r['workflow']['Transitions'].append(d)

  """
  @see IRepositoryProvider
  """
  def updateRepositoryTransitions(self, r):
    id = r['id']
    self.writeBlock("[updateRepositoryTransitions]: id=%s"%id)
    # Clear.
    self.transitions = []
    # Set.
    for attr in r.get('Transitions', []):
      self.setTransition(attr['id'], attr['id'], attr['name'], attr.get('type'), attr.get('icon_clazz', ''), attr.get('from', []), attr.get('to', ''), attr.get('performer', ''), attr.get('data', ''))
    return id


  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ZMSWorkflowTransitionsManager.setTransition
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def setTransition(self, id, newId, newName, newType, newIconClass='', newFrom=[], newTo='', newPerformer=[], newData=''):
    message = ''
    obs = self.transitions
    # Remove exisiting entry.
    if id in obs:
      i = obs.index(id)
      del obs[i] 
      del obs[i] 
    else: 
      i = len(obs)
    if len(newTo) == 0:
      newTo = []
    elif isinstance(newTo, str):
      newTo = [newTo]
    # Values.
    newValues = {}
    newValues['name'] = newName
    newValues['icon_clazz'] = newIconClass
    newValues['from'] = newFrom
    newValues['to'] = newTo
    newValues['performer'] = newPerformer
    # Zope Object.
    [zopeutil.removeObject(self, x) for x in [id, newId]]
    zopeutil.addObject(self, newType, newId, newName, newData)
    # Update attribute.
    obs.insert(i, newValues)
    obs.insert(i, newId)
    self.transitions = copy.copy(obs)
    # Return with message.
    return message


  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ZMSWorkflowTransitionsManager.getTransitions
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def getTransitions(self):
    obs = self.transitions
    transitions = []
    for i in range(len(obs)//2):
      id = obs[i*2]
      transition = obs[i*2+1].copy()
      transition['id'] = id
      transitions.append(transition)
    return transitions


  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ZMSWorkflowTransitionsManager.getTransitionIds
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def getTransitionIds(self):
    return [x['id'] for x in self.getTransitions()] 


  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ZMSWorkflowTransitionsManager.getTransition
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def getTransition(self, id, for_export=False):
    transition = [x for x in self.getTransitions() if x['id'] == id][0]
    transition = copy.deepcopy(transition)
    ob = zopeutil.getObject(self, transition['id'])
    if ob is not None:
      transition['ob'] = ob
      transition['type'] = ob.meta_type
    if 'dtml' in transition:
      del transition['dtml']
    return transition


  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ZMSWorkflowTransitionsManager.manage_changeTransitions:
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def manage_changeTransitions(self, lang, btn='', key='', REQUEST=None, RESPONSE=None):
    """ ZMSWorkflowTransitionsManager.manage_changeTransitions """
    message = ''
    id = REQUEST.get('id', '')
    
    # Cancel.
    # -------
    if btn in [ 'BTN_CANCEL', 'BTN_BACK']:
      id = ''
    
    # Change.
    # -------
    if btn == 'BTN_SAVE':
      item = self.getTransition(id)
      newId = REQUEST.get('inpId').strip()
      newIconClazz = REQUEST.get('inpIconClazz', '')
      newName = REQUEST.get('inpName').strip()
      newType = REQUEST.get('inpType', 'DTML Method').strip()
      newFrom = REQUEST.get('inpFrom', [])
      newTo = REQUEST.get('inpTo', [])
      newPerformer = REQUEST.get('inpPerformer', [])
      newData = REQUEST.get('inpData', '').strip()
      message += self.setTransition( item.get('id', None), newId, newName, newType, newIconClazz, newFrom, newTo, newPerformer, newData)
      message += self.getZMILangStr('MSG_CHANGED')
      id = newId
    
    # Delete.
    # -------
    elif btn == 'BTN_DELETE':
      id = self.delItem(id, 'transitions')
      message = self.getZMILangStr('MSG_CHANGED')
    
    # Insert.
    # -------
    elif btn == 'BTN_INSERT':
      item = {}
      newId = REQUEST.get('newId').strip()
      newName = REQUEST.get('newName').strip()
      newIconClazz = REQUEST.get('inpIconClazz', '')
      newType = REQUEST.get('newType', 'DTML Method').strip()
      message += self.setTransition( item.get('id', None), newId, newName, newType, newIconClazz)
      message += self.getZMILangStr('MSG_INSERTED')%id
      id = newId
    
    # Move to.
    # --------
    elif btn == 'move_to':
      pos = REQUEST['pos']
      self.moveItem(id, pos, 'transitions')
      message = self.getZMILangStr('MSG_MOVEDOBJTOPOS')%(("<i>%s</i>"%id), (pos+1))
      id = ''
    
    # Return with message.
    message = standard.url_quote(message)
    return RESPONSE.redirect('manage_main?id=%s&lang=%s&key=%s&manage_tabs_message=%s'%(id, lang, key, message))

################################################################################
