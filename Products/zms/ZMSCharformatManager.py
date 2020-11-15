################################################################################
# ZMSCharformatManager.py
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
import ZPublisher.HTTPRequest
import copy
# Product Imports.
from Products.zms import standard
from Products.zms import _blobfields


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
class ZMSCharformatManager(object):

    """
    ############################################################################
    #
    #  XML IM/EXPORT
    #
    ############################################################################
    """

    # --------------------------------------------------------------------------
    #  ZMSCharformatManager.importCharformatXml
    # --------------------------------------------------------------------------

    def _importCharformatXml(self, item, createIfNotExists=1):
      if createIfNotExists == 1:
        newId = self.id_quote(item.get('display', ''))
        if len(newId) == 0:
          newId = self.getNewId('fmt')
        newId = item.get('id', newId)
        newIconClazz = item.get('icon_clazz', '')
        newDisplay = item.get('display', '')
        newTag = item.get('tag', '')
        newAttrs = item.get('attrs', '')
        newJS = item.get('js', '')
        self.setCharformat( None, newId, newIconClazz, newDisplay, newTag, newAttrs, newJS)
        # Make persistent.
        self.charformats = copy.deepcopy(self.charformats)

    def importCharformatXml(self, xml, createIfNotExists=1):
      v = self.parseXmlString(xml)
      if isinstance(v, list):
        for item in v:
          self._importCharformatXml(item, createIfNotExists)
      else:
        self._importCharformatXml(v, createIfNotExists)


    # --------------------------------------------------------------------------
    #  ZMSCharformatManager.getCharFormats:
    # --------------------------------------------------------------------------
    def getCharFormats(self):
      return self.charformats


    # ------------------------------------------------------------------------------
    #  ZMSCharformatManager.moveCharformat:
    # ------------------------------------------------------------------------------
    def moveCharformat(self, id, pos):
      obs = self.charformats
      charformats = [x for x in obs if x['id'] == id]
      if len(charformats) == 1:
        ob = charformats[0]
        self.charformats.remove(ob)
        self.charformats.insert(pos, ob)
        # Make persistent.
        self.charformats = copy.deepcopy(self.charformats)


    # ------------------------------------------------------------------------------
    #  ZMSCharformatManager.delCharformat:
    # ------------------------------------------------------------------------------
    def delCharformat(self, id):
      obs = self.charformats
      charformats = [x for x in obs if x['id'] == id]
      if len(charformats) > 0:
        ob = charformats[0]
        self.charformats.remove(ob)
        # Make persistent.
        self.charformats = copy.deepcopy(self.charformats)
      return ''


    # ------------------------------------------------------------------------------
    #  ZMSCharformatManager.setCharformat:
    # ------------------------------------------------------------------------------
    def setCharformat(self, oldId, newId, newIconClazz, newDisplay, newTag='', newAttrs='', newJS=''):
      obs = self.charformats
      if oldId is None:
        oldId = newId
      oldCharformats = [x for x in obs if x['id'] == oldId]
      if len(oldCharformats) > 0:
        i = obs.index( oldCharformats[0])
      else:
        i = len(obs)
        obs.append({})
      ob = obs[i]
      ob['id'] = newId
      ob['icon_clazz'] = newIconClazz
      ob['display'] = newDisplay
      ob['tag'] = newTag
      ob['attrs'] = newAttrs
      ob['js'] = newJS
      # Make persistent.
      self.charformats = copy.deepcopy(self.charformats)
      return newId


    ############################################################################
    #  ZMSCharformatManager.manage_changeCharformat:
    #
    #  Change char-formats.
    ############################################################################
    def manage_changeCharformat(self, lang, btn, REQUEST, RESPONSE):
      """ ZMSCharformatManager.manage_changeCharformat """
      message = ''
      id = REQUEST.get('id', '')
      
      # Change.
      # -------
      if btn == 'BTN_SAVE':
        newId = REQUEST['new_id'].strip()
        newIconClazz = REQUEST.get('new_icon_clazz', '')
        newDisplay = REQUEST['new_display'].strip()
        newTag = REQUEST['new_tag'].strip()
        newAttrs = REQUEST['new_attrs'].strip()
        newJS = REQUEST['new_js'].strip()
        id = self.setCharformat(id, newId, newIconClazz, newDisplay, newTag, newAttrs, newJS)
        message = self.getZMILangStr('MSG_CHANGED')
      
      # Delete.
      # -------
      elif btn == 'BTN_DELETE':
        if id:
          ids = [id]
        else:
          ids = REQUEST.get('ids', [])
        for id in ids:
          self.delCharformat(id) 
        id = ''
        message = self.getZMILangStr('MSG_DELETED')%len(ids)
      
      # Insert.
      # -------
      elif btn == 'BTN_INSERT':
        fmts = self.getCharFormats()
        newId = REQUEST['_id'].strip()
        newIconClazz = REQUEST.get('_icon_clazz', '')
        newDisplay = REQUEST['_display'].strip()
        id = self.setCharformat(None, newId, newIconClazz, newDisplay)
        message = self.getZMILangStr('MSG_INSERTED')%id
      
      # Export.
      # -------
      elif btn == 'BTN_EXPORT':
        ids = REQUEST.get('ids', [])
        value = [x.copy() for x in self.getCharFormats() if x['id'] in ids or len(ids) == 0]
        if len(value)==1:
          value = value[0]
        content_type = 'text/xml; charset=utf-8'
        filename = 'export.charfmt.xml'
        export = self.getXmlHeader() + self.toXmlString(value, 1)
        RESPONSE.setHeader('Content-Type', content_type)
        RESPONSE.setHeader('Content-Disposition', 'attachment;filename="%s"'%filename)
        return export
      
      # Import.
      # -------
      elif btn == 'BTN_IMPORT':
        f = REQUEST['file']
        if f:
          filename = f.filename
          self.importCharformatXml(xml=f)
        else:
          filename = REQUEST['init']
          self.importConf(filename, createIfNotExists=1)
        message = self.getZMILangStr('MSG_IMPORTED')%('<i>%s</i>'%filename)
      
      # Move to.
      # --------
      elif btn == 'move_to':
        pos = REQUEST['pos']
        id = int(id)
        self.moveCharformat( self, id, pos)
        message = self.getZMILangStr('MSG_MOVEDOBJTOPOS')%(("<i>%s</i>"%str(id)), (pos+1))
        id = ''
      
      # Return with message.
      message = standard.url_quote(message)
      return RESPONSE.redirect('manage_charformats?lang=%s&manage_tabs_message=%s&id=%s'%(lang, message, id))

################################################################################
