"""
This script configures the environment variables required for rpy2 to locate the R installation
"""

import os
import platform
import subprocess

def configure_r_environment():
    if "R_HOME" in os.environ and os.environ["R_HOME"]:
        r_home = os.environ["R_HOME"]
    else:
        try:
            r_home = subprocess.check_output(
                ["R", "RHOME"],
                text=True,
                stderr=subprocess.DEVNULL
            ).strip()
            os.environ["R_HOME"] = r_home
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise EnvironmentError(
                "Could not locate R installation. Ensure R is installed"
            )

    if platform.system() == "Windows":
        bin_path = os.path.join(r_home, "bin", "x64")
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(bin_path)
        os.environ["PATH"] = bin_path + os.pathsep + os.environ["PATH"]
        
    elif platform.system() == "Darwin":
        # On macOS, rpy2 needs R's lib dir on the dynamic linker path
        lib_path = os.path.join(r_home, "lib")
        os.environ["DYLD_LIBRARY_PATH"] = (
            lib_path + os.pathsep + os.environ.get("DYLD_LIBRARY_PATH", "")
        )

    elif platform.system() == "Linux":
        lib_path = os.path.join(r_home, "lib")
        os.environ["LD_LIBRARY_PATH"] = (
            lib_path + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
        )

