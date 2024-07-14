from opt import software
from datetime import datetime
import time
import opt

while(1):
    opt.cron_function()
    print(datetime.now())
    #add 5 minutes dalay
    time.sleep(60)
    print(datetime.now())
    time.sleep(60)
    print(datetime.now())
    time.sleep(60)
    print(datetime.now())
    time.sleep(60)
    print(datetime.now())
