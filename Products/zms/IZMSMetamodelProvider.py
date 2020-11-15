################################################################################
# IZMSMetamodelProvider.py
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
from zope.interface import Interface

class IZMSMetamodelProvider(Interface):

  def getMetaobjId(self, name):
    """
    Returns id of meta-object specified by name.
    @rtype: C{string}
    """

  def getMetaobjIds(self, sort=None, excl_ids=[]):
    """ 
    Returns list of all meta-ids in model.
    @param sort if True sort by display_type, if False sort by name, else no sort.
    @rtype: C{list}
    """

  def getMetaobj(self, id):
    """
    Returns meta-object specified by meta-id.
    @rtype: C{dict}
    """

  def getMetaobjAttrIds(self, meta_id, types=[]):
    """
    Returns list of attribute-ids for meta-object specified by meta-id.
    @rtype: C{list}
    """

  def getMetaobjAttrs(self, meta_id, types=[]):
    """
    Get all attributes for meta-object specified by meta-id.
    @rtype: C{list}
    """

  def getMetaobjAttr(self, meta_id, key, sync=True):
    """
    Get attribute for meta-object specified by attribute-id.
    @rtype: C{dict}
    """

  def getMetaobjAttrIdentifierId(self, meta_id):
    """
    Get attribute-id of identifier for datatable specified by meta-id.
    @rtype: C{dict}
    """

  def notifyMetaobjAttrAboutValue(self, meta_id, key, value):
    """
    Notify attribute for meta-object specified by attribute-id about value.
    @rtype: C{dict}
    """
