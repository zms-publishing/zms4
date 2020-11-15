################################################################################
# IZMSConfigurationProvider.py
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

class IZMSConfigurationProvider(Interface):

  def manage_sub_options(self):
    """
    Returns sub-options 
    @rtype: C{string}
    """

  def getArtefacts(self):
    """
    Returns list of artefacts.
    @rtype: C{list}
    """
  
  def setArtefacts(self, artefacts):
    """
    Applies list of artefacts.
    @param artefacts: the artefacts
    @type artefacts: C{list}
    """
