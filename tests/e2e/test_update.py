from multiprocessing import Process, Queue
import threading
from time import sleep
from flask import Flask, jsonify, request
import json
import requests

key = '12345'
event = threading.Event()
host_name = "0.0.0.0"
port = 6077
REQUEST_HEADERS = {
    "Content-Type": "application/json",
    "auth": "very-secure-token"
}
global_events_log = Queue()


# сервер для приёма сообщений с клиента в тестовых целях
app = Flask(__name__)  # create an app instance


@app.route("/", methods=['POST'])
def data_receive():
    global global_events_log
    try:
        content = request.json
        print(f"получено сообщение: {content['msg']}")
        global_events_log.put(content['msg'])                
    except Exception as e:
        print(e)
        return "BAD DATA RESPONSE", 400
    return jsonify({"status": True})


# начало работы, загрузка, "включение тумблера"
def start():
    data = {}
    response = requests.post(
        "http://0.0.0.0:6064/start",
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200


# авторизация ключа
def key_in(name):
    data = {"name": name}
    response = requests.post(
        "http://0.0.0.0:6064/key_in",
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200


# извлечение указанного ключа
def key_out(name):
    data = {"name": name}
    response = requests.post(
        "http://0.0.0.0:6064/key_out",
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200


#остановка всех процессов системы, "выключение тумблера"
def stop():
    data = {}
    response = requests.post(
        "http://0.0.0.0:6064/stop",
        data=json.dumps(data),
        headers=REQUEST_HEADERS,
    )
    assert response.status_code == 200


###
### Functionally tests
###


def test_full_functionality():
    # поднимаем тестовую скаду для приёма сообщений
    global global_events_log
    server = Process(target=lambda: app.run(port=port, host=host_name))
    server.start()

    #вводим настройки для запуска
    with open('./file_server/data/settings.txt', 'w') as f:
        data = {
            "timeout": 2,
            "max": 20,
            "alarm_level": 15,
            "output": "http://172.17.0.1:" + str(port) + "/"
        }
        json.dump(data, f)
        f.close()
    start()

    # вводим ключи, даем отработать, извлекаем ключи, завершая работу с обновлением
    sleep(2)
    key_in('Technical')
    key_in('Security')
    sleep(15)
    key_out('Technical')
    key_out('Security')
    sleep(2)
    stop()
    sleep(2)

    # останавливаем тестовую скаду
    server.terminate()
    server.join()

    events_log = []
    try:
        # считываем все накопленные события
        while True:
            event = global_events_log.get_nowait()
            events_log.append(event)
    except Exception as _:
        # больше событий нет
        pass
    # print(f"список событий: {events_log}")
    assert 'Updates downloaded successfully' in events_log
