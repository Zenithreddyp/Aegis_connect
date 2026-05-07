import time
import os
import json 
from Publisher import addScantoResult

LOGFILE_NAME="logfiles.log"


def IngestionLoop():
    log_batch = []

    with open(LOGFILE_NAME, "r") as file:

        file.seek(0, 2)

        start_time = time.time()
        while True:
            
            line = file.readline().strip()

            if line:
                pyline = json.loads(line)
                log_batch.append(pyline)
                print(f"Captured log at: {pyline.get('@timestamp', 'N/A')}")
            else:
                time.sleep(0.1)

            if time.time() - start_time >= 1:
                if log_batch:
                    print(f"--- 1 sec done: Sending {len(log_batch)} logs to Queue ---")
                    addScantoResult(json.dumps(log_batch))
                    log_batch = []
            
                start_time = time.time()


if __name__ == "__main__":
    IngestionLoop()
