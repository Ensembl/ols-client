# -*- coding: utf-8 -*-

from coreapi import Client

import ebi.ols.api.helpers as helpers
from ols.api.base import decoders, site, DetailClientMixin, ListClientMixin, SearchClientMixin


class OlsClient(object):
    """
    TODO: add individuals and properties services
    OLS Client ontologies client

    """
    def __init__(self) -> None:
        self.client = Client(decoders=decoders)
        document = self.client.get(site)
        self.ontologies = ListClientMixin('ontologies', helpers.Ontology, document)
        self.ontology = DetailClientMixin('ontologies', helpers.Ontology)
        self.terms = ListClientMixin('terms', helpers.Term, document)
        self.term = DetailClientMixin('terms', helpers.Term)
        self.search = SearchClientMixin('search', helpers.Term, document)


if __name__ == "__main__":
    # TODO add arg parse and associated method calls
    print('Coming soon')
