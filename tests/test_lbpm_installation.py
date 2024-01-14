from pyLBPM import lbpm_setup

lbpm_install_path="~/tmp"

lbpm_config_setup=lbpm_setup.download_dependencies(lbpm_install_path)
lbpm_config_setup=lbpm_setup.install_dependencies(lbpm_install_path)
lbpm_config_setup=lbpm_setup.install_lbpm(lbpm_install_path)


print(lbpm_config_setup)
