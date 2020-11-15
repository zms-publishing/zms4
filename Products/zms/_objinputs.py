################################################################################
# _objinputs.py
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

# Product Imports.
from Products.zms import standard
from Products.zms import _zreferableitem


class ObjInputs(object):

  # ----------------------------------------------------------------------------
  # ObjInputs.getUrlInput:
  #
  #	@param fmName
  #	@param elName
  #	@param elTextName
  #	@param size
  #	@param value
  #	@param enabled
  #	@param css	CSS-Class
  #	@return String
  # ----------------------------------------------------------------------------
  def getUrlInput(self, fmName, elName, elTextName='', size=None, value='', enabled=True, css='form-control'):
    return self.getTextInput(fmName, elName, size, value, 'text', enabled=enabled, css=css+' url-input')


  # ----------------------------------------------------------------------------
  # getDateTimeInput:
  #
  #	@param fmName
  #	@param elName
  #	@param size
  #	@param value
  #	@param enabled
  #	@param css	CSS-Class
  #	@return String
  # ----------------------------------------------------------------------------
  def getDateTimeInput(self, fmName, elName, size=8, value=None, enabled=True, fmt_str='DATETIME_FMT', css='form-control'):
    manage_lang = self.get_manage_lang()
    html = []
    input_type = 'date'
    if not isinstance(value, str):
      fmt = {'DATE_FMT':'%Y-%m-%d','DATETIME_FMT':'%Y-%m-%dT%H:%M'}
      value = self.getLangFmtDate(value, manage_lang, fmt.get(fmt_str))
    if value is not None and self.parseLangFmtDate(value) is None:
      value = ''
    placeholder = self.getZMILangStr(fmt_str)
    if enabled:
      if fmt_str == 'DATE_FMT':
        css += ' datepicker'
      elif fmt_str == 'DATETIME_FMT':
        css += ' datetimepicker'
        input_type = 'datetime-local'
    html.append(self.getTextInput(fmName, elName, size, value, input_type, enabled, css=css, placeholder=placeholder))
    return ''.join(html)


  # ----------------------------------------------------------------------------
  # getPasswordInput:
  #
  #	@param fmName
  #	@param elName
  #	@param size
  #	@param value
  #	@param enabled
  #	@param css    CSS-Class
  #	@return String
  # ----------------------------------------------------------------------------
  def getPasswordInput(self, fmName, elName, size=15, value='', enabled=True, css='form-control'):
    return self.getTextInput(fmName, elName, size, value, 'password', enabled, css)


  # ----------------------------------------------------------------------------
  # getTextInput:
  #
  #	@param fmName
  #	@param elName
  #	@param size
  #	@param value  (optional)
  #	@param type   (optional: "text" or "password")
  #	@param css    CSS-Class
  #	@return String
  # ----------------------------------------------------------------------------
  def getTextInput(self, fmName, elName, size=None, value='', type='text', enabled=True, css='form-control', placeholder=''):
    lang = self.REQUEST.get('lang', self.getPrimaryLanguage())
    elId = elName
    if elId.endswith('_%s'%lang):
      elId = elId[:-len('_%s'%lang)]
    html = []
    html.append('<input ')
    html.append(' class="%s"'%' '.join([css, elId, lang]))
    html.append(' type="%s"'%type)
    html.append(' id="%s"'%elName.replace(':int', ''))
    html.append(' name="%s"'%elName)
    if size:
      html.append(' size="%i"'%size)
    if value is not None:
      html.append(' value="%s"'%standard.html_quote(value))
    if not enabled:
      html.append(' disabled="disabled"')
    if placeholder:
      html.append(' title="%s"'%placeholder)
    html.append('/>')
    return ''.join(html)


  # ----------------------------------------------------------------------------
  # getSelect:
  #
  #	@param fmName
  #	@param elName
  #	@param value
  #	@param inputtype
  #	@param lang_str
  #	@param required
  #	@param optpl
  #	@param enabled
  #	@param css    CSS-Class
  #	@return String
  # ----------------------------------------------------------------------------
  def getSelect(self, fmName, elName, value, inputtype, lang_str, required=False, optpl=[], enabled=True, css='form-control', maxlen=30):
    if inputtype in ['select', 'multiline']:
      return self.zmi_input_select(self, name=elName, value=value, lang_str=lang_str, mandatory=required, options=optpl, enabled=enabled)
    elif inputtype in ['color']:
      return self.zmi_input_color(self,name=elName,value=value,lang_str=lang_str,mandatory=required,options=optpl,enabled=enabled)
    elif inputtype in ['multiselect']:
      return self.zmi_input_multiselect(self, name=elName, value=value, lang_str=lang_str, mandatory=required, options=optpl, enabled=enabled)
    elif type in ['text']:
      return self.getTextArea(fmName, elName, 35, 4, value=value, enabled=enabled)
    else:
      return self.getTextInput(fmName=fmName, elName=elName, size=35, value=value, type='text', enabled=enabled)


  # ----------------------------------------------------------------------------
  #	getCheckbox:
  #
  #	@param fmName
  #	@param elName
  #	@param elId   (optional: "string" or "")
  #	@param value
  #	@param enabled
  #	@param hidden Add hidden Input-Field if not enabled
  #	@param css    CSS-Class
  #	@param btn    Appear as Bootstrap Button
  #	@return String
  #
  # Hint: In order to avoid multiple identical ids (HTML5 conformance) 
  # call getCheckbox(..., elId='', ...) with an empty string for elId
  # ----------------------------------------------------------------------------
  def getCheckbox(self, fmName, elName, elId=None, value=None, enabled=True, hidden=True, css='', btn=False, options=[0, 1]):
    lang = self.REQUEST.get('lang', self.getPrimaryLanguage())
    if elId==None:
      elId = elName
    if elId.endswith('_%s'%lang):
      elId = elId[:-len('_%s'%lang)]
    html = []
    if value in [True, False]:
      value = options[int(value)]
    checked = str(value) == str(options[1])
    html.append('<input ')
    html.append(' type="hidden"')
    html.append(' name="%s"'%elName)
    html.append(' value="%s"'%str(standard.nvl(value, options[0])))
    html.append(' />')
    if btn:
      html.append('<span class="btn btn-secondary">')
    html.append('<input ')
    if isinstance(elId, str) and elId!='':
      html.append(' id="%s"'%elId)
    html.append(' class="%s"'%' '.join([elId in [None,''] and elName or elId, css, lang]))
    html.append(' type="checkbox"')
    if not enabled:
      html.append(' disabled="disabled"')
    if checked: 
      html.append(' checked="checked"')
    html.append(' onclick="if(this.checked){$(this)%s.prev().val(\'%s\')}else{$(this)%s.prev().val(\'%s\')}"'%(['', '.parent()'][btn], options[1], ['', '.parent()'][btn], options[0]))
    html.append(' />')
    if btn:
      html.append('</span>')
    return ''.join(html)


  # ----------------------------------------------------------------------------
  # getTextArea:
  #
  #	@param fmName
  #	@param elName
  #	@param cols
  #	@param rows
  #	@param value
  #	@param enabled
  #	@param css    CSS-Class
  #	@param wrap   Word-Wrap (on|off)
  #	@return String
  # ----------------------------------------------------------------------------
  def getTextArea(self, fmName, elName, cols, rows, value, enabled=True, css='form-control', wrap='virtual'):
    lang = self.REQUEST.get('lang', self.getPrimaryLanguage())
    elId = elName
    if elId.endswith('_%s'%lang):
      elId = elId[:-len('_%s'%lang)]
    html = []
    html.append('<textarea ')
    html.append(' class="%s"'%' '.join([css, elId, lang]))
    html.append(' id="%s"'%elName)
    html.append(' name="%s"'%elName)
    if cols:
      html.append(' cols="%i"'%cols)
    if rows:
      html.append(' rows="%i"'%rows)
    html.append(' wrap="%s"'%wrap)
    if not enabled:
      html.append(' disabled="disabled"')
    html.append('>')
    if value is not None:
      if isinstance(value, list):
        for item in value:
          html.append('%s\n'%standard.html_quote(item))
      else:
        html.append('%s'%standard.html_quote(value))
    html.append('</textarea>')
    return ''.join(html)

################################################################################
