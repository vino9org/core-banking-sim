import sys
import tempfile
from multiprocessing import Process

import requests


def post_seed_data(url: str, start_n: int, stop_n: int) -> None:
    with tempfile.TemporaryFile(mode="w+") as temp_f:
        temp_f.write("customer_id,account_id,currency,avail_balance,balance,status\n")
        for nn in range(start_n, stop_n):
            seq = str(nn).zfill(7)
            line = f"CUS_{seq},ACC_{seq},SGD,100000.00,100000.00,1\n"
            temp_f.write(f"{line}")

        temp_f.seek(0)
        response = requests.post(
            f"{url}/core-banking/_internal/seed/", files={"content-type": "text/csv", "upload_file": temp_f}
        )
        if response.status_code != 200:
            print(f"got error posting data. {response.status_code}, {response.text}")

    return None


# currently running with multiple child process seems to be slower
# than running with a single process. need to investigate server logic

if __name__ == "__main__":
    url, batch_size, batches = sys.argv[1], int(sys.argv[2]), 1
    if len(sys.argv) > 3:
        batches = int(sys.argv[3])

    if batches > 100:
        print("batches must be <= 100")
        sys.exit(1)

    batch_size = int(batch_size / batches)
    children = []
    for num in range(batches):
        start_n, stop_n = num * batch_size, (num + 1) * batch_size
        print(f"starting child_p={start_n}-{stop_n}")
        child_p = Process(target=post_seed_data, args=(url, start_n, stop_n))
        child_p.start()
        children.append((start_n, stop_n, child_p))

    for start_n, stop_n, child_p in children:
        child_p.join()
        print(f"stopped child_p={start_n}-{stop_n}")
