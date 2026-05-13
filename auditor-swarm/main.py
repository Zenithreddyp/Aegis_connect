import os
import sys

from messaging.consumer import start_consumer

if __name__ == "__main__":
    try:
        start_consumer()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
