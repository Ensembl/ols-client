# -*- coding: utf-8 -*-
import time
import urllib.parse
import warnings

import coreapi.exceptions
from coreapi import Client, codecs

import ebi.ols.api.exceptions as exceptions
import ebi.ols.api.utils as utils
from ebi.ols.api.codec import HALCodec
import ebi.ols.api.helpers as helpers
import ebi.ols.api.lists as lists


class OntologiesClient(object):
    urn = "/ols/api/ontologies"
    document = None

    @property
    def uri(self):
        return self.parent.site + self.urn

    def __init__(self, parent) -> None:
        self.parent = parent
        self.document = parent.document

    def list(self, page=None, size=None) -> [helpers.Ontology] or exceptions.BadParameter:
        params = {'page': page if page else '', 'size': size if size else 20}
        document = self.parent.client.action(self.document, ['ontologies'], params=params, validate=False)

        if 'ontologies' in document.data:
            # only return ontologies if some exists
            return lists.OntologyList(self.parent, document)
        else:
            # else return a error
            raise exceptions.BadParameter(
                helpers.Error(error="Bad Parameter", message="No corresponding ontologies for request",
                              status=400, path='ontologies', timestamp=time.time()))

    def details(self, ontology_id):
        try:
            document = self.parent.client.get('/'.join([self.uri, ontology_id]))
            return utils.load_ontology(document)
        except coreapi.exceptions.CoreAPIException as e:
            raise exceptions.OlsException(e)

    def terms(self, ontology_id):
        try:
            document = self.parent.client.get('/'.join([self.uri, ontology_id, 'terms']))
            return lists.TermList(self.parent, document)
        except coreapi.exceptions.CoreAPIException as e:
            raise exceptions.OlsException(e)


class IndividualsClient(object):
    def __init__(self, document) -> None:
        super().__init__()
        self.document = document


class PropertiesClient(object):
    def __init__(self, document) -> None:
        super().__init__()
        self.document = document


class TermsClient(object):
    urn = "/ols/api/terms"

    def uri(self, ontology=None):
        if ontology:
            return '/'.join([OlsClient.site, OntologiesClient.urn, ontology])
        return OlsClient.site + self.urn

    def __init__(self, client) -> None:
        self.client = client.client
        self.document = client.document
        self.current_term_doc = None

    @staticmethod
    def term_uri(iri):
        return urllib.parse.quote_plus(urllib.parse.quote_plus(iri))

    def list(self, ontology=None, page=None, size=None, filters=None) -> lists.TermList:
        """
        Get ontologies terms, if no filter set, return a first page of terms
        TODO more testing about terms filtering parameters currently available in API
        :param ontology: ontology unique short code
        :param size: size of excpeted list, default 20
        :param page: the requested page number
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
        # reset current item if any
        if filters is None:
            filters = {}
        params = {'page': page if page else '', 'size': size if size else 20}
        if ontology:
            if isinstance(ontology, helpers.Ontology):
                path = self.uri(ontology.ontologyId)
            else:
                path = self.uri(ontology)
            self.document = self.client.get(path)
        else:
            warnings.warn('You should not consider calling terms without ontology filter, request may be slow')
            if params.get('size') < 200:
                params['size'] = 200
            path = self.uri()
            # document = self.document
        try:
            assert set(filters.keys()).issubset({'iri', 'obo_id', 'short_form'}), "Unauthorized filter key"
            assert len(filters.keys()) <= 1, "Only one filter can be applied at a time"
            params.update(filters)
        except AssertionError as e:
            raise exceptions.BadParameter(helpers.Error(error="Bad Request", message=str(e), status=400,
                                                        path=path, timestamp=time.time()))
        terms = self.client.action(self.document, ['terms'], params=params, validate=False)

        if 'terms' in terms.data:
            # only return ontologies if some exists
            return lists.TermList(self, terms)
        else:
            # else return a error
            raise exceptions.BadParameter(
                helpers.Error(error="Bad Parameter", message="No corresponding terms for request",
                              status=400, path='terms', timestamp=time.time()))

    def details(self, ontology, iri):
        base_url = '/'.join([self.uri(ontology), 'terms', self.term_uri(iri)])
        document = self.client.get(base_url)
        return utils.load_term(document)

    def _load_relation(self, term, relation):
        terms = self.client.get('/'.join([self.uri(term.ontology_name), 'terms', self.term_uri(term.iri), relation]))
        if 'terms' in terms.data:
            # only return ontologies if some exists
            return lists.TermList(self, terms)
        else:
            # else return a error
            raise exceptions.BadParameter(
                helpers.Error(error="Bad Parameter", message="No corresponding {} for {}".format(relation, term.label),
                              status=400, path='terms', timestamp=time.time()))

    def ancestors(self, term):
        return self._load_relation(term, 'ancestors')

    def parents(self, term):
        return self._load_relation(term, 'parents')

    def hierarchical_parents(self, term):
        return self._load_relation(term, 'hierarchicalParents')

    def hierarchical_ancestors(self, term):
        return self._load_relation(term, 'hierarchicalAncestors')

    def hierarchical_children(self, term):
        return self._load_relation(term, 'hierarchicalChildren')

    def hierarchical_descendants(self, term):
        return self._load_relation(term, 'hierarchicalDescendants')

    def graphs(self, term):
        return self._load_relation(term, 'graphs')

    def jstree(self, term):
        return self._load_relation(term, 'jstree')


class OlsClient(object):
    """
    TODO: add individuals and properties services
    OLS Client ontologies client

    """
    site = 'https://www.ebi.ac.uk'
    uri = "ols/api"
    decoders = [HALCodec(), codecs.JSONCodec()]
    document = None

    @property
    def url(self):
        return self.site + '/' + self.uri

    def __init__(self, site=None) -> None:
        self.client = Client(decoders=self.decoders)
        if site:
            self.site = site
        self.document = self.client.get(self.url)
        self.ontologies = OntologiesClient(self)
        self.terms = TermsClient(self)
        self.individuals = IndividualsClient(self)
        self.properties = PropertiesClient(self)

    def ontology(self, ontology_id) -> helpers.Ontology:
        """
        Short cut method to load an return a single Ontology document via a OntologyClient.details
        :param: ontology_id the ontology unique id

        """
        return self.ontologies.details(ontology_id)

    def term(self, ontology, iri):
        return self.terms.details(ontology, iri)

    def search(self, query, filters=None, rows=20, start=0) -> lists.TermList or coreapi.exceptions.ErrorMessage:
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
        uri = '/'.join([self.site, self.uri, 'search'])
        uri += '?q=' + query
        filters_uri = ''
        for filter_name, filter_value in filters.items():
            filters_uri += '&' + filter_name + '=' + urllib.parse.quote_plus(filter_value)
        if 'ontology' in filters.keys():
            uri = "q={}&exact=on&" + filters_uri + "&ontology={}".format(query, filters.get('ontology'))
        uri += '&rows={}&start={}'.format(rows, start)
        print('search uri ', uri)
        terms = self.client.get(uri, format='json')
        print(terms)
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
