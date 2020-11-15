# -*- coding: utf-8 -*-
################################################################################
# zmssqldb.py
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
from AccessControl import ClassSecurityInfo
from AccessControl.class_init import InitializeClass
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
import copy
import time
import zExceptions
# Product Imports.
from Products.zms import _confmanager
from Products.zms import _fileutil
from Products.zms import _globals
from Products.zms import standard
from Products.zms import zmscustom
from Products.zms import zopeutil


################################################################################
################################################################################
###
###   Constructor
###
################################################################################
################################################################################
manage_addZMSSqlDbForm = PageTemplateFile('manage_addzmssqldbform', globals()) 
def manage_addZMSSqlDb(self, lang, _sort_id, REQUEST, RESPONSE):
  """ manage_addZMSSqlDb """
  
  ##### Create ####
  id_prefix = standard.id_prefix(REQUEST.get('id_prefix', 'e'))
  new_id = self.getNewId(id_prefix)
  obj = ZMSSqlDb(new_id, _sort_id+1)
  self._setObject(obj.id, obj)
  
  obj = getattr(self, obj.id)
  ##### Object State ####
  obj.setObjStateNew(REQUEST)
  ##### Init Properties ####
  obj.manage_changeProperties(lang, REQUEST, RESPONSE)
  ##### VersionManager ####
  obj.onChangeObj(REQUEST)
  
  ##### Normalize Sort-IDs ####
  self.normalizeSortIds(id_prefix)
  
  # Return with message.
  if REQUEST.RESPONSE:
    message = self.getZMILangStr('MSG_INSERTED')%obj.display_type(REQUEST)
    REQUEST.RESPONSE.redirect('%s/%s/manage_main?lang=%s&manage_tabs_message=%s'%(self.absolute_url(), obj.id, lang, standard.url_quote(message)))


################################################################################
################################################################################
###   
###   Class
###   
################################################################################
################################################################################

class ZMSSqlDb(zmscustom.ZMSCustom):

    # Create a SecurityInfo for this class. We will use this
    # in the rest of our class definition to make security
    # assertions.
    security = ClassSecurityInfo()

    # Properties.
    # -----------
    meta_type = meta_id = "ZMSSqlDb"

    # Management Options.
    # -------------------
    manage_options = ( 
    {'label': 'TAB_EDIT',          'action': 'manage_main'},
    {'label': 'TAB_PROPERTIES',    'action': 'manage_properties'},
    {'label': 'TAB_CONFIGURATION', 'action': 'manage_configuration'},
    )

    # Management Permissions.
    # -----------------------
    __authorPermissions__ = (
        'manage', 'manage_main', 'manage_main_iframe', 'manage_workspace',
        'manage_moveObjUp', 'manage_moveObjDown', 'manage_moveObjToPos',
        'manage_cutObjects', 'manage_copyObjects', 'manage_pasteObjs',
        'manage_userForm', 'manage_user',
        'manage_zmi_input_form', 
        'manage_zmi_details_grid', 'manage_zmi_details_form',
        'manage_zmi_lazy_select_form',
        )
    __administratorPermissions__ = (
        'manage_properties', 'manage_changeProperties', 'manage_changeTempBlobjProperty',
        'manage_configuration','manage_configuration_table', 'manage_changeConfiguration',
        )
    __ac_permissions__=(
        ('ZMS Author', __authorPermissions__),
        ('ZMS Administrator', __administratorPermissions__),
        )

    # Management Interface.
    # ---------------------
    manage_zmi_input_form = PageTemplateFile('zpt/ZMSSqlDb/input_form', globals())
    manage_zmi_details_grid = PageTemplateFile('zpt/ZMSSqlDb/zmi_details_grid', globals())
    manage_zmi_details_form = PageTemplateFile('zpt/ZMSSqlDb/zmi_details_form', globals())
    manage_zmi_lazy_select_form = PageTemplateFile('zpt/ZMSSqlDb/zmi_lazy_select_form', globals())
    manage_main = PageTemplateFile('zpt/ZMSSqlDb/manage_main', globals())
    manage_properties = PageTemplateFile('zpt/ZMSSqlDb/manage_properties', globals())
    manage_configuration = PageTemplateFile('zpt/ZMSSqlDb/manage_configuration', globals())
    manage_configuration_table = PageTemplateFile('zpt/ZMSSqlDb/manage_configuration_table', globals())

    # Valid Types.
    # ------------
    valid_types = {
      'blob': {},
      'date': 1,
      'datetime': 1,
      'details': {},
      'fk': {},
      'html': 1,
      'multiselect': {},
      'multimultiselect': {},
      'pk': 1,
      'checkbox': 1,
      'password': 1,
      'richtext': 1,
      'text': 1,
      'time': 1,
      'url': 1,
    }


    ############################################################################
    ###
    ###   CONSTRUCTOR
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSSqlDb.filteredChildNodes:
    # --------------------------------------------------------------------------
    def filteredChildNodes(self, REQUEST={}, meta_types=None): 
      return []


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.getModelContainer:
    # --------------------------------------------------------------------------
    def getModelContainer( self):
      id = 'sqlmodel.xml'
      container = zopeutil.getObject(self,id)
      if container is None:
        model_xml =  getattr(self, 'model_xml', standard.str_json([]))
        container = zopeutil.addObject(self,'DTML Method',id,'SQL-Model (XML)',model_xml)
      return container


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.getModel:
    # --------------------------------------------------------------------------
    def getModel(self):
      container = self.getModelContainer()
      container_xml = zopeutil.readData(container)
      model_xml =  getattr(self, 'model_xml', None)
      if model_xml is None:
        model_xml = standard.str_json([])
        self.model_xml = model_xml
        self.model = []
      if container_xml != model_xml:
        self.model_xml = container_xml
        self.model = self.parseXmlString(self.model_xml)
      return self.model


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.setModel:
    # --------------------------------------------------------------------------
    def setModel(self, newModel):
      container = self.getModelContainer()
      id = container.id()
      zopeutil.removeObject(self,id)
      zopeutil.addObject(self,'DTML Method',id,'SQL-Model (XML)',newModel)


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.record_encode__:
    # --------------------------------------------------------------------------
    def record_encode__(self, cols, record, encoding='utf-8'):
      charset = getattr(self, 'charset', 'utf-8')
      row = {}
      for col in cols:
        k = col['id']
        v = record[k]
        if self.getConfProperty('ZMSSqlDb.record_encode__.k.lower'):
          k = k.lower()
        row[k] = v
      return row


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.getDA:
    #
    #  Return Database Adapter (DA).
    # --------------------------------------------------------------------------
    def getDA(self):
      da = None
      conn_id = getattr( self, "connection_id", None)
      if conn_id is not None:
        da = getattr(self, conn_id, None)
        if da is not None:
          if da.meta_type == 'Z MySQL Database Connection':
            # Try to re-connect if not connected.
            try: 
              dbc = da._v_database_connection 
            except AttributeError: 
              da.connect(da.connection_string) 
              dbc = da._v_database_connection
            # Try to set character-set to utf-8.
            try:
              dbc.query('SET NAMES utf8') 
              dbc.query('SET CHARACTER SET utf8')
            except:
              pass
      return da


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.getDA:
    #
    #  Return quoted value of table-column.
    # --------------------------------------------------------------------------
    def sql_quote__(self, tablename, columnname, v):
      entities = self.getEntities()
      entity = [x for x in entities if x['id'].upper()==tablename.upper()][0]
      col = ([x for x in entity['columns'] if x['id'].upper()==columnname.upper()]+[{'type':'string'}])[0]
      if col.get('nullable') and v in ['', None]:
        return "NULL"
      elif col['type'] in ['int']:
        try:
          return str(int(str(v)))
        except:
          return "NULL"
      elif col['type'] in ['float']:
        try:
          return str(float(str(v)))
        except:
          return "NULL"
      elif col['type'] in ['date', 'datetime', 'time']:
        try:
          d = self.parseLangFmtDate(v)
          if d is None:
            raise zExceptions.InternalError
          return "'%s'"%self.getLangFmtDate(d, 'eng', '%s_FMT'%col['type'].upper())
        except:
          return "NULL"
      else:
        if v.find("\'") >= 0: 
          v=''.join(v.split("\'"))
        return "'%s'"%v


    """
    Makes all changes made since the previous commit/rollback permanent and 
    releases any database locks currently held by the Connection object.
    """
    def commit(self):
      da = self.getDA()
      dbc = da._v_database_connection
      conn = dbc.getconn(False)
      conn.commit()


    """
    Undoes all changes made in the current transaction and releases any database
    locks currently held by this Connection object.
    """
    def rollback(self):
      da = self.getDA()
      dbc = da._v_database_connection
      conn = dbc.getconn(False)
      conn.rollback()


    """
    Execute sql-statement.
    Supports parameter-markers of python DB API.
    
    @param sql: The sql-statement
    @type sql: C{str}
    @param params: The values for the parameter-markers.
    @type params: C{tuple}
    @param max_rows: The maximum number of rows (default: 0, unlimited)
    @type max_rows: C{str}
    """
    def execute(self, sql, params=(), max_rows=0, encoding=None):
      da = self.getDA()
      dbc = da._v_database_connection
      c = getattr(dbc, "execute", None)
      if c is not None:
        result = dbc.execute(sql, params, max_rows)
      else:
        result = dbc.query(self.substitute_params(sql, params), max_rows)
      if encoding:
        result = self.assemble_query_result(result, encoding)
      return result


    """
    Substitute parameter-markers.
    
    @param sql: The sql-statement
    @type sql: C{str}
    @param params: The values for the parameter-markers.
    @type params: C{tuple}
    """
    def substitute_params(self, sql, params=()):
      nsl = [int,float]
      try:
        from psycopg2.extensions import Binary
        nsl.append(Binary)
      except:
        pass
      sql = sql.replace('?','%s')
      l = []
      for i in list(params):
        if i is None:
          i = "NULL"
        elif type(i) in nsl:
          i = str(i)
        else:
          i = str(i)
          i = i.replace('\'', '\'\'')
          i = '\'%s\''%i
        l.append(i)
      sql = sql%tuple(l)
      return sql


    """
    Assemble query-result.
    
    @return: Dictionary: columns C{list}, records C{list}.
    @rtype: C{dict}
    """
    def assemble_query_result(self, res, encoding=None):
      from io import StringIO
      from Shared.DC.ZRDB.Results import Results
      from Shared.DC.ZRDB import RDB
      if isinstance(res, str):
        f=StringIO()
        f.write(res)
        f.seek(0)
        result = RDB.File(f)
      else:
        result = Results(res)
      columns = []
      for result_column in result._searchable_result_columns():
        colName = result_column['name']
        colLabel = ''
        for s in colName.split('_'):
          colLabel += s.capitalize()
        try:
          colType = {'i':'int','n':'float','t':'string','s':'string','d':'datetime','l':'string'}[result_column['type']]
        except:
          colType = result_column.get('type', None)
          standard.writeError(self, '[query]: Column ' + colName + ' has unknown type ' + str(colType) + '!')
        column = {}
        column['id'] = colName
        column['key'] = colName
        column['label'] = colLabel
        column['name'] = colLabel
        column['type'] = colType
        column['sort'] = 1
        columns.append(column)
      if encoding:
        result = [self.record_encode__(columns, x, encoding) for x in result]
      return {'columns':columns,'records':result}


    """
    Execute select-statement.
    
    @param sql: The select-statement
    @type sql: C{str}
    @param max_rows: The maximum number of rows (default: 0, unlimited)
    @type max_rows: C{str}
    @return: Dictionary: columns C{list}, records C{list}.
    @rtype: C{dict}
    """
    def query(self, sql, max_rows=0, encoding=None):
      standard.writeLog( self, '[query]: sql=%s, max_rows=%i'%(sql, max_rows))
      da = self.getDA()
      dbc = da._v_database_connection
      if da.meta_type == 'Z SQLite Database Connection': sql = str(sql)
      return self.assemble_query_result(dbc.query(sql, max_rows), encoding)


    """
    Execute modify-statement.
    @param sql: The modify-statement
    @type sql: C{str}
    @return: Number of affected rows.
    @rtype: C{int}
    """
    def executeQuery(self, sql):
      from io import StringIO
      from Shared.DC.ZRDB.Results import Results
      from Shared.DC.ZRDB import RDB
      standard.writeBlock( self, '[executeQuery]: sql=%s'%sql)
      result = []
      if self.getConfProperty('ZMSSqlDb.execute', 1)==1:
        da = self.getDA()
        dbc = da._v_database_connection
        res = dbc.query(sql)
        if isinstance(res, str):
          f=StringIO()
          f.write(res)
          f.seek(0)
          result=RDB.File(f)
        else:
          result=Results(res)
      return len(result)


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.getEntityPK:
    #
    #  Returns primary key.
    # --------------------------------------------------------------------------
    def getEntityPK(self, tableName):
      columns = self.getEntity( tableName)['columns']
      # @todo
      pk = columns[0]['id']
      return pk


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.getEntityRecordHandler
    # --------------------------------------------------------------------------
    def getEntityRecordHandler(self, tableName, stereotypes=['*']):
      class EntityRecordHandler(object):
        def __init__(self, parent, tableName):
          self.parent = parent 
          self.tableName = tableName
        handle_record__roles__ = None
        def handle_record(self, r):
          context = self.parent
          d = {}
          for k in r:
            value = r[k]
            try:
              column = context.getEntityColumn(self.tableName, k, r)
              if '*' in stereotypes or len([x for x in stereotypes if x in column]) > 0:
                value =  column.get('value', value)
                if 'options' in column:
                  o = column['options']
                  v = value
                  if v:
                    value = []
                    if not isinstance(v, list):
                      v = [v]
                    for i in v:
                      l = [x for x in o if str(x[0])==str(i)]
                      if len(l) > 0:
                        value .append(l[0][1])
                    value = ', '.join(value)
            except:
              standard.writeError( self, '[getEntityRecordHandler]: can\'t %s'%k)
            d[k] = value
          primary_key = context.getEntityPK(tableName)
          rowid = context.operator_getitem(d, primary_key, ignorecase=True)
          d['__id__'] = rowid
          d['params'] = {'rowid':rowid}
          return d
      return EntityRecordHandler(self, tableName)


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.getEntityColumn:
    # --------------------------------------------------------------------------
    def getEntityColumn(self, tableName, columnName, row=None):
      column = {}
      try:
        request = self.REQUEST
        lang = request.get('lang', self.getPrimaryLanguage())
        encoding = getattr(self, 'charset', 'utf-8')
        qcharset = self.REQUEST.get('qcharset', 'utf-8')
        entity = self.getEntity(tableName)
        primary_key = self.getEntityPK(tableName)
        columns = entity['columns']
        column = copy.deepcopy([x for x in columns if x['id'].upper()==columnName.upper()][0])
        column['id'] = column['id'].lower()
        column['label'] = self.getLangStr(column['label'], lang)
        # Checkbox
        stereotype = column.get('checkbox')
        if stereotype not in ['', None]:
          column['type'] = 'boolean'
        # Url
        stereotype = column.get('url')
        if stereotype not in ['', None]:
          column['datatype_key'] = _globals.DT_URL
        # Blob
        stereotype = column.get('blob')
        if stereotype not in ['', None]:
          value = None
          column['type'] = stereotype['type']
          if row is not None:
            rowid = self.sql_quote__(tableName, primary_key, self.operator_getitem(row, primary_key, ignorecase=True))
            class BlobWrapper(object):
              def __init__(self, tableName, columnName, rowid, blob):
                self.tableName = tableName
                self.columnName = columnName
                self.rowid = rowid
                self.blob = blob
              getHref__roles__=None
              def getHref(self, request):
                href = 'get_blob?tablename=%s&id=%s&rowid=%s'%(self.tableName, self.columnName, rowid)
                if request.get('preview')=='preview':
                  href += '&preview=preview'
                return href
              getContentType__roles__=None
              def getContentType(self):
                return self.blob.getContentType()
              getFilename__roles__ = None
              def getFilename(self):
                return self.blob.filename
              getWidth__roles__ = None
              def getWidth(self):
                return self.blob.getWidth()
              getHeight__roles__ = None
              def getHeight(self):
                return self.blob.getHeight()
              get_size__roles__ = None
              def get_size(self):
                return self.blob.get_size()
            blob = self._get_blob(tableName, columnName, rowid)
            if blob is not None:
              value = BlobWrapper(tableName, columnName, rowid, blob)
          column['value'] = value
        # Text
        stereotype = column.get('text')
        if stereotype not in ['', None]:
          column['type'] = 'text'
        # Richtext
        stereotype = column.get('richtext')
        if stereotype not in ['', None]:
          column['type'] = 'richtext'
        # Select
        stereotype = column.get('fk')
        if isinstance(stereotype, dict):
          value = None
          options = []
          if row is not None:
            value = self.operator_getitem(row, columnName, ignorecase=True)
            # Select.MySQLSet
            if 'mysqlset' in stereotype:
              for r in self.query( 'DESCRIBE %s %s'%(tableName, columnName))['records']:
                rtype = r['type']
                for i in rtype[rtype.find('(')+1:rtype.rfind(')')].replace('\'', '').split(','):
                  options.append([i, i])
            # Select.Options
            elif 'options' in stereotype:
              options.extend(stereotype['options'])
            # Select.Fk
            elif 'tablename' in stereotype:
              sql = []
              sql.append( 'SELECT ' + stereotype['fieldname'] + ' AS qkey, ' + stereotype['displayfield'] + ' AS qvalue FROM ' + stereotype['tablename'])
              if 'lazy' in stereotype:
                where = ['1=0']
                v = value
                if v:
                  if not isinstance(v, list):
                    v = [v]
                  for i in v:
                    where.append( stereotype['fieldname'] + '=' + self.sql_quote__(stereotype['tablename'], stereotype['fieldname'], i))
                sql.append( 'WHERE ' + ' OR '.join(where))
              sql.append( 'ORDER BY ' + str(stereotype.get('sort', 2)))
              column['valuesql'] = '\n'.join(sql)
              for r in self.query('\n'.join(sql))['records']:
                qkey = r['qkey']
                qvalue = r['qvalue']
                options.append([qkey, qvalue])
          column['value'] = value
          column['options'] = options
        
        # Multiselect
        stereotype = column.get('multiselect')
        if isinstance(stereotype, dict):
          value = []
          options = []
          src = None
          dst = None
          if 'tablename' in stereotype and 'fk' in stereotype:
            intersection = self.getEntity(stereotype['tablename'])
            intersection_fk = [x for x in intersection['columns'] if isinstance(x.get('fk'), dict) and 'tablename' in x['fk']]
            column['intersection_fk'] = intersection_fk
            src = [x for x in intersection_fk if x['id'].upper()==stereotype['fk'].upper() and x['fk']['tablename'].upper()==tableName.upper()][0]
            dst = [x for x in intersection_fk if x['id'].upper()!=stereotype['fk'].upper() or x['fk']['tablename'].upper()!=tableName.upper()][0]
          # Multiselect.Selected
          if src is not None and dst is not None and row is not None:
            sql = '' \
              + 'SELECT ' + dst['id'] + ' AS dst_id ' \
              + 'FROM ' + intersection['id'] + ' ' \
              + 'WHERE ' + src['id'] + '=' + self.sql_quote__(tableName, primary_key, self.operator_getitem(row, primary_key, ignorecase=True))
            column['valuesql'] = sql
            for r in self.query(sql)['records']:
              value.append(r['dst_id'])
          # Multiselect.MySQLSet
          if 'mysqlset' in stereotype:
            if row is not None:
              value = standard.nvl(self.operator_getitem(row, columnName, ignorecase=True), '').split(',')
              for r in self.query( 'DESCRIBE %s %s'%(tableName, columnName))['records']:
                rtype = r['type']
                for i in rtype[rtype.find('(')+1:rtype.rfind(')')].replace('\'', '').split(','):
                  options.append([i, i])
          # Multiselect.Options
          elif dst is not None and 'options' in dst['fk']:
            options.extend(dst['fk']['options'])
          # Multiselect.Fk
          elif dst is not None and 'tablename' in dst['fk']:
            sql = []
            sql.append('SELECT ' + dst['fk']['fieldname'] + ' AS qkey, ' + dst['fk']['displayfield'] + ' AS qvalue')
            sql.append('FROM ' + dst['fk']['tablename'])
            if 'lazy' in stereotype and row is not None:
              where = ['1=0']
              v = value
              if v:
                if not isinstance(v, list):
                  v = [v]
                for i in v:
                  where.append( dst['fk']['fieldname'] + '=' + self.sql_quote__(dst['fk']['tablename'], dst['fk']['fieldname'], i))
              sql.append( 'WHERE ' + ' OR '.join(where))
            column['valuesql'] = '\n'.join(sql)
            for r in self.query('\n'.join(sql))['records']:
              qkey = r['qkey']
              qvalue = r['qvalue']
              options.append([qkey, qvalue])
          column['src'] = src
          column['dst'] = dst
          column['value'] = value
          column['options'] = options
        
        # Details
        stereotype = column.get('details')
        if isinstance(stereotype, dict):
          details = self.getEntity(stereotype['tablename'])
          # Details.Intersection
          if details['type']=='intersection':
            if row:
              ldst = [x for x in details['columns'] if x.get('fk') is not None and 'tablename' in x['fk'] and x['fk']['tablename']!=tableName]
              columns = []
              joins = []
              for x in [x['id'] for x in details['columns'] if x.get('datatype', '?')!='?']:
                columns.append(x)
                fdst = [x for x in ldst if x==dst['id']]
                if fdst:
                  dst = fdst[0]
                  fktablename = dst['fk']['tablename']
                  fkfieldname = dst['fk']['fieldname']
                  fkdisplayfield = dst['fk']['displayfield']
                  if fkdisplayfield.upper().find('%s.'%fktablename.upper())<0:
                    fkdisplayfield = '%s.%s'%(fktablename, fkdisplayfield)
                  columns.append('%s AS %s_label'%(fkdisplayfield, x))
                  joins.append('LEFT OUTER JOIN '+fktablename+' ON '+x+'=%s.%s '%(fktablename, fkfieldname))
              sql = '' \
                + 'SELECT '+', '.join(columns)+' ' \
                + 'FROM '+stereotype['tablename']+' ' \
                + '\n'.join(joins) \
                + 'WHERE '+stereotype['fk']+'=' + self.sql_quote__(tableName, primary_key, self.operator_getitem(row, primary_key, ignorecase=True)) 
              column['valuesql'] = sql
              column['value'] = []
              try:
                records = self.query(sql, encoding=encoding)['records']
                column['value'] = records
              except:
                column['error'] = standard.writeError(self, 'can\'t get value')
          # Details.Table
          else:
            if row:
              sql = '' \
                + 'SELECT * ' \
                + 'FROM '+stereotype['tablename']+' ' \
                + 'WHERE '+stereotype['fk']+'='+self.sql_quote__(tableName, primary_key, self.operator_getitem(row, primary_key, ignorecase=True))
              column['valuesql'] = sql
              column['value'] = []
              try:
                records = self.query(sql, encoding=encoding)['records']
                column['value'] = records
              except:
                column['error'] = standard.writeError(self, 'can\'t get value')
        
        # Multimultiselect
        stereotype = column.get('multimultiselect')
        if isinstance(stereotype, dict):
          items = stereotype.get('tables', [])
          for item in items:
            if item.get('lazy'):
              pass
            else:
              options = []
              sql = '' \
                + 'SELECT ' + item['fieldname'] + ' AS qkey, ' + item['displayfield'] + ' AS qvalue ' \
                + 'FROM ' + item['tablename'] + ' ' \
                + 'ORDER BY ' + item['displayfield']
              for r in self.query(sql)['records']:
                qkey = r['qkey']
                qvalue = r['qvalue']
                options.append([qkey, qvalue])
              stereotype['options'] = stereotype.get('options', {})
              stereotype['options'][item['tablename']] = options
          value = []
          if row:
            columns  = []
            leftjoins = []
            outerjoins = []
            for item in items:
              i = items.index(item)
              if item['fieldname'].find(item['tablename']+'.') < 0:
                item['fieldname'] = item['tablename']+'.'+item['fieldname'] 
              columns.append(item['fieldname']+' AS fk%i'%i)
              if item['displayfield'].find(item['tablename']+'.') < 0:
                item['displayfield'] = item['tablename']+'.'+item['displayfield'] 
              columns.append(item['displayfield']+' AS displayfield%i'%i)
              join = item['tablename']+' ON '+stereotype['tablename']+'.'+item['fk']+'='+item['fieldname']
              if item.get('nullable'):
                outerjoins.append(join)
              else:
                leftjoins.append(join)
            sql = []
            sql.append('SELECT '+', '.join(columns))
            sql.append(' FROM '+stereotype['tablename'])
            if leftjoins:
              sql.append(' LEFT JOIN '.join(['']+leftjoins))
            if outerjoins:
              sql.append(' LEFT OUTER JOIN '.join(['']+outerjoins))
            sql.append(' WHERE ' + stereotype['tablename'] + '.' + stereotype['fk'] + '=' + self.sql_quote__(tableName, primary_key, self.operator_getitem(row, primary_key, ignorecase=True)))
            column['valuesql'] = '\n'.join(sql)
            for r in self.query('\n'.join(sql))['records']:
              v = []
              l = []
              for item in items:
                i = items.index(item)
                qkey = ''
                qvalue = ''
                if r['fk%i'%i]:
                  qkey = str(r['fk%i'%i])
                  qvalue = str(r['displayfield%i'%i])
                v.append(qkey)
                l.append(qvalue)
              value.append(('|'.join(v), ' | '.join(l)))
          column['value']= value
        
        return column
      except:
        return standard.writeError(self, '[getEntityColumn]: can\'t %s.%s (%s)'%(tableName, columnName, str(column)))


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.getEntity:
    # --------------------------------------------------------------------------
    def getEntity(self, tableName):
      entities = self.getEntities()
      return [x for x in entities if x['id'].upper()==tableName.upper()][0]


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.getEntities:
    # --------------------------------------------------------------------------
    def getEntities(self):

      #-- [ReqBuff]: Fetch buffered value from Http-Request.
      REQUEST = self.REQUEST
      reqBuffId = 'getEntities'
      try: return self.fetchReqBuff( reqBuffId)
      except: pass
      
      entities = []
      da = self.getDA()
      if da is None: return entities
      
      tableBrwsrs = da.tpValues()
      
      # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
      # +- ENTITES
      # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
      
      #-- for custom entities please refer to $ZMS_HOME/conf/db/getEntities.Oracle.py
      method = getattr(self, 'getEntities%s'%self.connection_id, None)
      if method is not None:
        entities = method( self, REQUEST)
      
      #-- retrieve entities from table-browsers
      if len( entities) == 0:
        for tableBrwsr in tableBrwsrs:
          tableName = str(getattr(tableBrwsr, 'Name', getattr(tableBrwsr, 'name', None))())
          tableType = str(getattr(tableBrwsr, 'Type', getattr(tableBrwsr, 'type', None))())
          if tableType.upper() == 'TABLE':
            
            # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
            # +- COLUMNS
            # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
            cols = []
            try:
              columnBrwsrs = []
              if da.meta_type == 'Z SQLite Database Connection':
                for columnBrwsr in tableBrwsr.tpValues():
                  desc = getattr(columnBrwsr, 'Description', getattr(columnBrwsr, 'description', None))().upper()
                  desc = desc[desc.find("(")+1:desc.rfind(")")]
                  for cc in desc.split(","):
                    c = ''
                    for l in cc.split("\n"):
                      if l.find('--') >= 0:
                        l = l[:l.find('--')]
                      l = l.strip()
                      if len(l) > 0:
                        c += l + ' '
                    cl = [x for x in c.split(' ') if x.strip()]
                    if len(cl) >= 2:
                      cid = cl[0]
                      if cid.startswith('"') and cid.endswith('"'):
                        cid = cid[1:-1]
                      ucid = cid.upper() 
                      uctype = cl[1].upper()
                      if not ucid in ['CHECK', 'FOREIGN', 'PRIMARY'] and not uctype.startswith('KEY') and not uctype.startswith('(') and not ucid.startswith('\''):
                        col = {}
                        col["id"] = cid
                        col["description"] = ' '.join(cl[1:])
                        columnBrwsrs.append(col)
              else:
                for columnBrwsr in tableBrwsr.tpValues():
                  col = {}
                  col["id"] = columnBrwsr.tpId()
                  col["description"] = getattr(columnBrwsr, 'Description', getattr(columnBrwsr, 'description', None))().upper()
                  columnBrwsrs.append(col)
              for columnBrwsr in columnBrwsrs:
                colId = columnBrwsr["id"]
                colDescr = columnBrwsr["description"]
                colType = 'string'
                colSize = None
                if colDescr.find('INT') >= 0:
                  colType = 'int'
                elif colDescr.find('DATE') >= 0 or \
                     colDescr.find('TIME') >= 0:
                  colType = 'datetime'
                elif colDescr.find('CLOB') >= 0:
                  colType = 'text'
                elif colDescr.find('CHAR') >= 0 or \
                     colDescr.find('STRING') >= 0:
                  colSize = 255
                  i = colDescr.find('(')
                  if i >= 0:
                    j = colDescr.find(')')
                    if j >= 0:
                      colSize = int(colDescr[i+1:j])
                  if colSize > 255:
                    colType = 'text'
                  else:
                    colType = 'string'
                col = {}
                col['key'] = colId
                col['description'] = colDescr.strip()
                col['id'] = col['key']
                col['index'] = int(col.get('index', len(cols)))
                col['label'] = ' '.join([x.capitalize() for x in colId.split('_')]).strip()
                col['name'] = col['label']
                col['mandatory'] = colDescr.find('NOT NULL') > 0
                col['type'] = colType
                col['sort'] = 1
                col['nullable'] = not col['mandatory']
                # Add Column.
                cols.append(col)
            except:
              standard.writeError(self, '[getEntities]')
            
            # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
            # +- TABLE
            # +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
            if len(cols) > 0:
              entity = {}
              entity['id'] = tableName
              entity['type'] = 'table'
              entity['label'] = ' '.join([x.capitalize() for x in tableName.split('_')]).strip()
              entity['sort_id'] = entity['label'].upper()
              entity['columns'] = standard.sort_list(cols, 'index')
              # Add Table.
              entities.append(entity)
      
      #-- Custom properties
      model = self.getModel()
      s = []
      for entity in entities:
        tableName = entity['id']
        tableInterface = entity.get('interface', '')
        cols = []
        colNames = []
        for col in entity['columns']:
          colName = col['id'].upper()
          # Set custom column-properties
          for modelTable in [x for x in model if x['id'].upper()==tableName.upper()]:
            for modelTableCol in [x for x in modelTable.get('columns', []) if x['id'].upper()==colName]:
              for modelTableColProp in [x for x in modelTableCol if x not in ['id']]:
                col[modelTableColProp] = modelTableCol[modelTableColProp]
          cols.append(col)
          colNames.append(colName)
        # Add custom columns
        for modelTable in [x for x in model if x['id'].upper()==tableName.upper()]:
          tableInterface = modelTable.get('interface', tableInterface)
          for modelTableCol in [x for x in modelTable.get('columns', []) if x['id'].upper() not in colNames]:
            col = modelTableCol
            col['id'] = col.get('id', '?')
            col['index'] = int(col.get('index', len(cols)))
            col['type'] = col.get('type', '?')
            col['key'] = col.get('key', col.get('id'))
            col['label'] = col.get('label', col.get('id'))
            col['stereotypes'] = standard.intersection_list( list(self.valid_types), list(col))
            col['not_found'] = col.get('description') is None and len(col.get('stereotypes', []))==0
            cols.insert(col['index'], col)
            colNames.append(col['id'].upper())
        entity['interface'] = tableInterface
        entity['columns'] = standard.sort_list(cols, 'index')
        # Set custom table-properties
        for modelTable in [x for x in model if x['id'].upper()==tableName.upper()]:
          for modelTableProp in [x for x in modelTable if x not in ['columns']]:
            entity[modelTableProp] = modelTable[modelTableProp]
            entity['sort_id'] = entity['label'].upper()
        # Add
        s.append((entity['label'], entity))
      
      #-- Custom entities.
      for entity in model:
        tableName = entity['id']
        if 'not_found' in entity:
          del entity['not_found']
        if tableName.upper() not in [x['id'].upper() for x in entities]:
          cols = entity.get('columns', [])
          entity['id'] = tableName
          entity['type'] = entity.get('type', 'table')
          entity['label'] = entity.get('label', ' '.join([x.capitalize() for x in tableName.split('_')]).strip())
          entity['sort_id'] = entity['label'].upper()
          entity['columns'] = standard.sort_list(cols, 'index')
          # Add Table.
          entity['not_found'] = 1
          s.append((entity['label'], entity))
      
      #-- Sort entities
      s.sort()
      entities = [x[1] for x in s]
      
      #-- Defaults
      for entity in entities:
        for column in entity['columns']:
          #column['id'] = column['id'].lower()
          column['multilang'] = False
          column['datatype'] = column.get('type', '?')
          column['datatype_key'] = _globals.datatype_key(column['datatype'])
      
      #-- [ReqBuff]: Returns value and stores it in buffer of Http-Request.
      return self.storeReqBuff( reqBuffId, entities)


    ############################################################################
    ###
    ###   RecordSet
    ###
    ############################################################################

    """
    @rtype: C{string}
    """
    def recordSet_Select(self, tablename, select=None, where=None):
      tabledef = self.getEntity(tablename)
      tablecols = tabledef['columns']
      selectClause = []
      fromClause = [ tablename]
      whereClause = []
      if where:
        whereClause.append( where)
      if select:
        selectClause.append( select)
      else:
        fk_tablename_counter = {}
        table_AS = self.getConfProperty('ZMSSqlDb.table.AS', 'AS')
        for tablecol in tablecols:
          if tablecol.get('fk') and tablecol['fk'].get('tablename'):
            fk_tablename = tablecol['fk']['tablename']
            fk_tablename_counter[fk_tablename] = fk_tablename_counter.get(fk_tablename, 0)+1
            fk_tablename_alias = '%s%i'%(fk_tablename, fk_tablename_counter[fk_tablename])
            fk_fieldname = tablecol['fk']['fieldname']
            if fk_fieldname.upper().find(fk_tablename.upper()+'.') < 0:
              fk_fieldname = fk_tablename+'.'+fk_fieldname
            fk_fieldname = standard.re_sub( fk_tablename+'\.', fk_tablename_alias+'.', fk_fieldname, ignorecase=True)
            fk_displayfield = tablecol['fk']['displayfield']
            if fk_displayfield.upper().find(fk_tablename.upper()+'.') < 0:
              fk_displayfield = fk_tablename+'.'+fk_displayfield
            fk_displayfield = standard.re_sub( fk_tablename+'\.', fk_tablename_alias+'.', fk_displayfield, ignorecase=True)
            selectClause.append( '%s AS %s'%(fk_displayfield, tablecol['id']))
            fromClause.append( 'LEFT JOIN %s %s %s ON %s.%s=%s'%(fk_tablename, table_AS, fk_tablename_alias, tablename, tablecol['id'], fk_fieldname))
          elif tablecol.get('type', '?') != '?':
            selectClause.append( '%s.%s'%(tablename, tablecol['id']))
      sqlStatement = []
      sqlStatement.append( 'SELECT '+' , '.join(selectClause)+' ')
      sqlStatement.append( 'FROM '+' '.join(fromClause)+' ')
      if whereClause:
        sqlStatement.append( 'WHERE '+' AND '.join(whereClause)+' ')
      return ''.join(sqlStatement)


    """
    Initializes record-set.
    
    @param REQUEST: the triggering request
    @type REQUEST: ZPublisher.HTTPRequest
    @rtype: C{None}
    """
    def recordSet_Init(self, REQUEST):
      tabledefs = [x for x in self.getEntities() if not x.get('not_found')]
      tablename = standard.get_session_value(self,'qentity_%s'%self.id)
      #-- Sanity check.
      standard.set_session_value(self,'qentity_%s'%self.id, '')
      REQUEST.set('primary_key', '')
      REQUEST.set('grid_cols', [])
      sqlStatement = REQUEST.get('sqlStatement', [])
      if not isinstance(sqlStatement, list):
        sqlStatement = []
      if len(tabledefs) > 0:
        if tablename not in [x['id'] for x in tabledefs]:
          tablename = tabledefs[0]['id']
        tablename = REQUEST.form.get('qentity', tablename)
        tabledef = [x for x in tabledefs if x['id'].upper()==tablename.upper()][0]
        sqlStatement.append( self.recordSet_Select( tablename))
        tablecols = tabledef['columns']
        # Primary Key.
        primary_key = [x['id'] for x in tablecols if x.get('pk', 0)==1]
        primary_key.append(None)
        #-- Set environment.
        standard.set_session_value(self,'qentity_%s'%self.id, tablename)
        REQUEST.set('qentity', tablename)
        REQUEST.set('tabledef', tabledef)
        REQUEST.set('grid_cols', tablecols)
        REQUEST.set('primary_key', primary_key[0])
      REQUEST.set('sqlStatement', sqlStatement)


    """
    Assemble filter for where-clause
    
    @param l list of columns to filter
    @return: expression
    @rtype: C{string}
    """
    def assembleFilter(self, l):
      sql = []
      for d in l:
        tablename     = d['tablename']
        columnname    = d['columnname']
        qualifiedname = d.get('qualifiedname', columnname)
        op            = d['op']
        value         = d['value']
        if op=='':
          op = '='
        if op in [ 'NULL', 'NOT NULL']:
          sqlStatement.append('%s IS %s'%(qualifiedname, op))
        elif value != '':
          if op in ['LIKE']:
            if not value.endswith('%'):
              value += '%'
            name = 'LOWER(%s)'%qualifiedname
          sql.append('%s %s %s '%(qualifiedname, op, self.sql_quote__(tablename, columnname, value)))
      return ' AND '.join(sql)


    """
    Filter record-set by appending where clause to sql-statement.
    
    @param REQUEST: the triggering request
    @type REQUEST: ZPublisher.HTTPRequest
    @rtype: C{None}
    """
    def recordSet_Filter(self, REQUEST):
      sqlStatement = REQUEST.get('sqlStatement', [])
      # init filter from request.
      for filterIndex in range(100):
        for filterStereotype in ['attr', 'op', 'value']:
          requestkey = 'filter%s%i'%(filterStereotype, filterIndex)
          sessionkey = '%s_%s'%(requestkey, self.id)
          requestvalue = REQUEST.form.get(requestkey, standard.get_session_value(self,sessionkey, ''))
          if REQUEST.get('btn')=='BTN_RESET':
            requestvalue = ''
          REQUEST.set(requestkey, requestvalue)
          standard.set_session_value(self,sessionkey, requestvalue)
      standard.set_session_value(self,'qfilters_%s'%self.id, REQUEST.form.get('qfilters', standard.get_session_value(self,'qfilters_%s'%self.id, 1)))
      # apply filter
      tablename = standard.get_session_value(self,'qentity_%s'%self.id)
      tabledefs = [x for x in self.getEntities() if not x.get('not_found')]
      if len(tabledefs) > 0:
        tabledef = [x for x in tabledefs if x['id'].upper()==tablename.upper()][0]
        tablecols = tabledef['columns']
        l = []
        for filterIndex in range(100):
          suffix = '%i_%s'%(filterIndex, self.id)
          sessionattr = standard.get_session_value(self,'filterattr%s'%suffix, '')
          sessionop = standard.get_session_value(self,'filterop%s'%suffix, '')
          sessionvalue = standard.get_session_value(self,'filtervalue%s'%suffix, '')
          if sessionattr and sessionvalue:
            fk_tablename_counter = {}
            for tablecol in tablecols:
              if tablecol.get('fk') and tablecol['fk'].get('tablename'):
                fk_tablename = tablecol['fk']['tablename']
                fk_tablename_counter[fk_tablename] = fk_tablename_counter.get(fk_tablename, 0)+1
                fk_tablename_alias = '%s%i'%(fk_tablename, fk_tablename_counter[fk_tablename])
                fk_displayfield = tablecol['fk']['displayfield']
                if fk_displayfield.find(fk_tablename+'.') < 0:
                  fk_displayfield = fk_tablename+'.'+fk_displayfield
                coltable = fk_tablename
                colname = standard.re_sub( fk_tablename+'\.', fk_tablename_alias+'.', fk_displayfield, ignorecase=True)
                qualifiedname = colname
                if sessionop == '':
                  sessionop = 'LIKE'
                  sessionvalue += '%'
              else:
                coltable = tablename
                colname = tablecol['id']
                qualifiedname = '%s.%s'%(coltable, colname)
                if tablecol['datatype_key'] in _globals.DT_STRINGS:
                  if sessionop == '':
                    sessionop = 'LIKE'
                    sessionvalue += '%'
              if sessionattr.upper() == tablecol['id'].upper():
                l.append({'tablename':coltable,'columnname':colname,'qualifiedname':qualifiedname,'op':sessionop,'value':sessionvalue})
        #-- WHERE
        whereClause = self.assembleFilter(l)
        if len(whereClause) > 0:
          if ''.join(sqlStatement).upper().find('WHERE ') < 0:
            sqlStatement.append('WHERE ')
          else:
            sqlStatement.append('AND ')
          sqlStatement.append('(%s) '%whereClause)
        # TABLE-FILTER
        tablefilter = standard.dt_exec(self, tabledef.get('filter', ''))
        if len(tablefilter) > 0:
          if ''.join(sqlStatement).upper().find('WHERE ') < 0:
            sqlStatement.append('WHERE ')
          else:
            sqlStatement.append('AND ')
          sqlStatement.append('(%s) '%tablefilter)
      REQUEST.set('sqlStatement', sqlStatement)


    """
    Sort record-set by appending order-by clause to sql-statement.
    
    @param REQUEST: the triggering request
    @type REQUEST: ZPublisher.HTTPRequest
    @rtype: C{None}
    """
    def recordSet_Sort(self, REQUEST):
      tablename = standard.get_session_value(self,'qentity_%s'%self.id)
      tabledefs = [x for x in self.getEntities() if not x.get('not_found')]
      #-- Sanity check.
      qorder = REQUEST.get('qorder', standard.get_session_value(self,'qorder_%s'%self.id, ''))
      qorderdir = REQUEST.get('qorderdir', standard.get_session_value(self,'qorderdir_%s'%self.id, 'asc'))
      sqlStatement = REQUEST.get('sqlStatement', [])
      if len(tabledefs) > 0:
        tabledef = [x for x in tabledefs if x['id'].upper()==tablename.upper()][0]
        tablecols = tabledef['columns']
        #-- ORDER BY
        if qorder == '' or not qorder.lower() in [x['id'].lower() for x in tablecols]:
          for col in tablecols:
            if col.get('hide', 0) != 1:
              qorder = '%s.%s'%(tablename, col['id'])
              if col.get('type', '') in ['date', 'datetime', 'time']:
                qorderdir = 'desc'
              break
        if qorder:
          sqlStatement.append('ORDER BY ' + qorder + ' ' + qorderdir + ' ')
      REQUEST.set('sqlStatement', sqlStatement)
      REQUEST.set('qorder', qorder)
      REQUEST.set('qorderdir', qorderdir)
      standard.set_session_value(self,'qorder_%s'%self.id, qorder)
      standard.set_session_value(self,'qorderdir_%s'%self.id, qorderdir)


    ############################################################################
    ###
    ###   Actions
    ###
    ############################################################################

    """
    Get reference for foreign-key relation.
    
    @param tablename: Name of the SQL-Table.
    @type tablename: C{string}
    @return: ID of the row that was inserted.
    @rtype: int
    """
    def getFk(self, tablename, id, name, value, createIfNotExists=1):
      self.writeBlock('[getFk]: tablename=%s, id=%s, name=%s, value=%s, createIfNotExists=%s'%(tablename, id, name, str(value), str(createIfNotExists)))
      tabledefs = self.getEntities()
      tabledef = [x for x in tabledefs if x['id'].upper()==tablename.upper()][0]
      tablecols = tabledef['columns']
      primary_key = ([x['id'] for x in tablecols if x.get('pk', 0)==1]+[tablecols[0]['id']])[0]
      
      # Find existing row-id.
      sqlStatement = []
      sqlStatement.append( 'SELECT %s AS existing_id FROM %s'%(primary_key, tablename))
      sqlStatement.append( 'WHERE %s=%s'%(primary_key, self.sql_quote__(tablename, primary_key, value)))
      sqlStatement.append( 'OR %s=%s'%(name, self.sql_quote__(tablename, name, value)))
      sqlStatement = ' '.join(sqlStatement)
      try:
        rs = self.query(sqlStatement)['records']
        if len(rs) == 1:
          rowid = rs[0]['existing_id']
          return rowid
      except:
        raise zExceptions.InternalError(standard.writeError( self, '[getFk]: can\'t find existing row - sqlStatement=' + sqlStatement))
      
      rowid = None
      if createIfNotExists:
        # Get columns to insert
        c = []
        tablecol = tablecols[0]
        if tablecol.get('auto'):
          new_id = 0
          try:
            rs = self.query('SELECT MAX(%s) AS max_id FROM %s'%(primary_key, tablename))['records']
            if len(rs) == 1:
              new_id = int(rs[0]['max_id'])+1
          except:
            standard.writeError( self, '[getFk]: can\'t get max_id')
          c.append({'id':id,'value':str(new_id)})
        c.append({'id':name,'value':self.sql_quote__(tablename, name, value)})
        
        # Assemble sql-statement
        sqlStatement = []
        sqlStatement.append( 'INSERT INTO %s ('%tablename)
        sqlStatement.append( ', '.join([x['id'] for x in c]))
        sqlStatement.append( ') VALUES (')
        sqlStatement.append( ', '.join([x['value'] for x in c]))
        sqlStatement.append( ')')
        sqlStatement = ' '.join(sqlStatement)
        try:
          self.executeQuery( sqlStatement)
        except:
          raise zExceptions.InternalError(standard.writeError( self, '[createFk]: can\'t insert row - sqlStatement=' + sqlStatement))
        
        # Return with row-id.
        rowid = ([x for x in c if x['id']==primary_key]+[{'value':None}])[0]['value']
        if rowid is None:
          sqlStatement = []
          sqlStatement.append( 'SELECT %s AS value FROM %s WHERE '%(primary_key, tablename))
          sqlStatement.append( ' AND '.join([x['id']+'='+x['value'] for x in c if x['value'].upper()!='NULL']))
          sqlStatement = ' '.join(sqlStatement)
          try:
            for r in self.query( sqlStatement)['records']:
              rowid = r['value']
          except:
            raise zExceptions.InternalError(standard.writeError( self, '[createFk]: can\'t get primary-key - sqlStatement=' + sqlStatement))
      
      return rowid


    """
    Insert row into record-set.
    @param tablename: Name of the SQL-Table.
    @type tablename: C{string}
    @param values: Columns (id/value) to be inserted.
    @type values: C{dict}
    @return: ID of the row that was inserted.
    @rtype: C{any}
    """
    def recordSet_Insert(self, tablename, values={}, update_intersections=False):
      standard.triggerEvent(self.getParentNode(), '%s%sBeforeInsert'%(self.id, tablename.capitalize()))
      REQUEST = self.REQUEST
      auth_user = REQUEST.get('AUTHENTICATED_USER')
      lang = REQUEST['lang']
      da = self.getDA()
      if tablename is None:
        raise zExceptions.InternalError("[recordSet_Insert]: tablename must not be None!")
      tabledefs = self.getEntities()
      tabledef = [x for x in tabledefs if x['id'].upper()==tablename.upper()][0]
      tablecols = tabledef['columns']
      primary_key = ([x['id'] for x in tablecols if x.get('pk', 0)==1]+[tablecols[0]['id']])[0]
      
      # Get columns to insert
      blobs = {}
      c = []
      for tablecol in tablecols:
        id = tablecol['id']
        consumed = id in REQUEST.get('qexcludeids', [])
        if not consumed and tablecol.get('password'):
          if id in values:
            value = values.get(id)
            if value != '' and value != '******':
              c.append({'id':id,'value':value})
          consumed = True
        if not consumed and tablecol.get('auto'):
          if tablecol.get('auto') in ['insert', 'update']:
            if tablecol.get('type') in ['date', 'datetime']:
              c.append({'id':id,'value':self.getLangFmtDate(time.time(), lang, '%s_FMT'%tablecol['type'].upper())})
            elif tablecol.get('type') in ['int']:
              new_id = 0
              try:
                rs = self.query('SELECT MAX(%s) AS max_id FROM %s'%(id, tablename))['records']
                if len(rs) == 1:
                  new_id = int(rs[0]['max_id'])+1
              except:
                standard.writeError( self, '[recordSet_Insert]: can\'t get max_id')
              c.append({'id':id,'value':new_id})
          consumed = True
        if not consumed and tablecol.get('blob'):
          value = None
          blob = tablecol.get('blob')
          if values.get('blob_%s'%id, None) is not None and values.get('blob_%s'%id).filename:
            # Process blobs later...
            blobs['blob_%s'%id] = values['blob_%s'%id]
          consumed = True
        if not consumed and tablecol.get('fk') and tablecol.get('fk').get('editable'):
          if id in values:
            fk_tablename = tablecol.get('fk').get('tablename')
            fk_fieldname = tablecol.get('fk').get('fieldname')
            fk_displayfield = tablecol.get('fk').get('displayfield')
            value = values.get(id)
            if value == '' and tablecol.get('nullable'):
              value = None
            else:
              value = self.getFk( fk_tablename, fk_fieldname, fk_displayfield, value)
            if value is not None:
              c.append({'id':id,'value':value})
          consumed = True
        if not consumed and \
          (not tablecol.get('details')) and \
          (not tablecol.get('multiselect') or tablecol.get('multiselect').get('custom') or tablecol.get('multiselect').get('mysqlset')) and \
          (not tablecol.get('multimultiselect')):
          value = values.get(id, values.get(id.lower(), values.get(id.upper(), '')))
          if isinstance(value, list):
            value = ','.join(value)
          c.append({'id':id,'value':value})
      # Assemble sql-statement
      c = [x for x in c if self.sql_quote__(tablename, x['id'], x['value'])!='NULL']
      sqlStatement = []
      sqlStatement.append( 'INSERT INTO %s ('%tablename)
      sqlStatement.append( ', '.join([x['id'] for x in c]))
      sqlStatement.append( ') VALUES (')
      sqlStatement.append( ', '.join([self.sql_quote__(tablename, x['id'], x['value']) for x in c]))
      sqlStatement.append( ')')
      sqlStatement = ' '.join(sqlStatement)
      try:
        if da.meta_type == 'Z MySQL Database Connection':
          self.executeQuery('SET @auth_user=\'%s\''%auth_user)
      except:
        raise zExceptions.InternalError(standard.writeError( self, '[recordSet_Insert]: can\'t set auth_user variable'))
      try:
        self.executeQuery( sqlStatement)
      except:
        raise zExceptions.InternalError(standard.writeError( self, '[recordSet_Insert]: can\'t insert row - sqlStatement=' + sqlStatement))
      # Return with row-id.
      rowid = ([x for x in c if x['id']==primary_key]+[{'value':None}])[0]['value']
      if rowid is None:
        sqlStatement = []
        sqlStatement.append( 'SELECT %s AS value FROM %s WHERE '%(primary_key, tablename))
        sqlStatement.append( ' AND '.join([x['id']+'='+self.sql_quote__(tablename, x['id'], x['value']) for x in c if self.sql_quote__(tablename, x['id'], x['value']).upper()!='NULL']))
        sqlStatement = ' '.join(sqlStatement)
        try:
          for r in self.query( sqlStatement)['records']:
            rowid = r['value']
        except:
          raise zExceptions.InternalError(standard.writeError( self, '[recordSet_Insert]: can\'t get primary-key - sqlStatement=' + sqlStatement))
      # Update intersections.
      if update_intersections:
        self.recordSet_UpdateIntersections(tablename, rowid, values)
      # Process blobs now.
      if blobs:
        self.recordSet_Update(tablename, rowid, blobs)
      standard.triggerEvent(self.getParentNode(), '%s%sAfterInsert'%(self.id, tablename.capitalize()))
      return rowid


    """
    Update row in table.
    @param tablename: Name of the SQL-Table.
    @type tablename: C{string}
    @param rowid: ID of the row to be updated.
    @type rowid: C{any}
    @param values: Columns (id/value) to be updated.
    @type values: C{dict}
    @return: ID of the row that was updated.
    @rtype: C{any}
    """
    def recordSet_Update(self, tablename, rowid, values={}, old_values={}, update_intersections=False):
      standard.triggerEvent(self.getParentNode(), '%s%sBeforeUpdate'%(self.id, tablename.capitalize()))
      REQUEST = self.REQUEST
      auth_user = REQUEST.get('AUTHENTICATED_USER')
      lang = REQUEST['lang']
      da = self.getDA()
      if tablename is None:
        raise "[recordSet_Update]: tablename must not be None!"
      tabledefs = self.getEntities()
      tabledef = [x for x in tabledefs if x['id'].upper()==tablename.upper()][0]
      tablecols = tabledef['columns']
      primary_key = ([x['id'] for x in tablecols if x.get('pk', 0)==1]+[tablecols[0]['id']])[0]
      # Get old.
      sqlStatement = []
      sqlStatement.append( 'SELECT * FROM %s '%tablename)
      sqlStatement.append( 'WHERE %s=%s '%(primary_key, self.sql_quote__(tablename, primary_key, rowid)))
      sqlStatement = ' '.join(sqlStatement)
      try:
        old = self.query( sqlStatement)['records'][0]
      except:
        raise zExceptions.InternalError(standard.writeError( self, '[recordSet_Update]: can\'t get old - sqlStatement=' + sqlStatement))
      # Get columns to update
      c = []
      for tablecol in tablecols:
        id = tablecol['id']
        consumed = id in REQUEST.get('qexcludeids', [])
        if not consumed and tablecol.get('password'):
          if id in values:
            value = values.get(id)
            if value != '' and value != '******':
              c.append({'id':id,'value':value})
          consumed = True
        if not consumed and tablecol.get('auto'):
          if tablecol.get('auto') in ['update']:
            if tablecol.get('type') in ['date', 'datetime']:
              c.append({'id':id,'value':self.getLangFmtDate(time.time(), lang, '%s_FMT'%tablecol['type'].upper())})
          consumed = True
        if not consumed and tablecol.get('blob'):
          blob = tablecol.get('blob')
          remote = blob.get('remote', None)
          if values.get('delete_blob_%s'%id, None):
            if remote is None:
              value = self._delete_blob(tablename=tablename, id=id, rowid=rowid)
            else:
              value = self.http_import(self.url_append_params(remote+'/delete_blob', {'auth_user':blob.get('auth_user', auth_user.getId()),'tablename':tablename,'id':id,'rowid':rowid}), method='POST')
            c.append({'id':id,'value':value})
          elif values.get('blob_%s'%id, None) is not None and values.get('blob_%s'%id).filename:
            data = values.get('blob_%s'%id, None)
            file = self.FileFromData( data, data.filename)
            if remote is None:
              value = self._set_blob(tablename=tablename, id=id, rowid=rowid, file=file)
            else:
              xml = file.toXml()
              value = self.http_import(self.url_append_params(remote+'/set_blob', {'auth_user':blob.get('auth_user', auth_user.getId()),'tablename':tablename,'id':id,'rowid':rowid,'xml':xml}), method='POST')
            c.append({'id':id,'value':value})
          consumed = True
        if not consumed and tablecol.get('fk') and tablecol.get('fk').get('editable'):
          if id in values:
            fk_tablename = tablecol.get('fk').get('tablename')
            fk_fieldname = tablecol.get('fk').get('fieldname')
            fk_displayfield = tablecol.get('fk').get('displayfield')
            value = values.get(id)
            if value == '' and tablecol.get('nullable'):
              value = None
            else:
              value = self.getFk( fk_tablename, fk_fieldname, fk_displayfield, value)
            if value != old_values.get(id, old[id]):
              c.append({'id':id,'value':value})
          consumed = True
        if not consumed and \
           (not tablecol.get('details')) and \
           (not tablecol.get('multiselect') or tablecol.get('multiselect').get('custom') or tablecol.get('multiselect').get('mysqlset')) and \
           (not tablecol.get('multimultiselect')):
          if id in values and values.get(id) != old_values.get(id, old[id]):
            value = values.get(id)
            if value == '' and tablecol.get('nullable'):
              value = None
            elif isinstance(value, list):
              value = ','.join(value)
            if value != old_values.get(id, old[id]):
              c.append({'id':id,'value':value})
      # Assemble sql-statement
      if len(c) > 0:
        sqlStatement = []
        sqlStatement.append( 'UPDATE %s SET '%tablename)
        sqlStatement.append( ', '.join([x['id']+'='+self.sql_quote__(tablename, x['id'], x['value']) for x in  c]))
        sqlStatement.append( 'WHERE %s=%s '%(primary_key, self.sql_quote__(tablename, primary_key, rowid)))
        sqlStatement = ' '.join(sqlStatement)
        try:
          if da.meta_type == 'Z MySQL Database Connection':
            self.executeQuery('SET @auth_user=\'%s\''%auth_user)
        except:
          raise zExceptions.InternalError(standard.writeError( self, '[recordSet_Update]: can\'t set auth_user variable'))
        try:
          self.executeQuery( sqlStatement)
        except:
          raise zExceptions.InternalError(standard.writeError( self, '[recordSet_Update]: can\'t update row - sqlStatement=' + sqlStatement))
      # Update intersections.
      if update_intersections:
        self.recordSet_UpdateIntersections(tablename, rowid, values)
      # Return with row-id.
      standard.triggerEvent(self.getParentNode(), '%s%sAfterUpdate'%(self.id, tablename.capitalize()))
      return rowid


    """
    Update row-intersections in table.
    @param tablename: Name of the SQL-Table.
    @type tablename: C{string}
    @param rowid: ID of the row to be updated.
    @type rowid: C{any}
    @param values: Columns (id/value) to be updated.
    @type values: C{dict}
    """
    def recordSet_UpdateIntersections(self, tablename, rowid, values={}):
      tabledefs = self.getEntities()
      tabledef = [x for x in tabledefs if x['id'].upper()==tablename.upper()][0]
      tablecols = tabledef['columns']
      pk = ([x['id'] for x in tablecols if x.get('pk', 0)==1]+[tablecols[0]['id']])[0]
      for tablecol in tablecols:
        id = tablecol['id']
        column = self.getEntityColumn(tablename, id, row={})
        
        # Multiselect
        if tablecol.get('multiselect'):
          stereotype = tablecol['multiselect']
          # Multiselect.MySQLSet
          if 'mysqlset' in stereotype:
            v = values.get(id)
            if isinstance(v, list):
              v = '\'%s\''%(','.join(v))
            elif isinstance(v, str):
              v = '\'%s\''%v
            else:
              v = 'NULL'
            sql = []
            sql.append('UPDATE %s'%tablename)
            sql.append('SET %s=%s'%(id, v))
            sql.append('WHERE %s=%s'%(pk, self.sql_quote__(tablename, pk, rowid)))
            self.executeQuery('\n'.join(sql))
          # Multiselect.FK
          elif 'tablename' in stereotype:
            sql = []
            sql.append('DELETE FROM %s'%stereotype['tablename'])
            sql.append('WHERE %s=%s'%(stereotype['fk'], self.sql_quote__(tablename, pk, rowid)))
            self.executeQuery('\n'.join(sql))
            for v in standard.nvl(values.get(id), []):
              sql = []
              c = [(column['src']['id'], rowid), (column['dst']['id'], v)]
              sql.append('INSERT INTO %s (%s)'%(stereotype['tablename'], ' , '.join([x[0] for x in c])))
              sql.append('VALUES (%s)'%(' , '.join([self.sql_quote__(stereotype['tablename'], x[0], x[1]) for x in c])))
              self.executeQuery('\n'.join(sql))

        # Multimultiselect
        elif tablecol.get('multimultiselect'):
          stereotype = tablecol['multimultiselect']
          sql = []
          sql.append('DELETE FROM %s'%stereotype['tablename'])
          sql.append('WHERE %s=%s'%(stereotype['fk'], self.sql_quote__(tablename, pk, rowid)))
          self.executeQuery('\n'.join(sql))
          for v in standard.nvl(values.get(id), []):
            sql = []
            items = stereotype.get('tables', [])
            c = [(stereotype['fk'], rowid)]
            for item in items:
              i = items.index(item)
              c.append((item['fk'], v.split('|')[i]))
            sql.append('INSERT INTO %s (%s)'%(stereotype['tablename'], ' , '.join([x[0] for x in c])))
            sql.append('VALUES (%s)'%(' , '.join([self.sql_quote__(stereotype['tablename'], x[0], x[1]) for x in c])))
            self.executeQuery('\n'.join(sql))


    """
    Delete row from table.
    @param tablename: Name of the SQL-Table.
    @type tablename: C{string}
    @param rowid: ID of the row to be deleted.
    @type rowid: C{any}
    @rtype: C{None}
    """
    def recordSet_Delete(self, tablename, rowid):
      standard.triggerEvent(self.getParentNode(), '%s%sBeforeDelete'%(self.id, tablename.capitalize()))
      REQUEST = self.REQUEST
      auth_user = REQUEST.get('AUTHENTICATED_USER')      
      lang = REQUEST['lang']
      da = self.getDA()
      if tablename is None:
        raise zExceptions.InternalError("[recordSet_Delete]: tablename must not be None!")
      tabledefs = self.getEntities()
      tabledef = [x for x in tabledefs if x['id'].upper()==tablename.upper()][0]
      tablecols = tabledef['columns']
      primary_key = ([x['id'] for x in tablecols if x.get('pk', 0)==1]+[tablecols[0]['id']])[0]
      # Assemble sql-statement
      sqlStatement = []
      sqlStatement.append( 'DELETE FROM %s '%tablename)
      sqlStatement.append( 'WHERE %s=%s '%(primary_key, self.sql_quote__(tablename, primary_key, rowid)))
      sqlStatement = ' '.join(sqlStatement)
      try:
        if da.meta_type == 'Z MySQL Database Connection':
          self.executeQuery('SET @auth_user=\'%s\''%auth_user)
      except:
        raise zExceptions.InternalError(standard.writeError( self, '[recordSet_Update]: can\'t set auth_user variable'))      
      try:
        self.executeQuery( sqlStatement)
      except:
        raise zExceptions.InternalError(standard.writeError( self, '[recordSet_Delete]: can\'t delete row - sqlStatement=' + sqlStatement))
      standard.triggerEvent(self.getParentNode(), '%s%sAfterDelete'%(self.id, tablename.capitalize()))


    ############################################################################
    ###
    ###   Blob (remote)
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  ZMSSqlDb.delete_blob:
    # --------------------------------------------------------------------------
    def _delete_blob( self, tablename, id, rowid):
      tabledefs = self.getEntities()
      tabledef = [x for x in tabledefs if x['id'].upper()==tablename.upper()][0]
      tablecols = tabledef['columns']
      primary_key = ([x['id'] for x in tablecols if x.get('pk', 0)==1]+[tablecols[0]['id']])[0]
      column = self.getEntityColumn( tablename, id)
      blob = column['blob']
      path = blob['path']
      # Assemble sql-statement
      sqlStatement = []
      sqlStatement.append( 'SELECT '+id+' AS v FROM %s '%tablename)
      sqlStatement.append( 'WHERE %s=%s '%(primary_key, self.sql_quote__(tablename, primary_key, rowid)))
      sqlStatement = ' '.join(sqlStatement)
      try:
        for r in self.query( sqlStatement)['records']:
          filename = r['v']
          try:
            standard.localfs_remove(path+filename)
          except: pass
          value = ''
          if column.get('nullable'):
            value = None
          else:
            value = self.sql_quote__(tablename, id, value)
          return value
      except:
        raise zExceptions.InternalError(standard.writeError( self, '[get_blob]: can\'t delete blob - sqlStatement=' + sqlStatement))

    def delete_blob( self, auth_user, tablename, id, rowid, REQUEST=None, RESPONSE=None):
      """ ZMSSqlDb.delete_blob """
      user = self.findUser( auth_user)
      if user is None:
        raise zExceptions.Unauthorized
      return self._delete_blob( tablename=tablename, id=id, rowid=rowid)


    # --------------------------------------------------------------------------
    #  ZMSSqlDb._set_blob:
    # --------------------------------------------------------------------------
    def _set_blob( self, tablename, id, rowid=None, file=None, xml=None):
      tabledefs = self.getEntities()
      tabledef = [x for x in tabledefs if x['id'].upper()==tablename.upper()][0]
      tablecols = tabledef['columns']
      primary_key = ([x['id'] for x in tablecols if x.get('pk', 0)==1]+[tablecols[0]['id']])[0]
      column = self.getEntityColumn( tablename, id)
      blob = column['blob']
      path = blob['path']
      if file is None and xml is not None:
        file = self.parseXmlString( xml)
      # Normalize filename (crop path in local-fs)
      filename = file.filename
      i = max( filename.rfind('/'), filename.rfind('\\'))
      if i > 0:
        filename = filename[i+1:]
      fileext = ''
      i = filename.rfind( '.')
      if i > 0:
        fileext = filename[ i:]
        filename = filename[ :i]
      filename = filename + '_' + standard.pystr( rowid) + fileext
      # Update
      oldfilename = 'None'
      if rowid is not None:
        # Assemble sql-statement
        sqlStatement = []
        sqlStatement.append( 'SELECT '+id+' AS v FROM %s '%tablename)
        sqlStatement.append( 'WHERE %s=%s '%(primary_key, self.sql_quote__(tablename, primary_key, rowid)))
        sqlStatement = ' '.join(sqlStatement)
        try:
          for r in self.query( sqlStatement)['records']:
            oldfilename = r['v']
        except:
          raise zExceptions.InternalError(standard.writeError( self, '[set_blob]: can\'t set blob - sqlStatement=' + sqlStatement))
      # Remove old file from server-fs
      try:
        _fileutil.remove(path+oldfilename)
      except: pass
      # Write new file to server-fs
      _fileutil.exportObj(file.getData(), path+filename)
      return filename

    security.declareProtected('View', 'set_blob')
    def set_blob( self, auth_user, tablename, id, rowid=None, xml=None, REQUEST=None, RESPONSE=None):
      """ ZMSSqlDb.set_blob """
      user = self.findUser( auth_user)
      if user is None:
        raise zExceptions.Unauthorized
      return self._set_blob( tablename=tablename, id=id, rowid=rowid, xml=xml)


    # --------------------------------------------------------------------------
    #  ZMSSqlDb._get_blob:
    # --------------------------------------------------------------------------
    def _get_blob( self, tablename, id, rowid, cache='public, max-age=3600', REQUEST=None, RESPONSE=None):
      data = ''
      tabledefs = self.getEntities()
      tabledef = [x for x in tabledefs if x['id'].upper()==tablename.upper()][0]
      tablecols = tabledef['columns']
      primary_key = ([x['id'] for x in tablecols if x.get('pk', 0)==1]+[tablecols[0]['id']])[0]
      column = self.getEntityColumn( tablename, id)
      blob = column['blob']
      path = blob['path']
      # Assemble sql-statement
      sqlStatement = []
      sqlStatement.append( 'SELECT '+id+' AS v FROM %s '%tablename)
      sqlStatement.append( 'WHERE %s=%s '%(primary_key, self.sql_quote__(tablename, primary_key, rowid)))
      sqlStatement = ' '.join(sqlStatement)
      try:
        for r in self.query( sqlStatement)['records']:
          filename = r['v']
          if path is not None and filename is not None:
            fdata, mt, enc, fsize = _fileutil.readFile(path+filename)
            if RESPONSE is not None:
              if REQUEST is not None and REQUEST.get('preview')=='preview':
                cache = 'no-cache'
              standard.set_response_headers(filename, mt, fsize, REQUEST)
              RESPONSE.setHeader('Cache-Control', cache)
              RESPONSE.setHeader('Content-Encoding', enc)
            if blob['type'] == 'image':
              return self.ImageFromData(fdata, filename)
            else:
              return self.FileFromData(fdata, filename)
      except:
        standard.writeError( self, '[get_blob]: can\'t get_blob - sqlStatement=' + sqlStatement)
      return None


    # --------------------------------------------------------------------------
    #  ZMSSqlDb.get_blob:
    # --------------------------------------------------------------------------
    security.declareProtected('View', 'get_blob')
    def get_blob( self, tablename, id, rowid, REQUEST=None, RESPONSE=None):
      """ ZMSSqlDb.get_blob """
      blob = self._get_blob( tablename, id, rowid, REQUEST=REQUEST, RESPONSE=RESPONSE)
      return blob.getData()


    ############################################################################
    ###
    ###   Properties
    ###
    ############################################################################

    ############################################################################
    #  ZMSSqlDb.manage_changeProperties: 
    #
    #  Change Sql-Database properties.
    ############################################################################
    def manage_changeProperties(self, lang, REQUEST=None, RESPONSE=None): 
      """ ZMSSqlDb.manage_changeProperties """
      message = ''
      el_data = REQUEST.get('el_data', '')
      target = 'manage_properties'
      
      if REQUEST.get('btn', '') not in [ 'BTN_CANCEL', 'BTN_BACK']:
        self.connection_id = REQUEST['connection_id']
        self.charset = REQUEST['charset']
        self.setModel(REQUEST['model'])
        message = self.getZMILangStr('MSG_CHANGED')
      
      # Return with message.
      message = standard.url_quote(message)
      el_data = standard.url_quote(el_data)
      return RESPONSE.redirect('%s?lang=%s&manage_tabs_message=%s&el_data=%s'%(target, lang, message, el_data))


    ############################################################################
    ###
    ###   Configuration
    ###
    ############################################################################

    # --------------------------------------------------------------------------
    #  ObjAttrs.ajaxGetObjOptions:
    # --------------------------------------------------------------------------
    def ajaxGetObjOptions(self, REQUEST):
      """ ObjAttrs.ajaxGetObjOptions """
      tablename = REQUEST['obj_id']
      columnname = REQUEST['attr_id']
      RESPONSE = REQUEST.RESPONSE
      content_type = 'text/plain; charset=utf-8'
      filename = 'ajaxGetObjOptions.txt'
      RESPONSE.setHeader('Content-Type', content_type)
      RESPONSE.setHeader('Content-Disposition', 'inline;filename="%s"'%filename)
      RESPONSE.setHeader('Cache-Control', 'no-cache')
      RESPONSE.setHeader('Pragma', 'no-cache')
      l = []
      q = REQUEST.get( 'q', '').upper()
      limit = int(REQUEST.get('limit', self.getConfProperty('ZMS.input.autocomplete.limit', 15)))
      pk = self.getEntityPK(tablename)
      sql = 'SELECT %s AS pk, %s AS displayfield FROM %s WHERE UPPER(%s) LIKE %s ORDER BY UPPER(%s)'%(pk, columnname, tablename, columnname, self.sql_quote__(tablename, columnname, '%'+q+'%'), columnname)
      for r in self.query(sql)['records']:
        if len(l) < limit:
          l.append(r['displayfield'])
      if REQUEST.get('fmt') == 'json':
        return self.str_json(l)
      return '\n'.join(l)

    # --------------------------------------------------------------------------
    #  ZMSSqlDb.ajaxGetAutocompleteColumns:
    # --------------------------------------------------------------------------
    security.declareProtected('View', 'ajaxGetAutocompleteColumns')
    def ajaxGetAutocompleteColumns(self, tableName, fmt=None, REQUEST=None):
      """ ZMSSqlDb.ajaxGetAutocompleteColumns """
      RESPONSE = REQUEST.RESPONSE
      content_type = 'text/plain; charset=utf-8'
      filename = 'ajaxGetAutocompleteColumns.txt'
      RESPONSE.setHeader('Content-Type', content_type)
      RESPONSE.setHeader('Content-Disposition', 'inline;filename="%s"'%filename)
      RESPONSE.setHeader('Cache-Control', 'no-cache')
      RESPONSE.setHeader('Pragma', 'no-cache')
      l = [x['id'] for x in self.getEntity( tableName)['columns'] if x['type']!='?']
      q = REQUEST.get( 'q', '').upper()
      if q:
        l = [x for x in l if x.upper().find(q)>= 0]
      limit = int(REQUEST.get('limit', self.getConfProperty('ZMS.input.autocomplete.limit', 15)))
      if len(l) > limit:
        l = l[:limit]
      if fmt == 'json':
        return self.str_json(l)
      return '\n'.join(l)

    ############################################################################
    #  ZMSSqlDb.manage_changeConfiguration: 
    #
    #  Change Sql-Database configuration.
    ############################################################################
    def manage_changeConfiguration(self, lang, btn='', key='all', REQUEST=None, RESPONSE=None):
      """ ZMSSqlDb.manage_changeConfiguration """
      message = ''
      t0 = time.time()
      id = REQUEST.get('id', '')
      target = 'manage_configuration'
      
      # Change.
      # -------
      if btn == 'BTN_SAVE':
        model = self.getModel()
        entities = [x for x in model if x['id'].upper()==id.upper()]
        if entities:
          entity = entities[0]
        else:
          entity = {}
          entity['id'] = id
          entity['type'] = 'table'
          entity['columns'] = []
          model.append( entity)
        entity['label'] = REQUEST.get('label').strip()
        entity['type'] = REQUEST.get('type').strip()
        entity['interface'] = REQUEST.get('interface').strip()
        entity['filter'] = REQUEST.get('filter').strip()
        entity['access'] = {
         'insert': REQUEST.get( 'access_insert', []),
         'update': REQUEST.get( 'access_update', []),
         'delete': REQUEST.get( 'access_delete', []),
         'select': REQUEST.get( 'access_select', []),
        }
        cols = []
        for attr_id in REQUEST.get('attr_ids', []):
          col = {}
          col['id'] = REQUEST.get( 'attr_id_%s'%attr_id, attr_id).strip()
          try:
            col['label'] = REQUEST.get( 'attr_label_%s'%attr_id, '').strip()
          except:
            col['label'] = REQUEST.get( 'attr_label_%s'%attr_id, '')[0].strip()
          try:
            col['index'] = int(REQUEST.get( 'attr_index_%s'%attr_id))
          except:
            col['index'] = int(REQUEST.get( 'attr_index_%s'%attr_id)[0])
          try:
            col['hide'] = int(not REQUEST.get('attr_display_%s'%attr_id, 0)==1)
          except:
            col['hide'] = int(not REQUEST.get('attr_display_%s'%attr_id, 0)[0]==1)
          if 'attr_auto_%s'%attr_id in REQUEST:
            col['auto'] = REQUEST.get( 'attr_auto_%s'%attr_id)
          if 'attr_type_%s'%attr_id in REQUEST:
            t = REQUEST.get( 'attr_type_%s'%attr_id)
            if t in self.valid_types:
              d = copy.deepcopy( self.valid_types[ t])
              c = []
              if isinstance(d, dict):
                xs = 'attr_%s_'%t
                xe = '_%s'%attr_id
                for k in [x for x in REQUEST.form if x.startswith(xs) and x.endswith(xe)]:
                  xk = k[len(xs):-len(xe)].split('_')
                  xv = REQUEST[k]
                  if len( xk) == 1:
                    xk = xk[ 0]
                    if xk == 'options':
                      xv2 = []
                      for xi in xv.split('\n'):
                        xi = xi.replace('\r', '')
                        if xi.find('->') > 0:
                          xi0 = xi[:xi.find('->')]
                          xi1 = xi[xi.find('->')+len('->'):]
                          if len(xi0) > 0 and len( xi1) > 0:
                            xv2.append( [xi0, xi1])
                        else:
                          if len(xi) > 0:
                            xv2.append( [xi, xi])
                      if len( xv2) > 0:
                        d[ xk] = xv2
                    else:
                      if isinstance(xv, str):
                        xv = xv.strip()
                        if len( xv) > 0:
                          d[ xk] = xv
                      elif isinstance(xv, int):
                        if xv != 0:
                          d[ xk] = xv
                  else:
                    if xk[0] not in d:
                      d[ xk[0]] = {}
                      c.append( xk[0])
                    if xk[-1] not in d[ xk[0]]:
                      d[ xk[0]][ xk[-1]] = {}
                    if isinstance(xv, str):
                      xv = xv.strip()
                      if len( xv) > 0:
                        d[ xk[0]][ xk[-1]][ xk[1]] = xv
                    elif isinstance(xv, int):
                      if xv != 0:
                        d[ xk[0]][ xk[-1]][ xk[1]] = xv
              for i in c:
                l = d[i].values()
                l = sorted(x,key=lambda x:x.get('index', l.index(x)))
                for x in l:
                  if not x.get('display'):
                    x['hide'] = 1
                  try: del x['display']
                  except: pass
                  try: del x['index']
                  except: pass
                l = [x for x in l if len(x) > 0]
                d[i] = l
              col[ t] = d
          cols.append( ( col['index'], col))
        cols.sort()
        cols = [x[1] for x in cols]
        # Insert
        attr_id = REQUEST.get('attr_id', '').strip()
        attr_label = REQUEST.get('attr_label', '').strip()
        attr_type = REQUEST.get('attr_type', '').strip()
        if attr_id and attr_label and attr_type:
          newValue = {}
          newValue['id'] = attr_id
          newValue['label'] = attr_label
          newValue['hide'] = int(not REQUEST.get('attr_display', 0)==1)
          newValue[attr_type] = {}
          cols.append(newValue)
        entity['columns'] = cols
        f = self.toXmlString( model)
        self.setModel(f)
        message = self.getZMILangStr('MSG_CHANGED')
      
      # Delete.
      # -------
      elif btn == 'BTN_DELETE':
        attr_id = REQUEST['attr_id'].strip()
        model = self.getModel()
        entities = [x for x in model if x['id'].upper()==id.upper()]
        if entities:
          entity = entities[0]
          entity['columns'] = [x for x in entity['columns'] if x['id'].upper()!=attr_id.upper()]
        f = self.toXmlString( model)
        self.setModel(f)
        message = self.getZMILangStr('MSG_CHANGED')
      
      # Import.
      # -------
      elif btn == 'BTN_IMPORT':
        f = REQUEST['file']
        filename = f.filename
        self.setModel(f)
        message = self.getZMILangStr('MSG_IMPORTED')%('<i>%s</i>'%filename)
      
      # Insert.
      # -------
      elif btn == 'BTN_INSERT':
        attr_id = REQUEST['attr_id'].strip()
        model = self.getModel()
        newValue = {}
        newValue['id'] = attr_id
        newValue['label'] = REQUEST.get('attr_label').strip()
        newValue['hide'] = int(not REQUEST.get('attr_display', 0)==1)
        if REQUEST.get('attr_type'):
          newValue[REQUEST.get('attr_type')] = {}
        entities = [x for x in model if x['id'].upper()==id.upper()]
        if entities:
          entity = entities[0]
        else:
          entity = {}
          entity['id'] = id
          entity['type'] = 'table'
          entity['columns'] = []
          model.append( entity)
        entity['columns'].append(newValue)
        f = self.toXmlString( model)
        self.setModel(f)
        message += self.getZMILangStr('MSG_INSERTED')%attr_id
      
      # Move to.
      # --------
      elif key == 'attr' and btn == 'move_to':
        pos = REQUEST['pos']
        attr_id = REQUEST['attr_id']
        model = self.getModel()
        entities = [x for x in model if x['id'].upper()==id.upper()]
        if entities:
          entity = entities[0]
        else:
          entity = {}
          entity['id'] = id
          entity['type'] = 'table'
          entity['columns'] = [{'id':x['id']} for x in self.getEntity( id)['columns']]
          model.append( entity)
        cols = entity['columns']
        col = [x for x in cols if x['id'].upper()==attr_id.upper()][0]
        i = cols.index( col)
        cols.remove( col)
        cols.insert( pos, col)
        idx = 0
        for col in cols:
          col['index'] = idx
          idx = idx + 1
        f = self.toXmlString( model)
        self.setModel(f)
        message = self.getZMILangStr('MSG_MOVEDOBJTOPOS')%(("<i>%s</i>"%attr_id), (pos+1))
      
      # Return with message.
      target = self.url_append_params( target, { 'lang':lang, 'id':id, 'attr_id':REQUEST.get('attr_id', '')})
      if len( message) > 0:
        message += ' (in '+str(int((time.time()-t0)*100.0)/100.0)+' secs.)'
        target = self.url_append_params( target, { 'manage_tabs_message':message})
      return RESPONSE.redirect( target)


# call this to initialize framework classes, which
# does the right thing with the security assertions.
InitializeClass(ZMSSqlDb)

################################################################################
