"""
Render Djerba results in HTML and PDF format
"""

import json
import logging
import os
import pdfkit
from mako.template import Template
from mako.lookup import TemplateLookup

import djerba.util.constants as constants
import djerba.util.ini_fields as ini
from djerba.render.archiver import archiver
from djerba.util.logger import logger

class html_renderer(logger):

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        html_dir = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            '..',
            constants.DATA_DIR_NAME,
            'html'
        ))
        # strict_undefined=True provides an informative error for missing variables in JSON
        # see https://docs.makotemplates.org/en/latest/runtime.html#context-variables
        report_lookup = TemplateLookup(directories=[html_dir,], strict_undefined=True)
        self.template = report_lookup.get_template("clinical_report_template.html")

    def run(self, in_path, out_path, archive=True):
        with open(in_path) as in_file:
            data = json.loads(in_file.read())
            args = data.get(constants.REPORT)
            config = data.get(constants.SUPPLEMENTARY).get(constants.CONFIG)
        with open(out_path, 'w') as out_file:
            print(self.template.render(**args), file=out_file)
        if archive:
            self.logger.info("Finding archive parameters for {0}".format(out_path))
            try:
                archive_dir = config[ini.SETTINGS][ini.ARCHIVE_DIR]
            except KeyError:
                self.logger.warn("Archive directory not found in config")
                archive_dir = None
            try:
                patient_id = config[ini.DISCOVERED][ini.PATIENT_ID]
            except KeyError:
                patient_id = 'Unknown'
                msg = "Patient ID not found in config, falling back to '{0}'".format(patient_id)
                self.logger.warn(msg)
            if archive_dir:
                archive_args = [out_path, archive_dir, patient_id]
                archiver(self.log_level, self.log_path).run(**archive_args)
                self.logger.info("Archived {0} to {1} with ID '{2}'".format(**archive_args))
            else:
                self.logger.warn("No archive directory; omitting archiving")
        else:
            self.logger.info("Archive operation not requested; omitting archiving")


class pdf_renderer(logger):

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)

    # Running the PDF renderer requires the wkhtmltopdf binary on the PATH
    # This can be done by loading the wkhtmltopdf environment module:
    # https://gitlab.oicr.on.ca/ResearchIT/modulator/-/blob/master/code/gsi/70_wkhtmltopdf.yaml

    # Current implementation runs with javascript disabled
    # If javascript is enabled, PDF rendering attempts a callout to https://mathjax.rstudio.com
    # With Internet access, this works; otherwise, it times out after ~4 minutes and PDF rendering completes
    # But rendering without Javascript runs successfully with no apparent difference in output
    # So it is disabled, to allow fast running on a machine without Internet (eg. cluster node)
    # See https://github.com/wkhtmltopdf/wkhtmltopdf/issues/4506
    # An alternative solution would be changing the HTML generation to omit unnecessary Javascript

    def run(self, html_path, pdf_path, footer_text=None, footer=True):
        """Render HTML to PDF"""
        # create options, which are arguments to wkhtmltopdf for footer generation
        # the 'quiet' option suppresses chatter to STDOUT
        self.logger.info('Writing PDF to {0}'.format(pdf_path))
        if footer:
            if footer_text:
                self.logger.info("Including footer text for CGI clinical report")
                options = {
                    'footer-right': '[page] of [topage]',
                    'footer-center': footer_text,
                    'quiet': '',
                    'disable-javascript': ''
                }
            else:
                self.logger.info("Including page numbers but no additional footer text")
                options = {
                    'footer-right': '[page] of [topage]',
                    'quiet': '',
                    'disable-javascript': ''
                }
        else:
            self.logger.info("Omitting PDF footer")
            options = {
                'quiet': '',
                'disable-javascript': ''
            }
        pdfkit.from_file(html_path, pdf_path, options = options)
        self.logger.info('Finished writing PDF')
