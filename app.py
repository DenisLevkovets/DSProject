import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

counter = 1
ips = ['http://127.0.0.1:5566/', 'http://127.0.0.1:5577/', 'http://127.0.0.1:5588/']
available_ips = []

fs = {}
fs['dir1'] = {}
fs['dir1']['dir3'] = {}
fs['dir1']['dir2'] = {}


@app.route('/file/create', methods=['GET'])
def createFile():
    global counter
    path = request.args.get('path')
    cur_dir, filename = search(path)
    if type(cur_dir) is dict:
        try:
            check = cur_dir[filename]
            return {"res": "500"}
        except KeyError:
            cur_dir[filename] = [[], int(counter)]
            counter += 1
            return {'res': '200'}
    else:
        return {'res': '404'}


@app.route('/file/read', methods=['GET'])
def readFile():
    path = request.args.get('path')
    cur_dir, name = search(path)
    ping()
    try:
        if type(cur_dir[name]) is list and len(available_ips) > 0:
            return {"res": available_ips[0] + "get_file", 'id': int(cur_dir[name][1])}
    except KeyError:
        return {"res": "404"}


@app.route('/file/write', methods=['GET'])
def writeFile():
    global counter
    path = request.args.get('path')
    cur_dir, filename = search(path)
    ping()
    if type(cur_dir) is dict and len(available_ips) > 0:
        resp = {"res": available_ips[0] + 'upload', "id": int(counter)}
        counter += 1
        return resp
    else:
        return {"res": "404"}


@app.route('/file/upload/finish', methods=['GET'])
def uploadFinish():
    path = request.args.get('path')
    index = request.args.get('index')
    cur_dir, name = search(path)
    remote_addr = 'http://' + request.remote_addr + ":5566/"
    cur_dir[name] = [[remote_addr], int(index)]
    ips_to_sync = available_ips.copy()
    ips_to_sync.pop(available_ips.index(remote_addr))
    for ip in ips_to_sync:
        response = requests.post(ip + 'sync_recv', data={'ip': str(remote_addr), 'index': index, 'filename': name, 'path': path})
        if response.status_code == 400:
            return {"res": "400"}
        elif response.status_code == 200:
            cur_dir[name][0].append(ip)
    return {"res": "200"}


@app.route('/file/delete', methods=['GET'])
def deleteFile():
    path = request.args.get('path')
    cur_dir, name = search(path)
    ping()
    try:
        print(available_ips, 'delete')
        if type(cur_dir[name]) is list and len(available_ips) > 0:
            return {"res": available_ips[0] + "remove", 'id': int(cur_dir[name][1]), 'status': '200'}
        else:
            return {"res": "500"}
    except KeyError:
        return {"res": "404"}


@app.route('/file/delete/finish', methods=['GET'])
def deleteFinish():
    path = request.args.get('path')
    cur_dir, name = search(path)
    remote_addr = 'http://' + request.remote_addr + ":5566/"
    ips_to_sync = available_ips.copy()
    ips_to_sync.pop(available_ips.index(remote_addr))
    print(ips_to_sync, 'deletesync')
    try:
        if type(cur_dir[name]) is list:
            index = cur_dir[name][1]
            print(1)
            if len(ips_to_sync) >= 1:
                print(2)
                while len(ips_to_sync) != 0:
                    print(3)
                    for ip in ips_to_sync:
                        print(4)
                        response = requests.get(ip + 'sync_remove', params={'index': index})
                        if response.status_code == 400:
                            print('err')
                            return {"res": "404"}
                        elif response.status_code == 200:
                            ips_to_sync.pop(ips_to_sync.index(ip))
            cur_dir.pop(name)
            return {"res": "200"}
        else:
            return {"res": "500"}
    except KeyError:
        return {"res": "404"}


@app.route('/file/info', methods=['GET'])
def fileInfo():
    return 'Some info'


@app.route('/file/copy', methods=['GET'])
def copyFile():
    global counter
    source = request.args.get('source')
    destination = request.args.get('destination')
    cur_dir_s, name_s = search(source)
    cur_dir_d, name_d = search(destination)
    if name_s and name_d:
        try:
            cur_dir_d[name_d] = cur_dir_s[name_s].copy()
            cur_dir_d[name_d][1] = counter
            counter += 1
            return {"res": "200"}
        except KeyError:
            return {"res": "400"}
    else:
        return {"res": "400"}


@app.route('/file/move', methods=['GET'])
def moveFile():
    source = request.args.get('source')
    destination = request.args.get('destination')
    cur_dir_s, name_s = search(source)
    cur_dir_d, name_d = search(destination)
    if name_s and name_d:
        cur_dir_d[name_d] = cur_dir_s[name_s]
        cur_dir_s.pop(name_s)
        return {"res": "200"}
    else:
        return {"res": "400"}


@app.route('/init', methods=['GET'])
def init():
    global fs, available_ips
    fs = {}
    for ip in ips:
        try:
            response = requests.get(ip + 'ping')
            if response.status_code == 200:
                available_ips.append(ip)
            elif response.status_code == 400:
                pass
        except requests.exceptions.ConnectionError:
            pass
    return {"res": 'Initialization'}


@app.route('/dir/read', methods=['GET'])
def readDir():
    path = request.args.get('path')
    cur_dir, name = search(path)
    if len(path) == 0:
        return jsonify({"res": str(list(cur_dir.keys()))})
    else:
        return jsonify({"res": str(list(cur_dir[name].keys()))})


@app.route('/dir/make', methods=['GET'])
def makeDir():
    path = request.args.get('path')
    cur_dir, name = search(path)
    try:
        if type(cur_dir[name]) is dict:
            return {'res': "500"}
    except KeyError:
        if name:
            cur_dir[name] = {}
            return {'res': "200"}
        else:
            return {'res': "404"}


@app.route('/dir/delete', methods=['GET'])
def deleteDir():
    path = request.args.get('path')
    cur_dir, name = search(path)
    try:
        if type(cur_dir[name]) is dict:
            cur_dir.pop(name)
            return {"res": "200"}
        else:
            return {"res": "500"}
    except KeyError:
        return {"res": "404"}


@app.route('/dir/open', methods=['GET'])
def openDir():
    path = request.args.get('path')
    cur_dir, name = search(path)
    print(cur_dir, name)
    try:
        if type(cur_dir[name]) is dict:
            return {'res': '200'}
        else:
            return {'res': '500'}
    except KeyError:
        return {'res': '404'}


def search(path):
    dirs = path.split('/')
    filename = dirs[-1]
    try:
        if len(dirs) > 1:
            cur_dir = fs[dirs[0]]
            while len(dirs) > 2:
                if not type(cur_dir) is dict:
                    return False, False
                dirs = dirs[1:]
                cur_dir = cur_dir[dirs[0]]
            if type(cur_dir) is dict:
                return cur_dir, filename
            return False, False
        else:
            return fs, filename

    except KeyError:
        return False, False


def ping():
    global available_ips
    new_available_ips = []
    ips_to_sync = []
    for ip in ips:
        try:
            response = requests.get(ip + 'ping')
            if response.status_code == 200:
                new_available_ips.append(ip)
                if ip not in available_ips:
                    ips_to_sync.append(ip)
            elif response.status_code == 400:
                pass
        except requests.exceptions.ConnectionError:
            pass
    available_ips = new_available_ips
    if len(ips_to_sync) > 0:
        sync(ips_to_sync)


def sync(ips):
    for ip in ips:
        response = requests.get(ip + 'file_list')
        if response.status_code == 200:
            indexes = response.json()
            files_to_upload, files_to_delete = separate_from_dfs(ip, indexes)
            for file in files_to_upload:
                filename = file[1][:-1].split('/')[-1]
                path = file[1][:-1]
                index = file[0][1]
                remote_addr = file[0][0][0]
                cur_dir, name = search(path)
                response = requests.post(ip + 'sync_recv', data={'ip': str(remote_addr), 'index': index, 'filename': filename, 'path': path})
                if response.status_code == 400:
                    return {"res": "400"}
                elif response.status_code == 200:
                    cur_dir[name][0].append(ip)
            print(ip, files_to_delete)
            for file in files_to_delete:
                response = requests.get(ip + 'sync_remove', params={'index': file})
                if response.status_code == 400:
                    return {"res": "400"}


def separate_from_dfs(ip, indexes):
    dfs_files = dfs(fs, [])
    dfs_indexes = []
    files_to_upload = []
    files_to_delete = []
    for file in dfs_files:
        dfs_indexes.append(file[0][1])
        if ip not in file[0][0]:
            files_to_upload.append(file)
    for index in indexes:
        if int(index) not in dfs_indexes:
            files_to_delete.append(index)
    return files_to_upload, files_to_delete


def dfs(node, res, path=''):
    if type(node) is list:
        res.append([node, path])
        return res
    keys = node.keys()
    if len(keys) != 0:
        for key in keys:
            dfs(node[key], res, path + key + '/')
        return res
    else:
        return res


if __name__ == '__main__':
    init()
    app.run()
