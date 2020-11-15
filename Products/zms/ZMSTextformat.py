################################################################################
# ZMSTextformat.py
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
import re
# Product Imports.
from Products.zms import _globals
from Products.zms import standard


# ------------------------------------------------------------------------------
#  br_quote
# ------------------------------------------------------------------------------
def br_quote(text, subtag, REQUEST):
  if len(subtag) == 0:
    return text
  if not standard.is_str(text):
    text = standard.pystr(text)
  rtn = ''
  qcr = ''
  qtab = '&nbsp;'*6
  
  if standard.isManagementInterface(REQUEST):
    if 'format' not in REQUEST:
      qcr = '<span class="unicode">&crarr;</span>'
      qtab = '<span class="unicode">&rarr;</span>' + '&nbsp;' * 5
  
  if subtag == 'br':
    tmp = []
    for s in text.split('<%s>'%subtag):
      while len(s) > 0 and ord(s[0]) in [10, 13]: s = s[1:]
      if len(tmp) > 0:
        tmp.append('\n')
      tmp.append(s)
    text = ''.join(tmp)
  
  # handle nested lists
  ts = text.split('\n')
  ll = []
  c = 0
  for line in ts:
    if line.find( '\t* ') >= 0 or line.find( '\t# ') >= 0:
      i = 0
      while i < len( line) and line[ i] == '\t':
        i += 1
      if line[ i] in [ '*', '#']:
        level = i
        
        # open nested lists
        if level > len(ll):
          if line[ i] == '*':
            rtn += '<ul>'*(level-len(ll))
            ll.extend(['ul']*(level-len(ll)))
          elif line[ i] == '#':
            rtn += '<ol>'*(level-len(ll))
            ll.extend(['ol']*(level-len(ll)))
        
        # close nested lists
        elif level < len(ll):
          for li in range(len(ll)-level):
            rtn += '</%s>'%ll[-1]
            ll = ll[0:-1]
        
        rtn += '<li>%s</li>'%line[i+2:]
        continue
    
    # close nested lists
    if len(ll) > 0:
      level = 0
      for li in range(len(ll)-level):
        rtn += '</%s>'%ll[-1]
        ll = ll[0:-1]
    
    # handle leading whitespaces and tabs
    i = 0
    while i < len( line) and line[ i] in [ ' ', '\t']:
      if line[ i] == ' ':
        rtn += '&nbsp;'
      elif line[ i] == '\t':
        rtn += qtab
      i += 1
    rtn += '\n'
    line = line[ i:].strip()
    
    if subtag == 'br':
      rtn += line+qcr
      if c < len( ts):
        rtn += '<%s />'%subtag
    elif len(line) > 0:
      rtn += '<%s'%subtag
      rtn += '>'
      rtn += line+qcr
      rtn += '</%s>'%subtag
    c += 1
  
  # close nested lists
  if len(ll) > 0:
    level = 0
    for li in range(len(ll)-level):
      rtn += '</%s>'%ll[-1]
      ll = ll[0:-1]
  
  return rtn


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
class ZMSTextformat(object):

  # ----------------------------------------------------------------------------
  #  ZMSTextformat.__init__:
  #
  #  Constructor.
  # ----------------------------------------------------------------------------
  def __init__(self, id, ob, REQUEST):
    self.setId(id)
    if REQUEST is not None and \
       'manage_lang' in REQUEST and \
       REQUEST['manage_lang'] in ob['display']:
      self.setDisplay(ob['display'][REQUEST['manage_lang']])
    else:
      self.setDisplay(id)
    self.setTag(ob['tag'])
    self.setSubTag(ob['subtag'])
    self.setAttrs(ob['attrs'])
    self.setRichedit(ob.get('richedit', 0))
    self.setUsage(ob.get('usage', ['standard']))

  # ----------------------------------------------------------------------------
  #  Get/Set Id.
  # ----------------------------------------------------------------------------
  getId__roles__ = None
  def getId(self): return self.id
  def setId(self, id): self.id = id

  # ----------------------------------------------------------------------------
  #  Get/Set Display.
  # ----------------------------------------------------------------------------
  getDisplay__roles__ = None
  def getDisplay(self): return self.display
  def setDisplay(self, display): self.display = display

  # ----------------------------------------------------------------------------
  #  Get/Set <Tag>.
  # ----------------------------------------------------------------------------
  getTag__roles__ = None
  def getTag(self): return self.tag
  def setTag(self, tag): self.tag = tag

  # ----------------------------------------------------------------------------
  #  Assemble <Start-Tag>.
  # ----------------------------------------------------------------------------
  getStartTag__roles__ = None
  def getStartTag(self, id=None, clazz=None): 
    html = ''
    tag = self.getTag()
    if len(tag) > 0:
      html += '<%s'%tag
      if id is not None:
        html += ' id="%s"'%id
      if clazz is not None:
        html += ' class="%s"'%clazz
      attrs = self.getAttrs()
      if len(attrs) > 0:
        html += ' ' + attrs
      html += '>'
    return html

  # ----------------------------------------------------------------------------
  #  Assemble <End-Tag>.
  # ----------------------------------------------------------------------------
  getEndTag__roles__ = None
  def getEndTag(self): 
    html = ''
    tag = self.getTag()
    if len(tag) > 0:
      html += '</%s'%tag
      html += '>'
    return html

  # ----------------------------------------------------------------------------
  #  Get/Set <Sub-Tag>.
  # ----------------------------------------------------------------------------
  getSubTag__roles__ = None
  def getSubTag(self): return self.subtag
  def setSubTag(self, subtag): self.subtag = subtag

  # ----------------------------------------------------------------------------
  #  Get/Set <Tag>-Attributes.
  # ----------------------------------------------------------------------------
  getAttrs__roles__ = None
  def getAttrs(self): return self.attrs
  parseAttrs__roles__ = None
  def parseAttrs(self):
    d = []
    l = re.split('(.*?)="(.*?)"', self.attrs)
    for i in range(len(l)//3):
      d.append((l[i*3+1], l[i*3+2]))
    return d
  def setAttrs(self, attrs): self.attrs = attrs

  # ----------------------------------------------------------------------------
  #  Get/Set Richedit.
  # ----------------------------------------------------------------------------
  getRichedit__roles__ = None
  def getRichedit(self): return self.richedit
  def setRichedit(self, richedit):
    if _globals.is_str_type(richedit) and len(richedit) > 0:
      richedit = 1
    self.richedit = richedit

  # ----------------------------------------------------------------------------
  #  Get/Set Usage.
  # ----------------------------------------------------------------------------
  getUsage__roles__ = None
  def getUsage(self): return self.usage
  def setUsage(self, usage): self.usage = usage

  # ----------------------------------------------------------------------------
  #  HTML.
  # ----------------------------------------------------------------------------
  getHtml__roles__ = None
  def getHtml(self): 
    html = ''
    # Open tag.
    if len(self.getTag()) > 0:
      html += '&lt;'
      html += self.getTag()
      if len(self.getAttrs()) > 0:
        html += ' ' + self.getAttrs()
      html += '&gt;'
      html += '<br />'
    # Sub tag.
    subtag = self.getSubTag()
    if len(subtag)>0:
      if subtag == 'br':
        html += '&nbsp;&nbsp;...&lt;' + subtag + ' /&gt;'
      else:
        html += '&nbsp;&nbsp;&lt;' + subtag + '&gt;...&lt;/' + subtag + '&gt;'
      html += '<br />'
    else:
      html += '...'
    # Close tag.
    if len(self.getTag()) > 0:
      html += '&lt;/'
      html += self.getTag()
      html += '&gt;'
      html += '<br />'
    # Return.
    return html

  # ----------------------------------------------------------------------------
  #  Render text.
  # ----------------------------------------------------------------------------
  renderText__roles__ = None
  def renderText(self, text, REQUEST, id=None, clazz=None, encoding='utf-8', errors='strict'):
    html = ''
    # Open tag.
    html += self.getStartTag( id, clazz)
    # Sub tag.
    text = br_quote( text, self.getSubTag(), REQUEST)
    # Value.
    try:
      html += standard.pystr(text, encoding, errors)
    except:
      html += text
    # Close tag.
    html += self.getEndTag()
    # Return.
    return html

################################################################################
