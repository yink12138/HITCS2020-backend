import pymysql


def connect_db():
    db = pymysql.connect(host='localhost',
                         user='test',
                         password='test',
                         database='student')
    # return key-value mysql data
    cursor = db.cursor(cursor=pymysql.cursors.DictCursor)
    return db, cursor