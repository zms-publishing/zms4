################################################################################
# IZMSFormatProvider.py
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

class IZMSFormatProvider(Interface):

  def getTextFormatDefault(self):
    """
    Returns id of default text-format 
    @rtype: C{string}
    """
  
  def getTextFormat(self, id, REQUEST):
    """
    Returns text-format specified by given id 
    @param REQUEST: the triggering request
    @type REQUEST: ZPublisher.HTTPRequest
    """

  def getTextFormats(self, REQUEST):
    """
    Returns list of all text-formats 
    @param REQUEST: the triggering request
    @type REQUEST: ZPublisher.HTTPRequest
    @rtype: C{list}
    """

  def getCharFormats(self):
    """
    Returns list of all character-formats 
    @rtype: C{list}
    """
