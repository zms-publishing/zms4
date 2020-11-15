################################################################################
# _mimetypes.py
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


""" Globals. """

application_epub = "mime_type.application_epub+zip.gif"
application_docx = "mime_type.application_docx.png"
application_octet_stream = "mime_type.application_octet_stream.gif"
application_pdf = "mime_type.application_pdf.gif"
application_rtf = "mime_type.application_rtf.gif"
application_sh = "mime_type.application_sh.gif"
application_x_director = "mime_type.application_x_director.gif"
application_x_x509_ca_cert = "mime_type.application_x_x509_ca_cert.gif"
application_visio = "mime_type.application_visio.gif"
application_zip = "mime_type.application_zip.gif"
application_pptx = "mime_type.application_pptx.png"
application_xlsx = "mime_type.application_xlsx.png"
audio_basic = "mime_type.audio_basic.gif"
audio_midi = "mime_type.audio_midi.gif"
content_unknown = "mime_type.application_octet_stream.gif"
image_basic = "mime_type.image_basic.gif"
image_gif = "mime_type.image_gif.gif"
image_jpeg = "mime_type.image_jpeg.gif"
image_tiff = "mime_type.image_tiff.gif"
text_html = "mime_type.text_html.gif"
text_plain = "mime_type.text_plain.gif"
text_xml = "mime_type.text_xml.gif"
text_xsd = "mime_type.text_xsd.gif"
text_xsl = "mime_type.text_xsl.gif"
video_basic = "mime_type.video_basic.gif"

dctMimeType = {
   'application/epub+zip':application_epub
  ,'application/mspowerpoint':application_pptx
  ,'application/vnd.ms-excel':application_xlsx
  ,'application/vnd.ms-powerpoint':application_pptx
  ,'application/vnd.openxmlformats-officedocument.wordprocessingml.document':application_docx
  ,'application/vnd.openxmlformats-officedocument.presentationml.presentation':application_pptx
  ,'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':application_xlsx
  ,'application/msword':application_docx
  ,'application/octet-stream':application_octet_stream
  ,'application/pdf':application_pdf
  ,'application/rtf':application_rtf
  ,'application/vnd.visio':application_visio
  ,'application/x-director':application_x_director
  ,'application/x-excel':application_xlsx
  ,'application/x-gtar':application_zip
  ,'application/x-gzip':application_zip
  ,'application/x-pdf':application_pdf
  ,'application/x-sh':application_sh
  ,'application/x-tar':application_zip
  ,'application/x-unknown-content-type-Visio.Drawing.4':application_visio
  ,'application/x-x509-ca-cert':application_x_x509_ca_cert
  ,'application/x-zip-compressed':application_zip
  ,'application/zip':application_zip
  ,'audio/basic':audio_basic
  ,'audio/echospeech':audio_basic
  ,'audio/midi':audio_midi
  ,'audio/mpeg':audio_basic
  ,'audio/tsplayer':audio_basic
  ,'audio/voxware':audio_basic
  ,'audio/x-aiff':audio_basic
  ,'audio/x-bamba':audio_basic
  ,'audio/x-chacha':audio_basic
  ,'audio/x-mio':audio_basic
  ,'audio/x-pn-realaudio':audio_basic
  ,'audio/x-pn-realaudio-plugin':audio_basic
  ,'audio/x-twinvq':audio_basic
  ,'audio/x-twinvq-plugin':audio_basic
  ,'audio/x-wav':audio_basic
  ,'image/fif':image_basic
  ,'image/gif':image_gif
  ,'image/ief':image_basic
  ,'image/jpeg':image_jpeg
  ,'image/pjpeg':image_jpeg
  ,'image/png':image_basic
  ,'image/tiff':image_tiff
  ,'image/vasa':image_basic
  ,'image/x-cmu-raster':image_basic
  ,'image/x-freehand':image_basic
  ,'image/x-jps':image_basic
  ,'image/x-portable-anymap':image_basic
  ,'image/x-portable-bitmap':image_basic
  ,'image/x-portable-graymap':image_basic
  ,'image/x-portable-pixmap':image_basic
  ,'image/x-rgb':image_basic
  ,'image/x-xbitmap':image_basic
  ,'image/x-xpixmap':image_basic
  ,'image/x-xres':image_basic
  ,'image/x-xwindowdump':image_basic
  ,'text/html':text_html
  ,'text/plain':text_plain
  ,'text/richtext':application_rtf
  ,'text/tab-separated-values':text_plain
  ,'text/xml':text_xml
  ,'text/xsd':text_xsd
  ,'text/xsl':text_xsl
  ,'text/x-setext':text_plain
  ,'text/x-sgml':text_plain
  ,'text/x-speech':text_plain
  ,'text/x-vcard':text_plain
  ,'video/mpeg':video_basic
  ,'video/quicktime':video_basic
  ,'video/vnd.vivo':video_basic
  ,'video/x-bamba':video_basic
  ,'video/x-msvideo':video_basic
  ,'video/x-sgi-movie':video_basic
  ,'video/x-tango':video_basic
  ,'video/x-vif':video_basic
  }

################################################################################
