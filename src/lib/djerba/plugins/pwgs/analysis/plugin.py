"""Djerba plugin for pwgs reporting"""
import os
import csv
from decimal import Decimal
import csv
import re

from mako.lookup import TemplateLookup
from djerba.plugins.base import plugin_base
import djerba.plugins.pwgs.constants as constants
from djerba.util.subprocess_runner import subprocess_runner
import djerba.util.provenance_index as index
from djerba.core.workspace import workspace

class main(plugin_base):

    RESULTS_SUFFIX = '\.mrdetect\.txt$'
    VAF_SUFFIX = 'mrdetect.vaf.txt'
    HBC_SUFFIX = 'HBCs.csv'
    
    def configure(self, config_section):
        return config_section

    def extract(self, config_section):
        try:
            self.provenance = self.subset_provenance()
            results_file_path = self.parse_file_path(self.RESULTS_SUFFIX, self.provenance)
            vaf_file_path = self.parse_file_path(self.VAF_SUFFIX, self.provenance)
            hbc_file_path = self.parse_file_path(self.HBC_SUFFIX, self.provenance)
            self.logger.info("PWGS ANALYSIS: Files pulled from Provenance")
        except OSError:
            results_file_path = config_section[constants.RESULTS_FILE]
            vaf_file_path = config_section[constants.VAF_FILE]
            hbc_file_path = config_section[constants.HBC_FILE]
            self.logger.info("PWGS ANALYSIS: Files pulled from ini")
        hbc_results = self.preprocess_hbc(hbc_file_path)
        reads_detected = self.preprocess_vaf(vaf_file_path)
        mrdetect_results = self.preprocess_results(results_file_path)
        pwgs_base64 = self.write_pwgs_plot(hbc_file_path,vaf_file_path)
        self.logger.info("PWGS ANALYSIS: Finished preprocessing files")       
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
    
    def _get_most_recent_row(self, rows):
        # if input is empty, raise an error
        # otherwise, return the row with the most recent date field (last in lexical sort order)
        # rows may be an iterator; if so, convert to a list
        rows = list(rows)
        if len(rows)==0:
            msg = "Empty input to find most recent row; no rows meet filter criteria?"
            self.logger.debug(msg)
            raise MissingProvenanceError(msg)
        else:
            return sorted(rows, key=lambda row: row[index.LAST_MODIFIED], reverse=True)[0]
        
    def parse_file_path(self, file_pattern, provenance):
        # get most recent file of given workflow, metatype, file path pattern, and sample name
        # self._filter_* functions return an iterator
        iterrows = self._filter_file_path(file_pattern, rows=provenance)
        try:
            row = self._get_most_recent_row(iterrows)
            path = row[index.FILE_PATH]
        except MissingProvenanceError as err:
            msg = "No provenance records meet filter criteria: path-regex = {0}.".format(file_pattern)
            self.logger.debug(msg)
            path = None
        return path
    
    def _filter_file_path(self, pattern, rows):
        return filter(lambda x: re.search(pattern, x[index.FILE_PATH]), rows)
    
    def subset_provenance(self):
        provenance = []
        with self.workspace.open_gzip_file(constants.PROVENANCE_OUTPUT) as in_file:
            reader = csv.reader(in_file, delimiter="\t")
            for row in reader:
                if row[index.WORKFLOW_NAME] == "mrdetect":
                    provenance.append(row)
        return(provenance)

    
class MissingProvenanceError(Exception):
    pass
