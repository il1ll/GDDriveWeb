import base64
import gzip
import requests
import hashlib
import json
import random
import string
import zlib
import os
import io
from datetime import datetime
from flask import Flask, request, render_template, jsonify, send_file, redirect

app = Flask(__name__, template_folder='.')

headers = {"User-Agent": ""}
characters = string.ascii_letters + string.digits
start_of_level = "kS38,1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1000_7_1_15_1_18_0_8_1|1_0_2_102_3_255_11_255_12_255_13_255_4_-1_6_1001_7_1_15_1_18_0_8_1|1_0_2_102_3_255_11_255_12_255_13_255_4_-1_6_1009_7_1_15_1_18_0_8_1|1_255_2_255_3_255_11_255_12_255_13_255_4_-1_6_1002_5_1_7_1_15_1_18_0_8_1|1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1013_7_1_15_1_18_0_8_1|1_40_2_125_3_255_11_255_12_255_13_255_4_-1_6_1014_7_1_15_1_18_0_8_1|1_0_2_200_3_255_11_255_12_255_13_255_4_-1_6_1005_5_1_7_1_15_1_18_0_8_1|1_0_2_125_3_255_11_255_12_255_13_255_4_-1_6_1006_5_1_7_1_15_1_18_0_8_1|,kA13,0,kA15,0,kA16,0,kA14,,kA6,0,kA7,0,kA25,0,kA17,0,kA18,0,kS39,0,kA2,0,kA3,0,kA8,0,kA4,0,kA9,0,kA10,0,kA22,0,kA23,0,kA24,0,kA27,1,kA40,1,kA48,1,kA41,1,kA42,1,kA28,0,kA29,0,kA31,1,kA32,1,kA36,0,kA43,0,kA44,0,kA45,1,kA46,0,kA47,0,kA33,1,kA34,1,kA35,0,kA37,1,kA38,1,kA39,1,kA19,0,kA26,0,kA20,0,kA21,0,kA11,0;"
used_keys = [1, 6, 7, 8, 9, 10, 12, 20, 21, 22, 23, 24, 25, 28, 29, 33, 34, 45, 46, 47, 50, 51, 54, 61, 63, 68, 69, 71, 72, 73, 75, 76, 77, 80, 84, 85, 90, 91, 92, 95, 97, 105, 107, 108, 113, 114, 115]

def xor_cipher(text, key):
    result = []
    for i, ch in enumerate(text):
        byte = ord(ch)
        x_key = ord(key[i % len(key)])
        result.append(chr(byte ^ x_key))
    return "".join(result)

def generate_gjp2(password: str = "", salt: str = "mI29fmAnxgTs") -> str:
    password += salt
    return hashlib.sha1(password.encode()).hexdigest()

def generate_chk(values: list = [], key: str = "", salt: str = "") -> str:
    values.append(salt)
    string_val = ("").join(map(str, values))
    hashed = hashlib.sha1(string_val.encode()).hexdigest()
    xored = xor_cipher(hashed, key)
    return base64.urlsafe_b64encode(xored.encode()).decode()

def generate_upload_seed(data: str, chars: int = 50) -> str:
    if len(data) < chars: return data
    step = len(data) // chars
    return data[::step][:chars]

def parse_level(level_string: str):
    file_bytes = bytearray()
    level_objects = level_string.split(";")[1:]
    for obj in level_objects:
        split_object = obj.split(",")
        for i in range(0, len(split_object), 2):
            try:
                if int(split_object[i]) in used_keys:
                    val = int(split_object[i + 1])
                    if int(split_object[i]) != 1:
                        if val > 255: file_bytes.append(255)
                        elif val < 0: file_bytes.append(0)
                        else:
                            if i + 1 < len(split_object): file_bytes.append(val)
                    else:
                        if val > 255: file_bytes.append(255)
                        elif val < 0: file_bytes.append(0)
                        else:
                            if i + 1 < len(split_object): file_bytes.append(val - 1)
            except: continue
    return file_bytes

def make_level(file_bytes: bytearray):
    current_x, current_y = 0, 500
    i, key_on = 1, 1
    current_object = "1," + str(file_bytes[0] + 1) + ",2,0,3,500,"
    level_string = ""
    object_count = 1
    while i < len(file_bytes):
        current_object += str(used_keys[key_on]) + "," + str(file_bytes[i])
        key_on += 1
        if key_on == len(used_keys):
            key_on = 1
            i += 1
            level_string += current_object + ";"
            current_y -= 30
            if current_y < 0: current_y, current_x = 500, current_x + 30
            if i + 1 >= len(file_bytes): continue
            current_object = "1," + str(file_bytes[i] + 1) + ",2," + str(current_x) + ",3," + str(current_y) + ","
            object_count += 1
        else: current_object += ","
        i += 1
    level_string += current_object + ";"
    object_count += 1
    return start_of_level + level_string, object_count

def encode_level(level_string: str, is_official_level: bool) -> str:
    gzipped = gzip.compress(level_string.encode())
    base64_encoded = base64.urlsafe_b64encode(gzipped)
    if is_official_level: base64_encoded = base64_encoded[13:]
    return base64_encoded.decode()

def decode_level(level_data: str, is_official_level: bool) -> str:
    if is_official_level: level_data = 'H4sIAAAAAAAAA' + level_data
    base64_decoded = base64.urlsafe_b64decode(level_data.encode())
    decompressed = zlib.decompress(base64_decoded, 15 | 32)
    return decompressed.decode()

def downloadLevel(level_id: int) -> str:
    request_data = {"levelID": level_id, "secret": "Wmfd2893gb7"}
    req = requests.post(url="https://www.boomlings.com/database/downloadGJLevel22.php", data=request_data, headers=headers)
    split_res2 = req.text.split("#")[0].split(":")
    level_string = ""
    for i in range(0, len(split_res2), 2):
        if split_res2[i] == "4":
            level_string = split_res2[i + 1]
            break
    if level_string == "": return ""
    return decode_level(level_string, False)

def get_credentials():
    if os.path.exists("credentials.json"):
        with open("credentials.json", "r") as f: return json.load(f)
    return None

def get_index():
    if os.path.exists("index.json"):
        with open("index.json", "r") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_index(data):
    with open("index.json", "w") as f: json.dump(data, f)

@app.route('/')
def index():
    creds = get_credentials()
    idx = get_index()
    return render_template('index.html', credentials=creds, index_data=idx)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    account_id = request.form.get('account_id')
    gjp_2 = generate_gjp2(password)
    data = {"gjp2": gjp_2, "username": username, "account_id": account_id}
    with open("credentials.json", "w") as f: json.dump(data, f)
    return redirect('/')

@app.route('/upload', methods=['POST'])
def upload_file():
    creds = get_credentials()
    if not creds: return jsonify({"success": False, "error": "Unauthorized"}), 401
    file = request.files.get('file')
    if not file or file.filename == '': return jsonify({"success": False, "error": "No file"}), 400
    level_name = request.form.get('level_name')
    song_id = int(request.form.get('song_id', 763439))
    requested_stars = int(request.form.get('requested_stars', 10))
    unlisted = int(request.form.get('unlisted', 0))
    file_bytes = file.read()
    level_string, obj_count = make_level(bytearray(file_bytes))
    level_string = encode_level(level_string, False)
    data = {
        "gameVersion": 22, "binaryVersion": 47, "accountID": creds["account_id"], "gjp2": creds["gjp2"],
        "userName": creds["username"], "levelID": 0, "levelName": level_name, "levelDesc": "",
        "levelVersion": 999, "levelLength": 0, "audioTrack": 0, "auto": 0, "password": 1,
        "original": 0, "twoPlayer": 0, "songID": song_id, "objects": obj_count, "coins": 0,
        "requestedStars": requested_stars, "unlisted": unlisted, "ldm": 0, "levelString": level_string,
        "seed2": generate_chk(key="41274", values=[generate_upload_seed(level_string)], salt="xI25fpAapCQg"),
        "secret": "Wmfd2893gb7", "dvs": 3
    }
    req = requests.post(url="https://www.boomlings.com/database/uploadGJLevel21.php", data=data, headers=headers)
    if req.text != "-1":
        idx = get_index()
        idx[file.filename] = {"level_id": int(req.text), "level_name": level_name}
        save_index(idx)
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Upload failed"}), 400

@app.route('/download_id', methods=['POST'])
def download_by_id():
    level_id = request.form.get('level_id')
    file_name = request.form.get('file_name')
    if not level_id or not file_name: return "Error", 400
    l_str = downloadLevel(int(level_id))
    if not l_str: return "Not Found", 404
    f_bytes = parse_level(l_str)
    return send_file(io.BytesIO(f_bytes), as_attachment=True, download_name=file_name, mimetype='application/octet-stream')

@app.route('/delete', methods=['POST'])
def delete_file():
    creds = get_credentials()
    if not creds: return redirect('/')
    level_id = request.form.get('level_id')
    filename = request.form.get('filename')
    req_data = {
        "accountID": creds["account_id"], "gjp2": creds["gjp2"],
        "levelID": int(level_id), "secret": "Wmfv2898gc9"
    }
    req = requests.post(url="https://www.boomlings.com/database/deleteGJLevelUser20.php", data=req_data, headers=headers)
    if req.text != "-1":
        idx = get_index()
        if filename in idx:
            del idx[filename]
            save_index(idx)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, port=5000)

