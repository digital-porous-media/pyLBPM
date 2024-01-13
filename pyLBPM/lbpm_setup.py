import os
import platform
import subprocess
import yaml
from pathlib import Path

def get_config():

    config_file=Path('~/.pyLBPM/config.yml')
    config = None
    if config_file.is_file() :        
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
    else :
        print("No configuration found. Run lbpm_setup.initialize() to initialize the environment")

    return config


def initialize():
    config = None
    if platform.system() == "linux" or platform.system() == "linux2" or platform.system() == "Linux":
        print("Enter path to LBPM installation:")
        lbpm_install_path=Path(input())
        print("Installing LBPM software to "+str(lbpm_install_path))
        install_lbpm(lbpm_install_path)
        
    else :
        print("Your platform is "+str(platform.system()),": only linux installation is supported.")
        
    return config

def install_openmpi(install_path):
    success=false
        # check the operating system
    if platform.system() == "linux" or platform.system() == "linux2" or platform.system() == "Linux":
        # linux        
        #for the cuda version
        use_cuda=subprocess.check_output(['which','nvcc'])
        if (use_cuda):
            print("GPU detected: compling GPU enabled version of openmpi")
        else :
            print("No GPU detected: compiling CPU version of openmpi")

        success=subprocess.run(["bash scripts/install_lbpm.sh","install_path"])

    else :
        print("Your platform is "+str(platform),": only linux installation is supported.")
        success=false

    return success


def install_hdf5(install_path):
    success=True
    return success


def install_lbpm(install_path):
    success=True
    # check the operating system    
    if platform.system() == "linux" or platform.system() == "linux2" or platform.system() == "Linux":
        # linux

        success=subprocess.run(["bash", "scripts/install_lbpm.sh", "install_path"])

    else :
        print("Your platform is "+str(platform.system()),": only linux installation is supported.")
        success=false

    #success=True
    return success


