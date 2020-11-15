################################################################################
# _filtermanager.py
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
from Products.ExternalMethod import ExternalMethod
from Products.PageTemplates import ZopePageTemplate
from Products.PythonScripts import PythonScript
import ZPublisher.HTTPRequest
import copy
import os
import tempfile
import zExceptions
# Product Imports.
from Products.zms import _blobfields
from Products.zms import _fileutil
from Products.zms import standard
from Products.zms import zopeutil


"""
################################################################################
#
#   I M / E X P O R T
#
################################################################################
"""

# ------------------------------------------------------------------------------
#  _filtermanager.processData:
#
#  Process data with custom transformation.
# ------------------------------------------------------------------------------
def processData(self, processId, data, trans=None):
  # Create temporary folder.
  folder = tempfile.mktemp()
  # Save data to file.
  filename = _fileutil.getOSPath('%s/in.dat'%folder)
  _fileutil.exportObj(data, filename)
  # Save transformation to file.
  if trans:
    transfilename = _fileutil.getOSPath('%s/%s'%(folder, trans.getId()))
    _fileutil.exportObj(trans, transfilename)
  # Process file.
  filename = processFile(self, processId, filename, trans)
  # Read data from file.
  f = open(filename, 'rb')
  data = f.read()
  f.close()
  # Remove temporary folder.
  if not self.getConfProperty('ZMS.debug', 0):
    _fileutil.remove(folder, deep=1)
  # Return data.
  return data


# ------------------------------------------------------------------------------
#  _filtermanager.processMethod:
#
#  Process DTML method.
# ------------------------------------------------------------------------------
def processMethod(self, processId, filename, trans, REQUEST):
  standard.writeLog( self, '[processMethod]: processId=%s'%processId)
  infilename = filename
  outfilename = filename
  REQUEST.set( 'ZMS_FILTER_IN', infilename)
  REQUEST.set( 'ZMS_FILTER_OUT', outfilename)
  REQUEST.set( 'ZMS_FILTER_TRANS', trans)
  REQUEST.set( 'ZMS_FILTER_CUR_DIR', _fileutil.getFilePath(infilename))
  try:
    value = getattr( self, processId)( self, REQUEST)
  except:
    value = standard.writeError( self, '[processMethod]: processId=%s'%processId)
  outfilename = REQUEST.get( 'ZMS_FILTER_OUT')
  # Return filename.
  return outfilename


# ------------------------------------------------------------------------------
#  _filtermanager.processCommand:
#
#  Process file with command.
# ------------------------------------------------------------------------------
def processCommand(self, filename, command):
  standard.writeLog( self, '[processCommand]: infilename=%s'%filename)
  infilename = _fileutil.getOSPath( filename)
  outfilename = _fileutil.getOSPath( filename)
  mCurDir = '{cur_dir}'
  mIn = '{in}'
  mOut = '{out}'
  i = command.find(mOut[:-1])
  if i >= 0:
    j = command.find('}', i)
    mExt = command[i+len(mOut[:-1]):j]
    mOut = command[i:j+1]
    if len(mExt) > 0:
      outfilename = outfilename[:outfilename.rfind('.')] + mExt
    else:
      outfilename += '.tmp'
  tmpoutfilename = outfilename + '~'
  instance_home = standard.getINSTANCE_HOME()
  package_home = standard.getPACKAGE_HOME()
  package_home = os.path.normpath(package_home)
  command = command.replace( '{package_home}', package_home)
  command = command.replace( '{instance_home}', instance_home)
  command = command.replace( mCurDir, _fileutil.getFilePath(infilename))
  command = command.replace( mIn, infilename)
  command = command.replace( mOut, tmpoutfilename)
  # Change directory (deprecated!).
  if self.getConfProperty('ZMS.filtermanager.processCommand.chdir', 0):
    path = _fileutil.getFilePath(filename)
    standard.writeLog( self, '[processCommand]: path=%s'%path)
    os.chdir(path)
  # Execute command.
  standard.writeLog( self, '[processCommand]: command=%s'%command)
  os.system(command)
  # Check if output file exists.
  try: 
    os.stat( _fileutil.getOSPath( tmpoutfilename)) 
    standard.writeLog( self, '[processCommand]: rename %s to %s'%( tmpoutfilename, outfilename))
    try:
      os.remove( outfilename)
    except OSError:
      pass
    os.rename( tmpoutfilename, outfilename)
  except OSError:
    outfilename = infilename
  # Remove input file if it is the result of a transformation of output file.
  if outfilename != infilename:
    os.remove( infilename)
  # Return filename.
  standard.writeLog( self, '[processCommand]: outfilename=%s'%( outfilename))
  return outfilename


# ------------------------------------------------------------------------------
#  _filtermanager.processFile:
#
#  Process file with custom transformation.
# ------------------------------------------------------------------------------
def processFile(self, processId, filename, trans=None):
  standard.writeLog( self, '[processFile]: processId=%s'%processId)
  folder = _fileutil.getFilePath(filename)
  processOb = self.getFilterManager().getProcess(processId)
  command = processOb.get('command')
  # Save transformation to file.
  if trans:
    transfilename = '%s/%s'%( folder, trans.getId())
    command = command.replace( '{trans}', transfilename)
  # Execute command.
  filename = processCommand(self, filename, command)
  # Return filename.
  return filename


# ------------------------------------------------------------------------------
#  _filtermanager.processFilter:
#
#  Process filter.
# ------------------------------------------------------------------------------
def processFilter(self, ob_filter, folder, filename, REQUEST):
  for ob_process in self.getFilterManager().getFilterProcesses(ob_filter['id']):
    filename = self.execProcessFilter( ob_process, folder, filename, REQUEST)
  # Return filename.
  return filename


# ------------------------------------------------------------------------------
#  _filtermanager.importFilter:
# ------------------------------------------------------------------------------
def importFilter(self, filename, id, REQUEST):
  ob_filter = self.getFilterManager().getFilter(id)
  folder = _fileutil.getFilePath(filename)
  # Process filter.
  filename = processFilter(self, ob_filter, folder, filename, REQUEST)
  # Return filename.
  return filename


# ------------------------------------------------------------------------------
#  _filtermanager.exportFilter:
# ------------------------------------------------------------------------------
def exportFilter(self, id, REQUEST):
  # Set local variables.
  ob_filter = self.getFilterManager().getFilter(id)
  tempfolder, outfilename = self.initExportFilter( id, REQUEST)
  # Process filter.
  outfilename = processFilter(self, ob_filter, tempfolder, outfilename, REQUEST)
  # Return values.
  content_type = ob_filter.get('content_type', 'content/unknown')
  filename = 'exportFilter.%s'%content_type[content_type.find('/')+1:]
  # Zip File.
  if content_type == 'application/zip':
    data = _fileutil.buildZipArchive( outfilename, get_data=True)
  # Read File.
  else:
    standard.writeLog( self, '[exportFilter]: Read %s'%outfilename)
    f = open(outfilename, 'rb')
    data = f.read()
    f.close()
  # Remove temporary folder.
  if not self.getConfProperty('ZMS.debug', 0):
    _fileutil.remove( tempfolder, deep=1)
  # Return.
  return filename, data, content_type


################################################################################
################################################################################
###
###   class FilterItem
###
################################################################################
################################################################################
class FilterItem(object):

    # --------------------------------------------------------------------------
    #  FilterItem.initExportFilter:
    # --------------------------------------------------------------------------
    def initExportFilter(self, id, REQUEST):
      # Set environment variables.
      instance_home = standard.getINSTANCE_HOME()
      package_home = standard.getPACKAGE_HOME()
      package_home = os.path.normpath(package_home)
      REQUEST.set( 'ZMS_FILTER', True)
      REQUEST.set( 'ZMS_FILTER_INSTANCE_HOME', instance_home)
      REQUEST.set( 'ZMS_FILTER_PACKAGE_HOME', package_home)
      # Set local variables.
      ob_filter = self.getFilterManager().getFilter(id)
      ob_filter_format = ob_filter.get('format', '')
      # Create temporary folder.
      tempfolder = tempfile.mktemp()
      ressources = self.exportRessources( tempfolder, REQUEST, from_zms=ob_filter_format=='XHTML', from_home=ob_filter_format=='XHTML')
      # Export data to file.
      if ob_filter_format == 'export':
        outfilename = _fileutil.getOSPath('%s/INDEX0'%tempfolder)
      elif ob_filter_format in ['XML', 'XML_incl_embedded']:
        # Set XML.
        data = self.toXml( REQUEST)
        outfilename = _fileutil.getOSPath('%s/export.xml'%tempfolder)
        _fileutil.exportObj( data, outfilename)
      elif ob_filter_format == 'XHTML':
        # Set XHTML.
        data = self.toXhtml( REQUEST)
        outfilename = _fileutil.getOSPath('%s/export.html'%tempfolder)
        _fileutil.exportObj( data, outfilename)
      elif ob_filter_format == 'myXML':
        # Set myXML.
        data = self.getXmlHeader() + getattr( self, 'getObjToXml_DocElmnt')(context=self)
        outfilename = _fileutil.getOSPath('%s/export.xml'%tempfolder)
        _fileutil.exportObj( data, outfilename)
      else:
        raise zExceptions.InternalError("Unknown format '%s'"%ob_filter.get('format', ''))
      return tempfolder, outfilename


    # --------------------------------------------------------------------------
    #  FilterItem.execProcessFilter:
    # --------------------------------------------------------------------------
    def execProcessFilter(self, ob_process, folder, filename, REQUEST):
      processId = ob_process.get( 'id')
      processOb = self.getFilterManager().getProcess(processId)
      if processOb is not None:
        processType = processOb.get( 'type', 'process')
        trans = ob_process.get('file')
        # Save transformation to file.
        if trans:
          transfilename = '%s/%s'%(folder,trans.getId())
          _fileutil.exportObj( trans, transfilename)
        if processType in [ 'DTML Method', 'External Method', 'Script (Python)']:
          filename = processMethod(self, processId, filename, trans, REQUEST)
        else:
          filename = processFile(self, processId, filename, trans)
      # Return filename.
      return filename

################################################################################
