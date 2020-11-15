################################################################################
# ZMSTextformatManager.py
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
from App.Common import package_home
import copy
# Product Imports.
from Products.zms import ZMSTextformat
from Products.zms import standard


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
class ZMSTextformatManager(object):

    ############################################################################
    #
    #  XML IM/EXPORT
    #
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSTextformatManager.importTextformatXml
    # --------------------------------------------------------------------------

    def _importTextformatXml(self, item, createIfNotExists=1):
      id = item['key']
      dict = item['value']
      dict['default'] = dict.get('default', 0)
      if id in self.textformats:
        i = self.textformats.index(id)
        self.textformats[i+1] = dict
      else:
        self.textformats.extend([id, dict])
      # Make persistent.
      self.textformats = copy.deepcopy(self.textformats)

    def importTextformatXml(self, xml, createIfNotExists=1):
      v = standard.parseXmlString(xml)
      if isinstance(v, list):
        for item in v:
          self._importTextformatXml(item, createIfNotExists)
      else:
        self._importTextformatXml(v, createIfNotExists)


    # --------------------------------------------------------------------------
    #  ZMSTextformatManager.delTextformat:
    # --------------------------------------------------------------------------
    def delTextformat(self, id):
      i = self.textformats.index(id)
      del self.textformats[i]
      del self.textformats[i]
      # Make persistent.
      self.textformats = copy.deepcopy(self.textformats)


    # --------------------------------------------------------------------------
    #  ZMSTextformatManager.setTextformat:
    # --------------------------------------------------------------------------
    def setTextformat(self, id, newId, newDisplay, newZMILang, newTag='', newSubtag='', newAttrs='', newRichedit=0, newUsage=[]):
      if id in self.textformats:
        i = self.textformats.index(id)
      else:
        i = len(self.textformats)
        self.textformats.extend([newId, {'display':{},'default':0}])
      dict = self.textformats[i+1]
      dict['display'][newZMILang] = newDisplay
      dict['tag'] = newTag
      dict['subtag'] = newSubtag
      dict['attrs'] = newAttrs
      dict['richedit'] = newRichedit
      dict['usage'] = newUsage
      self.textformats[i] = newId
      self.textformats[i+1] = dict
      # Make persistent.
      self.textformats = copy.deepcopy(self.textformats)


    # --------------------------------------------------------------------------
    #  ZMSTextformatManager.getTextFormat:
    # --------------------------------------------------------------------------
    def getTextFormat(self, id, REQUEST):
      if id in self.textformats:
        i = self.textformats.index(id)
        d = self.textformats[i+1]
        return ZMSTextformat.ZMSTextformat(id, d, REQUEST)
      return None


    # --------------------------------------------------------------------------
    #  ZMSTextformatManager.getTextFormats:
    # --------------------------------------------------------------------------
    def getTextFormats(self, REQUEST):
      l = [self.getTextFormat(self.textformats[x*2], REQUEST) for x in range(len(self.textformats)//2)]
      return sorted(l,key=lambda x:x.getDisplay())


    # --------------------------------------------------------------------------
    #  ZMSTextformatManager.setDefaultTextformat:
    # --------------------------------------------------------------------------
    def setDefaultTextformat(self, id):
      if len(id) > 0 and id in self.textformats:
        [self.operator_setitem(self.textformats[x*2+1], 'default', 0) for x in range(len(self.textformats)//2)]
        i = self.textformats.index(id)
        self.textformats[i+1]['default'] = 1
        # Make persistent.
        self.textformats = copy.deepcopy(self.textformats)


    # --------------------------------------------------------------------------
    #  ZMSTextformatManager.getTextFormatDefault:
    # --------------------------------------------------------------------------
    def getTextFormatDefault(self):
      if len(self.textformats) == 0:
        return ''
      i = 0
      format_default = [x for x in range(len(self.textformats)//2) if self.textformats[x*2+1].get('default', 0) == 1]
      if len(format_default) == 1:
        i = format_default[0]*2
      elif 'body' in self.textformats:
        i = self.textformats.index('body')
      return self.textformats[i]


    ############################################################################
    #  ZMSTextformatManager.manage_changeTextformat:
    #
    #  Change text-formats.
    ############################################################################
    def manage_changeTextformat(self, lang, btn, REQUEST, RESPONSE): 
      """ ZMSTextformatManager.manage_changeTextformat """
      message = ''
      id = REQUEST.get('id', '')
      
      # Change.
      # -------
      if btn == 'BTN_SAVE':
        old_id = REQUEST['id']
        id = REQUEST['new_id'].strip()
        display = REQUEST['new_display'].strip()
        tag = REQUEST['new_tag'].strip()
        subtag = REQUEST['new_subtag'].strip()
        attrs = REQUEST['new_attrs'].strip()
        richedit = REQUEST.get('new_richedit', 0)
        usage = REQUEST.get('new_usage', [])
        self.setTextformat(old_id, id, display, self.get_manage_lang(), tag, subtag, attrs, richedit, usage)
        if 'new_default' in REQUEST:
          self.setDefaultTextformat(id)
        id = ''
        message = self.getZMILangStr('MSG_CHANGED')
      
      # Delete.
      # -------
      elif btn == 'BTN_DELETE':
        if id:
          ids = [id]
        else:
          ids = REQUEST.get('ids', [])
        for id in ids:
          self.delTextformat(id) 
        id = ''
        message = self.getZMILangStr('MSG_DELETED')%len(ids)
      
      # Insert.
      # -------
      elif btn == 'BTN_INSERT':
        id = REQUEST['_id'].strip()
        display = REQUEST['_display'].strip()
        self.setTextformat(None, id, display, self.get_manage_lang())
        message = self.getZMILangStr('MSG_CHANGED')
      
      # Export.
      # -------
      elif btn == 'BTN_EXPORT':
        value = []
        ids = REQUEST.get('ids', [])
        fmts = self.textformats
        for i in range(len(fmts)//2):
          id = fmts[i*2]
          ob = fmts[i*2+1]
          if id in ids or len(ids) == 0:
            value.append({'key':id,'value':ob})
        if len(value)==1:
          value = value[0]
        content_type = 'text/xml; charset=utf-8'
        filename = 'export.textfmt.xml'
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
          self.importTextformatXml(xml=f)
        else:
          filename = REQUEST['init']
          self.importConf(filename, createIfNotExists=1)
        message = self.getZMILangStr('MSG_IMPORTED')%('<i>%s</i>'%filename)
      
      # Return with message.
      if RESPONSE:
        message = standard.url_quote(message)
        return RESPONSE.redirect('manage_textformats?lang=%s&manage_tabs_message=%s&id=%s'%(lang, message, id))
      
      return message

################################################################################
