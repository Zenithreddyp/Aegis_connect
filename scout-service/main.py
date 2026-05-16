import sys
import time
import os
import json
from Publisher import addScantoResult

LOGFILE_NAME = os.getenv("LOGFILE_NAME", "logfiles.log")


def IngestionLoop():
    count = 1
    log_batch = []

    with open(LOGFILE_NAME, "r") as file:
        file.seek(0, 2)

        start_time = time.time()
        while True:
            line = file.readline().strip()

            if line:
                pyline = json.loads(line)
                log_batch.append(pyline)
            else:
                time.sleep(0.1)

            if time.time() - start_time >= 2:
                if log_batch:
                    print(
                        f"{count}--- 2 sec done: Sending {len(log_batch)} logs to Queue ---"
                    )
                    count = count + 1
                    addScantoResult(json.dumps(log_batch))
                    print("BATCH SENT")
                    log_batch = []

                start_time = time.time()


if __name__ == "__main__":
    try:
        print("STARTED SCOUT")
        IngestionLoop()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
