#! /usr/bin/env python3

import hashlib, logging, json, os, random, tempfile, unittest

from djerba.genetic_alteration import genetic_alteration
from djerba.report import report, DjerbaReportError
from djerba.sample import sample
from djerba.study import study
from djerba.utilities import constants
from djerba.validate import validator, DjerbaConfigError

class TestBase(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_test_')
    
    def verify_checksums(self, checksums, out_dir):
        """Checksums is a dictionary: md5sum -> relative path from output directory """
        for relative_path in checksums.keys():
            out_path = os.path.join(out_dir, relative_path)
            self.assertTrue(os.path.exists(out_path), out_path+" exists")
            md5 = hashlib.md5()
            with open(out_path, 'rb') as f:
                md5.update(f.read())
            self.assertEqual(md5.hexdigest(),
                             checksums[relative_path],
                             out_path+" checksums match")

    def tearDown(self):
        self.tmp.cleanup()

class TestReport(TestBase):
    """Tests for clinical report output"""

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_report_test_')

    def test_demo(self):
        """Test with default 'demo' output of the genetic_alteration superclass"""
        random.seed(42) # set the random seed to ensure consistent demo output
        out_dir = os.path.join(self.tmp.name, 'test_report_demo')
        os.mkdir(out_dir)
        with open(os.path.join(self.dataDir, 'study_config.json')) as configFile:
            config = json.loads(configFile.read())
        report_name = 'sample_report.json'
        report_path = os.path.join(out_dir, report_name)
        sample_id = 'OCT-01-0472-CAP'
        study_id = config[constants.STUDY_META_KEY][constants.STUDY_ID_KEY]
        test_report = report(config, sample_id, log_level=logging.ERROR)
        test_report.write_report_config(report_path)
        self.assertTrue(os.path.exists(report_path), "JSON report exists")
        checksum = {report_name: '2adf75bd2f70586b7703fe4bfb1c1759'}
        self.verify_checksums(checksum, out_dir)
        args = [config, 'nonexistent sample', logging.CRITICAL]
        self.assertRaises(DjerbaReportError, report, *args)

class TestScript(TestBase):
    """Minimal test of command-line script"""

    def setUp(self):
        super().setUp()
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.scriptName = 'djerba.py'
        self.scriptPath = os.path.join(self.testDir, os.pardir, 'bin', self.scriptName)

    def test_compile(self):
        with open(self.scriptPath, 'rb') as inFile:
            self.assertIsNotNone(
                compile(inFile.read(), self.scriptName, 'exec'),
                'Script compiled without error'
            )

class TestStudy(TestBase):

    """Tests for cBioPortal study generation"""

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))
        self.tmp = tempfile.TemporaryDirectory(prefix='djerba_study_test_')
        # clinical patients/samples files currently identical, but this will change
        # temporarily removed mutation config from study_config.json, so some case lists are omitted
        self.base_checksums = {
            'data_cancer_type.txt': '31d0678d437a5305dcf8e76a9ccc40ff',
            'data_clinical_patients.txt': 'd6fb18fa41b196964b45603fa06daf93',
            'data_clinical_samples.txt': 'd6fb18fa41b196964b45603fa06daf93',
            'meta_cancer_type.txt': '19d950648288bb7428e8aaf5ee2939a0',
            'meta_clinical_patients.txt': 'd5b8ba2aa2b50eb4f63f41ccda817618',
            'meta_clinical_samples.txt': '3e02417baf608dacb4e5e2df0733c9cf',
            'meta_study.txt': '10fe55a5d41501b9081e8ad69915fce5',
            #'case_lists/cases_3way_complete.txt': 'b5e5d0c300b3365eda75955c1be1f405',
            #'case_lists/cases_cnaseq.txt': 'a02611d78ab9ef7d7ac6768a2b9042b7',
            'case_lists/cases_custom.txt': 'e9bd0b716cdca7b34f20a70830598c2d',
            #'case_lists/cases_sequenced.txt': '634dfc2e289fe6877c35b8ab6d31c091'
        }

    def test_dry_run(self):
        """Test meta file generation in dry run of cBioPortal study"""
        out_dir = os.path.join(self.tmp.name, 'study_dry_run')
        os.mkdir(out_dir)
        config_path = os.path.join(self.dataDir, 'study_config.json')
        with open(config_path) as configFile:
            config = json.loads(configFile.read())
        test_study = study(config, log_level=logging.ERROR)
        test_study.write_all(out_dir, dry_run=True)
        self.verify_checksums(self.base_checksums, out_dir)

    def test_mutation_extended(self):
        """Test the mutation extended genetic alteration type"""
        out_dir = os.path.join(self.tmp.name, 'study_mutation_extended')
        os.mkdir(out_dir)
        config_path = os.path.join(self.dataDir, 'study_config_mx.json')
        with open(config_path) as configFile:
            config = json.loads(configFile.read())
        test_study = study(config, log_level=logging.ERROR)
        test_study.write_all(out_dir)
        checksums = self.base_checksums.copy()
        # clinical patient/sample data differs from default
        extra_checksums = {
            'data_clinical_patients.txt': '89980a5953c405fcf9cf8aa2037e0058',
            'data_clinical_samples.txt': '89980a5953c405fcf9cf8aa2037e0058',
            'data_mutation_extended.maf': '957c36b2dee54c9272da7591d0796bf8',
            'meta_mutation_extended.txt': 'cc5684c4b1558fb3fc93d30945e3cfeb',
            'case_lists/cases_sequenced.txt': 'de25114a2102fd0d67ba7335b8feaa25'
        }
        checksums.update(extra_checksums)
        self.verify_checksums(checksums, out_dir)

class TestValidator(unittest.TestCase):
    # TestBase methods not needed

    def setUp(self):
        self.testDir = os.path.dirname(os.path.realpath(__file__))
        self.dataDir = os.path.realpath(os.path.join(self.testDir, 'data'))

    def test(self):
        config_path = os.path.join(self.dataDir, 'study_config.json')
        with open(config_path) as configFile:
            config = json.loads(configFile.read())
        test_validator = validator(log_level=logging.CRITICAL)
        sample = 'OCT-01-0472-CAP'
        self.assertTrue(
            test_validator.validate(config, None),
            "Study config is valid"
        )
        self.assertTrue(
            test_validator.validate(config, sample),
            "Study config is valid with sample name"
        )
        args = [config, 'nonexistent_sample']
        self.assertRaises(
            DjerbaConfigError,
            test_validator.validate,
            *args
        )      
        del config[constants.GENETIC_ALTERATIONS_KEY]
        args = [config, None]
        self.assertRaises(
            DjerbaConfigError,
            test_validator.validate,
            *args
        )

if __name__ == '__main__':
    unittest.main()