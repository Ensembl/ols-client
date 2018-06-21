# -*- coding: utf-8 -*-
import time
import urllib.parse

from coreapi import Client, exceptions, Document
from hal_codec import HALCodec

import ebi.ols.api.helpers as helpers


# TODO: add coreapi dependencies
# TODO: create class hierarchy for api client
# TODO: shortcut all calls in subsequent methods name, respecting naming from OLS as far as possible
# TODO: manage errrors
# TODO: logs execution


class OLSClient(object):
    """
    OLS Client ontologies client

    """
    base_url = "https://www.ebi.ac.uk/ols/api"
    _client = None
    decoders = [HALCodec()]

    def __init__(self, url=None):
        self.client = Client(decoders=self.decoders)
        if url is not None:
            self.document = self.client.get(url)
            self.base_url = url
        else:
            self.document = self.client.get(self.base_url)

    def ontologies(self, page=None, size=None) -> Document:
        params = {'page': page if page else None, 'size': size if size else None}
        raw = self.client.action(self.document, ["ontologies"], params=params, validate=False)

        if 'ontologies' in raw.data:
            # only return ontologies if some exists
            return raw
        else:
            # else return a error
            raise exceptions.ErrorMessage(
                helpers.Error(error="Bad Request", message="No corresponding ontologies", status=400,
                              path='ontologies', timestamp=time.time()))

    def ontology(self, onto_name) -> Document:
        """
        Get ontology details from its short identifier i.e go, fypo etc.

        :param onto_name:
        """
        uri = "/".join([self.base_url, "ontologies", onto_name])
        document = self.client.get(uri)
        return document

    def terms(self, onto_name=None, page=0, size=20, filters=None) -> Document:
        """
        Get ontologies terms, if no filter set, return a first page of terms

        :param size: size of excpeted list, default 20
        :param page: the requested page number
        :param onto_name: filter terms by ontology
        :param filters: a dict with following possible keys
            - type: Restrict a search to an entity type, one of {class,property,individual,ontology}
            - slim: Restrict a search to an particular set of slims by name
            - fieldList: Specify the fields to return, the defaults are {iri,label,short_form,obo_id,ontology_name,ontology_prefix,description,type}
            - obsoletes: Set to true to include obsoleted terms in the results
            - local: Set to true to only return terms that are in a defining ontology e.g. Only return matches to gene ontology terms in the gene ontology, and exclude ontologies where those terms are also referenced
            - childrenOf: You can restrict a search to all children of a given term. Supply a list of IRI for the terms that you want to search under (subclassOf/is-a relation only)
            - allChildrenOf: You can restrict a search to all children of a given term. Supply a list of IRI for the terms that you want to search under (subclassOf/is-a plus any hierarchical/transitive properties like 'part of' or 'develops from')
            - rows: How many results per page
            - start: The results page number
        :return: A list of Term
        """
        if filters is None:
            filters = {}
        uri = "/".join([self.base_url, "ontologies", onto_name, "terms"])
        params = {"page": page, "size": size}
        final_uri = uri + urllib.parse.urlencode(params)
        # TODO add filters management according to https://www.ebi.ac.uk/ols/docs/api#resources-terms
        # Check passed filters and raise error
        final_uri += urllib.parse.urlencode(params) if filters else None
        terms = self.client.get(uri)
        print(terms.data["terms"])
        return terms

    def searchTerm(self, filters=None):
        if filters is None:
            filters = {}


if __name__ == "__main__":
    # TODO add arg parse and associated method calls
    print('Coming soon')
