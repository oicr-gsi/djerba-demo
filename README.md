# Djerba

Create reports from metadata and workflow output

## Introduction

Djerba translates cancer bioinformatics workflow outputs and metadata into standard reporting formats.

The current focus of Djerba is producing clinical reports, in the format developed by the Clinical Genome Informatics (CGI) group at [OICR](https://oicr.on.ca).

Djerba is named for an [island](https://en.wikipedia.org/wiki/Djerba) off the coast of North Africa. (The initial letter D is silent, so it is pronounced "jerba".)

## Quick start

- Run on an OICR cluster *compute node* -- not a head node, so R scripts work properly.
- See "INI configuration" below for the INI config file format.
- Load the Djerba environment module: `module load djerba`

### Examples

#### Generate a draft HTML report

`djerba.py draft --ini ${INI_INPUT_PATH} --dir ${INTERMEDIATE_OUTPUT_DIRECTORY} --html ${HTML_OUTPUT_PATH}`

#### Convert a CGI clinical report from HTML to PDF

Assuming appropriate HTML and analysis unit files are in `--pdf-dir`:

`djerba.py pdf --pdf-dir ${PDF_OUTPUT_DIR}`

More generally:

`djerba.py pdf --pdf-dir ${PDF_OUTPUT_DIR} --html ${HTML_PATH} --unit ${ANALYSIS_UNIT}`

#### One-step generation of a PDF report

`djerba.py all --ini ${INI_INPUT_PATH} --pdf-dir ${PDF_OUTPUT_DIR}`

## Command-line scripts

Run any script with `--help` for more information.

### `djerba.py`

This is the main script to run Djerba and generate reports.

Logging options are specified before the mode name, eg. `djerba.py --verbose --log-path djerba.log all ...`

#### Script modes

- `setup`: Set up an empty working directory for generating a CGI report
- `configure`: Read the INI config file supplied by the user; gather inputs from file provenance and other sources; write a fully-specified INI
- `extract`: Take a fully-specified INI as input; extract metrics and write to a reporting directory; optionally, write a JSON summary of metrics
- `html`: Input the reporting directory generated by `extract`, and write an HTML report
- `pdf`: Convert HTML to PDF. Default PDF output includes the CGI report footer; the footer may be omitted for general-purpose HTML to PDF conversion.
- `draft`: Generate a draft report, by running the configure/extract/html steps in sequence to output a reporting directory and HTML document. The draft output can then be edited, prior to generating a final PDF report.
- `all`: Run the complete reporting process, starting with user-supplied INI and finishing with PDF. Intermediate outputs such as HTML are optional.

#### INI configuration

The `configure`, `extract`, `draft` and `all` modes require an INI configuration file. Some parameters are required, while others are optional.

Documentation of file format and required parameters: [ini.md](./doc/ini.md)

Example INI file (with dummy value for the `mavis_file` parameter): [config_user.ini](./src/test/data/config_user.ini)

By default, the fully-specified INI file produced by `configure`, `draft`, or `all` will be archived to a location specified in the `archive_dir` INI parameter. This can be cancelled with the `--no-archive` argument to `djerba.py`.

### `html2pdf.py`

Convenience script for simple HTML to PDF conversion. Does not add the page footer used in Djerba reports.

### `sequenza_explorer.py`

Standalone script to explore available solutions in Sequenza output. (If gamma is not supplied to djerba.py, it will be found automatically.)

### `run_mavis.py`

Script to manually run the Mavis workflow, via the Cromwell development server. This will be required on a temporary basis before Mavis is added to automated CAP workflows, and later for troubleshooting.

### `wait_for_mavis.py`

Script to monitor the Mavis workflow launched by `run_mavis.py`. On successful completion, copies Mavis results to a given local directory.

## Prerequisites

The following OICR [Modulator](https://gitlab.oicr.on.ca/ResearchIT/modulator) environment modules are required:
- `python/3.7`
- `oncokb-annotator/2.0`
- `cbioportal/0.1`
- `rmarkdown/0.1m`
- `wkhtmltopdf/0.12.6`
- `cromwell/45.1`

Djerba has a `setup.py` script which will install its source code and Python dependencies. Production releases of Djerba will be installed as an environment modules in Modulator. Alternatively, install as described under `Installation`.

## Testing

- Clone the [Djerba test data repository](https://bitbucket.oicr.on.ca/projects/GSI/repos/djerba_test_data/browse)
- Set the environment variable `DJERBA_TEST_DATA` to the test data directory path
- Ensure all prerequisites are available
- Run unit tests with `src/test/test.py`

## Installation

- Ensure prerequisite modules are loaded and tests pass.
- Ensure an up-to-date version of [pip](https://pypi.org/project/pip/) is available.
- From the repo directory, run `pip install --prefix $INSTALL_DIR .` to install using `setup.py`. This will copy `djerba.py` to the `bin` directory, and relevant modules and data files to the `lib` directory, under the installation path `$INSTALL_DIR`.
- See `pip install --help` for further installation options.

## Development

### Repository Structure

#### Overview

- [src](./src): Production source code
- [src/bin/](./src/bin/): Scripts to run Djerba
- [src/lib/djerba](./src/lib/djerba): Python package for Djerba functions. Includes subdirectories for data files and R scripts.
- [src/test](./src/test): Tests for production code
- [prototypes](./prototypes): Development area for non-production scripts and tests

#### Contents of Djerba package directory

- Top-level python modules:
  - `configure.py`: Discover additional parameters for the user-supplied INI file
  - `main.py`: Main module to run Djerba functions
  - `mavis.py`: Manually run the Mavis workflow
  - `render.py`: Render output to HTML or PDF
  - `sequenza.py`: Process output from the Sequenza tool
- Python subpackages:
  - `extract`: Python classes to extract metrics from the given INI parameters
  - `util`: Constants and utility functions
- Other subdirectories:
  - `data`: Data files for Djerba Python classes and R scripts
  - `R_markdown`: R markdown script and ancillary files, for generating HTML
  - `R_stats`: R scripts for computing metrics, used by `extract`

### Release Procedure

- Update `CHANGELOG.md`
- Increment the version number in `setup.py`
- Commit (or merge) to the master branch, and tag the release on Github
- Update environment module configuration in [OICR Modulator](https://gitlab.oicr.on.ca/ResearchIT/modulator) to install the newly tagged release

### Development History

- **2019-01 to 2020-09**: The [cbioportal_tools](https://github.com/oicr-gsi/cbioportal_tools) project, also known as Janus, was a precursor to Djerba. This project was intended to produce reporting directories for [cBioPortal](https://cbioportal.org/).
- **2020-09**: The Djerba repository is created to replace `cbioportal_tools`. Its scope includes CGI clinical reporting as well as cBioPortal. Development releases, up to and including 0.0.4, address both output formats.
- **2021-05**: The scope of Djerba changes, to focus exclusively on CGI clinical reports and drop support for cBioPortal. Major overhaul and simplification of code, prior to release 0.0.5. Data processing for cBioPortal remains an option for the future.
- **2021-08**: Production release of Djerba for CGI reports.

## Copyright and License

Copyright (C) 2020, 2021 by Genome Sequence Informatics, Ontario Institute for Cancer Research.

Licensed under the [GPL 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html).
