################################################################################
# _accessmanager.py
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
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from OFS.userfolder import UserFolder
import copy
import six
import pickle
import re
import sys
import time
import zExceptions
# Product Imports.
from Products.zms import _confmanager
from Products.zms import _globals
from Products.zms import _xmllib
from Products.zms import standard


# ------------------------------------------------------------------------------
#  _accessmanager.updateVersion:
# ------------------------------------------------------------------------------
def updateVersion(root):
  if not root.REQUEST.get('_accessmanager_updateVersion', False):
    root.REQUEST.set('_accessmanager_updateVersion', True)
    if root.getConfProperty('ZMS.security.build', 0) == 0:
      root.setConfProperty('ZMS.security.build', 1)
      userDefs = {} 
      def visit(docelmnt):
        d = docelmnt.getConfProperty('ZMS.security.users', {})
        for name in d:
          value = d[name]
          userDef = userDefs.get(name)
          if userDef is None:
            userDef = {'nodes':{}}
            for key in value:
              if key not in userDef:
                userDef[key] = value[key]
          nodes = value.get('nodes', {})
          for nodekey in nodes:
            node = docelmnt.getLinkObj(nodekey)
            if node is not None:
              newkey = root.getRefObjPath(node)
              userDef['nodes'][newkey] = nodes[nodekey]
          userDefs[name] = userDef
        docelmnt.delConfProperty('ZMS.security.users')
        for client in docelmnt.getPortalClients():
          visit(client)
      visit(root)
      root.setConfProperty('ZMS.security.users', userDefs)
    # centralize ZMS.security.roles
    if root.getConfProperty('ZMS.security.build', 0) == 1:
      root.setConfProperty('ZMS.security.build', 2)
      roleDefs = {}
      def visit(docelmnt):
        d = docelmnt.getConfProperty('ZMS.security.roles', {})
        for name in d:
          value = d[name]
          roleDef = roleDefs.get(name, {})
          for nodekey in value:
            node = docelmnt.getLinkObj(nodekey)
            if node is not None:
              newkey = root.getRefObjPath(node)
              roleDef[newkey] = value[nodekey]
          roleDefs[name] = roleDef
        docelmnt.delConfProperty('ZMS.security.roles')
        for client in docelmnt.getPortalClients():
          visit(client)
      visit(root)
      root.setConfProperty('ZMS.security.roles', roleDefs)
    # centralize ZMS.security.roles
    if root.getConfProperty('ZMS.security.build', 0) == 2:
      root.setConfProperty('ZMS.security.build', 3)
      d = root.getConfProperty('ZMS.security.roles', {})
      for name in d:
        value = d[name]
        newvalue = {'nodes':{}}
        for nodekey in value:
          node = root.getLinkObj(nodekey)
          if node is not None:
            newvalue['nodes'][nodekey] = {'home_id':node.getHome().id,'roles':value[nodekey].get('roles', [])}
        d[name] = newvalue
      root.setConfProperty('ZMS.security.roles', d)
      d = root.getConfProperty('ZMS.security.users', {})
      for name in d:
        value = d[name]
        nodes = value.get('nodes', {})
        for nodekey in nodes:
          node = root.getLinkObj(nodekey)
          if node is not None:
            nodes[nodekey]['home_id'] = node.getHome().id
          else:
           del nodes[nodekey]
      root.setConfProperty('ZMS.security.users', d)

# ------------------------------------------------------------------------------
#  _accessmanager.user_folder_meta_types:
#
#  User Folder Meta-Types.
# ------------------------------------------------------------------------------
user_folder_meta_types = ['LDAPUserFolder', 'User Folder', 'Simple User Folder', 'Pluggable Auth Service']

# ------------------------------------------------------------------------------
#  _accessmanager.role_defs:
#
#  Role Definitions.
# ------------------------------------------------------------------------------
role_defs = {
   'ZMSAdministrator':['*']
  ,'ZMSEditor':['Access contents information', 'Add ZMSs', 'Add Documents, Images, and Files', 'Copy or Move', 'Delete objects', 'Manage properties', 'Use Database Methods', 'View', 'ZMS Author']
  ,'ZMSAuthor':['Access contents information', 'Add ZMSs', 'Copy or Move', 'Delete objects', 'Use Database Methods', 'View', 'ZMS Author']
  ,'ZMSSubscriber':['Access contents information', 'View']
  ,'ZMSUserAdministrator':['Access contents information', 'View', 'ZMS UserAdministrator']
}

# ------------------------------------------------------------------------------
#  _accessmanager.getUserId:
# ------------------------------------------------------------------------------
def getUserId(user):
  if isinstance(user, dict):
    user = user['name']
  elif user is not None and not isinstance(user,str):
    user = user.getId()
  return user

# ------------------------------------------------------------------------------
#  _accessmanager.updateUserPassword:
# ------------------------------------------------------------------------------
def updateUserPassword(self, user, password, confirm):
  if password!='******':
    if password != confirm:
      raise zExceptions.InternalError("Passwort <> Confirm")
    userFldr = user['localUserFldr']
    id = user['user_id_']
    if userFldr.meta_type == 'User Folder':
      roles = userFldr.getUser(id).getRoles()
      domains = userFldr.getUser(id).getDomains()
      userFldr.userFolderEditUser(id, password, roles, domains)
    elif userFldr.meta_type == 'Pluggable Auth Service' and user['plugin'].meta_type == 'ZODB User Manager':
      user['plugin'].updateUserPassword(id, password)
    return True
  return False

# ------------------------------------------------------------------------------
#  _accessmanager.addRole:
# ------------------------------------------------------------------------------
def addRole(self, id):
  #-- Add local role.
  root = self.getRootElement()
  home = root.getHome()
  if id not in home.valid_roles():
    home._addRole(role=id, REQUEST=self.REQUEST)
  #-- Prepare nodes from config-properties.
  security_roles = root.getConfProperty('ZMS.security.roles', {})
  security_roles[id] = security_roles.get(id, {'nodes':{}})
  root.setConfProperty('ZMS.security.roles', security_roles)

# ------------------------------------------------------------------------------
#  _accessmanager.setLocalRoles:
# ------------------------------------------------------------------------------
def setLocalRoles(self, id, roles=[]):
  filtered_roles = [x for x in roles if x in self.valid_roles()]
  if len(filtered_roles) > 0:
    self.manage_setLocalRoles(id, filtered_roles)
  if self.meta_type == 'ZMS':
    home = self.aq_parent
    setLocalRoles(home, id, roles)

# ------------------------------------------------------------------------------
#  _accessmanager.delLocalRoles:
# ------------------------------------------------------------------------------
def delLocalRoles(self, id):
  self.manage_delLocalRoles(userids=[id])
  if self.meta_type == 'ZMS':
    home = self.aq_parent
    delLocalRoles(home, id)

# ------------------------------------------------------------------------------
#  _accessmanager.deleteUser:
# ------------------------------------------------------------------------------
def deleteUser(self, id):
  
  # Delete local roles in node.
  nodes = self.getUserAttr(id, 'nodes', {})
  for node in nodes:
    ob = self.getLinkObj(node)
    if ob is not None:
      user_id = self.getUserAttr(id, 'user_id_', id)
      delLocalRoles(ob, user_id)
  
  # Delete user from ZMS dictionary.
  self.delUserAttr(id)

# ------------------------------------------------------------------------------
#  _accessmanager.UserFolderIAddUserPluginWrapper:
# ------------------------------------------------------------------------------
class UserFolderIAddUserPluginWrapper(object):

  def __init__(self, userFldr):
    self.userFldr = userFldr
    self.id = userFldr.id
    self.meta_type = userFldr.meta_type
    self.zmi_icon = getattr(userFldr,'zmi_icon','fas fa-users')

  absolute_url__roles__ = None
  def absolute_url( self):
    return self.userFldr.absolute_url()
  
  def doAddUser( self, login, password ):
    roles =  []
    domains =  []
    self.userFldr.userFolderAddUser(login, password, roles, domains)
  
  def removeUser( self, login):
    self.userFldr.userFolderDelUsers([login])


################################################################################
################################################################################
###
###   Class AccessableObject
###
################################################################################
################################################################################
class AccessableObject(object): 

    # --------------------------------------------------------------------------
    #  AccessableObject.getUsers:
    # --------------------------------------------------------------------------
    def getUsers(self, REQUEST=None):
      users = {}
      d = self.getSecurityUsers()
      for user in d:
        roles = self.getUserRoles( user, aq_parent=0)
        langs = self.getUserLangs( user, aq_parent=0)
        if len(roles) > 0 and len( langs) > 0:
          users[ user] = {'roles':roles,'langs':langs}
      return users

    # --------------------------------------------------------------------------
    #  AccessableObject.hasAccess:
    # --------------------------------------------------------------------------
    def hasAccess(self, REQUEST):
      auth_user = REQUEST.get('AUTHENTICATED_USER')
      access = auth_user.has_permission( 'View', self) in [ 1, True]
      if not access:
        access = access or self.hasPublicAccess() 
      return access

    # --------------------------------------------------------------------------
    #  AccessableObject.getUserRoles:
    # --------------------------------------------------------------------------
    def getUserRoles(self, userObj, aq_parent=True, resolve=True):
      roles = []
      try:
        roles.extend(list(userObj.getRolesInContext(self)))
        if 'Manager' in roles:
          roles = standard.concat_list(roles, ['ZMSAdministrator', 'ZMSEditor', 'ZMSAuthor', 'ZMSSubscriber', 'ZMSUserAdministrator'])
      except:
        pass
      root = self.getRootElement()
      nodes = self.getUserAttr(userObj, 'nodes', {})
      ob = self
      depth = 0
      while ob is not None:
        if depth > sys.getrecursionlimit():
          raise zExceptions.InternalError("Maximum recursion depth exceeded")
        depth = depth + 1
        nodekey = root.getRefObjPath(ob)
        if nodekey in nodes:
          roles = standard.concat_list(roles, nodes[nodekey]['roles'])
          break
        if aq_parent:
          ob = ob.getParentNode()
        else:
          ob = None
      # Resolve security_roles.
      if resolve:
        security_roles = self.getSecurityRoles()
        for id in [x for x in roles if x in security_roles]:
          d = security_roles.get(id, {}).get('nodes', {})
          for v in d.values():
            for role in [x.replace(' ', '') for x in v.get('roles', [])]:
              if role not in roles:
                roles.append( role)
      return roles

    # --------------------------------------------------------------------------
    #  AccessableObject.getUserLangs:
    # --------------------------------------------------------------------------
    def getUserLangs(self, userObj, aq_parent=1):
      langs = []
      try:
        langs.extend(list(getattr(userObj, 'langs', ['*'])))
      except:
        pass
      root = self.getRootElement()
      nodes = self.getUserAttr(userObj, 'nodes', {})
      ob = self
      depth = 0
      while ob is not None:
        if depth > sys.getrecursionlimit():
          raise zExceptions.InternalError("Maximum recursion depth exceeded")
        depth = depth + 1
        nodekey = root.getRefObjPath(ob)
        if nodekey in nodes:
          langs = nodes[nodekey]['langs']
          break
        if aq_parent:
          ob = ob.getParentNode()
        else:
          ob = None
      return langs


    ############################################################################
    ###
    ###  Public Access (Subscribers)
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  AccessableObject.hasRestrictedAccess:
    # --------------------------------------------------------------------------
    def hasRestrictedAccess(self):
      restricted = False
      if 'attr_dc_accessrights_restricted' in self.getMetaobjAttrIds(self.meta_id):
        restricted = restricted or self.attr( 'attr_dc_accessrights_restricted') in [ 1, True]
      return restricted

    # --------------------------------------------------------------------------
    #  AccessableObject.hasPublicAccess:
    # --------------------------------------------------------------------------
    def hasPublicAccess(self):
      public = True
      if 'attr_dc_accessrights_public' in self.getMetaobjAttrIds(self.meta_id):
        public = public and self.attr( 'attr_dc_accessrights_public') in [ 1, True]
      if not public:
        return public
      nodelist = self.breadcrumbs_obj_path()
      nodelist.reverse()
      for node in nodelist:
        f = getattr(node, 'hasRestrictedAccess', None)
        if f is not None:
          public = public and not f()
          if not public:
            return public
      return public


    # --------------------------------------------------------------------------
    #  AccessableObject.synchronizePublicAccess:
    # --------------------------------------------------------------------------
    def synchronizePublicAccess(self):
      # This is ugly, but necessary since ZMSObject is inherited from 
      # AccessableObject and ZMSContainerObject is inherited from 
      # AccessableContainer!
      restricted = self.hasRestrictedAccess()
      if self is not None and self.meta_type == 'ZMSLinkElement' and self.isEmbedded( self.REQUEST):
        ob = self.getRefObj()
        if ob is not None:
          for item in ob.breadcrumbs_obj_path():
            restricted = restricted or item.hasRestrictedAccess()
            if restricted: 
              break
      else:
        ob = self
      if isinstance( ob, AccessableContainer):
        if restricted:
          self.revokePublicAccess()
        else:
          self.grantPublicAccess()
      

    ############################################################################
    ###
    ###  Properties
    ###
    ############################################################################

    ############################################################################
    #  AccessableObject.manage_user:
    #
    #  Change user.
    ############################################################################
    manage_userForm = PageTemplateFile('zpt/ZMS/manage_user', globals())
    def manage_user(self, btn, lang, REQUEST, RESPONSE):
      """ AccessManager.manage_user """
      message = ''
      
      # Change.
      # -------
      if btn == 'BTN_SAVE':
        id = getUserId(REQUEST['AUTHENTICATED_USER'])
        user = self.findUser(id)
        password = REQUEST.get('password', '******')
        confirm = REQUEST.get('confirm', '')
        if updateUserPassword(self, user, password, confirm):
          self.setUserAttr(id, 'forceChangePassword', 0)
          message += self.getZMILangStr('ATTR_PASSWORD') + ': '
        self.setUserAttr(user, 'email', REQUEST.get('email', '').strip())
        #-- Assemble message.
        message += self.getZMILangStr('MSG_CHANGED')
      
      # Return with message.
      if RESPONSE:
        message = standard.url_quote(message)
        return RESPONSE.redirect('manage_main?lang=%s&manage_tabs_message=%s'%(lang, message))


################################################################################
################################################################################
###
###   Class AccessableContainer
###
################################################################################
################################################################################
class AccessableContainer(AccessableObject): 

    # --------------------------------------------------------------------------
    #  AccessableContainer.synchronizeRolesAccess:
    # --------------------------------------------------------------------------
    def synchronizeRolesAccess(self):
      standard.writeLog(self, '[synchronizeRolesAccess]')
      root = self.getRootElement()
      l = [(x, [x]) for x in role_defs]
      security_roles = self.getSecurityRoles()
      for id in security_roles:
        self.manage_role(role_to_manage=id, permissions=[])
        d_id = security_roles.get(id, {})
        d = d_id.get('nodes', {})
        for nodekey in d:
          node = root.getLinkObj(nodekey)
          if self.is_child_of(node):
            standard.writeLog(self, '[synchronizeRolesAccess]: security_role=%s, nodekey=%s'%(id, nodekey))
            l.append((id, d[nodekey]['roles']))
      manager_permissions = [x['name'] for x in self.permissionsOfRole('Manager') if x['selected'] == 'SELECTED']
      for i in l:
        standard.writeLog(self, '[synchronizeRolesAccess]: role=%s, role_permissions=%s'%(i[0], standard.pystr(i[1])))
        permissions = []
        for role in i[1]:
          role_permissions = role_defs.get(role, [])
          if '*' in role_permissions:
            role_permissions = manager_permissions
          permissions = standard.concat_list(permissions, role_permissions)
        standard.writeLog(self, '[synchronizeRolesAccess]: role_to_manage=%s, permissions=%s'%(i[0], standard.pystr(permissions)))
        self.manage_role(role_to_manage=i[0], permissions=permissions)

    # --------------------------------------------------------------------------
    #  AccessableContainer.grantPublicAccess:
    # --------------------------------------------------------------------------
    def grantPublicAccess(self):
      standard.writeLog(self, '[grantPublicAccess]')
      self.synchronizeRolesAccess()
      manager_permissions = [x['name'] for x in self.permissionsOfRole('Manager') if x['selected'] == 'SELECTED']
      # activate all acquired permissions
      self.manage_acquiredPermissions(manager_permissions)
      # unset access contents information
      for role_to_manage in ['Anonymous', 'Authenticated']:
        self.manage_role(role_to_manage, permissions=[])

    # --------------------------------------------------------------------------
    #  AccessableContainer.revokePublicAccess:
    # --------------------------------------------------------------------------
    def revokePublicAccess(self):
      standard.writeLog(self, '[revokePublicAccess]')
      self.synchronizeRolesAccess()
      manager_permissions = [x['name'] for x in self.permissionsOfRole('Manager') if x['selected'] == 'SELECTED']
      # deactivate all acquired permissions
      permissions = [x not in ['View'] for x in manager_permissions]
      self.manage_acquiredPermissions(permissions)
      # set access contents information
      for role_to_manage in ['Anonymous', 'Authenticated']:
        self.manage_role(role_to_manage, permissions=['Access contents information'])


################################################################################
################################################################################
###
###   Class AccessManager
###
################################################################################
################################################################################
class AccessManager(AccessableContainer): 

    # -------------------------------------------------------------------------- 
    #  AccessManager.initRoleDefs: 
    # 
    #  Init Role-Definitions and Permission Settings 
    # -------------------------------------------------------------------------- 
    def initRoleDefs(self): 
      
      # Init Roles. 
      manager_permissions = [x['name'] for x in self.permissionsOfRole('Manager') if x['selected'] == 'SELECTED']
      for role in role_defs: 
        role_def = role_defs[role] 
        # Add Local Role. 
        if not role in self.valid_roles(): 
            self._addRole(role) 
        # Set permissions for Local Role. 
        role_permissions = role_defs.get(role, [])
        if '*' in role_permissions:
          role_permissions = manager_permissions
        self.manage_role(role_to_manage=role, permissions=role_permissions) 
      
      # Grant public access. 
      self.synchronizePublicAccess() 

    # --------------------------------------------------------------------------
    #  AccessManager.getRoleName
    # --------------------------------------------------------------------------
    def getRoleName(self, role):
      langKey = 'ROLE_%s'%role.upper()
      langStr = self.getZMILangStr(langKey)
      if langKey == langStr:
        return role
      return langStr

    # --------------------------------------------------------------------------
    #  AccessManager.getSecurityRoles:
    # --------------------------------------------------------------------------
    def getSecurityRoles(self):
      roleDefs = {}
      root = self.getRootElement()
      d = root.getConfProperty('ZMS.security.roles', {})
      if root == self:
        roleDefs = copy.deepcopy(d)
      else:
        home_id = self.getHome().id
        for name in d:
          value = d[name]
          nodes = value.get('nodes', {})
          nodekeys = [x for x in nodes if nodes[x].get('home_id') == home_id]
          roleDef = {'nodes':{}}
          for key in value:
            if key not in roleDef:
              roleDef[key] = value[key]
          for nodekey in nodekeys:
            roleDef['nodes'][nodekey] = nodes[nodekey]
          roleDefs[name] = roleDef
      return roleDefs

    # --------------------------------------------------------------------------
    #  AccessManager.getSecurityUsers:
    # --------------------------------------------------------------------------
    def getSecurityUsers(self, acquired=False):
      userDefs = {}
      root = self.getRootElement()
      d = root.getConfProperty('ZMS.security.users', {})
      if root == self:
        userDefs = copy.deepcopy(d)
      else:
        home_id = self.getHome().id
        home_ids = list(self.getHome().getPhysicalPath())
        for name in d:
          value = d[name]
          nodes = value.get('nodes', {})
          nodekeys = [x for x in nodes if nodes[x].get('home_id') == home_id]
          aq_nodekeys = [x for x in nodes if nodes[x].get('home_id') in home_ids]
          if len(nodekeys) > 0 or (acquired and len(aq_nodekeys) > 0):
            userDef = {'nodes':{}}
            for key in value:
              if key not in userDef:
                userDef[key] = value[key]
            if acquired:
              userDef['acquired'] = len(nodekeys) == 0
              nodekeys.extend(aq_nodekeys)
            for nodekey in nodekeys:
              userDef['nodes'][nodekey] = nodes[nodekey]
            userDefs[name] = userDef
      return userDefs

    # --------------------------------------------------------------------------
    #  AccessManager.searchUsers:
    # --------------------------------------------------------------------------
    def searchUsers(self, search_term=''):
      users = []
      if search_term != '':
        userFldr = self.getUserFolder()
        doc_elmnts = userFldr.aq_parent.objectValues(['ZMS'])
        if doc_elmnts:
          if userFldr.meta_type == 'LDAPUserFolder':
            login_attr = self.getConfProperty('LDAPUserFolder.login_attr', userFldr.getProperty('_login_attr'))
            users.extend([x[login_attr] for x in userFldr.findUser(search_param=login_attr, search_term=search_term)])
          elif userFldr.meta_type == 'Pluggable Auth Service':
            users.extend([x['login'] for x in userFldr.searchUsers(login=search_term, id=None, exact_match=True)])
          else:
            login_attr = 'login'
            users.extend([x for x in userFldr.getUserNames() if x == search_term])
      return users
    # --------------------------------------------------------------------------
    #  AccessManager.getSearchableAttrs:
    #
    #  Return searchable attributes for current user-folder.
    # --------------------------------------------------------------------------
    def getSearchableAttrs(self):
      attrs = []
      def traverseUserFolders(context):
        if context.meta_type == 'LDAPUserFolder':
          for schema in context.getLDAPSchema():
            name = schema[0]
            label = schema[1]
            attr = (name,'%s (%s)'%(label,name))
            if attr not in attrs:
              attrs.append(attr)
        elif context.meta_type == 'Pluggable Auth Service':
          name = 'login'
          label = 'Login'
          attr = (name,'%s (%s)'%(label,name))
          if attr not in attrs:
            attrs.append(attr)
        # Traverse tree.
        for childNode in context.objectValues():
          traverseUserFolders(childNode)
      traverseUserFolders(self.getUserFolder())
      attrs = sorted(attrs,key=lambda x:x[1])
      return attrs


    # --------------------------------------------------------------------------
    #  AccessManager.getValidUserids:
    # --------------------------------------------------------------------------
    def getValidUserids(self, search_term='', search_term_param=None, without_node_check=True, exact_match=False):
      encoding = self.getConfProperty('LDAPUserFolder.encoding','latin-1')
      local_userFldr = self.getUserFolder()
      columns = None
      records = []
      c = [{'id':'name','name':'Name'}]
      userFldr = self.getUserFolder()
      users = []
      if userFldr.meta_type == 'LDAPUserFolder':
        if search_term != '':
          login_attr = self.getConfProperty('LDAPUserFolder.login_attr',userFldr.getProperty('_login_attr'))
          if exact_match:
            search_param = login_attr
          elif search_term_param:
            search_param = search_term_param
          else:
            search_param = self.getConfProperty('LDAPUserFolder.uid_attr',login_attr)
          users.extend(userFldr.findUser(search_param=search_param,search_term=search_term))
      elif userFldr.meta_type == 'Pluggable Auth Service':
        if search_term and search_term != '':
          login_attr = 'login'
          if exact_match:
            search_param = login_attr
          elif search_term_param:
            search_param = search_term_param
          else:
            search_param = self.getConfProperty('LDAPUserFolder.uid_attr',login_attr)
          kw = {search_param:search_term}
          usersDefs = userFldr.searchUsers(**kw)
          
          if exact_match:
            users.extend([x for x in usersDefs if x['login'] == search_term])
          elif search_param != login_attr:
            users.extend(usersDefs)
            # get local users
            for user in userFldr.searchUsers(login=search_term):
              plugin = getattr(userFldr,user['pluginid'])
              if plugin.meta_type == 'ZODB User Manager':
                users.append(user)
          else:
            users.extend(usersDefs)
      else:
        login_attr = 'name'
        for userName in userFldr.getUserNames():
          if without_node_check or (local_userFldr == userFldr) or self.get_local_roles_for_userid(userName):
            if (exact_match and search_term==userName) or \
               search_term == '' or \
               search_term.find(userName) >= 0:
              users.append({'name':userName})
      for user in users:
        login_name = user[login_attr]
        d = {}
        d['localUserFldr'] = userFldr
        d['name'] = login_name
        d['user_id_'] = login_name
        d['user_id'] = login_name
        d['roles'] = []
        d['domains'] = []
        extras = self.getConfProperty('LDAPUserFolder.extras','pluginid,givenName,sn,ou').split(',')
        luf = None
        plugin = None
        _uid_attr = None
        uid = None
        if userFldr.meta_type == 'LDAPUserFolder':
          luf = userFldr
        elif userFldr.meta_type == 'Pluggable Auth Service':
          pluginid = user['pluginid']
          plugin = getattr(userFldr,pluginid)
          if plugin.meta_type == 'LDAP Multi Plugin':
            for o in plugin.objectValues('LDAPUserFolder'):
              luf = o
              break
        if luf is not None:
          _login_attr = self.getConfProperty('LDAPUserFolder.login_attr',luf.getProperty('_login_attr'))
          if exact_match:
            _uid_attr = luf.getProperty('_uid_attr')
          else:
            _uid_attr = self.getConfProperty('LDAPUserFolder.uid_attr',luf.getProperty('_uid_attr'))
          if _uid_attr != _login_attr:
            uid = user[_uid_attr]
        elif plugin is not None and plugin.meta_type == 'ZODB User Manager':
          _uid_attr = login_attr
          uid = plugin.getUserIdForLogin(login_name)
        if uid is not None:
          d['user_id_'] = uid
          try:
            uid = standard.pybytes(uid)
            if uid.startswith(standard.pybytes('\x01\x05\x00\x00')):
              buid = None
              if six.PY2:
                buid = buffer(uid)
              elif six.PY3:
                buid = memoryview(uid)
              import binascii
              uid = binascii.b2a_hex(buid)
          except:
            standard.writeError(self,'[getValidUserids]: _uid_attr=%s'%_uid_attr)
          d['user_id'] = uid
          if len([x for x in c if x['id'] == 'user_id'])==0:
            c.append({'id':'user_id','name':_uid_attr.capitalize(),'type':'string'})
          c = [x for x in c if x['id'] != _uid_attr]
          extras = [x for x in extras if x != _uid_attr]
        for extra in user:
          if extra == 'pluginid':
            pluginid = user[extra]
            plugin = getattr(userFldr,pluginid)
            d['plugin'] = plugin
            editurl = userFldr.absolute_url()+'/'+user.get('editurl','%s/manage_main'%pluginid)
            container = userFldr.aq_parent
            v = '<a href="%s" title="%s" target="_blank"><i class="%s"></i></a>'%(editurl,'%s.%s (%s)'%(container.id,plugin.title_or_id(),plugin.meta_type),getattr(plugin,'zmi_icon','fas fa-users'))
            t = 'html'
          else:
            v = user[extra]
            t = 'string'
          d[extra] = v
          if extra in extras and len([x for x in c if x['id'] == extra])==0:
            c.append({'id':extra,'name':extra.capitalize(),'type':t})
        if exact_match and user[login_attr].lower() == search_term.lower():
          return d
        records.append(d)
      if exact_match:
        return None
      if columns is None:
        columns = c
      return {'columns':columns,'records':records}
  
  
    # --------------------------------------------------------------------------
    #  AccessManager.findUser:
    # --------------------------------------------------------------------------
    def findUser(self, name):
      user = self.getValidUserids(search_term=name,exact_match=True)
      if user is not None:
        userFldr = user['localUserFldr']
        # Change password?
        if userFldr.meta_type == 'User Folder':
          user['password'] = True
        elif userFldr.meta_type == 'Pluggable Auth Service' and user['plugin'].meta_type == 'ZODB User Manager':
          user['password'] = True
        # Details
        user['details'] = []
        if 'user_id' in user:
          name = 'user_id'
          label = 'User Id'
          value = user['user_id']
          user['details'].append({'name':name,'label':label,'value':value})
        # LDAP schema
        ldapUserFldr = None
        if userFldr.meta_type == 'LDAPUserFolder':
          ldapUserFldr = userFldr
        elif userFldr.meta_type == 'Pluggable Auth Service' and user['plugin'].meta_type == 'LDAP Multi Plugin':
          ldapUserFldr = getattr(user['plugin'],'acl_users')
        if ldapUserFldr is not None:
          details = ldapUserFldr.getUserDetails(encoded_dn=user['dn'],format='dictionary')
          for schema in ldapUserFldr.getLDAPSchema():
            name = schema[0]
            label = schema[1]
            value = user.get(name,'')
            user['details'].append({'name':name,'label':label,'value':value})
          # User ID
          user['details'] = [x for x in user['details'] if not x['label'].startswith('_')]
      return user


    # --------------------------------------------------------------------------
    #  AccessManager.getUserName:
    # --------------------------------------------------------------------------
    def getUserName(self, uid):
      d = self.getSecurityUsers()
      for k in d:
        if d.get('user_id_', k) == uid:
          return k
      return None

    # --------------------------------------------------------------------------
    #  AccessManager.setUserAttr:
    # --------------------------------------------------------------------------
    def setUserAttr(self, user, name, value):
      user = getUserId(user)
      root = self.getRootElement()
      d = root.getConfProperty('ZMS.security.users', {})
      i = d.get(user, {})
      if name == 'nodes' and isinstance(value, dict):
        t = {}
        for nodekey in value:
          node = self.getLinkObj(nodekey)
          if node is not None:
            newkey = root.getRefObjPath(node)
            t[newkey] = value[nodekey]
        value = t
      i[name] = value
      d[user] = i.copy()
      root.setConfProperty('ZMS.security.users', d)

    # --------------------------------------------------------------------------
    #  AccessManager.getUserAttr:
    # --------------------------------------------------------------------------
    def getUserAttr(self, user, name=None, default=None):
      user = getUserId(user)
      root = self.getRootElement()
      d = root.getConfProperty('ZMS.security.users', {})
      if name is None:
        v = d.get(user, None)
      else:
        i = d.get(user, {})
        v = i.get(name, default)
        if v is None:
          userObj = self.findUser(user)
          if userObj is not None:
            details = userObj.get('details', [])
            for detail in [x for x in details if x['name'] == name]:
              v = detail.get('value', None)
        if v is None and name == 'email':
          v = self.getUserAttr(user, 'mail')
      return v

    # --------------------------------------------------------------------------
    #  AccessManager.delUserAttr:
    # --------------------------------------------------------------------------
    def delUserAttr(self, user):
      user = getUserId(user)
      root = self.getRootElement()
      d = root.getConfProperty('ZMS.security.users', {})
      try:
        del d[user]
        root.setConfProperty('ZMS.security.users', d)
      except:
        standard.writeError(root, '[delUserAttr]: user=%s not deleted!'%user)


    # --------------------------------------------------------------------------
    #  AccessManager.getUserAdderPlugin:
    # --------------------------------------------------------------------------
    def getUserAdderPlugin(self):
      userFldr = self.getUserFolder()
      if userFldr.meta_type == 'User Folder':
        return UserFolderIAddUserPluginWrapper(userFldr)
      elif userFldr.meta_type == 'Pluggable Auth Service':
        for plugin_id in userFldr.plugins.getAllPlugins('IUserAdderPlugin')['active']:
          plugin = getattr(userFldr, plugin_id)
          return plugin
      return None


    # --------------------------------------------------------------------------
    #  AccessManager.getUserFolder:
    # --------------------------------------------------------------------------
    def getUserFolder(self):
      root = self.getRootElement()
      updateVersion(root)
      home = root.getHome()
      if 'acl_users' in home.objectIds():
        userFldr = home.acl_users
      else:
        # Create default user-folder.
        userFldr = UserFolder()
        home._setObject(userFldr.id, userFldr)
      return userFldr

    # --------------------------------------------------------------------------
    #  AccessManager.getUserDefinedRoles:
    # --------------------------------------------------------------------------
    def getUserDefinedRoles(self):
      return list(self.aq_parent.userdefined_roles())+list(self.userdefined_roles())

    ############################################################################
    ###
    ###  Local Users
    ###
    ############################################################################

    # ------------------------------------------------------------------------------
    #  AccessManager.purgeLocalUsers
    # ------------------------------------------------------------------------------
    def purgeLocalUsers(self, ob=None, valid_userids=[], invalid_userids=[]):
      rtn = ""
      if ob is None:
        ob = self
        d = self.getSecurityUsers()
        for userid in d:
          nodes = self.getUserAttr(userid, 'nodes', {}) 
          for node in nodes:
              target = self.getLinkObj(node)
              if target is None:
                self.delLocalUser(userid, node)
                rtn += userid + ": remove " + node + "<br/>"
      
      for local_role in ob.get_local_roles():
        b = False
        userid = local_role[0]
        userroles = local_role[1]
        if 'Owner' not in userroles:
          if userid not in valid_userids and userid not in invalid_userids:
            name = self.getUserName(userid)
            user = ob.findUser(name)
            if user is None:
              invalid_userids.append(userid)
            else:
              valid_userids.append(userid)
          if userid in valid_userids:
            nodes = self.getUserAttr(userid, 'nodes', {})
            if len([x for x in nodes if (x=="{$}" and ob.id=="content") or x=="{$%s}"%ob.id or x.endswith("/%s}"%ob.id)])==0:
              b = True
          elif userid in invalid_userids:
            b = True
        if b:
          rtn += ob.absolute_url()+ " " + userid + ": remove " + standard.pystr(userroles) + "<br/>"
          delLocalRoles(ob, userid)
      
      # Process subtree.
      for subob in ob.objectValues(list(ob.dGlobalAttrs)):
        rtn += self.purgeLocalUsers(subob, valid_userids, invalid_userids)
      
      return rtn


    # --------------------------------------------------------------------------
    #  AccessManager.toggleUserActive:
    # --------------------------------------------------------------------------
    def toggleUserActive(self, id):
      active = self.getUserAttr(id, 'attrActive', 1)
      attrActiveStart = self.parseLangFmtDate(self.getUserAttr(id, 'attrActiveStart', None))
      if attrActiveStart is not None:
        dt = DateTime(time.mktime(attrActiveStart))
        active = active and dt.isPast()
      attrActiveEnd = self.parseLangFmtDate(self.getUserAttr(id, 'attrActiveEnd', None))
      if attrActiveEnd is not None:
        dt = DateTime(time.mktime(attrActiveEnd))
        active = active and (dt.isFuture() or (dt.equalTo(dt.earliestTime()) and dt.latestTime().isFuture()))
      nodes = self.getUserAttr(id, 'nodes', {})
      for node in nodes:
        ob = self.getLinkObj(node)
        if ob is not None:
          user_id = self.getUserAttr(id, 'user_id_', id)
          if active:
            roles = nodes[node].get('roles', [])
            setLocalRoles(ob, user_id, roles)
          else:
            delLocalRoles(ob, user_id)


    # --------------------------------------------------------------------------
    #  AccessManager.setLocalUser:
    # --------------------------------------------------------------------------
    def setLocalUser(self, id, node, roles, langs):
      
      # Set user id.
      user = self.findUser(id)
      self.setUserAttr(id, 'user_id_', user['user_id_'])
      
      # Insert node to user-properties.
      root = self.getRootElement()
      nodes = root.getUserAttr(id, 'nodes', {})
      ob = self.getLinkObj(node)
      newkey = root.getRefObjPath(ob)
      nodes[newkey] = {'home_id':ob.getHome().id,'langs':langs,'roles':roles}
      root.setUserAttr(id, 'nodes', nodes)
      roles = list(roles)
      if 'ZMSAdministrator' in roles:
        roles.append('Manager')
      
      # Set local roles in node.
      ob = self.getLinkObj(node)
      if ob is not None:
        user_id = self.getUserAttr(id, 'user_id_', id)
        setLocalRoles(ob, user_id, roles)


    # --------------------------------------------------------------------------
    #  AccessManager.delLocalUser:
    # --------------------------------------------------------------------------
    def delLocalUser(self, id, node):
      
      # Delete node from user-properties.
      root = self.getRootElement()
      nodes = root.getUserAttr(id, 'nodes', {})
      if node in nodes: 
        del nodes[node]
        root.setUserAttr(id, 'nodes', nodes)
      
      # Delete local roles in node.
      ob = root.getLinkObj(node)
      if ob is not None:
        user_id = root.getUserAttr(id, 'user_id_', id)
        delLocalRoles(ob, user_id)


    ############################################################################
    ###
    ###  Properties
    ###
    ############################################################################

    # Management Interface.
    # ---------------------
    manage_users = PageTemplateFile('zpt/ZMS/manage_users', globals())
    manage_users_sitemap = PageTemplateFile('zpt/ZMS/manage_users_sitemap', globals())

    ############################################################################
    #  AccessManager.manage_roleProperties:
    #
    #  Change or delete roles.
    ############################################################################
    def manage_roleProperties(self, btn, key, lang, REQUEST, RESPONSE=None):
      """ AccessManager.manage_roleProperties """
      message = ''
      messagekey = 'manage_tabs_message'
      id = REQUEST.get('id', '')
      
      try:
          # Cancel.
          # -------
          if btn in [ 'BTN_CANCEL', 'BTN_BACK']:
            id = ''
          
          # Insert.
          # -------
          if btn == 'BTN_INSERT':
            if key=='obj':
              id = REQUEST.get('newId').strip()
              addRole(self, id)
              #-- Assemble message.
              message = self.getZMILangStr('MSG_INSERTED')%self.getZMILangStr('ATTR_ROLE')
            elif key=='attr':
              #-- Insert node to config-properties.
              root = self.getRootElement()
              nodekey = REQUEST.get('node')
              node = self.getLinkObj(nodekey)
              roles = REQUEST.get('roles', [])
              if not isinstance(roles, list): roles = [roles]
              security_roles = root.getConfProperty('ZMS.security.roles', {})
              newkey = root.getRefObjPath(node)
              d = security_roles.get(id, {'nodes':{}})
              d['nodes'][newkey] = {'home_id':node.getHome().id,'roles':roles}
              security_roles[id] = d
              root.setConfProperty('ZMS.security.roles', security_roles)
              #-- Set permissions in node.
              node.synchronizeRolesAccess()
              #-- Assemble message.
              message = self.getZMILangStr('MSG_INSERTED')%self.getZMILangStr('ATTR_NODE')
          
          # Delete.
          # -------
          elif btn == 'BTN_DELETE':
            if key=='obj':
              root = self.getRootElement()
              #-- Delete local role.
              for home in [self, self.getHome(), root, root.getHome()]:
                if id in home.valid_roles():
                  home._delRoles(roles=[id], REQUEST=REQUEST)
              #-- Delete nodes from config-properties.
              security_roles = root.getConfProperty('ZMS.security.roles', {})
              if id in security_roles: del security_roles[id]
              root.setConfProperty('ZMS.security.roles', security_roles)
              id = ''
            elif key=='attr':
              root = self.getRootElement()
              security_roles = root.getConfProperty('ZMS.security.roles', {})
              d = security_roles.get(id, {'nodes':{}})
              nodekeys = REQUEST.get('nodekeys', [])
              for nodekey in nodekeys:
                #-- Delete node from config-properties.
                if nodekey in d['nodes']:
                  del d['nodes'][nodekey]
                  security_roles[id] = d
                  root.setConfProperty('ZMS.security.roles', security_roles)
                #-- Set permissions in node.
                node = self.getLinkObj(nodekey)
                if node is not None:
                  node.synchronizeRolesAccess()
            #-- Assemble message.
            message = self.getZMILangStr('MSG_DELETED')%int(1)
      
      except:
        message = standard.writeError(self, "[manage_roleProperties]")
        messagekey = 'manage_tabs_error_message'
      
      # Return with message.
      if RESPONSE:
        target = REQUEST.get( 'manage_target', 'manage_users')
        target = self.url_append_params( target, { 'lang': lang, messagekey: message, 'id':id})
        return RESPONSE.redirect(target)


    ############################################################################
    #  AccessManager.manage_userProperties:
    #
    #  Change or delete users.
    ############################################################################
    def manage_userProperties(self, btn, key, lang, REQUEST, RESPONSE=None):
      """ AccessManager.manage_userProperties """
      message = ''
      messagekey = 'manage_tabs_message'
      id = REQUEST.get('id', '')
      
      try:
        # Cancel.
        # -------
        if btn in [ 'BTN_CANCEL', 'BTN_BACK']:
          id = ''
        
        # Add.
        # ----
        if btn == 'BTN_ADD':
          id = REQUEST.get('newId', '')
          newPassword = REQUEST.get('newPassword', '')
          newConfirm = REQUEST.get('newConfirm', '')
          newEmail = REQUEST.get('newEmail', '')
          userAdderPlugin = self.getUserAdderPlugin()
          userAdderPlugin.doAddUser( id, newPassword)
          self.setUserAttr( id, 'email', newEmail)
          #-- Assemble message.
          message = self.getZMILangStr('MSG_INSERTED')%self.getZMILangStr('ATTR_USER')
        
        # Insert.
        # -------
        elif btn == 'BTN_INSERT':
          langs = REQUEST.get('langs', [])
          if not isinstance(langs, list): langs = [langs]
          roles = REQUEST.get('roles', [])
          if not isinstance(roles, list): roles = [roles]
          node = REQUEST.get('node')
          ob = self.getLinkObj(node)
          docElmnt = ob.getRootElement()
          node = docElmnt.getRefObjPath(ob)
          docElmnt.setLocalUser(id, node, roles, langs)
          #-- Assemble message.
          message = self.getZMILangStr('MSG_INSERTED')%self.getZMILangStr('ATTR_NODE')
        
        # Change.
        # -------
        elif btn == 'BTN_SAVE':
          if key=='obj':
            attrActive = self.getUserAttr(id, 'attrActive', 1)
            newAttrActive = REQUEST.get('attrActive', 0)
            user = self.findUser(id)
            if user.get('password')==True:
              password = REQUEST.get('password', '******')
              confirm = REQUEST.get('confirm', '')
              updateUserPassword(self, user, password, confirm)
            self.setUserAttr(id, 'forceChangePassword', REQUEST.get('forceChangePassword', 0))
            self.setUserAttr(id, 'attrActive', newAttrActive)
            self.setUserAttr(id, 'attrActiveStart', self.parseLangFmtDate(REQUEST.get('attrActiveStart')))
            self.setUserAttr(id, 'attrActiveEnd', self.parseLangFmtDate(REQUEST.get('attrActiveEnd')))
            self.setUserAttr(id, 'email', REQUEST.get('email', '').strip())
            self.setUserAttr(id, 'profile', REQUEST.get('profile', '').strip())
            self.setUserAttr(id, 'user_id', REQUEST.get('user_id', '').strip())
            if attrActive != newAttrActive:
              self.toggleUserActive(id)
          elif key=='attr':
            pass
          #-- Assemble message.
          message = self.getZMILangStr('MSG_CHANGED')
        
        # Delete.
        # -------
        elif btn in ['delete', 'remove', 'BTN_DELETE']:
          if key=='obj':
            #-- Delete user.
            deleteUser(self, id)
            #-- Remove user.
            if btn == 'remove':
              userAdderPlugin = self.getUserAdderPlugin()
              userAdderPlugin.removeUser( id)
            id = ''
            #-- Assemble message.
            message = self.getZMILangStr('MSG_DELETED')%int(1)
          elif key=='attr':
            #-- Delete local user.
            nodekeys = REQUEST.get('nodekeys', [])
            for nodekey in nodekeys:
              try:
                self.delLocalUser(id, nodekey)
              except:
                standard.writeError(self, 'can\'t delLocalUser for nodekey=%s'%nodekey)
            #-- Assemble message.
            message = self.getZMILangStr('MSG_DELETED')%int(len(nodekeys))
        
        # Invite.
        # -------
        elif btn == 'BTN_INVITE':
          email = self.getUserAttr(id, 'email', '')
          nodekeys = REQUEST.get('nodekeys', [])
          if len(email) > 0 and len(nodekeys) > 0:
            # Send notification.
            # ------------------
            #-- Recipient
            mto = email
            #-- Body
            userObj = self.findUser(id)
            mbody = []
            mbody.append(self.getTitle(REQUEST)+' '+self.getHref2IndexHtml(REQUEST))
            mbody.append('\n')
            mbody.append('\n%s: %s'%(self.getZMILangStr('ATTR_ID'), id))
            mbody.append('\n')
            nodes = self.getUserAttr(id, 'nodes', {})
            security_roles = self.getSecurityRoles()
            for nodekey in nodes:
              if nodekey in nodekeys:
                node = nodes[nodekey]
                roles = node.get('roles', [])
                zms_roles = [x for x in roles if x not in security_roles]
                if len(zms_roles) > 0:
                  target = self.getLinkObj(nodekey)
                  if target is not None:
                    mbody.append('\n * '+target.getTitlealt(REQUEST)+' ['+self.getZMILangStr('ATTR_ROLES')+': '+', '.join([self.getRoleName(x) for x in zms_roles])+']: '+target.absolute_url()+'/manage')
                for security_role in [x for x in roles if x in security_roles]:
                  for role_nodekey in security_roles[security_role].get('nodes', {}):
                    target = self.getLinkObj(role_nodekey)
                    if target is not None:
                      mbody.append('\n * '+target.getTitlealt(REQUEST)+' ['+self.getZMILangStr('ATTR_ROLES')+': '+self.getRoleName(security_role)+']: '+target.absolute_url()+'/manage')
            mbody.append('\n')
            mbody.append('\n' + self.getZMILangStr('WITH_BEST_REGARDS').replace('\\n', '\n'))
            if len(self.getZMILangStr('WITH_BEST_REGARDS')) < 32:
                mbody.append('\n-------------------------------')
                mbody.append('\n' + standard.pystr(REQUEST['AUTHENTICATED_USER']))
                mbody.append('\n-------------------------------')
            mbody = ''.join(mbody)
            #-- Subject
            titlealt = self.getTitlealt(REQUEST)
            titlealt = titlealt.replace('&#8203;', '')
            titlealt = titlealt.replace('&nbsp;', ' ')
            titlealt = titlealt.replace('&zwnj;', '')
            msubject = '%s (%s)'%(titlealt, self.getZMILangStr('INVITATION'))
            #-- Send
            self.sendMail(mto, msubject, mbody, REQUEST)
            #-- Assemble message.
            message = self.getZMILangStr('MSG_CHANGED')
        
        # Export.
        # -------
        elif btn == 'BTN_EXPORT':
          content_type = 'text/xml; charset=utf-8'
          filename = 'userlist.xml'
          RESPONSE.setHeader('Content-Type', content_type)
          RESPONSE.setHeader('Content-Disposition', 'inline;filename="%s"'%filename)
          RESPONSE.setHeader('Cache-Control', 'no-cache')
          RESPONSE.setHeader('Pragma', 'no-cache')
          xml = self.getXmlHeader()
          xml += '<userlist>'
          userDefs = self.getSecurityUsers()
          userNames = list(userDefs)
          max_users = int(self.getConfProperty('ZMS.max_users_export', '0'))
          z = 0
          for userName in userNames:
            z += 1
            if max_users != 0:
              if z > max_users:
                break
            xml += '<user>'
            xml += '<uid>%s</uid>'%standard.html_quote(userName)
            email = self.getUserAttr(userName, 'email')
            if email is not None and email:
              xml += '<email>%s</email>'%standard.html_quote(email)
            nodes = self.getUserAttr(userName, 'nodes', {})
            xml += '<nodelist>'
            for nodekey in nodes:
              xml += '<node>'
              xml += '<nodeid>%s</nodeid>'%nodekey
              try:
                xml += '<nodeurl>%s</nodeurl>'%(self.getLinkObj(nodekey).getDeclUrl(REQUEST))
              except:
                xml += '<nodeurl></nodeurl>'
              try:  
                title = re.sub('&.*;', '', self.getLinkObj(nodekey).getTitle(REQUEST).strip())
                xml += '<nodetitle>%s</nodetitle>'%title
              except:
                xml += '<nodetitle></nodetitle>'
              xml += '<langlist>'
              for langid in nodes.get(nodekey, {}).get('langs', []):
                xml += '<lang>%s</lang>'%standard.html_quote(langid)
              xml += '</langlist>'
              xml += '<rolelist>'
              for roleid in nodes.get(nodekey, {}).get('roles', []):
                xml += '<role>%s</role>'%standard.html_quote(roleid)
              xml += '</rolelist>'
              xml += '</node>'
            xml += '</nodelist>'
            xml += '</user>'
          xml += '</userlist>'
          return xml
        
        # Import.
        # -------
        elif btn == 'BTN_IMPORT':
          f = REQUEST['file']
          filename = f.filename
          dom = _xmllib.parseString(f.read())
          for userElement in dom.getElementsByTagName('user'):
            userName = _xmllib.getText(userElement.getElementsByTagName('uid'))
            email = _xmllib.getText(userElement.getElementsByTagName('email'))
            if email:
              self.setUserAttr( userName, 'email', email)
            for nodeElement in userElement.getElementsByTagName('node'):
              node = _xmllib.getText(nodeElement.getElementsByTagName('nodeid'))
              langs = []
              for langElement in nodeElement.getElementsByTagName('lang'):
                langs.append(_xmllib.getText(langElement))
              roles = []
              for roleElement in nodeElement.getElementsByTagName('role'):
                roles.append(_xmllib.getText(roleElement))
              ob = self.getLinkObj(node)
              try:
                docElmnt = ob.getRootElement()
                node = docElmnt.getRefObjPath(ob)
                docElmnt.setLocalUser(userName, node, roles, langs)
              except:
                standard.writeError(self, 'can\'t setLocalUser nodekey=%s'%userName)
          message = self.getZMILangStr('MSG_IMPORTED')%('<em>%s</em>'%filename)
        
        # Fast-Export
        # -----------
        elif btn == 'fastexport':
          path = '%s/var/fastexport.pkl'%standard.getINSTANCE_HOME()
          data = self.getRootElement().getConfProperty('ZMS.security.users', {})
          output = open(path, 'wb')
          pickle.dump(data, output)
          output.close()
          message = self.getZMILangStr('MSG_EXPORTED')%('<em>%s</em>'%path)
        
        # Fast-Import
        # -----------
        elif btn == 'fastimport':
          path = '%s/var/fastexport.pkl'%standard.getINSTANCE_HOME()
          input = open(path, 'rb')
          data = pickle.load(input)
          input.close()
          self.getRootElement().setConfProperty('ZMS.security.users', data)
          message = self.getZMILangStr('MSG_IMPORTED')%('<em>%s</em>'%path)
      
      except:
        message = standard.writeError(self, "[manage_userProperties]")
        messagekey = 'manage_tabs_error_message'
      
      # Return with message.
      if RESPONSE:
        target = REQUEST.get( 'manage_target', 'manage_users')
        target = self.url_append_params( target, { 'lang': lang, messagekey: message, 'id':id})
        return RESPONSE.redirect(target)

################################################################################
