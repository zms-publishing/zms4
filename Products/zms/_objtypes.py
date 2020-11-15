################################################################################
# _objtypes.py
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
from Products.zms import _blobfields
from Products.zms import _confmanager
from Products.zms import _fileutil
from Products.zms import standard
from Products.zms import _zreferableitem


# ------------------------------------------------------------------------------
#  _objtypes.getHref2Zoom:
# ------------------------------------------------------------------------------
def getHref2Zoom(self, img, REQUEST):
  m = getattr( self, 'getCustomHref2Zoom', None)
  if m is not None:
    href = m( self, img=img, REQUEST=REQUEST)
  else:
    href = img.getHref(REQUEST)
  return href


class ObjTypes(object):

    # Autocomplete.
    # -------------
    zmi_input_autocomplete = PageTemplateFile('zpt/objattrs/zmi_input_autocomplete', globals())

    # String, Text, Select, Multiple-Select.
    # --------------------------------------
    zmi_input_multiselect = PageTemplateFile('zpt/objattrs/zmi_input_multiselect', globals())
    zmi_input_select = PageTemplateFile('zpt/objattrs/zmi_input_select', globals())
    zmi_input_color = PageTemplateFile('zpt/objattrs/zmi_input_color', globals()) 

    # Richtext.
    # ---------
    f_selectRichtext = PageTemplateFile('zpt/objattrs/f_select_richtext', globals())
    zmi_select_richtext_standard = PageTemplateFile('zpt/objattrs/zmi_select_richtext_standard', globals())
    zmi_select_richtext_wysiwyg = PageTemplateFile('zpt/objattrs/zmi_select_richtext_wysiwyg', globals())

    # Displaytype.
    # ------------
    zmi_displaytype_top = PageTemplateFile('zpt/objattrs/zmi_displaytype_top', globals())
    zmi_displaytype_right = PageTemplateFile('zpt/objattrs/zmi_displaytype_right', globals())
    zmi_displaytype_bottom = PageTemplateFile('zpt/objattrs/zmi_displaytype_bottom', globals())
    zmi_displaytype_left = PageTemplateFile('zpt/objattrs/zmi_displaytype_left', globals())
    zmi_displaytype_export = PageTemplateFile('zpt/objattrs/zmi_displaytype_export', globals())

    # File.
    # -----
    f_selectFile = PageTemplateFile('zpt/objattrs/f_select_file', globals()) 

    # Image.
    # ------
    f_selectImage = PageTemplateFile('zpt/objattrs/f_select_image', globals()) 

    ############################################################################
    #  dctDisplaytype :
    #         
    #  Dictionary of display-types. 
    ############################################################################
    dctDisplaytype = {
      '1': 'left',
      '2': 'top',
      '3': 'bottom',
      '4': 'right',
      '5': 'left',		# 'floatbefore'
      '6': 'right',		# 'floatafter'
      '7': 'left',		# 'behindtext'
    }


    ############################################################################
    #  ObjTypes.renderDisplaytype:
    #
    #  HTML presentation of Image and Text.
    #
    #  Parameters:
    #    IN:  @self          <Object>
    #         @displaytype   <String>
    #         @imgattr       Object-Attribute <String>
    #         @imghiresattr  Object-Attribute (High-Resolution) <String> 
    #         @imgurl        URL for Image
    #         @imgthumb      @deprecated
    #         @imgspecial    Special Attributes (for <img>-Tag, e.g. usemap)
    #         @imgclass      CSS Image-Class
    #         @text          String-Object
    #         @textalign     Text-Alignment (Left, Right, Center)
    #         @textclass     CSS Text-Class
    #         @REQUEST       Request-Object
    #    OUT: <html>         String-Object
    ############################################################################
    def renderDisplaytype(self, displaytype='', \
      imgattr='', imghiresattr='', imgurl='', imgthumb=None, imgspecial='', imgclass='', \
      text='', textalign='', textclass='', REQUEST=None):
      
      align = self.getObjProperty('align', REQUEST)
      
      # Export-Format.
      if 'export_format' in REQUEST:
        try:
          export_format = int( REQUEST.get('export_format'))
        except:
          displaytype = 'export'
      
      # Image.
      # ------
      img = self.getObjProperty(imgattr, REQUEST)
      imghires = None
      if imghiresattr is not None:
        imghires = self.getObjProperty(imghiresattr, REQUEST)
        if imghires is not None and displaytype == 'export_format':
          img = imghires
          imgattr = imghiresattr
          imghires = None
          imghiresattr = None
      
      imgtag = ''
      imgzoom = ''
      
      #-- IMAGE-PROPERTIES 
      if img is None or img == '' or (isinstance(img, _blobfields.MyBlob) and img.get_real_size() == 0):
        width = ''
        height = ''
        
        # Image (HiRes).
        # --------------
        if imghires is not None and imghires.get_real_size() != 0:
          s_url = getHref2Zoom(self, imghires, REQUEST)
          imgtag = ''
          imgtag += '<div class="caption">'
          imgtag += '<a href="%s"><img src="/++resource++zms_/img/mime_type.image_basic.gif" title="%s" border="0" align="middle" /></a>&nbsp;'%(s_url, imghires.getContentType())
          imgtag += '<a href="%s">%s</a>&nbsp;'%(s_url, imghires.filename)
          imgtag += '<b>(%s)</b>'%self.getDataSizeStr(imghires.get_size())
          imgtag += '</div>'
          
      else:
        imgzoomattr = ''
        
        # Dimensions.
        # -----------
        width = ''
        height = ''
        try:
          height = '%ipx'%int(img.height)
          width = '%ipx'%int(img.width)
        except:
          pass
        
        # Image (HiRes).
        # --------------
        if not (imghires is None or imghires.get_real_size() == 0):
          imgzoomobj = imghires
          imgzoomattr = imghiresattr 
        
        # Assemble img-tag.
        imgsrc = img.getHref(REQUEST)
        imgalt = img.getFilename()
        imgtag = '<img'
        imgtag += ' src="%s"'%imgsrc
        if imgclass is not None and len(imgclass) > 0:
          imgtag += ' class="%s"'%imgclass
        if imgspecial is not None and len(imgspecial) > 0:
          imgtag += ' %s'%imgspecial
        if imgspecial.find('alt=') < 0:
          imgtag += ' alt="%s"'%imgalt
        imgtag += ' />'
        
        # Image-Url.
        # ----------
        if imgurl is not None and len(imgurl) > 0:
          imgtarget = ''
          if not (imgurl.startswith('/') or imgurl.startswith('.') or imgurl.startswith( REQUEST[ 'BASE0'])):
            imgtarget = ' target="_blank"'
          imgtag = '<a href="%s"%s>%s</a>'%( imgurl, imgtarget, imgtag)
        
        # Zoom (HiRes).
        # -------------
        elif len(imgzoomattr) > 0:
          
          # Zoom (SuperRes).
          # ----------------
          key = 'imgsuperres'
          if key in self.getObjAttrs() and self.getConfProperty('ZMSGraphic.superres', 0)==1:
            imgsuperzoomobj = self.getObjProperty(key, REQUEST)
            if imgsuperzoomobj is not None:
              s_url = getHref2Zoom(self, imgzoomobj, REQUEST)
              imgzoomclazz = 'zoom'
              imgzoomalt = '%s (%s)'%(self.getZMILangStr('BTN_ZOOM'), self.getDataSizeStr(imgzoomobj.get_size()))
              imgzoom += '<a href="%s" class="%s fancybox" target="_blank"><img class="%s" src="%s" title="%s" border="0" /></a>'%( s_url, imgzoomclazz, imgzoomclazz, self.spacer_gif, imgzoomalt)
              s_url = getHref2Zoom(self, imgsuperzoomobj, REQUEST)
              imgzoomclazz = 'superzoom'
              imgzoomalt = '%s (%s)'%(self.getZMILangStr('ATTR_SUPERRES'), imgsuperzoomobj.getDataSizeStr())
              imgzoom += '<a href="%s" class="%s" target="_blank"><img class="%s" src="%s" title="%s" border="0" /></a>'%( s_url, imgzoomclazz, imgzoomclazz, self.spacer_gif, imgzoomalt)
          
          # Image-Zoom.
          if imgzoom is not None and len(imgzoom) > 0:
            imgtag += imgzoom
          else:
            imgtag = '<a href="%s" class="fancybox">%s</a>'%(imgzoomobj.getHref(REQUEST), imgtag)
      
      # Build <html>-presentation.
      renderer = getattr(self, 'zmi_displaytype_%s'%displaytype)
      html = renderer(self 
          , ob=self 
          , img=imgtag 
          , text=text 
          , textalign=textalign
          , textclass=textclass
          , height=height
          , width=width
          , align=align
          , float=align.find( '_FLOAT') >= 0)
      
      # Return <html>-presentation.
      return html

################################################################################
