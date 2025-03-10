from flask import Flask, Blueprint, send_from_directory
from datetime import datetime
from apis import api
import opt
import os

INTERVAL = os.getenv('INTERVAL', 5)
NOTIFY = os.getenv('NOTIFY', 1)

from uwsgidecorators import *


app = Flask(__name__)

# Prefixo para todas as rotas da API
blueprint = Blueprint('api', __name__, url_prefix='/ders/secondlayer')
api.init_app(blueprint)
app.register_blueprint(blueprint)

@app.route('/swaggerui/<path:path>')
def send_swagger_static(path):
    return send_from_directory('swaggerui', path)

#@cron(-NOTIFY, -1, -1, -1, -1)
#def print_ok(num):
#    print("OK", num, datetime.now())

@cron(-INTERVAL, -1, -1, -1, -1)
def print_opt(num):
    print('Running optimization - v4.2.1 ', num, datetime.now())
    opt.cron_function()


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
