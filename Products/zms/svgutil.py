################################################################################
# svglutil.py
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
from AccessControl.SecurityInfo import ModuleSecurityInfo
import six
import xml.dom.minidom

security = ModuleSecurityInfo('Products.zms.zmsutil')

security.declarePublic('get_svg_dimensions')
def get_dimensions(image):
    size = None
    if image.filename.endswith('.svg'):
        data = bytes(image.getData())
        xmldoc = xml.dom.minidom.parseString(data)
        for svg in xmldoc.getElementsByTagName('svg'):
            if 'height' in svg.attributes and 'width' in svg.attributes:
              w = int(float(svg.attributes['width'].value))
              h = int(float(svg.attributes['height'].value))
              size = (w,h)
              break
            elif 'viewBox' in svg.attributes:
              viewBox = svg.attributes['viewBox'].value
              viewBox = [int(float(x)) for x in viewBox.split(' ')]
              w = viewBox[2] - viewBox[0]
              h = viewBox[3] - viewBox[1]
              size = (w,h)
    return size

security.declarePublic('set_svg_dimensions')
def set_dimensions(image, size):
    svg_dim = get_dimensions(image)
    if svg_dim is not None:
        w = int(float(size[0]))
        h = int(float(size[1]))
        data = bytes(image.getData())
        xmldoc = xml.dom.minidom.parseString(data)
        for svg in xmldoc.getElementsByTagName('svg'):
            oldwidth = '<svg '
            newwidth = '<svg '
            oldheight = '<svg '
            newheight = '<svg '
            if 'width' in svg.attributes:
              oldwidth = 'width="%s"'%svg.attributes['width'].value
              newwidth = ''
            if 'height' in svg.attributes:
              oldheight = 'height="%s"'%svg.attributes['height'].value
              newheight = ''
            from Products.zms import standard
            data = data.replace(standard.six_ensure_binary(oldwidth),six.ensure_binary('%s width="%i" '%(newwidth,w)))
            data = data.replace(standard.six_ensure_binary(oldwidth),six.ensure_binary('%s height="%i" '%(newheight,h)))
        image.data = data
    return image

security.apply(globals())

################################################################################
