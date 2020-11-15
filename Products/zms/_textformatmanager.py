################################################################################
# _textformatmanager.py
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

import six
# Product Imports.
from Products.zms import standard
from Products.zms import _globals
from Products.zms import _objattrs


class TextFormatObject(object):

  # ----------------------------------------------------------------------------
  #  TextFormatObject.getSecNo
  #
  #  Returns section-number.
  # ----------------------------------------------------------------------------
  def getSecNo( self):
    sec_no = ''
    #-- [ReqBuff]: Fetch buffered value from Http-Request.
    parentNode = self.getParentNode()
    if parentNode is None or \
       getattr(parentNode, 'meta_type', None) not in self.dGlobalAttrs:
      return sec_no
    reqBuffId = 'getSecNo'
    try:
      levelnfc = parentNode.fetchReqBuff( '%s_levelnfc'%reqBuffId)
      if levelnfc > 0:
        sec_no = parentNode.fetchReqBuff( '%s_%s'%(reqBuffId, self.id))
    except:
      levelnfc = parentNode.attr('levelnfc')
      parentNode.storeReqBuff( '%s_levelnfc'%reqBuffId, levelnfc, self.REQUEST)
      if levelnfc is not None and len(levelnfc) > 0:
        parent_no = parentNode.getSecNo()
        sectionizer = _globals.MySectionizer(levelnfc)
        siblings = parentNode.filteredChildNodes( self.REQUEST)
        for sibling in siblings:
          curr_no = ''
          level = 0
          if sibling.isPageElement():
            format = sibling.attr('format')
            if format is not None and format.find('headline') == 0:
              level = int(format[len(standard.id_prefix(format)):])-1
          elif sibling.isPage():
            level = 1
          if level > 0:
            sectionizer.processLevel(level)
            curr_no = parent_no + str(sectionizer)
            if self == sibling:
              sec_no = curr_no
          #-- [ReqBuff]: Store value in buffer of Http-Request.
          parentNode.storeReqBuff( '%s_%s'%(reqBuffId, sibling.id), curr_no, self.REQUEST)
    #-- [ReqBuff]: Return value.
    return sec_no


  # ----------------------------------------------------------------------------
  #  TextFormatObject.getText
  #
  #  Returns text with section-number.
  # ----------------------------------------------------------------------------
  def getText( self, REQUEST, key='text', encoding='utf-8', errors='strict'):
    s = self.getObjProperty(key, REQUEST)
    if self.isPageElement():
      sec_no = self.getSecNo()
      if len(sec_no) > 0:
        s = '%s %s'%(sec_no, s)
    if six.PY2:
      return standard.pystr(s, encoding, errors)
    else:
      return s

  # ----------------------------------------------------------------------------
  #  TextFormatObject.renderText:
  # ----------------------------------------------------------------------------
  def renderText( self, format, key, text, REQUEST, id=None, clazz=None):
    # Process format.
    if format is not None:
      textformat = self.getTextFormat( format, REQUEST)
      if textformat is not None and len( text) > 0:
        text = textformat.renderText( text, REQUEST, id, clazz)
    # Custom hook.
    try:
      name = 'renderCustomText'
      if hasattr(self, name):
        text = getattr(self, name)(context=self, key=key, text=text, REQUEST=REQUEST)
    except:
      standard.writeError( self, '[renderText]: can\'t %s'%name)
    # Return.
    return text

################################################################################
