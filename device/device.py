import base64
import hashlib
import json
import os
import random
import subprocess
import time
from urllib.request import urlopen
import requests
from flask import Flask, request, jsonify
from uuid import uuid4
import threading

host_name = "0.0.0.0"
port = 6064

app = Flask(__name__)  # create an app instance

key_t = False
key_s = False
level = -1
key = '12345'
event = threading.Event()
url = ''

CONTENT_HEADER = {"Content-Type": "application/json"}
NEW_FW_PATHNAME = "/storage/new.txt"


# логгирование событий
def log(msg):
    try:
        print(msg)

        #отправка данных для теста
        send_data_to_server(msg)

        t = time.time()
        with open("/storage/log.txt", "a+") as f:
            f.write(f"{t} : {msg}\n")

    except Exception as e:
        print(f'[error] log failed, exception {e}')


#отправка данных наружу для тестов
def send_data_to_server(msg):
    try:
        data = {"msg": msg}
        requests.post(
            url,
            data=json.dumps(data),
            headers=CONTENT_HEADER,
        )
    except Exception as e:
        print(f'[error] delivery failed, exception {e}')


# заглушка логики контроля параметров прикладной программы
def settings_sanity_check():
    result = random.choices([True, False], weights=[90, 10])
    log("Diagnostic ended with status: " + str(result))
    return result


#основная система, которая периодически выдает ключи и проводит диагностику
def cron(t):
    global key, event
    while not event.is_set():
        time.sleep(t)
        check_status = settings_sanity_check()
        check_status = str(check_status)
        out_d("send_diagnostic", "Checked with status: " + check_status)




#вычислитель хеша
def md5(fname):
    hash_md5 = hashlib.md5()
    with open(fname, "rb") as f:
        for chunk in iter(lambda: f.read(1024), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


#аналоговый выходной порт
def out_a(value):
    data = {"value": value}
    requests.post(
        "http://scada:6069/data_a",
        data=json.dumps(data),
        headers=CONTENT_HEADER,
    )


#порт контакта с защитой
def out_b():
    data = {"status": True}
    requests.post(
        "http://protection:6068/alarm",
        data=json.dumps(data),
        headers=CONTENT_HEADER,
    )


#цифровой порт
def out_d(operation, msg):
    if operation == 'send_data':
        data = {"value": msg}
        requests.post(
            "http://scada:6069/data_d",
            data=json.dumps(data),
            headers=CONTENT_HEADER,
        )

    elif operation == 'send_diagnostic':
        data = {"status": msg}
        requests.post(
            "http://scada:6069/diagnostic",
            data=json.dumps(data),
            headers=CONTENT_HEADER,
        )

    elif operation == 'send_key':
        data = {"key": msg}
        requests.post(
            "http://scada:6069/key",
            data=json.dumps(data),
            headers=CONTENT_HEADER,
        )

    elif operation == 'send_error':
        data = {"error": msg}
        requests.post(
            "http://scada:6069/error",
            data=json.dumps(data),
            headers=CONTENT_HEADER,
        )


#запись обновления
def commit(name, payload):
    stored = False
    update_payload = base64.b64decode(payload)
    try:
        with open("/storage/" + name, "wb") as f:
            f.write(update_payload)
        stored = True
    except Exception as e:
        print(f'[error] failed to store blob in {os.getcwd()}: {e}')
    return stored


@app.route("/stop", methods=['POST'])
def stop():
    global event
    try:
        event.set()
        log("Stopped")
    except Exception as e:
        log(f"exception raised {e}")
        error_message = f"malformed request {request.data}"
        return error_message, 400
    return jsonify({"operation": "stopped"})


@app.route("/start", methods=['POST'])
def start():
    global event, key_s, key_t, level, key, url
    try:
        event = threading.Event()

        if os.path.exists(NEW_FW_PATHNAME) and (
                os.stat(NEW_FW_PATHNAME).st_mtime !=
                os.stat("/storage/old.txt").st_mtime):
            version = open(NEW_FW_PATHNAME, mode="r")
        else:
            version = open("/storage/old.txt", mode="r")
        version = version.readline()

        settings = open('/storage/settings.txt', 'r')
        data = json.load(settings)
        url = data['output']

        check_success = settings_sanity_check()

        #успешная загрузка
        if check_success:
            log("Loaded version: " + str(version))

            key_t = False
            key_s = False
            key = '12345'
            level = data['alarm_level']

            threading.Thread(
                target=lambda: cron(3 * data['timeout'] + 1)).start()

            old_hash = md5(NEW_FW_PATHNAME)
            subprocess.call('cp /storage/new.txt /storage/old.txt', shell=True)
            new_hash = md5(NEW_FW_PATHNAME)
            if old_hash != new_hash:
                print("[rewriting] error in sources found")

        #неуспешная загрузка
        else:
            event.set()
            print("[reloading] stopping all systems")
            os.remove(NEW_FW_PATHNAME)
            print("[reloading] new sources was rejected")
            start()

    except Exception as e:
        log(f"exception raised {e}")
        print("[error] during loading!")
        return "Error during loading", 400
    return jsonify({"operation": "start requested", "status": True})


#получение данных на вход
@app.route("/data", methods=['POST'])
def data():
    content = request.json
    global level
    try:
        if content['value'] >= level:
            log("Alarm with level " + str(content['value']))
            out_b()
        else:
            out_d("send_data", content['value'])
            out_a(content['value'])
    except Exception as e:
        log(f"exception raised {e}")
        error_message = f"malformed request {request.data}"
        return error_message, 400
    return jsonify({"operation": "data_a", "status": True})


@app.route("/key_in", methods=['POST'])
def key_in():
    global key_t, key_s, key
    content = request.json
    try:
        if content['name'] == 'Security':
            key_s = True
        if content['name'] == 'Technical':
            key_t = True
        log("Key input event: " + str(content['name']))

        if key_t and key_s:
            log("Service input port activated")
            payload_n = ''
            payload_s = ''
            request_url = 'http://file_server:6001/download-update/new.txt'
            response = urlopen(request_url)
            headers = response.getheaders()
            data = response.read()
            payload_n = base64.b64encode(data).decode('ascii')
            request_url = 'http://file_server:6001/download-update/settings.txt'
            response = urlopen(request_url)
            data = response.read()
            payload_s = base64.b64encode(data).decode('ascii')
            if key == headers[9][1]:
                commit("new.txt", payload_n)
                commit("settings.txt", payload_s)
                log("Updates downloaded successfully")
            else:
                log("Bad key found")
    except Exception as e:
        log(f"exception raised {e}")
        error_message = f"malformed request {request.data}"
        return error_message, 400
    return jsonify({"operation": "key in ", "status": True})


@app.route("/key_out", methods=['POST'])
def key_out():
    global key_t, key_s
    content = request.json
    try:
        if content['name'] == 'Security':
            key_s = False
        if content['name'] == 'Technical':
            key_t = False
        log("Key output event: " + str(content['name']))

        if not key_s and not key_t:
            log("Service input port deactivated")
    except Exception as e:
        log(f"exception raised {e}")
        error_message = f"malformed request {request.data}"
        return error_message, 400
    return jsonify({"operation": "key in ", "status": True})


if __name__ == "__main__":
    app.run(port=port, host=host_name)
