import json
import secrets
import string
from flask import make_response


def build_success_response(db,cursor,data):
    try:
        db.close()
        cursor.close()
    except:
        pass
    obj = {}
    obj["status"] = 200
    obj["data"] = data
    res = json.dumps(obj, indent=4, separators=(',', ':'))
    return make_response(res)


def build_fail_response(db,cursor,msg):
    try:
        db.close()
        cursor.close()
    except:
        pass
    obj = {}
    obj["status"] = 500
    obj["message"] = msg
    res = json.dumps(obj, indent=4, separators=(',', ':'))
    return make_response(res)


def build_session_id():
    alphabet = string.ascii_letters + string.digits + "-_"
    return ''.join(secrets.choice(alphabet) for i in range(14))


def check_session_id(db,cursor,session_id):
    if session_id is None:
        return False, build_fail_response(db,cursor,"session id不存在")
    sql = """
        SELECT b.id,b.name,b.studentId 
        FROM basic_info b INNER JOIN session_info s 
        ON s.session = %s AND b.studentId = s.studentId 
        WHERE s.expires_time > NOW();
        """
    cursor.execute(sql, session_id)
    result = cursor.fetchone()
    if result is None:
        return False, build_fail_response(db,cursor,"session id不合法")
    return True, result


def build_data_dict(result, keys):
    data = {key: result[key] for key in keys}
    return data


def select_one_info(db,cursor,student_id):
    sql = """
        SELECT b.id,b.name,b.studentId,
        a.className,a.city,a.coord,a.contact,a.mainwork,a.sentence 
        FROM basic_info b 
        INNER JOIN advance_info a 
        ON b.studentId = a.studentId
        WHERE b.studentId = %s;
    """
    cursor.execute(sql, student_id)
    result = cursor.fetchone()
    if result is not None:
        result["coord"] = json.loads(result["coord"])
    return result


def select_all_info(db,cursor):
    sql = """
        SELECT b.id,b.name,b.studentId,
        a.className,a.city,a.coord,a.contact,a.mainwork,a.sentence 
        FROM basic_info b 
        INNER JOIN advance_info a 
        ON b.studentId = a.studentId
    """
    cursor.execute(sql)
    result = cursor.fetchall()
    if result is not None:
        for item in result:
            item["coord"] = json.loads(item["coord"])
    return result
