from flask import Flask, request, jsonify

host_name = "0.0.0.0"
port = 6069

app = Flask(__name__)             # create an app instance


@app.route("/data_d", methods=['POST'])
def data_digit_msg_receive():
    try:
        content = request.json
        print(f"[DATA] получено цифровое значение: {content['value']}")
    except Exception as e:
        print(f"exception raised: {e}")
        return "BAD REQUEST", 400
    return jsonify({"operation": "data_d", "status": True})

@app.route("/data_a", methods=['POST'])
def data_analog_msg_receive():
    try:
        content = request.json
        print(f"[DATA] получено аналоговое значение: {content['value']}")
    except Exception as e:
        print(f"exception raised: {e}")
        return "BAD REQUEST", 400
    return jsonify({"operation": "data_a", "status": True})

@app.route("/diagnostic", methods=['POST'])
def diagnostic_msg_receive():
    try:
        content = request.json
        print(f"[DIAGNOSTIC] проверка завершена со статусом: {content['status']}")
    except Exception as e:
        print(f"exception raised: {e}")
        return "BAD REQUEST", 400
    return jsonify({"operation": "diagnostic", "status": True})

@app.route("/key", methods=['POST'])
def key_msg_receive():
    try:
        content = request.json
        print(f"[KEY] изменен ключ: {content['key']}")
    except Exception as e:
        print(f"exception raised: {e}")
        return "BAD REQUEST", 400
    return jsonify({"operation": "key", "status": True})

@app.route("/error", methods=['POST'])
def err_msg_receive():
    try:
        content = request.json
        print(f"[ERROR] произошла ошибка: {content['error']}")
    except Exception as e:
        print(f"exception raised: {e}")
        return "BAD REQUEST", 400
    return jsonify({"operation": "error", "status": True})

if __name__ == "__main__":        
    app.run(port = port, host=host_name)