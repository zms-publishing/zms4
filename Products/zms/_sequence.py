################################################################################
# _sequence.py
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
# Product Imports.
from Products.zms import standard
from Products.zms import ZMSItem


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
class Sequence(ZMSItem.ZMSItem):

    # Properties.
    # -----------
    meta_type = 'Sequence'
    zmi_icon = "fas fa-sort-numeric-down"
    icon_clazz = zmi_icon

    # Management Options.
    # -------------------
    manage_options = (
      {'label': 'TAB_CONFIGURATION','action': '../manage_customize'},
    ) 

    # Management Permissions.
    # -----------------------
    __administratorPermissions__ = (
      'manage_changeProperties', 'manage_main',
    )
    __ac_permissions__=(
      ('ZMS Administrator', __administratorPermissions__),
    )

    # Management Interface.
    # ---------------------
    manage_main = PageTemplateFile('zpt/Sequence/manage_main', globals())


    """
    ############################################################################
    ###
    ###   Constructor
    ###
    ############################################################################
    """

    ############################################################################
    #  Sequence.__init__: 
    #
    #  Initialise a new instance.
    ############################################################################
    def __init__(self, startvalue=0):
      self.id = 'acl_sequence'
      self.value = startvalue


    """
    ############################################################################
    ###
    ###   Functions
    ###
    ############################################################################
    """

    # --------------------------------------------------------------------------
    #  Sequence.nextVal
    # --------------------------------------------------------------------------
    def nextVal(self):
      self.value = self.value + 1
      return self.currVal()

    # --------------------------------------------------------------------------
    #  Sequence.currVal
    # --------------------------------------------------------------------------
    def currVal(self):
      return self.value


    """
    ############################################################################
    ###
    ###   Properties
    ###
    ############################################################################
    """

    ############################################################################
    #  Sequence.manage_changeProperties: 
    #
    #  Change Sequence properties.
    ############################################################################
    def manage_changeProperties(self, submit, currentvalue, REQUEST, RESPONSE): 
      """ Sequence.manage_changeProperties """
      
      message = ''

      # Set current value.
      if submit == 'Change':
        if currentvalue >= self.value:
          self.value = currentvalue
        
      # Fetch next value.
      if submit == 'Next':
        self.nextVal()

      # Return.
      if RESPONSE is not None:
        RESPONSE.redirect('%s?manage_tabs_message=%s'%(REQUEST[ 'HTTP_REFERER'], standard.url_quote(message)))

################################################################################
