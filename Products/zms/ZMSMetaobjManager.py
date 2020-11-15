################################################################################
# ZMSMetaobjManager.py
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
from distutils.version import LooseVersion
import ZPublisher.HTTPRequest
import collections
import copy
import os
import six
import sys
import time
import zExceptions
import zope.interface
# Product Imports.
from Products.zms import IZMSRepositoryProvider
from Products.zms import standard
from Products.zms import zopeutil
from Products.zms import _blobfields
from Products.zms import _fileutil
from Products.zms import _globals
from Products.zms import _ziputil


# ------------------------------------------------------------------------------
#  Synchronize type.
# ------------------------------------------------------------------------------
def syncZopeMetaobjAttr( self, metaObj, attr):
  id = metaObj['id']
  attr_id = attr['id']
  try:
    artefact = None
    if attr['type'] in self.valid_zopeattrs:
      artefact = getattr(self, id+'.'+attr_id, None)
    if attr['type'] in self.valid_zopetypes:
      container = self.getHome()
      for artefact_id in attr_id.split('/')[:-1]:
         container = getattr( container, artefact_id)
      artefact_id = attr['id'].split('/')[-1]
      artefact = zopeutil.getObject(container, artefact_id, attr.get('type'), attr.get('custom'))
    if artefact is not None:
      attr['ob'] = artefact
  except:
    standard.writeError(self, "[syncZopeMetaobjAttr]: %s.%s"%(id, attr_id))

# ------------------------------------------------------------------------------
#  Effective ids.
# ------------------------------------------------------------------------------
def effective_ids(self, ids):
  l = []
  keys = list(self.model)
  if ids:
    for id in [x for x in ids if x in keys]:
      metaObj = self.getMetaobj( id)
      l.append(id)
      if metaObj['type'] == 'ZMSPackage':
        for pkgMetaObjId in self.getMetaobjIds():
            pkgMetaObj = self.getMetaobj( pkgMetaObjId)
            if pkgMetaObj[ 'package'] == metaObj[ 'id']:
              l.append( pkgMetaObjId)
  else:
    l = keys
  l.sort()
  return l


################################################################################
################################################################################
###
###   Class
###
################################################################################
################################################################################
class ZMSMetaobjManager(object):

    # Globals.
    # --------
    valid_types =     ['amount', 'autocomplete', 'boolean', 'color', 'date', 'datetime', 'dictionary', 'file', 'float', 'identifier', 'image', 'int', 'list', 'multiautocomplete', 'multiselect', 'password', 'richtext', 'select', 'string', 'text', 'time', 'url', 'xml']
    valid_zopeattrs = ['method', 'py', 'zpt', 'interface', 'resource']
    valid_xtypes =    ['constant', 'delimiter', 'hint']+valid_zopeattrs
    valid_datatypes = sorted(valid_types+valid_xtypes)
    valid_objtypes =  [ 'ZMSDocument', 'ZMSObject', 'ZMSTeaserElement', 'ZMSRecordSet', 'ZMSResource', 'ZMSReference', 'ZMSLibrary', 'ZMSPackage', 'ZMSModule']
    valid_zopetypes = [ 'DTML Method', 'DTML Document', 'External Method', 'File', 'Folder', 'Image', 'Page Template', 'Script (Python)', 'Z SQL Method']
    deprecated_types = [] # [ 'DTML Method', 'DTML Document', 'method']


    ############################################################################
    #
    #  IRepositoryProvider
    #
    ############################################################################

    """
    @see IRepositoryProvider
    """
    def provideRepositoryModel(self, r, ids=None):
      standard.writeBlock(self,"[provideRepositoryModel]: ids=%s"%str(ids))
      valid_ids = self.getMetaobjIds()
      if ids is None:
        ids = valid_ids
      for id in [x for x in ids if x in valid_ids]:
        o = self.getMetaobj(id)
        if o and not o.get('acquired', 0):
          d = copy.deepcopy(o)
          attrs = d.get('attrs',[])
          package = d.get('package','')
          mandatory_keys = ['access','enabled','id','name','package','revision','type']
          for key in list(d):
            if key not in mandatory_keys:
              del d[key]
          d['__filename__'] = [[],[package]][len(package)>0]+[id,'__init__.py']
          for attr in attrs:
            syncZopeMetaobjAttr(self, d, attr)
            mandatory_keys = ['id', 'name', 'type', 'meta_type', 'default', 'keys', 'mandatory', 'multilang', 'ob', 'repetitive']
            if attr['type']=='interface':
              attr['name'] = attr['id']
            if attr['type']=='constant':
              mandatory_keys += ['custom']
            for key in list(attr):
              if not key in mandatory_keys:
                del attr[key]
          d['Attrs'] = attrs
          r[id] = d

    """
    @see IRepositoryProvider
    """
    def updateRepositoryModel(self, r):
      id = r['id']
      if not id.startswith('__') and not id.endswith('__'):
        standard.writeBlock(self,"[updateRepositoryModel]: id=%s"%id)
        r['attrs'] = r.get('Attrs', [])
        if 'Attrs' in r: del r['Attrs']
        self.delMetaobj(id)
        self.setMetaobj(r)
        for attr in r['attrs']:
          if attr['type'] in self.valid_zopeattrs+self.valid_zopetypes:
            oldId = attr['id']
            newId = attr['id']
            newName = attr['name']
            newMandatory = attr.get('mandatory', 0)
            newMultilang = attr.get('multilang', 0)
            newRepetitive = attr.get('repetitive', 0)
            newType = attr['type']
            newKeys = attr.get('keys', [])
            newCustom = attr.get('data', '')
            newDefault = attr.get('default', '')
            if newType in ['resource']:
              newCustom = _blobfields.createBlobField( self, _blobfields.MyFile, {'data':newCustom,'filename':newId})
            self.setMetaobjAttr(id, oldId, newId, newName, newMandatory, newMultilang, newRepetitive, newType, newKeys, newCustom, newDefault)
      return id


    ############################################################################
    #
    #  XML IM/EXPORT
    #
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.importMetaobjXml
    # --------------------------------------------------------------------------
    def _importMetaobjXml(self, item, createIfNotExists=1, createIdsFilter=None):
      ids = []
      id = item['key']
      standard.writeBlock(self,'[ZMSMetaobjManager._importMetaobjXml]: id=%s'%str(id))
      meta_types = list(self.model)
      if (createIfNotExists == 1) and \
         (createIdsFilter is None or (id in createIdsFilter)):
        # Register Meta Attributes.
        metadictAttrs = []
        if id in meta_types:
          valid_types = self.valid_datatypes+self.valid_zopetypes+meta_types+['*']
          metaObj = self.getMetaobj( id)
          for metaObjAttr in metaObj['attrs']:
            if metaObjAttr['type'] not in valid_types+metadictAttrs:
              metadictAttrs.append( metaObjAttr['type'])
        newValue = item.get('value')
        newAttrs = newValue.get('attrs', newValue.get('__obj_attrs__'))
        newValue['attrs'] = []
        newValue['id'] = id
        newValue['enabled'] = newValue.get('enabled', item.get('enabled', 1))
        # Delete Object.
        oldAttrs = None
        if id in ids:
          self.delMetaobj( id)
        # Set Object.
        self.setMetaobj( newValue)
        # Set Attributes.
        attr_ids = []
        for attr in newAttrs:
          # Mandatory.
          attr_id = attr['id']
          newName = attr['name']
          newMandatory = attr.get('mandatory', 0)
          newMultilang = attr.get('multilang', 0)
          newRepetitive = attr.get('repetitive', 0)
          newType = attr.get('meta_type','')
          if not newType:
            newType = attr['type']
          # Optional.
          newKeys = attr.get('keys', [])
          newCustom = attr.get('custom', '')
          newDefault = attr.get('default', '')
          # Backwards compatibility: map interface.name to interface.custom.
          if newType == 'interface' and newName and not newCustom:
            newCustom = newName
            newName = ''
          # Old Attribute.
          if isinstance(oldAttrs, list) and len(oldAttrs) > 0:
            while len(oldAttrs) > 0 and not (attr_id == oldAttrs[0]['id'] and newType == oldAttrs[0]['type']):
              oldAttr = oldAttrs[0]
              # Set Attribute.
              if oldAttr['id'] not in attr_ids:
                self.setMetaobjAttr( id, None, oldAttr['id'], oldAttr['name'], oldAttr['mandatory'], oldAttr['multilang'], oldAttr['repetitive'], oldAttr['type'], oldAttr['keys'], oldAttr['custom'], oldAttr['default'])
                attr_ids.append(oldAttr['id'])
              # Deregister Meta Attribute.
              if oldAttr['id'] in metadictAttrs:
                metadictAttrs.remove(oldAttr['id'])
              oldAttrs.remove( oldAttr)
            if len(oldAttrs) > 0:
              oldAttrs.remove( oldAttrs[0])
          # Set Attribute.
          if attr_id not in attr_ids:
            self.setMetaobjAttr( id, attr_id, attr_id, newName, newMandatory, newMultilang, newRepetitive, newType, newKeys, newCustom, newDefault)
            attr_ids.append(attr_id)
          # Deregister Meta Attribute.
          if attr_id in metadictAttrs:
            metadictAttrs.remove(attr_id)
        # Set Meta Attributes.
        for attr_id in metadictAttrs:
          newName = attr_id
          newMandatory = 0
          newMultilang = 0
          newRepetitive = 0
          newType = attr_id
          newKeys = []
          newCustom = ''
          newDefault = ''
          # Set Attribute.
          if attr_id not in attr_ids:
            self.setMetaobjAttr( id, None, attr_id, newName, newMandatory, newMultilang, newRepetitive, newType, newKeys, newCustom, newDefault)
            attr_ids.append(attr_id)
      return id

    def importMetaobjXml(self, xml, createIfNotExists=1, createIdsFilter=None):
      self.REQUEST.set( '__get_metaobjs__', True)
      ids = []
      v = standard.parseXmlString(xml)
      if not isinstance(v, list):
        v = [v]
      for item in v:
        id = self._importMetaobjXml(item, createIfNotExists, createIdsFilter)
        ids.append( id)
      if len( ids) == 1:
        ids = ids[ 0]
      standard.writeBlock(self,'[ZMSMetaobjManager.importMetaobjXml]: ids=%s'%str(ids))
      return ids

    def exportMetaobjXml(self, ids, REQUEST=None, RESPONSE=None):
      value = []
      revision = '0.0.0'
      for id in effective_ids(self, ids):
        ob = None
        context = self
        while ob is None:
          ob = context.__get_metaobj__(id)
          if ob.get('acquired', 0):
            ob = None
            context = context.getPortalMaster().metaobj_manager
        ob = copy.deepcopy(ob)
        revision = self.getMetaobjRevision(id)
        attrs = []
        for attr_id in [x['id'] for x in ob['attrs']]:
          attr = self.getMetaobjAttr(id, attr_id)
          mandatory_keys = ['id', 'name', 'type', 'meta_type', 'default', 'keys', 'mandatory', 'multilang', 'ob', 'repetitive']
          if attr['type']=='interface':
            attr['name'] = attr['id']
          if attr['type']=='constant':
            mandatory_keys += ['custom']
          for key in list(attr):
            if (not attr[key] and REQUEST is None) or \
               (not key in mandatory_keys):
              del attr[key]
          if 'ob' in attr:
            attr['custom'] = attr['ob']
            del attr['ob']
          attrs.append( attr)
        ob['__obj_attrs__'] = attrs
        for key in ['attrs', 'acquired']:
          if key in ob:
            del ob[key]
        # Value.
        value.append({'key':id,'value':ob})
      if len(value)==1:
        value = value[0]
      # XML.
      if len(ids)==1:
        filename = '%s-%s.metaobj.xml'%(ids[0], revision)
      else:
        filename = 'export.metaobj.xml'
      # Export value with filename.
      content_type = 'text/xml; charset=utf-8'
      processing_instruction = '<?zms version=\'%s\'?>'%(self.zms_version())
      export = self.getXmlHeader() + processing_instruction + standard.toXmlString(self, value, xhtml=True)
      if RESPONSE:
        RESPONSE.setHeader('Content-Type', content_type)
        RESPONSE.setHeader('Content-Disposition', 'attachment;filename="%s"'%filename)
      return export


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.importTheme
    #
    #  Import theme.
    # --------------------------------------------------------------------------
    def importTheme(self, id):
      home = self.getHome()
      def traverse(context, container_id):
        for childNode in context.objectValues():
          if childNode.meta_type in ['Folder', 'Filesystem Directory View']:
            traverse(childNode, container_id)
          elif childNode.meta_type in ['DTML Document', 'DTML Method', 'External Method', 'Image', 'File', 'Filesystem File', 'Filesystem Image', 'Filesystem Page Template', 'Filesystem Script (Python)', 'Page Template', 'Script (Python)']:
            newIds = childNode.getPhysicalPath()
            newIds = [container_id+'~'] + list(newIds[newIds.index(container_id)+1:])
            newId = '/'.join(newIds)
            newName = childNode.title_or_id()
            newType = childNode.meta_type
            newType = {'Filesystem File':'File', 'Filesystem Image':'Image', 'Filesystem Page Template':'Page Template'}.get(newType,newType)
            newCustom = zopeutil.readData(childNode)
            self.setMetaobjAttr(id,None,newId=newId,newName=newName,newType=newType,newCustom=newCustom)
      if id in self.model:
        del self.model[id]
      container = getattr(home,id)
      self.setMetaobj({'id':id,'name':container.title_or_id(),'type':'ZMSLibrary'})
      traverse(container,id)


    ############################################################################
    #
    #   OBJECTS
    #
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.renderTemplate
    #
    #  Renders template for meta-object.
    # --------------------------------------------------------------------------
    def renderTemplate(self, obj):
      v = ""
      id = obj.meta_id
      tmpltIds = []
      if obj.REQUEST.get("ZMS_SKIN") is not None and  obj.REQUEST.get("ZMS_EXT") is not None:
        tmpltIds.append("%s_%s"%(obj.REQUEST.get("ZMS_SKIN"), obj.REQUEST.get("ZMS_EXT")))
      tmpltIds.append("standard_html")
      tmpltIds.append("bodyContentZMSCustom_%s"%id)
      for tmpltId in tmpltIds:
        if tmpltId in obj.getMetaobjAttrIds(id):
          if obj.getMetaobjAttr(id, tmpltId)['type'] in ['method', 'py', 'zpt']:
            v = obj.attr(tmpltId)
            break
          elif tmpltId not in ["standard_html"]:
            tmplt = getattr(obj, tmpltId, None)
            if tmplt is not None:
              v = tmplt(obj, obj.REQUEST)
              if type(v) is bytes:
                v = v.decode('utf-8','ignore')
              break
      return v


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.__get_metaobjs__:
    #
    #  Returns all meta-objects (including acquisitions).
    # --------------------------------------------------------------------------
    def __get_metaobjs__(self):
      #-- [ReqBuff]: Fetch buffered value from Http-Request.
      reqBuffId = 'ZMSMetaobjManager.__get_metaobjs__'
      try: return self.fetchReqBuff(reqBuffId)
      except: pass
      # Get value.
      obs = {}
      m = self.model
      aq_obs = None
      for id in m:
        ob = m[id]
        # handle acquisition
        if ob.get('acquired', 0) == 1:
          acquired = 1
          subobjects = ob.get('subobjects', 1)
          if aq_obs is None:
            portalMaster = self.getPortalMaster()
            if portalMaster is not None:
              aq_obs = portalMaster.metaobj_manager.__get_metaobjs__()
          if aq_obs is not None:
            if id in aq_obs:
              ob = aq_obs[id].copy()
            else:
              ob = {'id':id,'type':'ZMSUnknown'}
            ob['acquired'] = acquired
            ob['subobjects'] = subobjects
            obs[id] =  ob
            if ob['type'] == 'ZMSPackage' and ob['subobjects'] == 1:
              for aq_id in aq_obs:
                ob = aq_obs[aq_id].copy()
                if ob.get( 'package') == id:
                  ob['acquired'] = 1
                  obs[aq_id] =  ob
        else:
          obs[id] = ob
      #-- [ReqBuff]: Returns value and stores it in buffer of Http-Request.
      return self.storeReqBuff( reqBuffId, obs)


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.__get_metaobj__:
    #
    #  Returns meta-object identified by id.
    # --------------------------------------------------------------------------
    def __get_metaobj__(self, id):
      obs = self.__get_metaobjs__()
      ob = obs.get( id)
      return ob


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.getMetaobjIds:
    #
    #  Returns list of all meta-ids in model.
    # --------------------------------------------------------------------------
    def getMetaobjIds(self, sort=None, excl_ids=[]):
      obs = self.__get_metaobjs__()
      ids = [obs[x]['id'] for x in obs]
      # exclude ids
      if excl_ids:
        ids = [x for x in ids if x not in excl_ids]
      # sort
      if sort == True:
        ids = sorted(ids,key=lambda x:self.display_type(self.REQUEST, x))
      elif sort == False:
        ids = sorted(ids,key=lambda x:obs[x].get('name',x))
      return ids


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.getMetaobj:
    #
    #  Returns meta-object specified by id.
    # --------------------------------------------------------------------------
    def getMetaobj(self, id, aq_attrs=[]):
      ob = standard.nvl( self.__get_metaobj__(id), {'id': id, 'attrs': [], })
      if ob.get('acquired'):
        for k in aq_attrs:
          v = self.get_conf_property('%s.%s'%(id, k), None)
          if v is not None:
            ob[k] = v
      return ob


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.getMetaobjRevision:
    #
    #  Returns meta-object-revision specified by id.
    # --------------------------------------------------------------------------
    def getMetaobjRevision(self, id):
      ob = self.getMetaobj(id)
      if ob is not None and ob.get('type') == 'ZMSPackage':
        metaobjs = [x for x in self.__get_metaobjs__().values() if x.get('package') == ob['id']]
        # https://stackoverflow.com/questions/11887762/how-do-i-compare-version-numbers-in-python
        revisions = sorted(['0.0.0'] + [standard.nvl(x.get('revision'), '0.0.0') for x in metaobjs],
                           key=lambda v: LooseVersion(v))
        if LooseVersion(revisions[-1]) > LooseVersion(ob.get('revision','0.0.0')):
          ob['revision'] = revisions[-1]
      return ob.get('revision', '0.0.0')


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.getMetaobjId:
    #
    #  Returns id of meta-object specified by name.
    # --------------------------------------------------------------------------
    def getMetaobjId(self, name):
      for id in self.getMetaobjIds():
        if name == self.display_type(meta_type=id):
          return id
      return None


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.setMetaobj:
    #
    #  Sets meta-object with specified values.
    # --------------------------------------------------------------------------
    def setMetaobj(self, ob):
      self.clearReqBuff('ZMSMetaobjManager')
      obs = self.model
      ob = ob.copy()
      ob[ 'name'] = ob.get( 'name', '')
      ob[ 'revision'] = ob.get( 'revision', '0.0.0')
      ob[ 'type'] = ob.get( 'type', '')
      ob[ 'package'] = ob.get( 'package', '')
      ob[ 'attrs'] = ob.get( 'attrs', ob.get( '__obj_attrs__', []))
      ob[ 'acquired'] = ob.get( 'acquired', 0)
      ob[ 'enabled'] = ob.get( 'enabled', 1)
      if '__obj_attrs__' in ob:
        del ob['__obj_attrs__']
      obs[ob['id']] = ob
      # Make persistent.
      self.model = self.model.copy()


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.acquireMetaobj:
    #
    #  Acquires meta-object specified by id.
    # --------------------------------------------------------------------------
    def acquireMetaobj(self, id, subobjects=1):
      self.clearReqBuff('ZMSMetaobjManager')
      obs = self.model
      ob = self.getMetaobj( id)
      if ob is not None and len(ob) > 0 and subobjects == 1:
        if ob.get('type', '') == 'ZMSPackage':
          pk_obs = [x for x in obs.values() if x.get('package') == id]
          pk_ids = [x['id'] for x in pk_obs]
          for pk_id in pk_ids:
            self.delMetaobj( pk_id, acquire=True)
        self.delMetaobj( id, acquire=True)
      ob = {}
      ob['id'] = id
      ob['acquired'] = 1
      ob['subobjects'] = subobjects
      self.setMetaobj( ob)
      # Make persistent.
      self.model = self.model.copy()


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.delMetaobj:
    #
    #  Delete meta-object specified by id.
    # --------------------------------------------------------------------------
    def delMetaobj(self, id, acquire=False):
      self.clearReqBuff('ZMSMetaobjManager')
      # Handle type.
      ids = [x for x in self.objectIds() if x.startswith(id+'.')]
      if ids:
        self.manage_delObjects( ids)
      # Delete object.
      cp = self.model
      obs = {}
      for key in cp:
        if key == id:
          # Delete attributes.
          attr_ids = [x['id'] for x in cp[key]['attrs']]
          for attr_id in attr_ids:
            self.delMetaobjAttr( id, attr_id, acquire)
        else:
          obs[key] = cp[key]
      # Make persistent.
      self.model = obs.copy()


    ############################################################################
    #
    #   ATTRIBUTES
    #
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.notifyMetaobjAttrAboutValue:
    #
    #  Notify attribute for meta-object specified by attribute-id about value.
    # --------------------------------------------------------------------------
    def notifyMetaobjAttrAboutValue(self, meta_id, key, value):
      sync_id = False
      
      attr = self.getMetaobjAttr( meta_id, key)
      if attr is not None:
        # Self-learning auto-complete attributes.
        if attr.get('type') in ['autocomplete', 'multiautocomplete']:
          keys = attr['keys']
          if ''.join(keys).find('<dtml') < 0:
            if not isinstance(value, list):
              value = [value]
            for v in value:
              if v not in keys:
                keys.append(v)
                sync_id = meta_id
            if sync_id:
              self.setMetaobjAttr( meta_id, key, key, attr['name'], attr['mandatory'], attr['multilang'], attr['repetitive'], attr['type'], keys, attr.get('custom',None), attr['default'])
      
      ##### SYNCHRONIZE ####
      if sync_id:
        self.synchronizeObjAttrs( sync_id)


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.getMetaobjAttrIdentifierId:
    #
    #  Get attribute-id of identifier for datatable specified by meta-id.
    # --------------------------------------------------------------------------
    def getMetaobjAttrIdentifierId(self, meta_id):
      for attr_id in self.getMetaobjAttrIds( meta_id, types=[ 'identifier', 'string', 'int']):
        return attr_id
      return None


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.getMetaobjAttrIds:
    #
    #  Returns list of attribute-ids for meta-object specified by meta-id.
    # --------------------------------------------------------------------------
    def getMetaobjAttrIds(self, id, types=[]):
      return [x['id'] for x in self.getMetaobjAttrs( id, types)]


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.getMetaobjAttrs:
    #
    #  Returns list of attribute-ids for meta-object specified by meta-id.
    # --------------------------------------------------------------------------
    def getMetaobjAttrs(self, id, types=[]):
      attrs = []
      ob = self.__get_metaobj__(id)
      if ob is not None:
        attrs = ob.get('attrs', ob.get('__obj_attrs__', []))
        if len( types) > 0:
          attrs = [x for x in attrs if x['type'] in types]
      return attrs


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.evalMetaobjAttr
    # --------------------------------------------------------------------------
    def evalMetaobjAttr(self, id, attr_id, zmscontext=None, options={}):
      value = None
      # Find meta-object attributes by given id.
      metaObjAttrs = []
      # all meta-objects:
      if id == '*':
        metaObjs = self.__get_metaobjs__()
        for metaObjId in metaObjs:
          metaObj = metaObjs[metaObjId]
          for metaObjAttr in [x for x in metaObj.get('attrs', []) if x['id'] == attr_id]:
            metaObjAttrs.append(self.getMetaobjAttr( metaObjId, attr_id))
      # single meta-object:
      else:
        metaObjAttrs.append(self.getMetaobjAttr( id, attr_id))
      metaObjAttrs = [x for x in metaObjAttrs if x is not None]
      # Process meta-object attributes.
      for metaObjAttr in metaObjAttrs:
        if metaObjAttr['type'] == 'constant':
          value = metaObjAttr.get('custom', '')
        elif metaObjAttr['type'] == 'resource':
          value = metaObjAttr.get('ob', None)
        elif metaObjAttr['type'] in self.valid_zopeattrs:
          ob = metaObjAttr.get('ob', None)
          if ob:
            value = zopeutil.callObject(ob, zmscontext, options)
      # Return value.
      return value


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.getMetaobjAttr:
    # 
    #  Get attribute for meta-object specified by attribute-id.
    # --------------------------------------------------------------------------
    def getMetaobjAttr(self, id, attr_id, sync=True):
      meta_objs = self.__get_metaobjs__()
      if meta_objs.get(id, {}).get('acquired', 0) == 1:
        portalMaster = self.getPortalMaster()
        if portalMaster is not None:
          attr = portalMaster.getMetaobjAttr( id, attr_id, sync)
          return attr
      meta_obj = self.getMetaobj(id)
      attrs = meta_obj.get('attrs', meta_obj.get('__obj_attrs__', []))
      for attr in attrs:
        valid_datatype = attr['type'] in self.valid_datatypes
        if attr_id == attr['type'] and not valid_datatype:
          meta_attrs = self.getMetadictAttrs()
          if attr['type'] in meta_attrs:
            attr_type = attr['type']
            attr = self.getMetadictAttr(attr['type'])
            attr = attr.copy()
            attr['meta_type'] = attr_type
            return attr
        if attr_id == attr['id']:
          attr = attr.copy()
          attr['datatype_key'] = _globals.datatype_key(attr['type'])
          attr['mandatory'] = attr.get('mandatory', 0)
          attr['multilang'] = attr.get('multilang', 1)
          attr['errors'] = attr.get('errors', '')
          attr['meta_type'] = ['', '?'][int(attr['type']==attr['id'] and not valid_datatype)]
          if sync:
            syncZopeMetaobjAttr( self, meta_obj, attr)
          return attr
      return None


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.setMetaobjAttr:
    #
    #  Set/add meta-object attribute with specified values.
    # --------------------------------------------------------------------------
    def setMetaobjAttr(self, id, oldId, newId, newName='', newMandatory=0, newMultilang=1, newRepetitive=0, newType='string', newKeys=[], newCustom='', newDefault=''):
      self.writeBlock("[setMetaobjAttr]: %s %s %s"%(str(id), str(oldId), str(newId)))
      self.clearReqBuff('ZMSMetaobjManager')
      ob = self.__get_metaobj__(id)
      if ob is None: return
      attrs = copy.copy(ob['attrs'])
      
      # Set Attributes.
      if newType in ['delimiter', 'hint']:
        newCustom = ''
      if newType in ['resource'] and (isinstance(newCustom, str) or isinstance(newCustom, int)):
        newCustom = None
      if newType not in ['*', 'autocomplete', 'color', 'multiautocomplete', 'multiselect', 'recordset', 'select']:
        newKeys = []
      if newType in self.getMetadictAttrs():
        newId = newType
      if newType in self.getMetaobjIds()+['*']:
        newMultilang = 0
      
      # Defaults for Insert
      method_types = [ 'method', 'py', 'zpt'] + self.valid_zopetypes
      if oldId is None and not newCustom:
        if newType in [ 'method', 'DTML Method', 'DTML Document']:
          newCustom = ''
          newCustom += '<!-- '+ newId + ' -->\n'
          newCustom += '\n'
          newCustom += '<!-- /'+ newId + ' -->\n'
        elif newType in [ 'External Method']:
          newCustom = ''
          newCustom += '# Example code:\n'
          newCustom += '\n'
          newCustom += 'def ' + newId + '( self):\n'
          newCustom += '  return "This is the external method ' + newId + '"\n'
        elif newType in [ 'zpt']:
          newCustom = ''
          newCustom += '<!-- '+ newId + ' -->\n\n'
          newCustom += '<tal:block tal:define="zmscontext options/zmscontext;\n'
          newCustom += '\t\ttitle python:zmscontext getTitle(request);">\n'
          newCustom += '\t<h4 tal:content="structure title">the title</h4>\n'
          newCustom += '</tal:block>\n\n'
          newCustom += '<!--/ '+ newId + ' -->\n'
        elif newType in [ 'Page Template']:
          newCustom = ''
          newCustom += '<span tal:replace="here/title_or_id">content title or id</span>'
          newCustom += '<span tal:condition="template/title" tal:replace="template/title">optional template title</span>'
        elif newType in [ 'py', 'Script (Python)']:
          newCustom = '## Script (Python) ""\n'
          newCustom += '##bind container=container\n'
          newCustom += '##bind context=context\n'
          newCustom += '##bind namespace=\n'
          newCustom += '##bind script=script\n'
          newCustom += '##bind subpath=traverse_subpath\n'
          newCustom += '##parameters='
          if newType in ['py']: newCustom += 'zmscontext=None,options=None'
          newCustom += '\n'
          newCustom += '##title='
          if newType in ['py']: newCustom += newType+': '
          newCustom += newName
          newCustom += '\n'
          newCustom += '##\n'
          newCustom += '# --// '+ newId + ' //--\n'
          newCustom += '# Example code:\n'
          newCustom += '\n'
          newCustom += '# Import a standard function, and get the HTML request and response objects.\n'
          newCustom += 'from Products.PythonScripts.standard import html_quote\n'
          newCustom += 'from Products.zms import standard\n'
          newCustom += 'request = container.REQUEST\n'
          newCustom += 'RESPONSE =  request.RESPONSE\n'
          newCustom += '\n'
          newCustom += '# Return a string identifying this script.\n'
          newCustom += 'p = []\n'
          newCustom += 'p.append("This is the Python Script %s" % script.getId())\n'
          newCustom += 'p.append("in %s" % container.absolute_url())\n'
          newCustom += 'return "\\n".join(p)\n'
          newCustom += '\n'
          newCustom += '# --// /'+ newId + ' //--\n'
        elif newType in [ 'Z SQL Method']:
          newCustom = ''
          newCustom += '<connection>%s</connection>\n'%self.SQLConnectionIDs()[0][1]
          newCustom += '<params></params>\n'
          newCustom += 'SELECT * FROM tablename\n'
      
      # Handle resources.
      if (newType in ['resource']) or \
         (newMandatory and newType in self.getMetaobjIds()) or \
         (newRepetitive and newType in self.getMetaobjIds()):
        if not newCustom:
          if oldId is not None and id+'.'+oldId in self.objectIds():
            self.manage_delObjects(ids=[id+'.'+oldId])
        elif isinstance( newCustom, _blobfields.MyBlob):
          if oldId is not None and id+'.'+oldId in self.objectIds():
            self.manage_delObjects(ids=[id+'.'+oldId])
          zopeutil.addFile(self, id+'.'+newId, newCustom.getFilename(), newCustom.getData())
        elif oldId is not None and oldId != newId and id+'.'+oldId in self.objectIds():
          self.manage_renameObject(id=id+'.'+oldId, new_id=id+'.'+newId)
        if not ob['type'] == 'ZMSRecordSet':
          newCustom = ''
      
      attr = {}
      attr['id'] = newId
      attr['name'] = newName
      attr['mandatory'] = newMandatory
      attr['multilang'] = newMultilang
      attr['repetitive'] = newRepetitive
      attr['type'] = newType
      attr['keys'] = newKeys
      attr['custom'] = newCustom if type(newCustom) in (int, str) else None
      attr['default'] = newDefault
      
      # Handle special methods and interfaces.
      mapTypes = {'method':'DTML Method','py':'Script (Python)','zpt':'Page Template'}
      message = ''
      if newType in ['interface']:
        newType = standard.dt_executable(self, newCustom)
        if not newType:
          newType = 'method'
        newName = '%s: %s'%(newId, newType)
      if newType in mapTypes:
        oldObId = '%s.%s'%(id, oldId)
        newObId = '%s.%s'%(id, newId)
        # Remove Zope-Object (if exists)
        zopeutil.removeObject(self, oldObId)
        zopeutil.removeObject(self, newObId)
        # Insert Zope-Object.
        if isinstance(newCustom,_blobfields.MyBlob): newCustom = newCustom.getData()
        if standard.is_str(newCustom): newCustom = newCustom.replace('\r', '')
        try:
          zopeutil.addObject(self, mapTypes[newType], newObId, newName, newCustom)
          del attr['custom']
        except:
          standard.writeError(self,"can't addObject %s (%s)"%(newObId,newType))
      
      # Replace
      ids = [x['id'] for x in attrs]
      if oldId in ids:
        i = ids.index(oldId)
        attrs[i] = attr
      elif newId in ids:
        i = ids.index(newId)
        attrs[i] = attr
      # Always append new methods at the end.
      elif newType in method_types:
        attrs.append( attr)
      # Insert new attributes before methods
      else:
          i = len( attrs)
          while i > 0 and attrs[i-1]['type'] in method_types:
            i -= 1
          if i < len(attrs):
            attrs.insert( i, attr)
          else:
            attrs.append( attr)
      ob['attrs'] = attrs
      
      # Handle native Zope-Objects.
      if newType in self.valid_zopetypes:
        # Get container.
        container = self.getHome()
        for ob_id in newId.split('/')[:-1]:
          if ob_id not in container.objectIds():
            container.manage_addFolder(id=ob_id, title='Folder: %s'%id)
          container = getattr( container, ob_id)
        newObId = newId.split('/')[-1]
        zopeutil.removeObject(container, newObId)
        # Get container (old).
        if oldId is not None:
          oldContainer = self.getHome()
          for ob_id in oldId.split('/')[:-1]:
            if oldContainer is not None:
              oldContainer = getattr(oldContainer, ob_id, None)
          if oldContainer is not None:
            oldObId = oldId.split('/')[-1]
            zopeutil.removeObject(oldContainer, oldObId)
        # Insert Zope-Object.
        if isinstance(newCustom,_blobfields.MyBlob): newCustom = newCustom.getData()
        # Line-breaks.
        if standard.is_str(newCustom): 
           newCustom = newCustom.replace('\r', '')
         # Strip errors.
        if isinstance(newCustom,six.string_types): 
           if newCustom.find("## Errors:") >= 0:
             lines = [x for x in newCustom.split('\n')]
             remove = False
             i = 0
             while lines and lines[i].startswith("##"):
               if lines[i].startswith("## Errors:"):
                 remove = True
               else: 
                 i += 1
               if remove:
                 lines.pop(i)
             newCustom = '\n'.join(lines)
        try:
          newOb = zopeutil.addObject(container, newType, newObId, newName, newCustom)
          if newOb is not None:
            del attr['custom']
        except:
          attr['custom'] = "## Errors:\n" + "##  " + standard.writeError(self,"") + "\n" + "##\n" + newCustom
        # Change Zope-Object (special).
        newOb = zopeutil.getObject(container, newObId)
        if newType == 'Folder':
          if isinstance( newCustom, _blobfields.My) and len(newCustom.getData()) > 0:
            newOb.manage_delObjects(ids=newOb.objectIds())
            _ziputil.importZip2Zodb( newOb, newCustom.getData())
      
      # Assign attributes to meta-object.
      self.model[id] = ob
      # Make persistent.
      self.model = self.model.copy()
      
      # Return with message.
      return message


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.delMetaobjAttr:
    #
    #  Delete attribute from meta-object specified by id.
    # --------------------------------------------------------------------------
    def delMetaobjAttr(self, id, attr_id, acquire=False):
      ob = self.__get_metaobj__(id)
      attrs = copy.copy(ob.get('attrs', []))
      
      # Delete Attribute.
      cp = []
      for attr in attrs:
        if attr['id'] == attr_id:
          if id+'.'+attr['id'] in self.objectIds():
            ob_id = id+'.'+attr['id']
            zopeutil.removeObject(self, ob_id, removeFile=True)
          if not acquire and attr['type'] in self.valid_zopetypes:
            # Get container.
            container = self.getHome()
            ids = attr['id'].split('/')
            for ob_id in ids[:-1]:
              container = getattr( container, ob_id)
            ob_id = ids[-1]
            zopeutil.removeObject(container, ob_id, removeFile=True)
        else:
          cp.append(attr)
      ob['attrs'] = cp
      
      # Assign Attributes to Meta-Object.
      self.model[id] = ob
      
      # Make persistent.
      self.model = self.model.copy()


    # --------------------------------------------------------------------------
    #  ZMSMetaobjManager.moveMetaobjAttr:
    #
    #  Move meta-object attribute to specified position.
    # --------------------------------------------------------------------------
    def moveMetaobjAttr(self, id, attr_id, pos):
      ob = self.__get_metaobj__(id)
      attrs = copy.copy(ob['attrs'])
      # Move Attribute.
      ids = self.getMetaobjAttrIds(id)
      i = ids.index(attr_id)
      attr = attrs[i]
      attrs.remove(attr)
      attrs.insert(pos, attr)
      ob['attrs'] = attrs
      # Assign Attributes to Meta-Object.
      self.model[id] = ob
      # Make persistent.
      self.model = self.model.copy()


    ############################################################################
    #  ZMSMetaobjManager.manage_ajaxChangeProperties:
    #
    #  Change properties.
    ############################################################################
    def manage_ajaxChangeProperties(self, id, REQUEST, RESPONSE=None):
      """ MetaobjManager.manage_ajaxChangeProperties """
      xml = self.getXmlHeader()
      xml += '<result '
      xml += ' id="%s"'%id
      ob = self.__get_metaobj__(id)
      prefix = 'set'
      for key in REQUEST.form:
        if key.startswith(prefix):
          k = key[len(prefix):].lower()
          v = REQUEST.form.get(key)
          if k in ob:
            if ob.get('acquired'):
              self.setConfProperty('%s.%s'%(id, k), v)
            else:
              ob[k] = v
            xml += ' %s="%s"'%(k, str(v))
      xml += '/>'
      # Assign Attributes to Meta-Object.
      self.model[id] = ob
      # Make persistent.
      self.model = self.model.copy()
      # Return with xml
      if RESPONSE is not None:
        content_type = 'text/xml; charset=utf-8'
        filename = 'manage_ajaxChangeProperties.xml'
        RESPONSE.setHeader('Content-Type', content_type)
        RESPONSE.setHeader('Content-Disposition', 'inline;filename="%s"'%filename)
        RESPONSE.setHeader('Cache-Control', 'no-cache')
        RESPONSE.setHeader('Pragma', 'no-cache')
        return xml


    ############################################################################
    #  ZMSMetaobjManager.manage_changeProperties:
    #
    #  Change properties.
    ############################################################################
    def manage_changeProperties(self, lang, btn='', key='all', REQUEST=None, RESPONSE=None):
        """ ZMSMetaobjManager.manage_changeProperties """
        old_model = copy.deepcopy(self.model)
        message = ''
        messagekey = 'manage_tabs_message'
        extra = {}
        t0 = time.time()
        id = REQUEST.get('id', '').strip()
        target = REQUEST.get('target', 'manage_main')
        REQUEST.set( '__get_metaobjs__', True)
        
        #try:
        if True:
          sync_id = []
          
          # Delete.
          # -------
          # Delete Object.
          if btn == 'BTN_DELETE' and key == 'obj':
            if id:
              meta_ids = [id]
            else:
              meta_ids = REQUEST.get('ids', [])
            for meta_id in meta_ids:
              metaObj = self.getMetaobj( meta_id)
              if metaObj.get('type','') == 'ZMSPackage':
                for pkgMetaObjId in self.getMetaobjIds():
                  pkgMetaObj = self.getMetaobj( pkgMetaObjId)
                  if pkgMetaObj.get('package') == metaObj.get('id'):
                    if pkgMetaObjId not in meta_ids:
                      meta_ids.append( pkgMetaObjId)
            for meta_id in meta_ids:
              self.delMetaobj(meta_id)
            id = ''
            message = self.getZMILangStr('MSG_DELETED')%len(meta_ids)
          # Delete Attribute.
          elif btn == 'BTN_DELETE' and key == 'attr':
            attr_id = REQUEST['attr_id']
            self.delMetaobjAttr( id, attr_id)
          
          # Change.
          # -------
          elif key == 'all' and btn == 'BTN_SAVE':
            savedAttrs = copy.copy(self.getMetaobj(id)['attrs'])
            # Change object.
            newValue = {}
            newValue['id'] = id.strip()
            newValue['name'] = REQUEST['obj_name'].strip()
            newValue['revision'] = REQUEST.get('obj_revision', '').strip()
            newValue['type'] = REQUEST['obj_type'].strip()
            newValue['package'] = REQUEST.get('obj_package', '').strip()
            newValue['attrs'] = savedAttrs
            newValue['enabled'] = REQUEST.get('obj_enabled', 0)
            newValue['access'] = {
             'insert_deny': REQUEST.get( 'access_insert_deny', []),
             'insert_custom': REQUEST.get( 'access_insert_custom', ''),
             'delete_deny': REQUEST.get( 'access_delete_deny', []),
             'delete_custom': REQUEST.get( 'access_delete_custom', ''),
            }
            self.setMetaobj( newValue)
            # Change attributes.
            for old_id in REQUEST.get('old_ids', []):
              attr_id = REQUEST['attr_id_%s'%old_id].strip()
              newName = REQUEST.get('attr_name_%s'%old_id, '').strip()
              newMandatory = REQUEST.get( 'attr_mandatory_%s'%old_id, 0)
              newMultilang = REQUEST.get( 'attr_multilang_%s'%old_id, 0)
              newRepetitive = REQUEST.get( 'attr_repetitive_%s'%old_id, 0)
              newType = REQUEST.get( 'attr_type_%s'%old_id)
              newKeys = standard.string_list(REQUEST.get('attr_keys_%s'%old_id, ''), trim=False)
              newCustom = REQUEST.get('attr_custom_%s'%old_id, '')
              newDefault = REQUEST.get('attr_default_%s'%old_id, '')
              # Upload resource.
              if isinstance(newCustom, ZPublisher.HTTPRequest.FileUpload):
                  if len(getattr(newCustom, 'filename', '')) > 0:
                      newCustom = _blobfields.createBlobField( self, _blobfields.MyFile, newCustom)
                  else:
                      REQUEST.set('attr_custom_%s_modified'%old_id, '0')
              # Restore resource.
              if REQUEST.get('attr_custom_%s_modified'%old_id, '1') == '0' and \
                 REQUEST.get('attr_custom_%s_active'%old_id, '0') == '1':
                  savedAttr = [x for x in savedAttrs if x['id'] == old_id][0]
                  syncZopeMetaobjAttr( self, newValue, savedAttr)
                  if savedAttr['ob']:
                    filename = savedAttr['ob'].title
                    data = bytes(zopeutil.readData(savedAttr['ob']))
                    newCustom = _blobfields.createBlobField( self, _blobfields.MyFile, {'filename':filename,'data':data})
              # Change attribute.
              message += self.setMetaobjAttr( id, old_id, attr_id, newName, newMandatory, newMultilang, newRepetitive, newType, newKeys, newCustom, newDefault)
            # Return with message.
            message += self.getZMILangStr('MSG_CHANGED')
            # Insert attribute.
            attr_id = REQUEST.get('attr_id', '').strip()
            newName = REQUEST.get('attr_name', '').strip()
            newMandatory = REQUEST.get('_mandatory', 0)
            newMultilang = REQUEST.get('_multilang', 0)
            newRepetitive = REQUEST.get('_repetitive', 0)
            newType = REQUEST.get('_type', 'string')
            newKeys = REQUEST.get('_keys', [])
            newCustom = REQUEST.get('_custom', '')
            newDefault = REQUEST.get('_default', '')
            if (len(attr_id) > 0 and len(newName) > 0 and len(newType) > 0) or newType in self.getMetadictAttrs():
              message += self.setMetaobjAttr( id, None, attr_id, newName, newMandatory, newMultilang, newRepetitive, newType, newKeys, newCustom, newDefault)
              message += self.getZMILangStr('MSG_INSERTED')%attr_id
          elif key == 'obj' and btn == 'BTN_SAVE':
            # Change Acquired-Object.
            subobjects = REQUEST.get('obj_subobjects', 0)
            self.acquireMetaobj( id, subobjects)
            # Return with message.
            message += self.getZMILangStr('MSG_CHANGED')
          
          # Copy.
          # -----
          elif btn == 'BTN_COPY':
            metaOb = self.getMetaobj(id)
            if metaOb.get('acquired', 0) == 1:
              package = metaOb.get('package', '')
              if package:
                metaPkg = self.getMetaobj(package)
                if metaPkg.get('acquired', 0) == 1:
                  metaPkg['acquired'] = 0
                  self.setMetaobj(metaPkg)
              xml = self.exportMetaobjXml([id])
              self.importMetaobjXml(xml=xml)
              message = self.getZMILangStr('MSG_IMPORTED')%('<em>%s</em>'%id)
          
          # Export.
          # -------
          elif btn == 'BTN_EXPORT':
            ids = REQUEST.get('ids', [])
            return self.exportMetaobjXml(ids, REQUEST, RESPONSE)
          
          # Insert.
          # -------
          elif btn == 'BTN_INSERT':
            # Insert Object.
            if key == 'obj':
              id = REQUEST['_meta_id'].strip()
              newValue = {}
              newValue['id'] = id
              newValue['name'] = REQUEST.get('_meta_name').strip()
              newValue['type'] = REQUEST.get('_meta_type').strip()
              self.setMetaobj( newValue)
              # Insert Attributes.
              if newValue['type'] == 'ZMSDocument':
                message += self.setMetaobjAttr(id, None, newId='titlealt', newType='titlealt')
                message += self.setMetaobjAttr(id, None, newId='title', newType='title')
              elif newValue['type'] == 'ZMSTeaserElement':
                message += self.setMetaobjAttr(id, None, newId='titlealt', newType='titlealt')
                message += self.setMetaobjAttr(id, None, 'attr_penetrance', self.getZMILangStr('ATTR_PENETRANCE'), 1, 1, 0, 'select', ['this', 'sub_nav', 'sub_all'])
              elif newValue['type'] == 'ZMSRecordSet':
                message += self.setMetaobjAttr(id, None, 'records', self.getZMILangStr('ATTR_RECORDS'), 1, 1, 0, 'list')
                message += self.setMetaobjAttr(id, None, 'col_id', 'COL_ID', 1, 0, 0, 'identifier', [], 0)
                message += self.setMetaobjAttr(id, None, 'col_1', 'COL_1', 0, 0, 0, 'string', [], 1)
                message += self.setMetaobjAttr(id, None, 'col_2', 'COL_2', 0, 0, 0, 'string', [], 1)
              elif newValue['type'] == 'ZMSModule':
                message += self.setMetaobjAttr(id, None, 'zexp', 'ZEXP', 0, 0, 0, 'resource')
              # Insert Template.
              if newValue['type'] not in [ 'ZMSModule', 'ZMSPackage']:
                tmpltId = 'standard_html'
                tmpltName = 'Template: %s'%newValue['name']
                tmpltCustom = []
                tmpltCustom.append('<!-- %s.%s -->\n'%(id, tmpltId))
                tmpltCustom.append('\n')
                tmpltCustom.append('<tal:block tal:define="\n')
                tmpltCustom.append('\t\tzmscontext options/zmscontext">\n')
                if newValue['type'] == 'ZMSRecordSet':
                  tmpltCustom.append('\t<h2 tal:content="python:zmscontext.getTitlealt(request)">The title.alt</h2>\n')
                  tmpltCustom.append('\t<p class="description" tal:content="python:\'%i %s\'%(len(zmscontext.attr(zmscontext.getMetaobj(zmscontext.meta_id)[\'attrs\'][0][\'id\'])),zmscontext.getLangStr(\'ATTR_RECORDS\',request[\'lang\']))">#N records</p>\n')
                tmpltCustom.append('</tal:block>\n')
                tmpltCustom.append('\n')
                tmpltCustom.append('<!-- /%s.%s -->\n'%(id, tmpltId))
                tmpltCustom = ''.join(tmpltCustom)
                message += self.setMetaobjAttr(id, None, tmpltId, tmpltName, 0, 0, 0, 'zpt', [], tmpltCustom)
              message += self.getZMILangStr('MSG_INSERTED')%id
          
          # Acquire.
          # --------
          elif btn == 'BTN_ACQUIRE':
            immediately = REQUEST.get('immediately', 0)
            overwrite = []
            ids = REQUEST.get('aq_ids', [])
            for id in ids:
              if not immediately and id in self.getMetaobjIds():
                overwrite.append( id)
              else:
                self.acquireMetaobj( id)
            if overwrite:
              id = ''
              extra['section'] = 'acquire'
              extra['temp_ids'] = ','.join(overwrite)
            else:
              # Return with message.
              message = self.getZMILangStr('MSG_INSERTED')%str(len(ids))
          
          # Import.
          # -------
          elif btn == 'BTN_IMPORT':
            immediately = False
            xmlfile = None
            temp_folder = getattr(self,'temp_folder',None)
            temp_id = self.id + '_' + REQUEST['AUTHENTICATED_USER'].getId() + '.xml'
            if temp_folder is None:
              immediately = True
            elif REQUEST.get('temp_import_file_id')==temp_id and temp_id in temp_folder.objectIds():
              if temp_id in temp_folder.objectIds():
                filename = str(getattr( temp_folder, temp_id).title)
                xmlfile = standard.getTempFile(self,temp_id)
                temp_folder.manage_delObjects([temp_id])
                immediately = True
            if REQUEST.get('file'):
              f = REQUEST['file']
              filename = f.filename
              xmlfile = f
            if REQUEST.get('init'):
              file = REQUEST['init']
              filename,xmlfile = self.getConfXmlFile( file)
            if xmlfile is not None:
              # extract xml from zip
              if filename.endswith('.zip'):
                 import zipfile
                 zip_buffer = zipfile.ZipFile(xmlfile,"r")
                 for name in zip_buffer.namelist():
                   if name.endswith(".xml"):
                     filename = name
                     xmlfile = standard.PyBytesIO(zip_buffer.read(filename))
                     break
              # parse xml
              if not immediately:
                xml = xmlfile.read()
                # open string-io.
                xmlfile = standard.PyBytesIO(xml)
                v = standard.parseXmlString(xmlfile)
                xmlfile = standard.PyBytesIO(xml)
                if not isinstance(v,list):
                  v = []
                if temp_id in temp_folder.objectIds():
                  temp_folder.manage_delObjects([temp_id])
                file = zopeutil.addFile(temp_folder, temp_id, filename, xmlfile)
                extra['section'] = 'import'
                extra['temp_import_file_id'] = temp_id
              else:
                createIdsFilter = REQUEST.get('createIdsFilter')
                ids = self.importMetaobjXml(xmlfile, createIdsFilter=createIdsFilter)
                if isinstance(ids, list):
                  sync_id.extend(ids)
                else:
                  sync_id.append(ids)
                message = self.getZMILangStr('MSG_IMPORTED')%('<em>%s</em>'%filename)
          
          # Move to.
          # --------
          elif key == 'attr' and btn == 'move_to':
            pos = REQUEST['pos']
            attr_id = REQUEST['attr_id']
            self.moveMetaobjAttr( id, attr_id, pos)
            message = self.getZMILangStr('MSG_MOVEDOBJTOPOS')%(("<em>%s</em>"%attr_id), (pos+1))
          
          ##### SYNCHRONIZE ####
          types = self.valid_types+[self.metas[x*2] for x in range(len(self.metas)//2)]
          for k in self.getMetaobjIds():
            if k not in sync_id:
              if k in self.model and k in old_model:
                d = self.model[k]
                types_attrs = [(x['id'], x) for x in d.get('attrs', []) if x['type'] in types]
                d = old_model[k]
                old_types_attrs = [(x['id'], x) for x in d.get('attrs', []) if x['type'] in types]
                if types_attrs != old_types_attrs:
                  sync_id.append(k)
              else:
                sync_id.append(k)
          if len(sync_id) > 0:
            self.synchronizeObjAttrs( sync_id)
        
          # Sync with repository.
          self.getRepositoryManager().exec_auto_commit(self, id)
        
        # Handle exception.
        try:
          pass
        except:
          message = standard.writeError(self, "[manage_changeProperties]")
          messagekey = 'manage_tabs_error_message'
        
        # Return with message.
        if RESPONSE:
          if len( message) > 0:
            message += ' (in '+str(int((time.time()-t0)*100.0)/100.0)+' secs.)'
            target = self.url_append_params( target, { messagekey: message})
          target = self.url_append_params( target, { 'lang': lang, 'id':id, 'attr_id':REQUEST.get('attr_id', '')})
          target = self.url_append_params( target, extra)
          if 'inp_id_name' in REQUEST:
            target += '&inp_id_name=%s'%REQUEST.get('inp_id_name')
            target += '&inp_name_name=%s'%REQUEST.get('inp_name_name')
            target += '&inp_value_name=%s'%REQUEST.get('inp_value_name')
            target += '#Edit'
          return RESPONSE.redirect( target)
        
        return message

################################################################################
