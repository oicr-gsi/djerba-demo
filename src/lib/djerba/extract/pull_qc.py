#!/usr/bin/env python3

import json
import logging
import urllib.request as request
from djerba.util.logger import logger
try:
    import gsiqcetl.column
    from gsiqcetl import QCETLCache
except ImportError:
        raise ImportError('Error Importing QC-ETL, try checking python versions')

class pull_qc(logger):

    class Requisition():
        def __init__(self, pinery_requisition, pinery_assay):
            self.id: int = pinery_requisition['id']
            self.name: str = pinery_requisition['name']
            self.assay: str = pinery_assay['name']
            self.assay_id: int = pinery_assay['id']
            self.assay_description: str = pinery_assay['description']
            self.assay_version: str = pinery_assay['version']

    QCETL_CACHE = "/scratch2/groups/gsi/production/qcetl_v1"
    PINERY_URL = "http://pinery.gsi.oicr.on.ca"

    def __init__(self, log_level=logging.WARNING, log_path=None):
        self.logger = self.get_logger(log_level, __name__, log_path)


    def fetch_callability_etl_data(self,donor):
        etl_cache = QCETLCache(self.QCETL_CACHE)
        callability = etl_cache.mutectcallability.mutectcallability
        columns = gsiqcetl.column.MutetctCallabilityColumn
        callability_select = [
            columns.Donor, 
            columns.TissueType, 
            columns.GroupID,  
            columns.Callability
        ]
        data = callability.loc[
            (callability[columns.Donor] == donor),
            callability_select]
        callability_val = round(data.iloc[0][columns.Callability].item() * 100,1)
        return(callability_val)

    def fetch_coverage_etl_data(self,donor):
        etl_cache = QCETLCache(self.QCETL_CACHE)
        coverage = etl_cache.bamqc4merged.bamqc4merged
        cov_columns = gsiqcetl.column.BamQc4MergedColumn
        cov_select = [
            cov_columns.Donor, 
            cov_columns.TissueType,
            cov_columns.GroupID, 
            cov_columns.CoverageDeduplicated
        ]
        data = coverage.loc[
            (coverage[cov_columns.Donor] == donor) &
            (coverage[cov_columns.TissueType] != "R"),
            cov_select]
        cov_val = round(data.iloc[0][cov_columns.CoverageDeduplicated].item(),1)
        return(cov_val)

    def fetch_pinery_assay(self,requisition_name: str):
        pinery_requisition = self.pinery_get(f'/requisition?name={requisition_name}')
        pinery_assay = self.pinery_get(f'/assay/{pinery_requisition["assay_id"]}')
        requisition = self.Requisition(pinery_requisition, pinery_assay)    
        return(requisition.assay)

    def pinery_get(self,relative_url: str) -> dict:
        if not relative_url.startswith('/'):
            raise RuntimeError('Invalid relative url')
        return json.load(request.urlopen(f'{self.PINERY_URL}{relative_url}'))
    
