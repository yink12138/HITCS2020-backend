import json
from flask import Blueprint
from database import connect_db
from flask import request
import bcrypt
from datetime import datetime, timedelta
from tool import build_success_response, build_fail_response, \
    build_session_id, check_session_id, build_data_dict, select_one_info, \
    select_all_info

auth = Blueprint('auth', __name__)
info = Blueprint('info', __name__)


@auth.route("/manual_login", methods=['PUT'])
def manual_login():
    db, cursor = None, None
    try:
        db,cursor = connect_db()
        params = json.loads(request.get_data(as_text=True))
        student_id = params["account"]
        pw_hashed_submit = params["pwHashed1"]
        auto_login = params["autoLogin"]
        period = 7 if auto_login else 1

        sql = "SELECT * FROM `student`.`basic_info`" \
              "WHERE studentId = %s"
        cursor.execute(sql, student_id)
        result = cursor.fetchone()
        if result is None:
            return build_fail_response(db,cursor,"账号不存在")
        pw_hashed_correct = result['pwHashed']

        if bcrypt.checkpw(pw_hashed_submit.encode(), pw_hashed_correct.encode()):
            keys = ("id", "name", "studentId")
            data = build_data_dict(result, keys)

            session_id = build_session_id()
            sql = """
                INSERT INTO `student`.`session_info`(`studentId`, `session`, `create_time`, `expires_time`) 
                VALUES (%s, %s, now(), date_add(now(), interval %s day))
                """
            cursor.execute(sql, (result["studentId"], session_id, period))
            db.commit()

            resp = build_success_response(db,cursor,data)
            expires_time = datetime.now() + timedelta(days=period)
            resp.set_cookie('SessionID', session_id, expires=expires_time)
            return resp
        else:
            return build_fail_response(db,cursor,"密码错误")
    except:
        return build_fail_response(db,cursor,"未知错误")


@auth.route("/auto_login", methods=['GET'])
def auto_login():
    db, cursor = None, None
    try:
        db,cursor = connect_db()
        session_id = request.cookies.get("SessionID")
        validity, result = check_session_id(db,cursor,session_id)
        if not validity:
            return result
        return build_success_response(db,cursor,result)
    except:
        return build_fail_response(db,cursor,"未知错误")


@auth.route("/logout", methods=['DELETE'])
def logout():
    db, cursor = None, None
    try:
        db,cursor = connect_db()
        session_id = request.cookies.get("SessionID")
        validity, result = check_session_id(db,cursor,session_id)
        if not validity:
            return result

        student_id = result["studentId"]
        sql = """
        DELETE FROM `student`.`session_info`
        WHERE studentId = %s
        """
        cursor.execute(sql, student_id)
        db.commit()
        resp = build_success_response(db,cursor,None)
        resp.delete_cookie('SessionID')
        return resp
    except:
        return build_fail_response(db,cursor,"未知错误")


@auth.route("/change_pw", methods=['PUT'])
def change_pw():
    db, cursor = None, None
    try:
        db,cursor = connect_db()
        session_id = request.cookies.get("SessionID")
        validity, result = check_session_id(db,cursor,session_id)
        if not validity:
            return result

        params = json.loads(request.get_data(as_text=True))
        old_passwd_hashed_submit = params.get("oldPwHashed1")
        new_passwd_hashed_submit = params.get("newPwHashed1")
        student_id = result["studentId"]

        sql = "SELECT * FROM `student`.`basic_info`" \
              "WHERE studentId = %s"
        cursor.execute(sql, student_id)
        result = cursor.fetchone()
        if result is None:
            return build_fail_response(db,cursor,"账号不存在")
        old_passwd_hashed_correct = result["pwHashed"]

        if bcrypt.checkpw(old_passwd_hashed_submit.encode(), old_passwd_hashed_correct.encode()):
            new_passwd_hashed_correct = bcrypt.hashpw(new_passwd_hashed_submit.encode(), bcrypt.gensalt(10))
            sql = """
            UPDATE `student`.`basic_info` 
            SET pwHashed = %s 
            WHERE studentId = %s
            """
            cursor.execute(sql,
                           (new_passwd_hashed_correct.decode(), student_id))
            db.commit()

            sql = """
            DELETE FROM `student`.`session_info`
            WHERE studentId = %s
            """
            cursor.execute(sql, student_id)
            db.commit()

            resp = build_success_response(db,cursor,None)
            resp.delete_cookie('SessionID')
            return resp
        else:
            return build_fail_response(db,cursor,"密码错误")
    except:
        return build_fail_response(db,cursor,"未知错误")


@info.route("/get_one", methods=['GET'])
def get_one():
    db, cursor = None, None
    try:
        db,cursor = connect_db()
        session_id = request.cookies.get("SessionID")
        validity, result = check_session_id(db,cursor,session_id)
        if not validity:
            return result

        student_id = request.args.get("studentId")
        result = select_one_info(db,cursor,student_id)
        if result is None:
            return build_success_response(db,cursor,None)
        return build_success_response(db,cursor,result)
    except:
        return build_fail_response(db,cursor,"未知错误")


@info.route("/get_all", methods=['GET'])
def get_all():
    db, cursor = None, None
    try:
        db,cursor = connect_db()
        session_id = request.cookies.get("SessionID")
        validity, result = check_session_id(db,cursor,session_id)
        if not validity:
            return result

        result = select_all_info(db,cursor)
        keys = ("id", "name", "studentId", "className", "city", "coord")
        data = [build_data_dict(i, keys) for i in result]
        return build_success_response(db,cursor,data)
    except:
        return build_fail_response(db,cursor,"未知错误")


@info.route("/get_all_coords")
def get_all_coords():
    db, cursor = None, None
    try:
        db,cursor = connect_db()
        result = select_all_info(db,cursor)
        keys = ("coord",)
        data = [build_data_dict(item, keys) for item in result]
        return build_success_response(db,cursor,data)
    except:
        return build_fail_response(db,cursor,"未知错误")


@info.route("/submit", methods = ['POST'])
def submit_info():
    db, cursor = None, None
    try:
        db,cursor = connect_db()
        session_id = request.cookies.get("SessionID")
        validity, result = check_session_id(db,cursor,session_id)
        if not validity:
            return result

        # check if previous info exists
        if select_one_info(db,cursor,result["studentId"]):
            return build_fail_response(db,cursor,"请不要重复提交")

        # insert info
        params = json.loads(request.get_data(as_text=True))
        if "contact" not in params.keys():
            params["contact"] = None
        if "mainwork" not in params.keys():
            params["mainwork"] = None
        if "sentence" not in params.keys():
            params["sentence"] = None

        sql = """
            INSERT INTO `student`.`advance_info`(`studentId`, `className`, `city`, `coord`, `contact`, `mainwork`, `sentence`)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
        cursor.execute(sql,
                       (result["studentId"], params["className"], params["city"],
                        json.dumps(params["coord"]), params["contact"], params["mainwork"], params["sentence"]))
        db.commit()
        return build_success_response(db,cursor,None)
    except:
        return build_fail_response(db,cursor,"未知错误")


@info.route("/update", methods = ['PUT'])
def update_info():
    db, cursor = None, None
    try:
        db,cursor = connect_db()
        session_id = request.cookies.get("SessionID")
        validity, result = check_session_id(db,cursor,session_id)
        if not validity:
            return result

        # check if previous info exists
        if not select_one_info(db,cursor,result["studentId"]):
            return build_fail_response(db,cursor,"请先提交信息")

        # update info
        params = json.loads(request.get_data(as_text=True))
        params["coord"] = json.dumps(params["coord"])
        if "contact" not in params.keys():
            params["contact"] = None
        if "mainwork" not in params.keys():
            params["mainwork"] = None
        if "sentence" not in params.keys():
            params["sentence"] = None
        sql = """
        UPDATE `student`.`advance_info` 
        SET `className` = %s, `city` = %s, `coord` = %s, 
        `contact` = %s, `mainwork` = %s, `sentence` = %s
        WHERE `studentId` = %s
        """
        cursor.execute(sql,
                       (params["className"], params["city"],
                        params["coord"], params["contact"], params["mainwork"],
                        params["sentence"], result["studentId"]))
        db.commit()
        return build_success_response(db,cursor,None)
    except:
        return build_fail_response(db,cursor,"未知错误")


@info.route("/delete", methods = ['DELETE'])
def delete_info():
    db, cursor = None, None
    try:
        db,cursor = connect_db()
        session_id = request.cookies.get("SessionID")
        validity, result = check_session_id(db,cursor,session_id)
        if not validity:
            return result

        # delete info
        sql = """
            DELETE FROM `student`.`advance_info`
            WHERE studentId = %s
        """
        cursor.execute(sql, result["studentId"])
        db.commit()
        return build_success_response(db,cursor,None)
    except:
        return build_fail_response(db,cursor,"未知错误")
