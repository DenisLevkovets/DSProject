from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

counter = 0

ips = []

fs = {}
fs['dir1'] = {}
fs['dir1']['dir3'] = {}
fs['dir1']['dir2'] = {}
fs['dir1']['dir2']['filename.txt'] = [[1, 2], counter]  # ss and id


@app.route('/file/create', methods=['GET'])
def createFile():
    path = request.json['path']
    cur_dir, filename = search(path)
    if type(cur_dir) is dict:
        cur_dir[filename] = [[1], counter]
        print(fs)
        return 'File was created'
    else:
        return "Error"


@app.route('/file/read', methods=['GET'])
def readFile():
    return 'File was readed'


@app.route('/file/write', methods=['POST'])
def writeFile():
    return 'File was written'


@app.route('/file/delete', methods=['GET'])
def deleteFile():
    return 'File was deleted'


@app.route('/file/info', methods=['GET'])
def fileInfo():
    return 'Some info'


@app.route('/file/copy', methods=['GET'])
def copyFile():
    source = request.json['source']
    destination = request.json['destination']
    cur_dir_s, name_s = search(source)
    cur_dir_d, name_d = search(destination)
    print(fs)
    if name_s and name_d:
        try:
            cur_dir_d[name_d] = cur_dir_s[name_s].copy()
            cur_dir_d[name_d]['id'] += 1
            print(fs)
            return 'File was copied'
        except KeyError:
            return 'error'
    else:
        return 'error'


@app.route('/file/move', methods=['GET'])
def moveFile():
    source = request.json['source']
    destination = request.json['destination']
    cur_dir_s, name_s = search(source)
    cur_dir_d, name_d = search(destination)
    print(fs)
    if name_s and name_d:
        cur_dir_d[name_d] = cur_dir_s[name_s]
        cur_dir_s.pop(name_s)
        print(fs)
        return 'File was moved'
    else:
        return 'error'


@app.route('/init', methods=['GET'])
def init():
    return 'Initialization'


@app.route('/dir/read', methods=['GET'])
def readDir():
    path = request.args.get('path')
    cur_dir, name = search(path)
    return jsonify(str(list(cur_dir[name].keys())))


@app.route('/dir/make', methods=['GET'])
def makeDir():
    path = request.json['path']
    cur_dir, name = search(path)
    if name:
        cur_dir[name] = {}
        print(fs)
        return '200'
    else:
        print(fs)
        return '404'


@app.route('/dir/delete', methods=['GET'])
def deleteDir():
    path = request.json['path']
    cur_dir, name = search(path)
    if name:
        cur_dir.pop(name)
        print(fs)
        return '200'
    else:
        print(fs)
        return '404'


def search(path):
    dirs = path.split('/')
    filename = dirs[-1]
    try:
        if len(dirs) > 1:
            cur_dir = fs[dirs[0]]
            print(dirs)
            while len(dirs) > 2:
                if not type(cur_dir) is dict:
                    return False, False
                dirs = dirs[1:]
                cur_dir = cur_dir[dirs[0]]
                print(cur_dir)
            if type(cur_dir) is dict:
                return cur_dir, filename
            return False, False
        else:
            return fs, filename
    except KeyError:
        return False, False


def ping():
    pass


if __name__ == '__main__':
    app.run()
