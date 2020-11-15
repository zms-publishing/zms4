# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
# +- ENTITES (!!! this is only an example for Postgres!!!)
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-
def getEntities(here, request):
    for node in here.getSelf(here.PAGES).filteredTreeNodes(request,'ZMSSqlDb'):
        tablename = ''
        entities = []
        entity = {}
        columns = []
        for record in query( \
                'select pt.tablename as table_name, pa.attname as column_name, py.typname as data_type, pa.attnotnull ' + \
                'from pg_attribute pa, pg_class pc, pg_tables pt, pg_type py ' + \
                'where pa.attrelid = pc.relfilenode ' + \
                'and pa.attnum > 0 ' + \
                'and py.typelem = pa.atttypid ' + \
                'and pc.relname = pt.tablename ' + \
                'and pt.tableowner=\'postgres\' ' + \
                'and pt.schemaname=\'public\' ' + \
                'order by pt.tablename, pa.attnum ' \
                )['records']:
            if record['table_name'] != tablename:
                if tablename:
                    entities.append(entity)
                tablename = record['table_name']
                entity = {}
                columns = []
                entity['id'] = tablename
                entity['label'] = ' '.join([x.capitalize() for x in tablename.split('_')]).strip()
                entity['type'] = 'table'
                entity['columns'] = columns
            column = {}
            colName = record['column_name']
            colType = record['data_type']
            colSize = -1
            if colType.find('_')>0:
                colType = colType[1:]
            if colType.find('char')>0:
                colType = 'string'
            elif colType.find('int')>0:
                colSize = int(colType[3:])
                colType = 'int'
            column['key'] = colName
            column['id'] = colName
            column['label'] = ' '.join([x.capitalize() for x in colName.split('_')]).strip()
            column['name'] = column['label']
            column['mandatory'] = attnotnull=='True'
            column['type'] = colType
            column['sort'] = 1
            column['nullable'] = not column['mandatory']
            columns.append(column)
        if tablename:
            entities.append(entity)
    return entities
