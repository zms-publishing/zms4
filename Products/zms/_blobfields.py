################################################################################
# _blobfields.py
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
from DateTime.DateTime import DateTime
from ZPublisher import HTTPRangeSupport, HTTPRequest
from OFS.Image import Image, File
# from mimetools import choose_boundary
from email.generator import _make_boundary as choose_boundary
import base64
import copy
import re
import six
import time
import warnings
import zExceptions 
# Product Imports.
from Products.zms import _fileutil
from Products.zms import _globals
from Products.zms import pilutil
from Products.zms import standard
from Products.zms import svgutil
from Products.zms import zopeutil

__all__= ['MyBlob', 'MyImage', 'MyFile']

# PY3 PATCH
def rfc1123_date():
 return 'ERROR rfc1123_date()'


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_blobfields.rfc1123_date:
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def rfc1123_date(dt):
  from wsgiref.handlers import format_date_time
  stamp = time.mktime(time.gmtime(dt))
  return format_date_time(stamp)


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_blobfields.recurse_downloadRessources:

Download from ZODB to file-system during Export.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def recurse_downloadRessources(self, base_path, REQUEST):
  ressources = []
  # Check Constraints.
  root = getattr( self, '__root__', None)
  if root is not None:
    return ressources
  # Attributes.
  langs = self.getLangIds()
  prim_lang = self.getPrimaryLanguage()
  obj_attrs = self.getObjAttrs()
  for key in obj_attrs:
    obj_attr = self.getObjAttr(key)
    datatype = obj_attr['datatype_key']
    if datatype in _globals.DT_BLOBS:
      for lang in langs:
        try:
          if obj_attr['multilang'] or lang==prim_lang or (obj_attr['multilang']==0 and lang!=prim_lang):
            req = {'lang':lang,'preview':'preview'}
            obj_vers = self.getObjVersion(req)
            blob = self._getObjAttrValue(obj_attr, obj_vers, lang)
            if blob is not None: 
              filename = blob.getFilename()
              filename = getLangFilename(self, filename, lang)
              filename = '%s%s'%(base_path, filename)
              filename = _fileutil.getOSPath(filename)
              _fileutil.exportObj(blob, filename)
              ressources.append( { 'filepath':filename, 'content_type':blob.getContentType()})
        except:
          standard.writeError(self, "[recurse_downloadRessources]: Can't export %s"%key)
    elif datatype == _globals.DT_LIST:
      for lang in langs:
        try:
          if obj_attr['multilang'] or lang==prim_lang or (obj_attr['multilang']==0 and lang!=prim_lang):
            req = {'lang':lang,'preview':'preview'}
            obj_vers = self.getObjVersion(req)
            v = self._getObjAttrValue(obj_attr, obj_vers, lang)
            i = 0
            for r in v:
              uu = []
              if isinstance(r, dict):
                for k in r:
                  u = r[k]
                  if isinstance(u, MyImage) or isinstance(u, MyFile):
                    uu.append( u)
              elif isinstance(r, MyImage) or isinstance(r, MyFile):
                uu.append( r)
              for u in uu:
                filename = u.getFilename()
                filename = getLangFilename(self, filename, lang)
                filename = '%s@%i/%s'%(base_path, i, filename)
                filename = _fileutil.getOSPath(filename)
                _fileutil.exportObj(u, filename)
                ressources.append( { 'filepath':filename, 'content_type':u.getContentType()})
              i = i + 1
        except:
          standard.writeError(self, "[recurse_downloadRessources]: Can't export %s"%key)
  # Process children.
  for child in self.getChildNodes():
    ressources.extend( recurse_downloadRessources( child, base_path+child.id+'/', REQUEST))
  # Return list of ressources.
  return ressources


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_blobfields.createBlobField:

Create blob-field of desired object-type and initialize it with given file.

IN:    clazz        [C{MyImage}|C{MyFile}]
        file        [ZPublisher.HTTPRequest.FileUpload|dictionary]
OUT:    blob        [MyImage|MyFile]
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def createBlobField(self, objtype, file=b''):
  if standard.is_bytes(file):
    blob = uploadBlobField( self, objtype, file)
  elif isinstance(file, dict):
    data = file.get( 'data', '')
    if standard.is_str(data):
      data = standard.pybytes(data,'utf-8')
      data = standard.PyBytesIO( data)
    blob = uploadBlobField( self, objtype, data, file.get('filename', ''))
    if file.get('content_type'):
      blob.content_type = file.get('content_type')
  else:
    blob = uploadBlobField( self, objtype, file, file.filename)
  return blob


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_blobfields.uploadBlobField
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def uploadBlobField(self, clazz, file=b'', filename=''):
  try:
    file = file.read()
  except:
    pass
  f = None
  if isinstance(file,six.string_types):
    f = re.findall('^data:(.*?);base64,([\s\S]*)$',file)
  if f:
    mt = f[0][0]
    file = base64.b64decode(f[0][1])
  else:
    mt, enc = standard.guess_content_type(filename,file)
  if clazz in [_globals.DT_IMAGE, 'image'] or mt.startswith('image'):
    clazz = MyImage
  elif clazz in [_globals.DT_FILE, 'file']:
    clazz = MyFile
  # blob = clazz( id='', title='', file='')
  blob = clazz( id='', title='', file=standard.pybytes('','utf-8'))
  blob.update_data(file, content_type=mt, size=len(file))
  blob.aq_parent = self
  blob.mediadbfile = None
  blob.filename = standard.pystr(_fileutil.extractFilename( filename, undoable=True))
  # Check size.
  if self is not None:
    maxlength_prop = 'ZMS.input.%s.maxlength'%['file','image'][isinstance(blob,MyImage)]
    maxlength = self.getConfProperty(maxlength_prop, '')
    if len(maxlength) > 0:
      size = blob.get_size()
      if size > int(maxlength):
        raise zExceptions.Forbidden('size=%i > %s=%i' %(size, maxlength_prop, int(maxlength)))
  return blob


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_blobfields.getLangFilename:
  
Returns filename concatenated with language suffix.
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def getLangFilename(self, filename, lang):
  i = filename.rfind('.')
  name = filename[:i]
  name = name.replace(' ', '_')
  ext = filename[i+1:]
  if len(self.getLangIds()) > 1 and lang is not None:
    suffix = '_' + lang
    if len(name) < len(suffix) or name[-len(suffix):] != suffix:
      name += suffix
  name += '.' + ext
  return name


################################################################################
###
###  THUMBNAILS
###
################################################################################

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_blobfields.thumbnailImageFields:

Process image-fields and shrink superres to hires and hires to lores. 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def thumbnailImageFields(self, lang, REQUEST):
  message = ''
  if pilutil.enabled():
    obj_attrs = self.getObjAttrs()
    for key in obj_attrs:
      obj_attr = self.getObjAttr(key)
      datatype = obj_attr['datatype_key']
      if datatype == _globals.DT_IMAGE:
        message += thumbnailImage(self, '%ssuperres'%key, '%shires'%key, self.getConfProperty('InstalledProducts.pil.hires.thumbnail.max'), lang, REQUEST)
        message += thumbnailImage(self, '%shires'%key, '%s'%key, self.getConfProperty('InstalledProducts.pil.thumbnail.max'), lang, REQUEST)
  return message


"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
_blobfields.thumbnailImage:

Process image-field and shrink attribute given by hiresKey to attribute given 
by loresKey. 
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
def thumbnailImage(self, hiresKey, loresKey, maxdim, lang, REQUEST):
  message = ''
  try:
    if hiresKey in self.getObjAttrs() and REQUEST.get('generate_preview_%s_%s'%(hiresKey,lang),0) == 1:
      pilutil.generate_preview(self, hiresKey, loresKey, maxdim)
  except:
    standard.writeError( self, '[thumbnailImage]')
  return message


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
class MyBlob(object):

    # Documentation string.
    __doc__ = """ZMS product module."""
    # Version string. 
    __version__ = '0.1' 

    __class_name__ = '{{MyBlob}}'
    
    def __str__(self):
      return self.__class_name__


    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
    #  <BO> Copied from OFS/Image.py:
    #  Modifications: self._p_mtime -> self.aq_parent._p_mtime
    # >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

    def _if_modified_since_request_handler(self, REQUEST, RESPONSE):
        # HTTP If-Modified-Since header handling: return True if
        # we can handle this request by returning a 304 response
        header=REQUEST.get_header('If-Modified-Since', None)
        if header is not None:
            header=header.split( ';')[0]
            # Some proxies seem to send invalid date strings for this
            # header. If the date string is not valid, we ignore it
            # rather than raise an error to be generally consistent
            # with common servers such as Apache (which can usually
            # understand the screwy date string as a lucky side effect
            # of the way they parse it).
            # This happens to be what RFC2616 tells us to do in the face of an
            # invalid date.
            try:    mod_since=int(DateTime(header).timeTime())
            except: mod_since=None
            if mod_since is not None:
                if self.aq_parent._p_mtime:
                    last_mod = int(self.aq_parent._p_mtime)
                else:
                    last_mod = int(0)
                if last_mod > 0 and last_mod <= mod_since:
                    RESPONSE.setHeader('Last-Modified',
                                       rfc1123_date(self.aq_parent._p_mtime))
                    RESPONSE.setHeader('Content-Type', self.content_type)
                    RESPONSE.setHeader('Accept-Ranges', 'bytes')
                    RESPONSE.setStatus(304)
                    return True

    def _range_request_handler(self, REQUEST, RESPONSE):
        # HTTP Range header handling: return True if we've served a range
        # chunk out of our data.
        range = REQUEST.get_header('Range', None)
        request_range = REQUEST.get_header('Request-Range', None)
        if request_range is not None:
            # Netscape 2 through 4 and MSIE 3 implement a draft version
            # Later on, we need to serve a different mime-type as well.
            range = request_range
        if_range = REQUEST.get_header('If-Range', None)
        if range is not None:
            ranges = HTTPRangeSupport.parseRange(range)
            
            if if_range is not None:
                # Only send ranges if the data isn't modified, otherwise send
                # the whole object. Support both ETags and Last-Modified dates!
                if len(if_range) > 1 and if_range[:2] == 'ts':
                    # ETag:
                    if if_range != self.http__etag():
                        # Modified, so send a normal response. We delete
                        # the ranges, which causes us to skip to the 200
                        # response.
                        ranges = None
                else:
                    # Date
                    date = if_range.split( ';')[0]
                    try: mod_since=int(DateTime(date).timeTime())
                    except: mod_since=None
                    if mod_since is not None:
                        if self.aq_parent._p_mtime:
                            last_mod = int(self.aq_parent._p_mtime)
                        else:
                            last_mod = int(0)
                        if last_mod > mod_since:
                            # Modified, so send a normal response. We delete
                            # the ranges, which causes us to skip to the 200
                            # response.
                            ranges = None

            if ranges:
                # Search for satisfiable ranges.
                satisfiable = 0
                for start, end in ranges:
                    if start < self.size:
                        satisfiable = 1
                        break

                if not satisfiable:
                    RESPONSE.setHeader('Content-Range',
                        'bytes */%d' % self.size)
                    RESPONSE.setHeader('Accept-Ranges', 'bytes')
                    RESPONSE.setHeader('Last-Modified',
                        rfc1123_date(self.aq_parent._p_mtime))
                    RESPONSE.setHeader('Content-Type', self.content_type)
                    RESPONSE.setHeader('Content-Length', self.size)
                    RESPONSE.setStatus(416)
                    return True

                ranges = HTTPRangeSupport.expandRanges(ranges, self.size)

                if len(ranges) == 1:
                    # Easy case, set extra header and return partial set.
                    start, end = ranges[0]
                    size = end - start

                    RESPONSE.setHeader('Last-Modified',
                        rfc1123_date(self.aq_parent._p_mtime))
                    RESPONSE.setHeader('Content-Type', self.content_type)
                    RESPONSE.setHeader('Content-Length', size)
                    RESPONSE.setHeader('Accept-Ranges', 'bytes')
                    RESPONSE.setHeader('Content-Range',
                        'bytes %d-%d/%d' % (start, end - 1, self.size))
                    RESPONSE.setStatus(206) # Partial content

                    data = self.data
                    if isinstance(data,six.string_types):
                        RESPONSE.write(data[start:end])
                        return True

                    # Linked Pdata objects. Urgh.
                    pos = 0
                    while data is not None:
                        l = len(data.data)
                        pos = pos + l
                        if pos > start:
                            # We are within the range
                            lstart = l - (pos - start)

                            if lstart < 0: lstart = 0

                            # find the endpoint
                            if end <= pos:
                                lend = l - (pos - end)

                                # Send and end transmission
                                RESPONSE.write(data[lstart:lend])
                                break

                            # Not yet at the end, transmit what we have.
                            RESPONSE.write(data[lstart:])

                        data = data.next

                    return True

                else:
                    boundary = choose_boundary()

                    # Calculate the content length
                    size = (8 + len(boundary) + # End marker length
                        len(ranges) * (         # Constant lenght per set
                            49 + len(boundary) + len(self.content_type) +
                            len('%d' % self.size)))
                    for start, end in ranges:
                        # Variable length per set
                        size = (size + len('%d%d' % (start, end - 1)) +
                            end - start)


                    # Some clients implement an earlier draft of the spec, they
                    # will only accept x-byteranges.
                    draftprefix = (request_range is not None) and 'x-' or ''

                    RESPONSE.setHeader('Content-Length', size)
                    RESPONSE.setHeader('Accept-Ranges', 'bytes')
                    RESPONSE.setHeader('Last-Modified',
                        rfc1123_date(self.aq_parent._p_mtime))
                    RESPONSE.setHeader('Content-Type',
                        'multipart/%sbyteranges; boundary=%s' % (
                            draftprefix, boundary))
                    RESPONSE.setStatus(206) # Partial content

                    data = self.data
                    # The Pdata map allows us to jump into the Pdata chain
                    # arbitrarily during out-of-order range searching.
                    pdata_map = {}
                    pdata_map[0] = data

                    for start, end in ranges:
                        RESPONSE.write('\r\n--%s\r\n' % boundary)
                        RESPONSE.write('Content-Type: %s\r\n' %
                            self.content_type)
                        RESPONSE.write(
                            'Content-Range: bytes %d-%d/%d\r\n\r\n' % (
                                start, end - 1, self.size))

                        if isinstance(data,six.string_types):
                            RESPONSE.write(data[start:end])

                        else:
                            # Yippee. Linked Pdata objects. The following
                            # calculations allow us to fast-forward through the
                            # Pdata chain without a lot of dereferencing if we
                            # did the work already.
                            first_size = len(pdata_map[0].data)
                            if start < first_size:
                                closest_pos = 0
                            else:
                                closest_pos = (
                                    ((start - first_size) >> 16 << 16) +
                                    first_size)
                            pos = min(closest_pos, max(pdata_map))
                            data = pdata_map[pos]

                            while data is not None:
                                l = len(data.data)
                                pos = pos + l
                                if pos > start:
                                    # We are within the range
                                    lstart = l - (pos - start)

                                    if lstart < 0: lstart = 0

                                    # find the endpoint
                                    if end <= pos:
                                        lend = l - (pos - end)

                                        # Send and loop to next range
                                        RESPONSE.write(data[lstart:lend])
                                        break

                                    # Not yet at the end, transmit what we have.
                                    RESPONSE.write(data[lstart:])

                                data = data.next
                                # Store a reference to a Pdata chain link so we
                                # don't have to deref during this request again.
                                pdata_map[pos] = data

                    # Do not keep the link references around.
                    del pdata_map

                    RESPONSE.write('\r\n--%s--\r\n' % boundary)
                    return True

    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<
    #  <EO> Copied from OFS/Image.py
    # <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.equals
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def equals(self, ob):
      """
      Indicates whether some other MyBlob-object is "equal to" this one.
      """
      b = ob is not None
      try:
        if b:
          attrs = self.__obj_attrs__
          for attr in attrs:
            if b and attr not in ['data', 'aq_parent']:
              b = b and getattr( self, attr) == getattr( ob, attr)
      except:
        b = False
      return b


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob._createCopy:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def _createCopy(self, aq_parent, key):
      value = self._getCopy()
      value.is_blob = True
      value.aq_parent = aq_parent
      value.key = key
      value.lang = aq_parent.REQUEST.get( 'lang')
      return value


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.__call__: 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __bobo_traverse__(self, TraversalRequest, name):
      return self


    __call____roles__ = None
    def __call__(self, REQUEST=None, **kw):
      """"""
      if REQUEST is not None and 'path_to_handle' in REQUEST:
        REQUEST['path_to_handle']=[]
        RESPONSE = REQUEST.RESPONSE
        parent = self.aq_parent
        
        access = parent.hasAccess( REQUEST) or parent.getConfProperty( 'ZMS.blobfields.grant_public_access', 0) == 1
        # Hook for custom access rules: return True/False, return 404 (Forbidden) if you want to perform redirect
        if access:
          # @deprecated
          # @TODO log deprecation warning
          try:
            name = 'hasCustomAccess'
            if hasattr(parent,name):
              v = zopeutil.callObject(getattr(parent,name),parent)
              if type( v) is bool:
                access = access and v
              elif type( v) is int and v == 404:
                return ''
          except:
            standard.writeError(parent,'[__call__]: can\'t %s'%name)
        # Raise unauthorized error.
        else:
          RESPONSE.setHeader('Expires', '-1')
          RESPONSE.setHeader('Cache-Control', 'no-cache')
          RESPONSE.setHeader('Pragma', 'no-cache')
          raise zExceptions.Unauthorized
        
        # Set custom response-headers:
        # - explicit Last-Modified
        # - explicit Content-Disposition and Content-Type
        # - addtional Content-Disposition via ZMS_ADDITIONAL_CONTENT_DISPOSITION
        try:
          name = 'getCustomBlobResponseHeaders'
          if hasattr(parent,name):
            zopeutil.callObject(getattr(parent,name),parent)
        except:
          standard.writeError(parent,'[__call__]: can\'t %s'%name)
        
        if not RESPONSE.getHeader('Last-Modified') and self._if_modified_since_request_handler(REQUEST, RESPONSE):
            # we were able to handle this by returning a 304 (not modified) 
            # unfortunately, because the HTTP cache manager uses the cache
            # API, and because 304 (not modified) responses are required to carry the Expires
            # header for HTTP/1.1, we need to call ZCacheable_set here.
            # This is nonsensical for caches other than the HTTP cache manager
            # unfortunately.
            self.ZCacheable_set(None)
            return ''
        
        if isinstance(self,MyImage) and self._range_request_handler(REQUEST, RESPONSE):
            # we served a chunk of content in response to a range request.
            return ''
        
        # If blob-object came from call of py-attribute by path-handler check content-disposition and content-type.
        if not (RESPONSE.getHeader('Content-Disposition') and RESPONSE.getHeader('Content-Type')):
          standard.set_response_headers(self.getFilename(),self.getContentType(),self.get_size(),REQUEST)
        if not (RESPONSE.getHeader('Last-Modified')):
          RESPONSE.setHeader('Last-Modified', rfc1123_date(parent._p_mtime))
        
        # Cacheable.
        cacheable = not REQUEST.get('preview') == 'preview'
        if cacheable: 
          cacheable = parent.hasPublicAccess()
        if not cacheable:
          RESPONSE.setHeader('Expires', '-1')
          RESPONSE.setHeader('Cache-Control', 'no-cache')
          # IE6 SSL Download bug:
          # http://support.microsoft.com/kb/812935/en-us
          # http://support.microsoft.com/kb/323308/en-us
          if not REQUEST.get('URL', '').startswith( 'https://'):
            RESPONSE.setHeader('Pragma', 'no-cache')
        
        if self.ZCacheable_isCachingEnabled():
            result = self.ZCacheable_get(default=None)
            if result is not None:
                # We will always get None from RAMCacheManager and HTTP
                # Accelerated Cache Manager but we will get
                # something implementing the IStreamIterator interface
                # from a "FileCacheManager"
                return result
        
        self.ZCacheable_set(None)
        
        mediadb = parent.getMediaDb()
        if mediadb is not None:
          mediadbfile = self.getMediadbfile()
          if mediadbfile is not None:
            return mediadb.retrieveFileStreamIterator( mediadbfile, REQUEST)
        
        RESPONSE.setBase(None)
        return self.getData()
        
      return self

    index_html=None


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.getObjAttrs:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getObjAttrs__roles__ = None
    def getObjAttrs(self, meta_type=None):
      return {}


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.getData:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getData__roles__ = None
    def getData(self, parent=None):
      """
      Returns data.
      """
      data = ''
      mediadbfile = self.getMediadbfile()
      if mediadbfile is not None:
        if parent is None:
          parent = self.aq_parent
        mediadb = parent.getMediaDb()
        if mediadb is not None:
          try:
            data = mediadb.retrieveFile( mediadbfile)
          except:
            standard.writeError( parent, "[getData]: can't retrieve file from mediadb: %s"%standard.pystr(mediadbfile))
      else:
        data = getattr(self, 'data', '')
      return data


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.getDataURI
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getDataURI__roles__ = None
    def getDataURI(self):
      dataURI = 'data:%s;base64,%s'%(self.getContentType(),base64.b64encode(self.getData()))
      return dataURI


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.getHref:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getHref__roles__ = None
    def getHref(self, REQUEST):
      """
      Returns absolute url.
      @var REQUEST: the triggering request
      @type REQUEST: ZPublisher.HTTPRequest
      """
      parent = self.aq_parent
      key = self.key
      rownum = ''
      i = key.find( ':')
      if i > 0:
        rownum = '/@%s'%key[ i+1:]
      filename = getLangFilename( parent, self.getFilename(), self.lang)
      filename = standard.url_encode( filename)
      qs = ''
      zms_version_key = 'ZMS_VERSION_%s'%parent.id
      if REQUEST.get( zms_version_key, None) is not None:
        qs = standard.qs_append( qs, zms_version_key, REQUEST.get( zms_version_key))
      elif standard.isPreviewRequest( REQUEST):
        qs = standard.qs_append( qs, 'preview', 'preview')
      base = '/'.join(parent.getPhysicalPath())
      href = base+rownum+'/'+filename+qs
      return href


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.on_setobjattr: 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def on_setobjattr(self):
      # store data in media-db.
      parent = self.aq_parent
      if parent is not None:
        mediadb = parent.getMediaDb()
        if mediadb is not None and getattr(self,'mediadbfile') is None:
          self.mediadbfile = mediadb.storeFile( self)
          self.data = ''
      # unset parent to avoid TypeError: Can't pickle objects in acquisition wrappers.
      self.aq_parent = None

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.getMediadbfile: 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getMediadbfile__roles__ = None
    def getMediadbfile(self):
      """
      Returns mediadb-filename.
      @rtype: C{string}
      """
      return getattr(self, 'mediadbfile', None)


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.getFilename: 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getFilename__roles__ = None
    def getFilename(self):
      """
      Returns filename.
      @rtype: C{string}
      """
      filename = self.filename
      if isinstance(filename,bytes):
        filename = filename.decode()
      while filename.startswith( '_'):
        filename = filename[1:]
      for ch in [ '+', '%', ' ', '!', '?', '#', '"', '(', ')', '&' ]:
        filename = filename.replace(ch, '')
      if filename != self.filename and len( self.data) > 0: 
        self.filename = filename
      return filename


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.get_size: 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    get_size__roles__ = None


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.get_real_size: 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    get_real_size__roles__ = None
    def get_real_size(self):
      """
      Returns real size in ZODB.
      @rtype: C{int}
      """
      if self.mediadbfile is None:
        return self.get_size()
      else:
        return len(self.mediadbfile)


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.getDataSizeStr:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getDataSizeStr__roles__ = None
    def getDataSizeStr(self):
      """
      Returns display string for file-size (KB).
      @rtype: C{string}
      @deprecated: Use standard.getDataSizeStr(len) instead!
      """
      warnings.warn('Using MyBlob.getDataSizeStr() is deprecated.'
                   ' Use standard.getDataSizeStr(len) instead.',
                     DeprecationWarning, 
                     stacklevel=2)
      return _fileutil.getDataSizeStr(self.get_size())


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.getContentType:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getContentType__roles__ = None
    def getContentType(self):
      """
      Returns MIME-type (e.g. image/gif, text/xml).
      @rtype: C{string}
      """
      return self.content_type


    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlob.getMimeTypeIconSrc:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getMimeTypeIconSrc__roles__ = None
    def getMimeTypeIconSrc(self):
      """
      Returns the absolute-url of an icon representing the MIME-type of this MyBlob-object.
      @rtype: C{string}
      @deprecated: Use zmscontext.getMimeTypeIconSrc(mt) instead!
      """
      from Products.zms import _mimetypes
      warnings.warn('Using MyBlob.getMimeTypeIconSrc() is deprecated.'
                   ' Use zmscontext.getMimeTypeIconSrc(mt) instead.',
                     DeprecationWarning, 
                     stacklevel=2)
      return '/++resource++zms_/img/' + _mimetypes.dctMimeType.get( self.getContentType(), _mimetypes.content_unknown)


################################################################################
################################################################################

class MyImage(MyBlob, Image):

    # Documentation string.
    __doc__ = """ZMS product module."""
    # Version string. 
    __version__ = '0.1' 
    

    __obj_attrs__  = ['content_type', 'size', 'data', 'filename', 'mediadbfile', 'width', 'height', 'aq_parent']
    __xml_attrs__  = ['content_type', 'width', 'height']


    def _getCopy(self):
      """
      Get copy of this blob.
      @return: the copy of this blob.
      @rtype: C{_blobfields.MyFile}
      """
      self.getFilename() # Normalize filename
      ob = self
      clone = MyImage(id='', title='', file=b'')
      attrs = self.__obj_attrs__
      for attr in attrs:
        if hasattr(ob, attr):
          setattr(clone, attr, getattr(ob, attr))
      return clone


    def toXml(self, sender=None, base_path='', data2hex=True):
      """
      Serialize this file to xml-string.
      @param sender: the sender-node
      @type sender: C{zmsobject.ZMSObject=None}
      @param base_path: the base-path
      @type base_path: C{str=''}
      @param data2hex: convert data inline to hex, otherwise saved to file in base-path
      @type data2hex: C{Bool=True}
      @return: the xml-string
      @rtype: C{str}
      """
      data = ''
      objtype = ''
      filename = _fileutil.getOSPath(_fileutil.extractFilename(getattr(self, 'filename', '')))
      content_type = getattr(self, 'content_type', '')
      if data2hex:
        if content_type.startswith('text/') or content_type in ['application/css','application/javascript','image/svg']:
          data = '<![CDATA[%s]]>'%standard.pystr(self.getData(sender),'utf-8')
        else:
          data = standard.bin2hex(standard.pybytes(self.getData(sender)))
        objtype = ' type="image"'
      else:
        filename = self.getFilename()
        filename = getLangFilename(sender, filename, self.lang)
        filename = '%s%s'%(base_path, filename)
      xml = '\n<data'
      xml += ' width="%s"'%standard.pystr(getattr(self, 'width', ''))
      xml += ' height="%s"'%standard.pystr(getattr(self, 'height', ''))
      xml += ' content_type="%s"'%content_type
      xml += ' filename="%s"'%filename
      xml += objtype + '>' + data
      xml += '</data>'
      return xml


    getWidth__roles__ = None
    def getWidth(self):
      """
      Get width of this image.
      @return: the width of this image.
      @rtype: C{int}
      """
      w = self.width
      if not w:
          try:
            size = svgutil.get_dimensions(self)
            if size is not None:
              self.width = int(size[0])
              self.height = int(size[1])
            w = self.width
          except:
            standard.writeError(self.aq_parent,'can\'t geWidth')
      if not w:
        w = self.aq_parent.getConfProperty('ZMS.image.default.width', 640)
      return w


    getHeight__roles__ = None
    def getHeight(self):
      """
      Get height of this image.
      @return: the height of this image.
      @rtype: C{int}
      """
      h = self.height
      if not h:
          try:
            size = svgutil.get_dimensions(self)
            if size is not None:
              self.width = int(size[0])
              self.height = int(size[1])
            h = self.height
          except:
            standard.writeError(self.aq_parent,'can\'t getHeight')
      if not h:
        h = self.aq_parent.getConfProperty('ZMS.image.default.height', 400)
      return h


################################################################################
################################################################################

class MyFile(MyBlob, File):

    # Documentation string.
    __doc__ = """ZMS product module."""
    # Version string. 
    __version__ = '0.1' 


    __obj_attrs__  = ['content_type', 'size', 'data', 'filename', 'mediadbfile', 'aq_parent']
    __xml_attrs__  = ['content_type']
    __class_name__ = '{{MyFile}}'

    def _getCopy(self):
      """
      Get copy of this blob.
      @return: the copy of this blob.
      @rtype: C{_blobfields.MyFile}
      """
      self.getFilename() # Normalize filename
      ob = self
      clone = MyFile(id='', title='', file=b'')
      attrs = self.__obj_attrs__
      for attr in attrs:
        if hasattr(ob, attr):
          setattr(clone, attr, getattr(ob, attr))
      return clone


    def toXml(self, sender=None, base_path='', data2hex=True):
      """
      Serialize this file to xml-string.
      @param sender: the sender-node
      @type sender: C{zmsobject.ZMSObject=None}
      @param base_path: the base-path
      @type base_path: C{str=''}
      @param data2hex: convert data inline to hex, otherwise saved to file in base-path
      @type data2hex: C{Bool=True}
      @return: the xml-string
      @rtype: C{str}
      """
      data = ''
      objtype = ''
      filename = _fileutil.getOSPath(_fileutil.extractFilename(getattr(self, 'filename', '')))
      content_type = getattr(self, 'content_type', '')
      if data2hex:
        if content_type.startswith('text/') or content_type in ['application/css','application/javascript','image/svg']:
          data = '<![CDATA[%s]]>'%standard.pystr(self.getData(sender),'utf-8')
        else:
          data = standard.bin2hex(standard.pybytes(self.getData(sender)))
        objtype = ' type="file"'
      else:
        filename = self.getFilename()
        filename = getLangFilename(sender, filename, self.lang)
        filename = '%s%s'%(base_path, filename)
      xml = '\n<data'
      xml += ' content_type="%s"'%content_type
      xml += ' filename="%s"'%filename
      xml += objtype + '>' + data
      xml += '</data>'
      return xml


################################################################################
################################################################################

class MyBlobWrapper(object):

    # Documentation string.
    __doc__ = """ZMS product module."""
    # Version string. 
    __version__ = '0.1' 

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlobWrapper.__init__:
    
    Constructor
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    def __init__(self, f):
      self.f = f

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlobWrapper.getHref:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getHref__roles__ = None
    def getHref(self, REQUEST):
      return self.f.absolute_url()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlobWrapper.getFilename: 
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getFilename__roles__ = None
    def getFilename(self):
      return self.f.getId()

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlobWrapper.getData:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getData__roles__ = None
    def getData(self, parent=None):
      return self.f.data

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlobWrapper.getDataURI:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    getDataURI__roles__ = None
    def getDataURI(self):
      dataURI = 'data:%s;base64,%s'%(self.getContentType(),base64.b64encode(self.getData()))
      return dataURI

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    MyBlobWrapper.__str__:
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
    __str____roles__ = None
    def __str__(self):
      return standard.pybytes(self.getData())

################################################################################