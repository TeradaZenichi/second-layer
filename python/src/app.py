from uwsgidecorators import *
from datetime import datetime
from flask import Flask
from apis import api
import opt


app = Flask(__name__)
api.init_app(app)


@cron(-1, -1, -1, -1, -1)
def print_ok(num):
    print("OK", num, datetime.now())

@cron(-5, -1, -1, -1, -1)
def print_opt(num):
    print('Running optimization', num, datetime.now())
    opt.cron_function()


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
