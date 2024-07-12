import os
import platform
import subprocess
import yaml
from pathlib import Path

def get_config():

    config_file=Path('~/.pyLBPM/config.yml')
    environment_file=Path('~/.pyLBPM/config.sh')
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

def install_dependencies(install_path):
    success=False
        # check the operating system
    if platform.system() == "linux" or platform.system() == "linux2" or platform.system() == "Linux":
        # linux
        download_dependencies(install_path)
        success=subprocess.run(["bash", "install_lbpm_dependencies.sh","install_path", "--install"])

    else :
        print("Your platform is "+str(platform),": only linux installation is supported.")
        success=False

    return success

def download_dependencies(install_path):
    success=False
        # check the operating system
    if platform.system() == "linux" or platform.system() == "linux2" or platform.system() == "Linux":
        # linux        
        success=subprocess.run(["bash", "install_lbpm_dependencies.sh","install_path", "--download"])

    else :
        print("Your platform is "+str(platform),": only linux installation is supported.")
        success=False

    return success


def install_lbpm(install_path):
    success=True
    # check the operating system    
    if platform.system() == "linux" or platform.system() == "linux2" or platform.system() == "Linux":
        # linux

        success=subprocess.run(["bash", "install_lbpm.sh"])

    else :
        print("Your platform is "+str(platform.system()),": only linux installation is supported.")
        success=False

    #success=True
    return success

