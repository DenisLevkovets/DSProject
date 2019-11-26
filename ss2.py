import os
from flask import Flask, request, send_from_directory, make_response, jsonify
from werkzeug.utils import secure_filename
from werkzeug.middleware.shared_data import SharedDataMiddleware
import requests
from flask_cors import CORS

UPLOAD_FOLDER = './ss2'
ns_ip = "http://127.0.0.1:5000"
app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 128 * 1024 * 1024
app.secret_key = 'some secret key'

app.wsgi_app = SharedDataMiddleware(app.wsgi_app, {
    '/ss2': app.config['UPLOAD_FOLDER']
})

@app.route('/init', methods=['GET'])
def init():
    files = [file for file in os.listdir(app.config['UPLOAD_FOLDER'])]
    for file in files:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file))
    return make_response('succeed', 200)


@app.route('/copy', methods=['GET'])
def copy():
    try:
        index = request.args.get('index')
        indexNew = request.args.get('new_index')
        in_file = open(os.path.join(app.config['UPLOAD_FOLDER'], index), "rb")
        data = in_file.read()
        in_file.close()

        out_file = open(os.path.join(app.config['UPLOAD_FOLDER'], indexNew), "wb")
        out_file.write(data)
        out_file.close()
        return make_response('succeed', 200)
    except OSError:
        return make_response('failed', 400)


@app.route('/remove', methods=['GET'])
def remove():
    index = request.args.get('index')
    path = os.path.join(app.config['UPLOAD_FOLDER'], index)
    origin_path = request.args.get('path')
    os.remove(path)
    requests.get(ns_ip+"/file/delete/finish", params={'path': origin_path})
    return make_response('succeed', 200)

@app.route('/sync_remove', methods=['GET'])
def sync_remove():
    try:
        index = request.args.get('index')
        path = os.path.join(app.config['UPLOAD_FOLDER'], index)
        os.remove(path)
        return make_response('succeed', 200)
    except OSError:
        return make_response('not succeed', 400)


@app.route('/get_file', methods=['GET'])
def uploaded_file():
    index = request.args.get('index')
    return send_from_directory(app.config['UPLOAD_FOLDER'], index)


@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        return make_response('error', 400)
    index = request.form['index']
    path = request.form['path']
    if file:
        index = secure_filename(index)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], index))
        requests.get(ns_ip+"/file/upload/finish", params={'path': path,
                                                                         'index': index})
        return make_response('succeed', 200)
    return make_response('error', 400)


@app.route('/ping')
def ping():
    return make_response(request.host, 200)


@app.route('/file_list', methods=['GET'])
def file_list():
    files = [file for file in os.listdir(app.config['UPLOAD_FOLDER'])]
    print(files)
    return make_response(jsonify(files), 200)


@app.route('/info')
def info():
    index = request.form['index']
    size = round(os.path.getsize(os.path.join(app.config['UPLOAD_FOLDER'], index)) / (1024 * 1024), 2)
    return make_response(jsonify(size), 200)


@app.route('/sync_recv', methods=['POST'])
def sync_recv():
    ip = request.form['ip']
    index = request.form['index']
    print(ip, str(ip))
    path = request.form['path']
    filename = request.form['filename']
    if ip and index:
        payload = {'index': index, 'filename': filename}
        r = requests.get(ip + "get_file", params=payload)
        file = open(os.path.join(app.config['UPLOAD_FOLDER'], index), "wb")
        file.write(r.content)
        file.close()
        return make_response(jsonify(filename=filename,
                                     path=path,
                                     index=index), 200)
    return make_response('error (ip or index is missing)', 400)


if __name__ == '__main__':
    app.run(debug=True, port=5577)
