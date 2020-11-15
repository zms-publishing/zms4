# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
# +- ENTITES (!!! this is only an example for an Oracle_Database_Connection!!!)
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
def getEntities(here, request):
    for node in here.getSelf(here.PAGES).filteredTreeNodes(request,'ZMSSqlDb'):
        tablename = ''
        entities = []
        entity = {}
        columns = []
        for record in node.query('select * from all_tab_columns where owner = \'ORACLEUSER\'')['records']:
            if record['TABLE_NAME'] != tablename:
                if tablename:
                    entities.append(entity)
                tablename = record['TABLE_NAME']
                entity = {}
                columns = []
                entity['id'] = tablename
                entity['type'] = 'table'
                entity['label'] = ' '.join([x.capitalize() for x in tablename.split('_')]).strip()
                entity['sort_id'] = entity['label'].upper()
                entity['columns'] = columns
            column = {}
            colName = record['COLUMN_NAME']
            colType = record['DATA_TYPE']
            colSize = record['DATA_LENGTH']
            if colType.find('CHAR')>0:
                colType = 'string'
                if colSize>50:
                    colType = 'text'
            elif colType.find('INT')>0:
                colType = 'int'
            
            column['key'] = colName
            column['id'] = colName
            column['index'] = int(column.get('index',len(columns)))
            column['label'] = ' '.join([x.capitalize() for x in colName.split('_')]).strip()
            column['name'] = column['label']
            column['mandatory'] = record['NULLABLE'] == 'N'
            column['type'] = colType
            column['sort'] = 1
            column['nullable'] = not column['mandatory']
            columns.append(column)
        if tablename:
            entities.append(entity)
    return entities
