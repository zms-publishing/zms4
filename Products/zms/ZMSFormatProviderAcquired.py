################################################################################
# ZMSFormatProviderAcquired.py
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
import copy
from zope.interface import implementer
# Product Imports.
from Products.zms import IZMSFormatProvider, ZMSFormatProvider


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
@implementer(
        IZMSFormatProvider.IZMSFormatProvider)
class ZMSFormatProviderAcquired(
        ZMSFormatProvider.ZMSFormatProvider):

    # Properties.
    # -----------
    meta_type = 'ZMSFormatProviderAcquired'

    """
    ############################################################################
    #
    #   Constructor
    #
    ############################################################################
    """

    ############################################################################
    #  ZMSFormatProvider.__init__: 
    #
    #  Initialise a new instance.
    ############################################################################
    def __init__(self, textformats=[], charformats=[]):
      self.id = 'format_manager'

    def getTextFormatDefault(self):
      portal_master = self.getPortalMaster()
      if portal_master is not None:
        return portal_master.getTextFormatDefault()
      return None
  
    def getTextFormat(self, id, REQUEST):
      portal_master = self.getPortalMaster()
      if portal_master is not None:
        return portal_master.getTextFormat(id, REQUEST)
      return None

    def getTextFormats(self, REQUEST):
      rtn = []
      portal_master = self.getPortalMaster()
      if portal_master is not None:
        rtn.extend(portal_master.getTextFormats(REQUEST))
      return rtn

    def getCharFormats(self):
      rtn = []
      portal_master = self.getPortalMaster()
      if portal_master is not None:
        rtn.extend(copy.deepcopy(portal_master.getCharFormats()))
        for d in rtn:
          btn = d.get('btn')
          if isinstance(btn, str) and btn.find('/') < 0:
            d['btn'] = '%s/%s'%(portal_master.getFormatManager().absolute_url(), btn)
      return rtn

################################################################################
