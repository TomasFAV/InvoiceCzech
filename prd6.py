
import os
from pathlib import Path
from PIL import Image

def main():
    path: str = Path("/home/tom-k/Desktop/faktury/training/png/zacerneno/B")

    file_list = os.listdir(path)

    file_paths = [Path(os.path.join(path,f)) for f in file_list if Path(os.path.join(path,f)).exists()]

    for file_path in file_paths:
        if file_path.suffix != ".png":
            continue

        img = Image.open(file_path)
        res = img.resize((1654, 2339))
        res.save(file_path)

if __name__ == "__main__":
    main()
