################################################################################
# _zcatalogmanager.py
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
import re
import sys
import zope.interface
# Product Imports.
from Products.zms import standard


################################################################################
################################################################################
###
###   class ZCatalogManager
###
################################################################################
################################################################################
class ZCatalogManager(object):

    # --------------------------------------------------------------------------
    #  ZCatalogManager.getCatalogQueryString:
    #    
    #  @deprecated
    # --------------------------------------------------------------------------
    def getCatalogQueryString(self, raw, option='AND', only_words=False):
      qs = []
      i = 0
      for si in raw.split('"'):
        si = si.strip()
        if si:
          if i % 2 == 0:
            for raw_item in si.split(' '):
              raw_item = raw_item.strip()
              if len(raw_item) > 1 and not raw_item.upper() in ['AND', 'OR']:
                raw_item = raw_item.replace('-', '* AND *')
                if not only_words and not raw_item.endswith('*'):
                  raw_item += '*'
                if raw_item not in qs:
                  qs.append( raw_item)
          else:
            raw_item = '"%s"'%si
            if raw_item not in qs:
              qs.append( raw_item)
        i += 1
      return (' %s '%option).join([x for x in qs if x.strip()])


    # --------------------------------------------------------------------------
    #  ZCatalogManager.getCatalogPathObject:
    #
    #  Returns object from catalog-path.
    #  @deprecated
    # --------------------------------------------------------------------------
    def getCatalogPathObject(self, path):
      ob = self.getHome()
      l = path.split( '/')
      if ob.id not in l:
        docElmnt = self.getDocumentElement()
        if docElmnt.id not in l:
          ob = docElmnt
      else:
        l = l[ l.index(ob.id)+1:]
      for id in l:
         if len( id) > 0 and ob is not None:
          ob = getattr(ob, id, None)
      return ob


    # --------------------------------------------------------------------------
    #  ZCatalogManager.submitCatalogQuery:
    #
    #  Submits query to catalog.
    #  @deprecated
    # --------------------------------------------------------------------------
    def submitCatalogQuery(self, search_query, search_order_by, search_meta_types=[], search_clients=False, REQUEST=None):
      return self.getCatalogAdapter().search(search_query, search_order_by)

################################################################################
