# -*- coding: utf-8 -*-
import time
import urllib.parse
import warnings

import coreapi.exceptions
from coreapi import Client

import ebi.ols.api.exceptions as exceptions
import ebi.ols.api.helpers as helpers
import ebi.ols.api.lists as lists
import ebi.ols.api.utils as utils
from ols.api.base import decoders, site, DetailClientMixin, ListClientMixin


class OlsClient(object):
    """
    TODO: add individuals and properties services
    OLS Client ontologies client

    """
    uri = "ols/api"

    document = None

    @property
    def url(self):
        return site + '/' + self.uri

    def __init__(self) -> None:
        self.client = Client(decoders=decoders)
        document = self.client.get(site)
        self.ontologies = ListClientMixin('ontologies', helpers.Ontology, document)
        self.ontology = DetailClientMixin('ontologies', helpers.Ontology)
        self.terms = ListClientMixin('terms', helpers.Term, document)
        self.term = DetailClientMixin('terms', helpers.Term)
        self.individuals = ListClientMixin('individuals', helpers.Individual, document)
        self.properties = ListClientMixin('properties', helpers.Property, document)

    def ontology(self, ontology_id) -> helpers.Ontology:
        """
        Short cut method to load an return a single Ontology document via a OntologyClient.details
        :param: ontology_id the ontology unique id

        """
        return self.ontologies.details(ontology_id)

    def term(self, ontology, iri):
        return self.terms.details(ontology, iri)

    def search(self, query, filters=None, rows=20, start=0) -> lists.SearchTermsList or coreapi.exceptions.ErrorMessage:
        # TODO take care of when search will be listed as method in base_uri
        """
        Search term with query string
        Currently doesn't support filters on ChildrenOf and allChildrenOf
        Warning: not fully tested

        :param query:
        :param filters:
        :param rows:
        :param start:
        :return:
        """

        if filters is None:
            filters = {}
        try:
            assert set(filters.keys()).issubset(
                {'ontology', 'type', 'slim', 'queryFields', 'exact', 'fieldList', 'groupField', 'obsoletes',
                 'local'}) or len(filters) == 0, "Unauthorized filter key"
        except AssertionError as e:
            raise exceptions.BadParameter(
                helpers.Error(error="Bad Parameter", message="Unexpected parameter name {}".format(e),
                              status=400, path='search', timestamp=time.time()))
        try:
            if 'fieldList' in filters:
                param = 'fieldList'
                assert (set(filters['fieldList'].keys().issubset(
                    {'iri', 'ontology_name', 'ontology_prefix', 'short_form', 'description', 'id', 'label',
                     'is_defining_ontology', 'obo_id', 'type'}
                )))
            if 'queryFields' in filters:
                param = 'queryFields'
                assert (set(filters['queryFields'].keys().issubset(
                    {'label', 'synonym', 'description', 'short_form', 'obo_id', 'annotations', 'logical_description',
                     'iri'}
                )))
            if 'type' in filters:
                param = 'type'
                assert (set(filters['queryFields'].keys().issubset(
                    {'class', 'property', 'individual', 'ontology'}
                )))
            if 'exact' in filters:
                param = 'exact'
                assert (filters['exact'] in ['true', 'false'])
            if 'groupFields' in filters:
                param = 'groupFields'
                assert (filters['groupFields'] in ['true', 'false'])
            if 'obsoletes' in filters:
                param = 'obsoletes'
                assert (filters['obsoletes'] in ['true', 'false'])
            if 'local' in filters:
                param = 'local'
                assert (filters['local'] in ['true', 'false'])

        except AssertionError as e:
            raise exceptions.BadParameter(
                helpers.Error(error="Bad Parameter", message="Unexpected value {} for param {}".format(e, param),
                              status=400, path='search', timestamp=time.time()))
        uri = '/'.join([site, self.uri, 'search'])
        uri += '?q=' + query
        filters_uri = ''
        for filter_name, filter_value in filters.items():
            filters_uri += '&' + filter_name + '=' + urllib.parse.quote_plus(filter_value)
        if 'ontology' in filters.keys():
            uri = "q={}&exact=on&" + filters_uri + "&ontology={}".format(query, filters.get('ontology'))
        uri += '&rows={}&start={}'.format(rows, start)
        terms = self.client.get(uri, format='json')
        if 'response' in terms and 'docs' in terms.get('response'):
            # only return ontologies if some exists
            return lists.SearchTermsList(self, terms, query, filters, rows, start)
        else:
            # else return a error
            raise exceptions.BadParameter(
                helpers.Error(error="Bad Parameter", message="No corresponding terms for request",
                              status=400, path='search', timestamp=time.time()))


if __name__ == "__main__":
    # TODO add arg parse and associated method calls
    print('Coming soon')
