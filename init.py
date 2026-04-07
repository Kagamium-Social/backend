import os
import subprocess
import sys
import database

def file(target): # stupid but why not
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), target)

def init():
    print("Checking requirements...")
    miss_req = []
    try:
        from importlib.metadata import version, PackageNotFoundError
        from packaging.requirements import Requirement
        from packaging.version import Version
        with open("requirements.txt") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                req = Requirement(line)
                try:
                    installed = Version(version(req.name))
                    if req.specifier and installed not in req.specifier:
                        miss_req.append(req.name)
                except PackageNotFoundError:
                    miss_req.append(req.name)
    except ImportError:
        miss_req = ["sex"]
    if miss_req:
        if "sex" in miss_req:
            print("Some requirements are not installed or have unsupported version.")
        else:
            print("Following requirements are not installed or have unsupported version:")
            for x in miss_req:
                print(x)
        install_req = input("Install requirements? (y/N): ")
        if install_req == "Y" or install_req == "y":
            print("Running \'python -m pip install -r requirements.txt\'...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", file("requirements.txt")])
        else:
            return 0
    print("Done.")

    print("Initializing database...")
    database.init()
    print("Done.")


if init() != 0:
    print("Starting api.py, good luck")
    import api
else:
    print("lol gg skill issue low aura -999999 social credit")