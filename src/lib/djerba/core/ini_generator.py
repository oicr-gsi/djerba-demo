"""
Generate an expected INI file for a list of plugins
File can then be manually completed
"""

import logging
import tempfile
from configparser import ConfigParser
from djerba.core.base import base as core_base
from djerba.core.configure import configurer as core_configurer
from djerba.core.workspace import workspace
import djerba.util.ini_fields as ini
from djerba.core.loaders import plugin_loader, merger_loader, helper_loader

class ini_generator(core_base):

    def __init__(self, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.plugin_loader = plugin_loader(self.log_level, self.log_path)
        self.merger_loader = merger_loader(self.log_level, self.log_path)
        self.helper_loader = helper_loader(self.log_level, self.log_path)

    def generate_config(self, component_names):
        # create a throwaway workspace
        tmp = tempfile.TemporaryDirectory(prefix='djerba_ini_generator')
        tmp_workspace = workspace(tmp.name, self.log_level, self.log_path)
        # load components and find expected ini for each
        config = ConfigParser()
        for name in component_names:
            if name == ini.CORE:
                component = core_configurer(self.log_level, self.log_path)
            elif self._is_helper_name(name):
                component = self.helper_loader.load(name, tmp_workspace)
            elif self._is_merger_name(name):
                component = self.merger_loader.load(name)
            else:
                component = self.plugin_loader.load(name, tmp_workspace)
            component_config = component.get_expected_config()
            config.add_section(name)
            for option in component_config.options(name):
                value = component_config.get(name, option)
                config.set(name, option, value)
        tmp.cleanup()
        return config

    def write_config(self, component_names, out_path):
        config = self.generate_config(component_names)
        with open(out_path, 'w') as out_file:
            config.write(out_file)
