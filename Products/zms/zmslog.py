################################################################################
# zmslog.py
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
import copy
import logging
import os
import time
# Product Imports.
from Products.zms import standard
from Products.zms import ZMSItem
from Products.zms import _fileutil


def severity_string(severity, mapping={
    logging.DEBUG:   'DEBUG',
    logging.INFO:    'INFO',
    logging.ERROR:   'ERROR',
    }):
    """Convert a severity code to a string."""
    return mapping.get(int(severity), '')


def log_time():
  """Return a simple time string without spaces suitable for logging."""
  return ("%4.4d-%2.2d-%2.2dT%2.2d:%2.2d:%2.2d"
          % time.localtime()[:6])


################################################################################
###
###   Class
###
################################################################################
class ZMSLog(ZMSItem.ZMSItem):

    # Properties.
    # -----------
    meta_type = 'ZMSLog'
    zmi_icon = "fas fa-bug"
    icon_clazz = zmi_icon


    # Management Options.
    # -------------------
    def manage_options(self):
      return (
        { 'label': 'Settings','action': '../manage_customize'},
        )

    # Management Interface.
    # ---------------------
    manage_main = PageTemplateFile( 'zpt/ZMSLog/manage_main', globals())
    manage_remote = PageTemplateFile( 'zpt/ZMSLog/manage_remote', globals())

    LOGGER = logging.getLogger("ZMS")

    ############################################################################
    #  ZMSLog.__init__: 
    #
    #  Initialise a new instance of ZMSLog.
    ############################################################################
    def __init__(self, copy_to_stdout=False, logged_entries=[ 'ERROR']):
      self.id = 'zms_log'
      self.copy_to_stdout = copy_to_stdout
      self.logged_entries = logged_entries

    ############################################################################
    #  ZMSLog.setProperties: 
    #
    #  Set properties.
    ############################################################################
    def setProperties(self, REQUEST, RESPONSE): 
      """ ZMSLog.setProperties """
      self.tail_event_log_linesback = REQUEST.get('tail_event_log_linesback', 100)
      self.copy_to_stdout = 'copy_to_stdout' in REQUEST
      self.logged_entries = REQUEST.get( 'logged_entries', [])
      return RESPONSE.redirect( REQUEST[ 'HTTP_REFERER'])

    # --------------------------------------------------------------------------
    #  ZMSLog.hasSeverity:
    # --------------------------------------------------------------------------
    def hasSeverity(self, severity):
      return severity_string(severity) in self.logged_entries

    # --------------------------------------------------------------------------
    #  ZMSLog.LOG:
    # --------------------------------------------------------------------------
    def LOG(self, severity, info):
      log_severity = severity
      if log_severity == logging.DEBUG:
        log_severity = logging.INFO
      self.LOGGER.log( severity, info)
      if getattr( self, 'copy_to_stdout', True):
        standard.writeStdout(self, '%s %s(%i) %s'%(str(log_time()), severity_string(severity), int(severity), info))

    # --------------------------------------------------------------------------
    #  ZMSLog.getLOG:
    # --------------------------------------------------------------------------
    def getLOG(self, REQUEST, RESPONSE=None):
      """ ZMSLog.getLOG """
      filename = os.path.join(standard.getINSTANCE_HOME(),'var','log','event.log')
      RESPONSE.setHeader( 'Content-Type','text/plain')
      RESPONSE.setHeader( 'Content-Disposition','inline;filename="%s"'%_fileutil.extractFilename( filename))
      file = open( filename, 'r')
      rtn = file.read() 
      file.close()
      return rtn

    # --------------------------------------------------------------------------
    #  ZMSLog.tail_event_log:
    # --------------------------------------------------------------------------
    def tail_event_log(self, linesback=100, returnlist=True):
      filename = os.path.join(standard.getINSTANCE_HOME(),'var','log','event.log')
      return _fileutil.tail_lines(filename,linesback,returnlist)



    ############################################################################
    ###
    ###  Remote System
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSLog.getPath
    # --------------------------------------------------------------------------
    def getPath(self, REQUEST): 
      path = standard.getPACKAGE_HOME()
      if 'path' in REQUEST:
        path = REQUEST['path']
      path = path.strip()
      return path

    # --------------------------------------------------------------------------
    #  ZMSLog.readDir
    # --------------------------------------------------------------------------
    def readDir(self, path): 
      return _fileutil.readDir( path)

    # --------------------------------------------------------------------------
    #  ZMSLog.getParentDir
    # --------------------------------------------------------------------------
    def getParentDir(self, path): 
      return _fileutil.getFilePath( path)


    ############################################################################
    #  ZMSLog.manage_index_html: 
    #
    #  Display file.
    ############################################################################
    def manage_index_html(self, REQUEST, RESPONSE): 
      """ZMSLog.manage_index_html"""
      path = self.getPath( REQUEST)
      RESPONSE.setHeader( 'Content-Type', 'Unknown')
      RESPONSE.setHeader( 'Content-Disposition', 'inline;filename="%s"'%_fileutil.extractFilename( path))
      file = open( path, 'rb')
      rtn = file.read() 
      file.close()
      return rtn


    ############################################################################
    #  ZMSLog.manage_submit: 
    #
    #  Submit action.
    ############################################################################
    def manage_submit(self, REQUEST, RESPONSE): 
      """ZMSLog.manage_submit"""
      
      path = self.getPath(REQUEST)
      message = ""
      
      if REQUEST.get("btn") == "Execute":
        command = REQUEST['command']
        _fileutil.executeCommand(path, command)
        message = "Command executed."
        
      elif REQUEST.get("btn") == "Upload":
        obj = REQUEST['file']
        type = 'b'
        filename = "%s%s%s"%(path, os.sep, _fileutil.extractFilename(obj.filename))
        _fileutil.exportObj( obj, filename, type)
        message = "Upload complete."
      
      return REQUEST.RESPONSE.redirect( self.url_append_params( REQUEST[ 'HTTP_REFERER'], { 'manage_tabs_message' :message }))

################################################################################
