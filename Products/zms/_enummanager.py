################################################################################
# _enummanager.py
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
from App.Common import package_home
# Product Imports.
from Products.zms import _xmllib


################################################################################
################################################################################
###
###   class EnumManager
###
################################################################################
################################################################################
class EnumManager(object):

  # ----------------------------------------------------------------------------
  #  EnumManager.__init__:
  #
  #  Constructor
  # ----------------------------------------------------------------------------
  def __init__(self):
    pass
    
  # ----------------------------------------------------------------------------
  #  EnumManager.getValues:
  #
  #  Returns values for enumeration specified by Id.
  # ----------------------------------------------------------------------------
  getValues__roles__ = None
  def getValues(self, id, path=None):
    if path is None:
      path = package_home(globals())+'/import/'
    filename = path + 'enum.%s.xml'%id
    xml = open(filename)
    builder = _xmllib.XmlAttrBuilder()
    v = builder.parse(xml)
    xml.close()
    if isinstance(v, dict):
      l = sorted([(v[x], x) for x in v])
      v = []
      for i in l:
        v.append([i[1], i[0]])
    return v

################################################################################
