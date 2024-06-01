import psycopg2
from psycopg2 import sql
from psycopg2._psycopg import AsIs

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(database='MyDataBase', user='MyUser',
                                     password='SECRET', host='MeServ', port=5432)
        self.cursor = self.conn.cursor()

    def listColledjeForPage(self, tables, order, schema='organization', Page=1, SkipSize=1, wheres=''):
        sql = f"""select * from %(schemas)s.%(tables)s o
        %(wheres)s
        ORDER BY o.%(orders)s 
        OFFSET %(skipsPage)s ROWS FETCH NEXT %(SkipSizes)s ROWS only;"""
        self.cursor.execute(sql, {'schemas': AsIs(schema), 'tables': AsIs(tables), 'orders': AsIs(order),
                                  'skipsPage': ((Page - 1) * SkipSize), 'SkipSizes': SkipSize, 'wheres': AsIs(wheres)})
        res = self.cursor.fetchall()
        self.cursor.execute(f"""select Count(*) from %(schemas)s.%(tables)s o %(wheres)s;""",
                            {'schemas': AsIs(schema), 'tables': AsIs(tables),'wheres': AsIs(wheres)})
        count = self.cursor.fetchone()[0]
        return res, len(res), count