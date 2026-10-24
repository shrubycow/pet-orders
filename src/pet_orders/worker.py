import os
import time


def main() -> None:
    if not os.environ.get("RABBITMQ_URL"):
        raise RuntimeError("RABBITMQ_URL is not set")
    print("worker started")
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
