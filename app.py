from flask import Flask, render_template, jsonify, request
import threading
import os
from main import run_check

app = Flask(__name__)

status = {
    'running': False,
    'progress': '',
    'logs': []
}

def add_log(msg):
    status['logs'].append(msg)
    if len(status['logs']) > 100:
        status['logs'].pop(0)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_check():
    if status['running']:
        return jsonify({'error': 'Уже запущено'}), 400
    
    start_row = request.json.get('start_row', 2)
    
    def run():
        status['running'] = True
        status['logs'] = []
        try:
            run_check(start_row, add_log)
        except Exception as e:
            add_log(f"Ошибка: {e}")
        finally:
            status['running'] = False
    
    thread = threading.Thread(target=run)
    thread.start()
    
    return jsonify({'status': 'started'})

@app.route('/api/status')
def get_status():
    return jsonify(status)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
