################################################################################
# ZMSWorkflowActivitiesManager.py
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
import ZPublisher.HTTPRequest
import copy
# Product Imports.
from Products.zms import IZMSRepositoryProvider
from Products.zms import standard
from Products.zms import _blobfields


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
class ZMSWorkflowActivitiesManager(object):

  ############################################################################
  #
  #  IRepositoryProvider
  #
  ############################################################################

  """
  @see IRepositoryProvider
  """
  def provideRepositoryActivities(self, r, ids=None):
    self.writeBlock("[provideRepositoryActivities]: ids=%s"%str(ids))
    r['workflow']['Activities'] = []
    for id in self.getActivityIds():
      d = self.getActivity(id)
      d['id'] = id
      r['workflow']['Activities'].append(d)

  """
  @see IRepositoryProvider
  """
  def updateRepositoryActivities(self, r):
    id = r['id']
    self.writeBlock("[updateRepositoryActivities]: id=%s"%id)
    # Clear.
    self.activities = []
    # Set.
    for attr in r.get('Activities', []):
      self.setActivity(attr['id'], attr['id'], attr['name'], attr.get('icon_clazz'), attr.get('icon'))
    return id


  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ZMSWorkflowActivitiesManager.setActivity
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def setActivity(self, id, newId, newName, newIconClazz=None, newIcon=None):
    obs = self.activities
    # Remove exisiting entry.
    if id in obs:
      i = obs.index(id)
      del obs[i] 
      del obs[i] 
    else: 
      i = len(obs)
    # Values.
    newValues = {}
    newValues['name'] = newName
    newValues['icon_clazz'] = newIconClazz
    newValues['icon'] = newIcon
    for obj_id in ['%s.icon'%str(id), '%s.icon'%str(newId)]:
      if obj_id in self.objectIds():
        self.manage_delObjects([obj_id])
    if isinstance(newIcon, _blobfields.MyBlob):
      self.manage_addFile(id='%s.icon'%newId, title=newIcon.getFilename(), file=newIcon.getData())
    # Update attribute.
    obs.insert(i, newValues)
    obs.insert(i, newId)
    self.activities = copy.copy(obs)
    # Return with new id.
    return newId

  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ZMSWorkflowActivitiesManager.getActivities
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def getActivities(self): 
    obs = self.activities
    activities = []
    for i in range(len(obs)//2):
      id = obs[i*2]
      activity = obs[i*2+1].copy()
      activity['id'] = id
      activities.append(activity)
    return activities


  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ZMSWorkflowActivitiesManager.getActivityIds
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def getActivityIds(self):
    obs = self.getActivities()
    return [x['id'] for x in obs] 


  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ZMSWorkflowActivitiesManager.getActivity
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def getActivity(self, id, for_export=False):
    activity = None
    activities = [x for x in self.getActivities() if x['id']==id]
    if activities:
      activity = activities[0]
      if not for_export:
        d = {}
        for key in activity:
          if key == 'icon' and activity.get('icon'):
            d[key] = self.absolute_url()+'/'+id+'.icon'
          else:
            d[key] = activity[key]
        activity = d
    return activity


  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ZMSWorkflowActivitiesManager.getActivityDetails
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def getActivityDetails(self, id):
    ids = self.getActivityIds()
    froms = []
    tos = []
    for transition in self.getTransitions():
      if transition['to'] is not None and len(transition['to']) > 0 and id in transition['to']:
        for ac_id in transition['from']:
          if ac_id in ids:
            idx = ids.index(ac_id)
            if idx not in froms:
              froms.append(idx)
      if transition['from'] is not None and len(transition['from']) > 0 and id in transition['from']:
        for ac_id in transition['to']:
          if ac_id in ids:
            idx = ids.index(ac_id)
            if idx not in tos:
              tos.append(idx)
    froms.sort()
    tos.sort()
    idxs = standard.concat_list(froms, tos)
    idx = ids.index(id)
    return {'froms':froms, 'tos': tos, 'idxs': idxs, 'idx': idx}


  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  ZMSWorkflowActivitiesManager.manage_changeActivities
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def manage_changeActivities(self, lang, btn='', REQUEST=None, RESPONSE=None):
    """ ZMSWorkflowActivitiesManager.manage_changeActivities """
    message = ''
    id = REQUEST.get('id', '')
    
    # Cancel.
    # -------
    if btn in [ 'BTN_CANCEL', 'BTN_BACK']:
      id = ''
    
    # Change.
    # -------
    if btn == 'BTN_SAVE':
      item = self.getActivity(id, for_export=True)
      newId = REQUEST.get('inpId').strip()
      newName = REQUEST.get('inpName').strip()
      newIconClazz = REQUEST.get('inpIconClazz', '').strip()
      newIcon = None
      if len(newIconClazz) == 0:
        newIcon = REQUEST.get('inpIcon', '')
        if isinstance(newIcon, ZPublisher.HTTPRequest.FileUpload):
          if len(getattr(newIcon, 'filename', ''))==0:
            newIcon = item.get('icon', None)
          else:
            newIcon = _blobfields.createBlobField(self, _blobfields.MyImage, newIcon)
      id = self.setActivity( item.get('id', None), newId, newName, newIconClazz, newIcon)
      message = self.getZMILangStr('MSG_CHANGED')
    
    # Delete.
    # -------
    elif btn == 'BTN_DELETE':
      id = self.delItem(id, 'activities')
      message = self.getZMILangStr('MSG_CHANGED')
    
    # Insert.
    # -------
    elif btn == 'BTN_INSERT':
      item = {}
      newId = REQUEST.get('newId').strip()
      newName = REQUEST.get('newName').strip()
      newIconClazz = REQUEST.get('newIconClazz', '').strip()
      newIcon = None
      if len(newIconClazz) == 0:
        newIcon = REQUEST.get('newIcon', '')
        if isinstance(newIcon, ZPublisher.HTTPRequest.FileUpload):
          if len(getattr(newIcon, 'filename', ''))==0:
            newIcon = item.get('icon', None)
          else:
            newIcon = _blobfields.createBlobField(self, _blobfields.MyImage, newIcon)
      id = self.setActivity( item.get('id', None), newId, newName, newIconClazz, newIcon)
      message = self.getZMILangStr('MSG_INSERTED')%id
    
    # Move to.
    # --------
    elif btn == 'move_to':
      pos = REQUEST['pos']
      self.moveItem(id, pos, 'activities')
      message = self.getZMILangStr('MSG_MOVEDOBJTOPOS')%(("<i>%s</i>"%id), (pos+1))
      id = ''
    
    # Return with message.
    message = standard.url_quote(message)
    return RESPONSE.redirect('manage_main?lang=%s&manage_tabs_message=%s'%(lang, message))

################################################################################
