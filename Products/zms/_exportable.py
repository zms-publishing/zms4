################################################################################
# _exportable.py
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
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from App.Common import package_home
from OFS.Image import Image
import codecs
import copy
import tempfile
import os
import re
import sys
# Product Imports.
from Products.zms import _blobfields
from Products.zms import _fileutil
from Products.zms import _filtermanager
from Products.zms import _globals
from Products.zms import _xmllib
from Products.zms import standard


def writeFile(self, filename, data, mode='w', encoding='utf-8'):
  try:
    f = codecs.open( filename, mode=mode, encoding=encoding)
    f.write( data)
    f.close()
  except:
    standard.writeError( self, "[writeFile]")
    f = open( filename, mode=mode)
    f.write( data)
    f.close()


# ------------------------------------------------------------------------------
#  _exportable.exportFiles:
# ------------------------------------------------------------------------------
def exportFiles(self, root, id, path):
  if hasattr(root, id):
    folder = getattr(root, id)
    for ob in folder.objectValues(['File', 'Image']):
      try:
        ob_id = ob.id()
      except:
        ob_id = standard.pystr(ob.id)
      _fileutil.exportObj(ob, '%s/%s'%(path, ob_id))


# ------------------------------------------------------------------------------
#  _exportable.exportFolder:
# ------------------------------------------------------------------------------
def exportFolder(self, root, path, id, REQUEST, depth=0):
  if hasattr(root, id):
    folder = getattr(root, id)
    for ob in folder.objectValues():
      ob_id = ob.getId()
      if ob.meta_type == 'Folder':
        exportFolder(self, ob, '%s/%s'%(path, id), ob_id, REQUEST, depth+1)
      elif 'content' not in folder.objectIds(['ZMS']):
        if ob.meta_type in [ 'DTML Document', 'DTML Method', 'Page Template', 'Script (Python)']:
          try:
            if ob.meta_type in [ 'DTML Document', 'DTML Method', 'Page Template']:
              v = ob(ob, REQUEST)
            elif ob.meta_type in [ 'Script (Python)']:
              v = ob()
            v = localHtml( ob, v)
            v = localIndexHtml( self, ob, len(ob.absolute_url().split('/'))-len(root.absolute_url().split('/'))+depth, v)
            ob = v
          except:
            standard.writeError( self, "[exportFolder]")
        _fileutil.exportObj(ob, '%s/%s/%s'%(path, id, ob_id))


# ------------------------------------------------------------------------------
#  _exportable.findDelimiter:
# ------------------------------------------------------------------------------
def findDelimiter(s, delimiters=['"', "'"]):
  rtn = -1
  for delimiter in delimiters:
    i = s.find(delimiter)
    if rtn == -1:
      rtn = i
    elif i >= 0:
      rtn = min(rtn, i)
  return rtn


# ------------------------------------------------------------------------------
#  _exportable.rfindDelimiter:
# ------------------------------------------------------------------------------
def rfindDelimiter(s, delimiters=['"', "'"]):
  rtn = -1
  for delimiter in delimiters:
    i = s.rfind(delimiter)
    rtn = max(rtn, i)
  return rtn


# ------------------------------------------------------------------------------
#  _exportable.localHtml:
#
#  Process encoding.
# ------------------------------------------------------------------------------
def localHtml(self, html):
  try:
    default_charset = 'utf-8'
    charset = self.REQUEST.get('ZMS_CHARSET', default_charset)
    if not isinstance(html, str):
      html = standard.pystr( html, default_charset)
    html = html.encode( charset)
  except ( UnicodeDecodeError, UnicodeEncodeError):
    standard.writeError( self, "[localHtml]")
    v = standard.pystr(sys.exc_info()[1])
    STR_POSITION = ' position '
    i = v.find(STR_POSITION)
    if i > 0:
      v = v[i+len(STR_POSITION):]
      if v.find('-') > 0:
        l = int( v[:v.find('-')])
        h = int( v[v.find('-')+1:v.find(':')])
      else:
        l = int( v[:v.find(':')])
        h = l
      ln = max( l - 20, 0)
      hn = min( h + 20, len(html))
  return html


# ------------------------------------------------------------------------------
#  _exportable.localIndexHtml:
# ------------------------------------------------------------------------------
def localIndexHtml(self, obj, level, html, xhtml=False):
   REQUEST = self.REQUEST
   
   sRoot = ''
   for i in range(level):
     sRoot = '../%s'%sRoot
   
   # Process aliases.
   doc_url = self.getDocumentElement().absolute_url()
   url = doc_url
   url = url[url.find('://')+3:]
   url = url[url.find('/'):]
   base_url = doc_url
   base_url = base_url[ : base_url.find(url)]
   html = re.sub( '"([^("\')]*?)'+url+'([^("\')]*?)"', '"'+base_url+url+'\\2"', html)
   
   # Process absolute URLs.
   s_new = '%s'%sRoot
   s_old = '%s/'%self.absolute_url()
   if xhtml or level != 0:
     html = html.replace( s_old, s_new)
   if self.getConfProperty('ZMS.pathhandler', 0) != 0:
     s_old = '%s/'%self.getDeclUrl( REQUEST)
     html = html.replace( s_old, s_new)
   s_old = '%s/'%self.getDocumentElement().absolute_url()
   html = html.replace( s_old, s_new)
   s_old = '%s/'%self.getHome().absolute_url()
   html = html.replace( s_old, s_new)
   
   # Process links to resource-folders: images and assets.
   for container in self.getResourceFolders():
     id = container.id
     s_new = '"%s%s/'%(sRoot, id)
     s_old = '"./%s/'%(id)
     html = html.replace(s_old, s_new)
     s_old = '"%s/'%(id)
     html = html.replace(s_old, s_new)
   
   # Process links to product-folder: images and assets.
   s_new = '"%smisc_/zms/'%sRoot
   s_old = '"/++resource++zms_/img/'
   html = html.replace(s_old, s_new)
   s_old = '"misc_/zms/'
   html = html.replace(s_old, s_new)
   # starting with '(' (in styles)
   s_new = '(%smisc_/zms/'%sRoot
   s_old = '(/++resource++zms_/img/'
   html = html.replace(s_old, s_new)
   s_old = '(misc_/zms/'
   html = html.replace(s_old, s_new)
   
   # Remove preview parameters.
   html = re.sub(r'(\?|&)preview=preview', '', html)
   
   # Process declarative URLs
   if self.getConfProperty('ZMS.pathhandler', 0):
     for x in html.split('href="./'):
       href = x[:x.find('"')]
       if href.endswith('.html'):
         href = href.split('/')
         new_href = []
         ob = self
         for ob_id in href[:-1]:
           if ob is not None:
             if ob_id == '..':
               ob = ob.getParentNode()
               if ob is not None:
                 new_href.append(ob_id)
             else:
               ob = getattr(ob, ob_id, None)
               if ob is not None:
                 new_href.append(ob.getDeclId(REQUEST))
         if ob is not None:
           new_href.append(href[-1])
           html = html.replace('"./%s"'%('/'.join(href)), '"./%s"'%('/'.join(new_href)))
     if self.getConfProperty('ZMS.export.pathhandler', 0):
       newTmp = '..\\'
       oldTmp = '../'
       # Save links to root.
       html = html.replace( oldTmp, newTmp)
       # Replace 'index' in declarative URLs
       pageexts = ['.html']
       if 'attr_pageext' in self.getObjAttrs().keys():
         obj_attr = self.getObjAttr('attr_pageext')
         if 'keys' in obj_attr and len(obj_attr.get('keys')) > 0:
           pageexts = obj_attr.get('keys')
       for pageext in pageexts:
         s_new = pageext
         s_old = '/index_%s%s'%(REQUEST['lang'], pageext)
         html = html.replace( s_old, s_new)
       # Restore links to root.
       html = html.replace( newTmp, oldTmp)
   
   return html


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
class Exportable(_filtermanager.FilterItem):

    # Create a SecurityInfo for this class. We will use this
    # in the rest of our class definition to make security
    # assertions.
    security = ClassSecurityInfo()


    ############################################################################
    #  Exportable.manage_export:
    #
    #  Exports ZMS-object.
    ############################################################################
    def manage_export(self, export_format, lang, REQUEST, RESPONSE):
      """ Exportable.manage_export """
      
      title = self.getHome().id + '_' + self.id_quote( self.getTitlealt( REQUEST))
      
      # Get export format.
      try:
        export_format = int( export_format)
      except:
        pass
      
      get_data = REQUEST.get( 'download', 1) == 1
      
      # ZEXP.
      if export_format == 0:
        filename = '%s.zexp'%self.id
        export = self.aq_parent.manage_exportObject( id=self.id, download=1)
        content_type = 'application/data'
      
      # HTML.
      elif export_format == 1:
        filename = '%s_html.zip'%title
        export = self.toZippedHtml( REQUEST, get_data)
        content_type = 'application/zip'
      
      # XML.
      elif export_format == 2: 
        filename = '%s_xml.zip'%title
        export = self.toZippedXml( REQUEST, get_data)
        content_type = 'application/zip'
      
      # myXML.
      elif export_format == 3: 
        instance_home = standard.getINSTANCE_HOME()
        package_home = standard.getPACKAGE_HOME()
        package_home = os.path.normpath(package_home)
        REQUEST.set( 'ZMS_FILTER_INSTANCE_HOME', instance_home)
        REQUEST.set( 'ZMS_FILTER_PACKAGE_HOME', package_home)
        filename = '%s.xml'%title
        export = self.getXmlHeader() + getattr( self, 'getObjToXml_DocElmnt')(context=self)
        content_type = 'text/xml'
      
      # Export Filter.
      elif export_format in self.getFilterManager().getFilterIds():
        if REQUEST.get('debug'):
          url = self.url_append_params( 'manage_importexportDebugFilter', { 'lang': lang, 'filterId': export_format, 'debug': 1})
          return RESPONSE.redirect( url)
        else:
          filename, export, content_type = _filtermanager.exportFilter(self, export_format, REQUEST)
      
      # return export for download to browser
      if get_data:
        RESPONSE.setHeader('Content-Type', content_type)
        RESPONSE.setHeader('Content-Disposition', 'inline;filename="%s"'%filename)
        return export
      else:
        message = 'Exported to %s (%s)'%(export, content_type)
        url = '%s/manage_importexport'%self.absolute_url()
        url = self.url_append_params( url, { 'lang': lang, 'manage_tabs_message': message})
        RESPONSE.redirect( url)


    # --------------------------------------------------------------------------
    #  Exportable.getObjToXml:
    #
    #  myXML
    # --------------------------------------------------------------------------
    def getObjToXml(self):
      xml = []
      method = getattr( self, 'getObjToXml_%s'%self.meta_id, None)
      if method is not None:
        xml.append( method( context=self))
      return ''.join(xml)


    # --------------------------------------------------------------------------
    #  Exportable.getObjChildrenToXml:
    #
    #  myXML
    # --------------------------------------------------------------------------
    def getObjChildrenToXml(self):
      REQUEST = self.REQUEST
      xml = []
      for context in self.filteredChildNodes(REQUEST):
        xml.append( context.getObjToXml())
      return ''.join(xml)


    # --------------------------------------------------------------------------
    #  Exportable.toXhtml:
    #
    #  (X)HTML
    # --------------------------------------------------------------------------
    def toXhtml(self, REQUEST, deep=True):
      standard.writeLog( self, '[toXhtml]')
      level = 0
      html = ''
      if 'ZMS_PAGE_HTML_HEADER' in REQUEST:
        html += getattr( self, REQUEST.get( 'ZMS_PAGE_HTML_HEADER'))( self, REQUEST)
      else:
        html += '<html>\n'
        html += '<head>\n'
        html += self.f_headMeta_Locale( self, REQUEST)
        html += '<title>%s</title>\n'%self.getTitle(REQUEST)
        html += '</head>\n'
        html += '<body>\n'
      print_html = self.printHtml( level, _globals.MySectionizer(), REQUEST, deep)
      try:
        html += print_html
      except:
        html += standard.writeError(self, "[toXhtml]: can't append printHtml")
      if 'ZMS_PAGE_HTML_FOOTER' in REQUEST:
        html += getattr( self, REQUEST.get( 'ZMS_PAGE_HTML_FOOTER'))( self, REQUEST)
      else:
        html += '</body>\n'
        html += '</html>\n'
      html = localHtml( self, html)
      html = localIndexHtml( self, self, level, html, xhtml=True)
      return html


    # --------------------------------------------------------------------------
    #  Exportable.toXml:
    # --------------------------------------------------------------------------
    def toXml(self, REQUEST, deep=True, data2hex=False):
      xml = ''
      xml += _xmllib.xml_header()
      xml += _xmllib.getObjToXml( self, REQUEST, deep, base_path='', data2hex=data2hex)
      return xml 


    # --------------------------------------------------------------------------
    #  Exportable.exportRessources:
    #
    #  Returns list of exported resources (Images, StyleSheets, etc.)
    # --------------------------------------------------------------------------
    def exportRessources(self, tempfolder, REQUEST, from_content=True, from_zms=False, from_home=False):
      ressources = []
      
      if from_zms:
        exportFiles( self, self.getDocumentElement(), 'metaobj_manager', '%s/metaobj_manager'%tempfolder)
      
      if from_home:
        root = self.getHome()
        exportFiles( self, root.aq_parent, root.id, tempfolder)
        for id in root.objectIds(['Folder']):
          exportFolder( self, root, tempfolder, id, REQUEST)
      
      if from_content:
        base_path = tempfolder+'/'
        ressources.extend( _blobfields.recurse_downloadRessources( self, base_path, REQUEST))
      
      return ressources


    # --------------------------------------------------------------------------
    #  Exportable.exportExternalResources
    # --------------------------------------------------------------------------
    def exportExternalResources(self, obj, html, path, REQUEST):
      domains = []
      for domain in self.getConfProperty('ZMS.export.domains', '').split(','):
        domain = domain.strip()
        if len( domain) > 0:
          domains.append( domain)
      if len( domains) == 0:
        return html
      for http_prefix in [ 'http:']:
        i = html.find( http_prefix)
        while i > 0:
          d = rfindDelimiter(html[:i]) # search delimiter ' or "
          k = rfindDelimiter(html[:d], '=') # search equal-sign between attribute name
          t = rfindDelimiter(html[:k], '<') # search start of tag
          # <img src="url">
          # <a href='url'">
          if (html[ t + 1: t + 4].lower() == 'img' and html[ k - 3: k].lower() == 'src') \
              or (html[ t + 1].lower() == 'a' and html[ k - 4: k].lower() == 'href'):
            l = findDelimiter(html[ d + 1:])
            url = html[ d + 1: d + l + 1]
            for domain in domains:
              if domain in url:
                try:
                  standard.writeLog( self, '[exportExternalResources]: url=%s'%url)
                  s_new = s_old = url
                  for repl in ':/%&?;=':
                    s_new = s_new.replace(repl, '_')
                  # test if extension is a real extension at the end ?
                  # http://host:port/uri.gif?a=x&b=k => http___host_port_uri.gif_a_x_b_k.gif
                  # http://host:port/uri.gif => http__host_port_uri.gif
                  # http://host:port/draw/ID/png => http__host_port_draw_ID_png.png
                  # http://host:port/draw/ID?fmt=pdf&scale=2 => http__host_port_draw_ID_fmt_pdf_scale_2.pdf
                  for ext in ['gif', 'jpg', 'png', 'pdf', 'csv', 'xls', 'doc', 'ppt']:
                    if ext in url:
                      if s_new[-len(ext)-1:] != '.%s' % ext:
                        s_new = "%s.%s" %(s_new, ext)
                      break
                  ext_path = '%s/%s'%( path, s_new)
                  if not os.path.exists( ext_path):
                    data = self.http_import( url)
                    f = open( ext_path, 'w')
                    f.write( data)
                    f.close()
                  html = html.replace( s_old, s_new)
                except:
                  standard.writeError( self, '[exportExternalResources]: url=%s'%url)
                break
          i = html.find( http_prefix, i + len( http_prefix))
      return html


    # --------------------------------------------------------------------------
    #  Exportable.recurse_downloadHtmlPages:
    # --------------------------------------------------------------------------
    def recurse_downloadHtmlPages(self, obj, path, lang, REQUEST):
      try:
        os.mkdir(path)
      except:
        pass
      
      level = obj.getLevel()
      key = 'index'
      REQUEST.set('ZMS_PATH_HANDLER', True)
      try:
        
        # Remember others.
        others = copy.copy(REQUEST.other.keys())
        
        root = getattr( obj, '__root__', None)
        if root is not None:
          REQUEST.set('ZMS_PROXY_%s'%root.id, obj)
          html = root.f_index_html( root, REQUEST)
        else:
          html = obj.f_index_html( obj, REQUEST)
        
        # Remove new others.
        for rk in REQUEST.other.keys():
          if rk not in others:
            try:
              del REQUEST.other[rk]
            except:
              pass
        
        # Blank lines in includes cause PHP session errors
        # @see http://bugs.php.net/bug.php?id=8974
        html = standard.re_sub(r'^\s*', '', html)
        
        # Localize html.
        html = localHtml( obj, html)
        
        # Save html to file.
        if level > 0 and \
           self.getConfProperty('ZMS.pathhandler', 0) != 0 and \
           self.getConfProperty('ZMS.export.pathhandler', 0) == 1:
          html = localIndexHtml( self, obj, level - 1, html)
          filename = '%s/../%s%s'%( path, obj.getDeclId(REQUEST), obj.getPageExt(REQUEST))
        else:
          pageext = obj.getPageExt( REQUEST)
          html = localIndexHtml( self, obj, level - self.getLevel(), html)
          filename = '%s/%s_%s%s'%( path, key, lang, pageext)
        
        html = self.exportExternalResources( obj, html, path, REQUEST)
        
        # @see http://docs.python.org/howto/unicode.html (Reading and Writing Unicode Data)
        encoding = REQUEST.get( 'ZMS_CHARSET', 'utf-8')
        mode = 'w'
        writeFile( obj, filename, html, mode, encoding)
        
        # Root folder requires and defaults to "index.html" at most systems.
        if lang == self.getPrimaryLanguage():
          filename = '%s/%s%s'%( path, key, obj.getPageExt( REQUEST))
          writeFile( obj, filename, html, mode, encoding)
      
      except:
        standard.writeError( obj, "[recurse_downloadHtmlPages]: Can't get html '%s'"%key)
      
      # Process methods of meta-objects.
      for metadictAttrId in self.getMetaobjAttrIds( obj.meta_id):
        try:
          metadictAttr = self.getMetaobjAttr( obj.meta_id, metadictAttrId)
          if metadictAttr is not None and metadictAttr['meta_type'] and metadictAttr['type'] in self.getMetaobjIds():
            metaObj = self.getMetaobj( metadictAttr['type'])
            if metaObj['type'] == 'ZMSResource':
              for metadictObj in obj.getObjChildren( metadictAttr['id'], REQUEST):
                for metaObjAttr in metaObj['attrs']:
                  if metaObjAttr['type'] in [ 'DTML Document', 'DTML Method', 'Page Template', 'Script (Python)']:
                    ob = getattr( obj, metaObjAttr['id'])
                    html = ob( obj, REQUEST)
                    html = localHtml( obj, html)
                    filename = '%s/%s'%( path, metaObjAttr['id'])
                    f = open(filename, 'w')
                    f.write(html)
                    f.close()
        except:
          standard.writeError( self, "[recurse_downloadHtmlPages]: can't process method '%s' of meta-object"%metadictAttr)
      
      # Process children.
      for child in obj.filteredChildNodes(REQUEST, self.PAGES):
        self.recurse_downloadHtmlPages(child, '%s/%s'%(path, child.getDeclId(REQUEST)), lang, REQUEST)


    # --------------------------------------------------------------------------
    #  Exportable.toZippedHtml:
    # --------------------------------------------------------------------------
    def toZippedHtml(self, REQUEST, get_data=True):
      REQUEST.set('ZMS_INDEX_HTML', 1)
      REQUEST.set('ZMS_HTML_EXPORT', 1)
      
      #-- Create temporary folder.
      tempfolder = tempfile.mktemp()
      ressources = self.exportRessources( tempfolder, REQUEST, from_zms=self.getLevel()==0, from_home=True)
      
      #-- Download HTML-pages.
      for lang in self.getLangIds():
        REQUEST.set('lang', lang)
        REQUEST.set('preview', None)
        self.recurse_downloadHtmlPages( self, tempfolder, lang, REQUEST)
      
      #-- Get zip-file.
      zipfiles = _fileutil.getOSPath('%s/*'%tempfolder)
      rtn = _fileutil.buildZipArchive( zipfiles, get_data)
      
      #-- Remove temporary folder.
      if not self.getConfProperty('ZMS.debug', 0):
        _fileutil.remove( tempfolder, deep=1)
      
      return rtn


    # --------------------------------------------------------------------------
    #  Exportable.toZippedXml:
    # --------------------------------------------------------------------------
    def toZippedXml(self, REQUEST, get_data=True):

      #-- Create temporary folder.
      tempfolder = tempfile.mktemp()
      ressources = self.exportRessources( tempfolder, REQUEST)
      
      #-- Get xml-export.
      xml = self.toXml(REQUEST)
      
      #-- Write xml-export to file.
      xmlfilename = os.path.join(tempfolder,'content.xml')
      _fileutil.exportObj(xml, xmlfilename)
      
      #-- Get zip-file.
      zipfiles = _fileutil.getOSPath('%s/*'%tempfolder)
      rtn = _fileutil.buildZipArchive( zipfiles, get_data)
      
      #-- Remove temporary folder.
      if not self.getConfProperty('ZMS.debug', 0):
        _fileutil.remove( tempfolder, deep=1)
      
      return rtn


# call this to initialize framework classes, which
# does the right thing with the security assertions.
InitializeClass(Exportable)

################################################################################
