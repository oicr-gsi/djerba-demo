"""Djerba merger for gene information"""

import logging
import os
import re
import djerba.render.constants as constants # TODO how do we handle constants in plugins?
from djerba.mergers.base import merger_base

class main(merger_base):

    SCHEMA_FILENAME = 'gene_information_schema.json'
    SORT_KEY = 'Gene_URL'

    def __init__(self, log_level=logging.WARNING, log_path=None):
        schema_path = os.path.join(os.path.dirname(__file__), self.SCHEMA_FILENAME)
        super().__init__(schema_path, log_level, log_path)

    def table_header(self):
        names = [
            constants.GENE,
            constants.SUMMARY
        ]
        return self.thead(names)

    def table_rows(self, row_fields):
        rows = []
        for row in row_fields:
            # italicize the gene name where it appears in the summary
            # name must be:
            # - preceded by a space or start-of-string
            # - followed by a space or listed punctuation
            summary = re.sub('(^| ){0}[,.;: ]'.format(row[constants.GENE]),
                             lambda m: '<i>{0}</i>'.format(m[0]),
                             row[constants.SUMMARY])
            cells = [
                self.td(
                    self.href(row[constants.GENE_URL], row[constants.GENE]), italic=True
                ),
                self.td(summary)
            ]
            rows.append(self.tr(cells))
        return rows

    def render(self, inputs):
        self.validate_inputs(inputs)
        data = self.merge_and_sort(inputs, self.SORT_KEY)
        # TODO use CSS/Mako for appropriate template style
        html = [self.TABLE_START, self.table_header()]
        html.extend(self.table_rows(data))
        html.append(self.TABLE_END)
        return "\n".join(html)

