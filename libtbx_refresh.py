import dials.precommitbx.nagger

dials.precommitbx.nagger.nag()

# Find the xia2 package root directory
import libtbx.load_env
import os

libtbx_xia2_module = libtbx.env.module_dict["xia2"]
xia2_path = abs(libtbx_xia2_module.dist_paths[0])
if not os.path.isdir(xia2_path):
    raise RuntimeError("xia2 installation not found at", repr(xia2_path))
print(xia2_path)

import pkg_resources

installed_python_packages = {pkg.key for pkg in pkg_resources.working_set}

import subprocess
import sys

if "xia2" not in installed_python_packages:
    # First time installation
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--no-deps", "-e", xia2_path],
        check=True,
    )
else:
    # Update installation
    subprocess.run(
        [sys.executable, "setup.py", "develop", "--no-deps"], cwd=xia2_path, check=True
    )

# the import implicitly updates the .gitversion file
from xia2.XIA2Version import Version

print(Version)
