import csv
import sys
from datetime import datetime
from typing import List

import redis
import requests
from redis_om.model.encoders import jsonable_encoder

from core_banking.ledger import init_from_csv


def account_for(aid: int):
    seq = str(aid).zfill(7)
    return {
        "pk": f":core_banking.models.CheckingAccount:ACC_{seq}",
        "customer_id": f"CUS_{seq}",
        "account_id": f"ACC_{seq}",
        "currency": "SGD",
        "avail_balance": "100000.00",
        "balance": "100000.00",
        "status": 1,
        "updated_at": datetime.now().isoformat(),
    }


def encode_account(obj: dict) -> List[str]:
    pk = obj["pk"]
    items = ["HSET", pk]
    for pair in jsonable_encoder(obj).items():
        items.extend(pair)
    return items


def gen_protocol(start_n: int, stop_n: int, out_f=sys.stdout.buffer):
    conn = redis.Connection()
    for aid in range(start_n, stop_n):
        acc = account_for(aid)
        out_f.write(conn.pack_command(*encode_account(acc))[0])


def gen_seed_csv(filename: str, start_n: int, stop_n: int) -> None:
    with open(filename, "w") as out_f:
        fields = ["customer_id", "account_id", "currency", "avail_balance", "balance", "status", "limit"]
        writer = csv.DictWriter(out_f, fieldnames=fields)
        writer.writeheader()
        for nn in range(start_n, stop_n):
            seq = str(nn).zfill(7)
            writer.writerow(
                {
                    "customer_id": f"CUS_{seq}",
                    "account_id": f"ACC_{seq}",
                    "currency": "SGD",
                    "avail_balance": "100000.00",
                    "balance": "100000.00",
                    "status": 1,
                    "limit": "5000000.00",
                }
            )


def post_seed_data(url: str, filename: str) -> None:
    with open(filename, "r") as f:
        response = requests.post(
            f"{url}/core-banking/_internal/seed/", files={"content-type": "text/csv", "upload_file": f}  # type: ignore
        )
        if response.status_code != 200:
            print(f"got error posting data. {response.status_code}, {response.text}")
        else:
            print("done")


def usage():
    print(
        """
Usage: python seed_data.py <command>

where <command> is

   gen   <csv_file> <start> <stop>   generate seed data using id from <start> to <stop> and write output to csv file
   load  <csv_file>                  load seed data from csv file.
   post  <url> <csv_file>            read seed data csv file and post to API endpoint
   bulk  <start> <stop>              generate seed data in redis binary protocol format using id start to stop and
                                     write output to stdout, which is usable with for bulk loading with redis-cli --pipe
"""
    )


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("load", "bulk", "gen", "post"):
        usage()
        sys.exit(1)

    if sys.argv[1] == "bulk" and len(sys.argv) == 4:
        # to use the output with redis-cli, pipe the output to redis-cli --pipe
        start_n, stop_n = int(sys.argv[2]), int(sys.argv[3]) + 1
        gen_protocol(start_n, stop_n)

    elif sys.argv[1] == "load" and len(sys.argv) == 3:
        with open(sys.argv[2], "r") as f:
            init_from_csv(f, 10000)

    elif sys.argv[1] == "gen" and len(sys.argv) == 5:
        start_n, stop_n = int(sys.argv[3]), int(sys.argv[4]) + 1
        with open(sys.argv[3], "w") as f:
            gen_seed_csv(sys.argv[2], start_n, stop_n)

    elif sys.argv[1] == "post" and len(sys.argv) == 4:
        with open(sys.argv[3], "r") as f:
            post_seed_data(sys.argv[2], sys.argv[3])

    else:
        usage()
        sys.exit(1)
