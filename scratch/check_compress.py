import gzip
import os

db_path = "data/anime.db"
gz_path = "data/anime.db.gz"

if os.path.exists(db_path):
    print(f"Original DB size: {os.path.getsize(db_path) / (1024*1024):.2f} MB")
    with open(db_path, "rb") as f_in:
        with gzip.open(gz_path, "wb", compresslevel=6) as f_out:
            while chunk := f_in.read(1024 * 1024):
                f_out.write(chunk)
    print(f"Compressed GZ size: {os.path.getsize(gz_path) / (1024*1024):.2f} MB")
