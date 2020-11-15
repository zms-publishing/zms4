################################################################################
# _zmsattributecontainer.py
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
from __future__ import absolute_import
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.Folder import Folder
import time
# Product Imports.
from Products.zms import _objattrs
from Products.zms import _pathhandler
from Products.zms import standard


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Constructor
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def manage_addZMSAttributeContainer(self):
  """ manage_addZMSAttributeContainer """
  id = str(time.time())
  while id in self.objectIds():
    id = str(time.time())
  obj = ZMSAttributeContainer(id)
  self._setObject(id, obj)
  obj = getattr(self, id)
  return obj


def containerFilter(container):
  return container.meta_type.startswith('ZMS')


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Class
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
class ZMSAttributeContainer(
      Folder,
      _objattrs.ObjAttrs,
      _pathhandler.PathHandler):

  # Properties.
  # -----------
  meta_type = 'ZMSAttributeContainer'

  # Management Options.
  # -------------------
  manage_options = (
    {'label': 'Contents', 'action': 'manage_main'},
    {'label': 'Properties', 'action': 'manage_propertiesForm'},
  ) 

  # Management Interface.
  # ---------------------
  manage_propertiesForm = PageTemplateFile('zpt/objattrs/manage_propertiesform', globals())


  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  Constructor
  """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
  def __init__(self, id): 
    self.id = id


  # ----------------------------------------------------------------------------
  #  ZMSAttributeContainer.getObjAttrs:
  #
  #  Delegates getObjAttrs to parent.
  # ----------------------------------------------------------------------------
  def getObjAttrs(self, meta_type=None):
    return self.aq_parent.getObjAttrs(meta_type)


  # ----------------------------------------------------------------------------
  #  ZMSAttributeContainer.getObjVersion:
  #
  #  Overrides method from _versionmanager.VersionManager.
  # ----------------------------------------------------------------------------
  def getObjVersion(self, REQUEST={}):
    return self


  # ----------------------------------------------------------------------------
  #  ZMSAttributeContainer.getParentNode:
  #
  #  Delegates getParentNode to parent.
  # ----------------------------------------------------------------------------
  getParentNode__roles__ = None
  def getParentNode(self):
    """
    Delegates getParentNode to parent.
    """
    return self.aq_parent.getParentNode()


  # ----------------------------------------------------------------------------
  #  ZMSAttributeContainer.getChildNodes:
  # ----------------------------------------------------------------------------
  def getChildNodes(self, REQUEST={}, meta_types=None, reid=None):
    return []


  ##############################################################################
  #  ZMSAttributeContainer.manage_changeProperties: 
  #
  #  Change properties.
  ##############################################################################
  def manage_changeProperties(self, REQUEST, RESPONSE): 
    """ ZMSAttributeContainer.manage_changeProperties """
    message = ''
    for key in self.getObjAttrs():
      obj_attr=self.getObjAttr(key)
      if obj_attr['multilang']:
        for lang in self.getLangIds():
          REQUEST.set('lang', lang)
          self.setReqProperty(key, REQUEST, 1)
      else:
        REQUEST.set('lang', self.getPrimaryLanguage())
        self.setReqProperty(key, REQUEST, 1)
    # Return with message.
    return RESPONSE.redirect('manage_propertiesForm?manage_tabs_message=%s'%(standard.url_quote(message)))

################################################################################
