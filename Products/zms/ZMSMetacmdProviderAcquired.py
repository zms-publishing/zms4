################################################################################
# ZMSMetacmdProviderAcquired.py
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
from zope.interface import implementer
# Product Imports.
from Products.zms import IZMSMetacmdProvider, ZMSMetacmdProvider


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
@implementer(
        IZMSMetacmdProvider.IZMSMetacmdProvider)
class ZMSMetacmdProviderAcquired(
        ZMSMetacmdProvider.ZMSMetacmdProvider):

    # Properties.
    # -----------
    meta_type = 'ZMSMetacmdProviderAcquired'

    ############################################################################
    #  ZMSMetacmdProviderAcquired.__init__: 
    #
    #  Constructor.
    ############################################################################
    def __init__(self, commands=[]):
      self.id = 'metacmd_manager'

    def getMetaCmdDescription(self, id):
      """ getMetaCmdDescription """
      portal_master = self.getPortalMaster()
      if portal_master is not None:
        return self.getPortalMaster().getMetaCmdDescription(id)
      return ''

    def getMetaCmdIds(self, sort=True):
      rtn = []
      portal_master = self.getPortalMaster()
      if portal_master is not None:
        rtn.extend(portal_master.getMetaCmdIds(sort))
      return rtn

    def getMetaCmds(self, context=None, stereotype='', sort=True):
      rtn = []
      portal_master = self.getPortalMaster()
      if portal_master is not None:
        rtn.extend(portal_master.getMetaCmds(context, stereotype, sort))
        for d in rtn:
            d['acquired'] = 1
      return rtn

################################################################################