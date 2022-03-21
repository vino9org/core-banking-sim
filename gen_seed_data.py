import ulid

with open("seed.csv", "w") as f:
    for _ in range(0, 100):
        cust_id = f"CUS{str(ulid.new())}"
        acc_id = f"ACC{str(ulid.new())}"
        f.write(f"{cust_id},{acc_id},SGD,200000.00,active,\n")
