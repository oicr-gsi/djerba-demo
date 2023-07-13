"""
Plugin for TAR SWGS.
"""

# IMPORTS
import os
from djerba.plugins.base import plugin_base
from mako.lookup import TemplateLookup
import djerba.plugins.tar.swgs.constants as constants
from djerba.plugins.tar.swgs.preprocess import preprocess
from djerba.plugins.tar.swgs.extract import data_builder 
import djerba.core.constants as core_constants


class main(plugin_base):
    
    PLUGIN_VERSION = '1.0.0'
    PRIORITY = 100 
    TEMPLATE_NAME = 'swgs_template.html'
    
    def specify_params(self):

      # Required parameters for swgs
      self.add_ini_required('seg_file')

      # Default parameters for priorities
      #self.set_ini_default('configure_priority', 100)
      #self.set_ini_default('extract_priority', 100)
      #self.set_ini_default('render_priority', 100)
      self.set_priority_defaults(self.PRIORITY)

      # Default parameters for clinical, supplementary
      self.set_ini_default(core_constants.CLINICAL, True)
      self.set_ini_default(core_constants.SUPPLEMENTARY, False)

    def configure(self, config):
      config = self.apply_defaults(config)
      return config

    def extract(self, config):
      

      wrapper = self.get_config_wrapper(config)
      
      # Get the seg file from the config
      seg_file = wrapper.get_my_string('seg_file')
    

      # Pre-process all the files
      work_dir = self.workspace.get_work_dir()
      preprocess(work_dir, seg_file).run_R_code()

      data = {
          'plugin_name': 'Shallow Whole Genome Sequencing (sWGS)',
          'version': self.PLUGIN_VERSION,
          'priorities': wrapper.get_my_priorities(),
          'attributes': wrapper.get_my_attributes(),
          'merge_inputs': {},
          'results': data_builder(work_dir, seg_file).build_swgs()
      }
      return data

    def render(self, data):
      super().render(data)
      args = data
      html_dir = os.path.realpath(os.path.join(
          os.path.dirname(__file__),
          'html'
      ))
      report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
      mako_template = report_lookup.get_template(self.TEMPLATE_NAME)
      try:
          html = mako_template.render(**args)
      except Exception as err:
          msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
          self.logger.error(msg)
          raise
      return html
