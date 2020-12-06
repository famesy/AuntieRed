import time

start = time.time()
while(1):
    now = time.time()
    print(now)
    if now - start > 10:
        break