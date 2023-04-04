"""
Abstract base class for mergers
Cannot be used to create an object (abstract) but can be subclassed (base class)
"""

import logging
from abc import ABC
from djerba.core.json_validator import json_validator
from djerba.util.html import html_builder
from djerba.util.logger import logger

class merger_base(logger, html_builder, ABC):

    def __init__(self, schema_path, log_level=logging.INFO, log_path=None):
        self.log_level = log_level
        self.log_path = log_path
        self.logger = self.get_logger(log_level, __name__, log_path)
        self.logger.debug("Using constructor of parent class")
        self.json_validator = json_validator(schema_path, self.log_level, self.log_path)

    def merge_and_sort(self, inputs, sort_key):
        """
        Merge a list of inputs matching the schema, remove duplicates, sort by given key
        """
        merged = list(set(inputs))
        return sorted(merged, key = lambda x: x[sort_key])

    def render(self, inputs):
        """
        Input is a list of data structures, obtained one or more plugins
        Each input structure must match the schema for this merger
        Output is a string (for inclusion in an HTML document)
        """
        msg = "Using method of parent class; checks inputs and returns empty string"
        self.logger.debug(msg)
        for item in inputs:
            self.json_validator.validate_data(item)
        return ''

    def validate_inputs(self, inputs):
        for item in inputs:
            self.json_validator.validate_data(item)
        self.logger.info("All merger inputs validated")
