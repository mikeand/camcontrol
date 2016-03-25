import os

from flask import Flask, jsonify, request

app = Flask(__name__)
ENABLED_FILE = '/tmp/pir_enable'


@app.route('/motion/')
def get_motion():
    is_enabled = os.path.exists(ENABLED_FILE)
    return jsonify({
        'enabled': is_enabled
    })


@app.route('/motion/', methods=['POST'])
def post_motion():
    is_enabled = True
   
    status = request.get_json()
    if status and 'enabled' in status.keys():
        if status['enabled']:
            open(ENABLED_FILE, 'a').close()
            is_enabled = True
        else:
            try:
                os.remove(ENABLED_FILE)
            except:
                pass
            finally:
                is_enabled = False

        return jsonify({
            'enabled': is_enabled
        }), 201
    return "Bad Request", 400

if __name__ == '__main__':
    app.run()

