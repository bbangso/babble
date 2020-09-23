from flask import Flask, request
from ObjDetection.yolo import YOLO
from PIL import Image
from io import BytesIO
import json
import pyrebase
import requests
import pickle
import tensorflow as tf
# import 추가

app = Flask(__name__)
app.yolo = YOLO()
app.config['JSON_AS_ASCII'] = False

graph = tf.get_default_graph()

# Initialize firebase app
with open("config.pickle", "rb") as f:
    config = pickle.load(f)

firebase = pyrebase.initialize_app(config)
storage = firebase.storage()

@app.route('/')
def index_page():
    return "AI Server!"

@app.route('/tags', methods=['POST'])
def tags():
    
    # firebase image path
    path = json.loads(request.get_data(), encoding='utf-8')
    path = path['path']


    # load image
    url = storage.child(path).get_url(None)
    res = requests.get(url)
    img = Image.open(BytesIO(res.content))
    
    tags=[] # 추출된 tag가 담길 list

    # obj detection을 통한 tag 추출
    with graph.as_default():
        tags += app.yolo.extract_tag(img)

    data = {
        'tags': tags
    }

    return data

if __name__ == '__main__':
    app.run()