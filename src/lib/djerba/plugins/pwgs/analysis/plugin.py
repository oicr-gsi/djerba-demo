"""Djerba plugin for pwgs reporting"""
import os
import csv
import logging
from decimal import Decimal

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as constants
from djerba.util.subprocess_runner import subprocess_runner
from djerba.util.logger import logger

class main(plugin_base):

    def configure(self, config_section):
        return config_section

    def extract(self, config_section):
        hbc_results = self.preprocess_hbc(config_section[constants.HBC_FILE])
        reads_detected = self.preprocess_vaf(config_section[constants.VAF_FILE])
        mrdetect_results = self.preprocess_results(config_section[constants.RESULTS_FILE])
        pwgs_base64 = self.write_pwgs_plot(config_section[constants.HBC_FILE],config_section[constants.VAF_FILE])
        self.logger.info("PWGS: Finished preprocessing files")       
        data = {
            'plugin_name': 'pwgs.analysis',
            'clinical': True,
            'failed': False,
            'merge_inputs': {
                'gene_information': []
            },
            'results': {
                'outcome': mrdetect_results['outcome'],
                'significance_text': mrdetect_results['significance_text'],
                'TFZ': mrdetect_results['TF'],
                'TFR': round(reads_detected / hbc_results['reads_checked']*100,4) ,
                'sites_checked': hbc_results['sites_checked'],
                'reads_checked': hbc_results['reads_checked'],
                'sites_detected': hbc_results['sites_detected'],
                'reads_detected': reads_detected,
                'p-value': mrdetect_results['pvalue'],
                'hbc_n': hbc_results['hbc_n'],
                'pwgs_base64': pwgs_base64
            }
        }
        return data

    def render(self, data):
        args = data
        html_dir = os.path.realpath(os.path.join(
            os.path.dirname(__file__),
            '..',
            'html'
        ))
        report_lookup = TemplateLookup(directories=[html_dir, ], strict_undefined=True)
        mako_template = report_lookup.get_template(constants.ANALYSIS_TEMPLATE_NAME)
        try:
            html = mako_template.render(**args)
        except Exception as err:
            msg = "Unexpected error of type {0} in Mako template rendering: {1}".format(type(err).__name__, err)
            self.logger.error(msg)
            raise
        return html    

    def preprocess_hbc(self, hbc_path):
        """
        summarize healthy blood controls (HBC) file
        """
        sites_checked = []
        reads_checked = []
        sites_detected = []
        with open(hbc_path, 'r') as hbc_file:
            reader_file = csv.reader(hbc_file, delimiter=",")
            next(reader_file, None)
            for row in reader_file:
                try:
                    sites_checked.append(row[2])
                    reads_checked.append(row[3])
                    sites_detected.append(row[4])
                except IndexError as err:
                    msg = "Incorrect number of columns in HBC row: '{0}'".format(row)+\
                        "read from '{0}'".format(hbc_path)
                    raise RuntimeError(msg) from err
        hbc_n = len(sites_detected) - 1
        hbc_dict = {'sites_checked': int(sites_checked[0]),
                    'reads_checked': int(reads_checked[0]),
                    'sites_detected': int(sites_detected[0]),
                    'hbc_n': hbc_n}
        return hbc_dict
    
    def preprocess_vaf(self, vaf_path):
        """
        summarize Variant Allele Frequency (VAF) file
        """
        reads_detected = 0
        with open(vaf_path, 'r') as hbc_file:
            reader_file = csv.reader(hbc_file, delimiter="\t")
            next(reader_file, None)
            for row in reader_file:
                try: 
                    reads_tmp = row[1]
                    reads_detected = reads_detected + int(reads_tmp)
                except IndexError as err:
                    msg = "Incorrect number of columns in vaf row: '{0}' ".format(row)+\
                          "read from '{0}'".format(vaf_path)
                    raise RuntimeError(msg) from err
        return reads_detected
    
    def preprocess_results(self, results_path):
        """
        pull data from results file
        """
        results_dict = {}
        with open(results_path, 'r') as hbc_file:
            reader_file = csv.reader(hbc_file, delimiter="\t")
            next(reader_file, None)
            for row in reader_file:
                try:
                    results_dict = {
                                    'TF': round(float(row[7])*100*2,4),
                                    'pvalue':  float('%.3E' % Decimal(row[10]))
                                    }
                except IndexError as err:
                    msg = "Incorrect number of columns in vaf row: '{0}' ".format(row)+\
                          "read from '{0}'".format(results_path)
                    raise RuntimeError(msg) from err
        if results_dict['pvalue'] > float(constants.DETECTION_ALPHA) :
            significance_text = "not significantly larger"
            results_dict['outcome'] = "NEGATIVE"
            results_dict['TF'] = 0
        elif results_dict['pvalue'] <= float(constants.DETECTION_ALPHA):
            significance_text = "significantly larger"
            results_dict['outcome'] = "POSITIVE"
        else:
            msg = "results pvalue {0} incompatible with detection alpha {1}".format(results_dict['pvalue'], constants.DETECTION_ALPHA)
            self.logger.error(msg)
            raise RuntimeError
        results_dict['significance_text'] = significance_text
        return results_dict
    
    def write_pwgs_plot(self, hbc_path, vaf_file, output_dir = None):
        if output_dir == None:
            output_dir = os.path.join('./')
        args = [
            os.path.join('/.mounts/labs/CGI/scratch/fbeaudry/reporting/djerba/src/lib/djerba/plugins/pwgs/analysis/','plot_detection.R'),
            '--hbc_results', hbc_path,
            '--vaf_results', vaf_file,
            '--output_directory', output_dir 
        ]
        pwgs_results = subprocess_runner().run(args)
        os.remove(os.path.join(output_dir,'pWGS.svg'))
        return(pwgs_results.stdout.split('"')[1])