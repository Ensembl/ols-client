# -*- coding: utf-8 -*-

from collections import namedtuple, OrderedDict

import inflection
from coreapi import Object, Link

from ebi.ols.api.base import *


def convert_keys(data) -> OrderedDict:
    """
    Convert Json like keyx into Python-like keys
    :param data: a OrderedDict or None
    :return: OrderedDict
    """
    if data is None:
        return OrderedDict({})
    return OrderedDict(
        {inflection.underscore(k): convert_keys(v) if isinstance(v, dict) or isinstance(v, Object) else v for k, v in
         data.items()})


class OlsDto(object):
    """
    Base Transfer object, mainly assign dynamically received dict keys to object attributes
    """
    path = None

    def __init__(self, data, **kwargs) -> None:
        super().__init__()
        for name, value in kwargs.items():
            self.__setattr__(name, value)
        for name, value in data.items():
            self.__setattr__(name, value) if type(value) is not Link else None

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class OntoAnnotation(OlsDto):
    license = None
    creator = None
    rights = None
    format_version = None
    comment = None
    default_namespace = None


class Config(OlsDto):
    id = None
    version_iri = None
    title = None
    namespace = None
    preferred_prefix = None
    description = None
    homepage = None
    version = None
    mailing_list = None
    creators = None
    annotations = None
    fileLocation = None
    reasoner_type = None
    obo_slims = None
    label_property = None
    definition_properties = None
    synonym_properties = None
    hierarchical_properties = None
    base_uris = None
    hidden_properties = None
    internal_metadata_properties = None
    skos = None

    def __init__(self, data) -> None:
        onto_annotations = OntoAnnotation(data.pop("annotations", None))
        super().__init__(data, annotations=onto_annotations)


class Ontology(OlsDto):
    path = 'ontologies'
    ontology_id = None
    loaded = None
    updated = None
    status = None
    message = None
    version = None
    number_of_terms = None
    number_of_properties = None
    number_of_individuals = None
    config = None

    def __init__(self, data) -> None:
        converted = convert_keys(data)
        config = converted.pop("config", None)
        onto_config = Config(data=config)
        super().__init__(data=converted, config=onto_config)

    def __repr__(self):
        return '<Ontology(ontology_id={}, name={}, namespace={}, data_version={})>'.format(
            self.ontology_id, self.config.title, self.config.namespace, self.version)

    def terms(self, filters=None):
        client = ListClientMixin('ontologies/' + self.ontology_id, Term)
        return client(filters=filters)

    def individuals(self, filters=None):
        client = ListClientMixin('ontologies/' + self.ontology_id, Individual)
        return client(filters=filters)

    def properties(self, filters=None):
        client = ListClientMixin('ontologies/' + self.ontology_id, Property)
        return client(filters=filters)


class OntologyLink(OlsDto):
    self = None
    terms = None
    properties = None
    individual = None


class OboXref(OlsDto):
    database = None
    id = None
    description = None
    ur = None


class OboCitation(OlsDto):
    definition = None
    oboXref = None


class TermAnnotation(OlsDto):
    database_cross_reference = None
    has_obo_namespace = None
    id = None


class TermsLink(OlsDto):
    parents = None
    ancestors = None
    hierarchicalParents = None
    hierarchicalAncestors = None
    jstree = None
    children = None
    descendants = None
    hierarchicalChildren = None
    hierarchicalDescendants = None
    graph = None


class Term(OlsDto):
    path = 'terms'
    iri = None
    label = None
    description = None
    OntoAnnotation = None
    synonyms = None
    ontology_name = None
    ontology_prefix = None
    ontology_iri = None
    is_obsolete = None
    term_replaced_by = None
    is_defining_ontology = None
    has_children = None
    is_root = None
    short_form = None
    obo_id = None
    in_subset = None
    obo_definition_citation = None
    obo_xref = None
    obo_synonym = None

    def __repr__(self):
        return '<Term(term_id={}, name={}, ontology_id={}, subsets={}, short_form={})>'.format(
            self.obo_id, self.label, self.ontology_name, self.in_subset, self.short_form)

    def _load_relation(self, term, relation):
        terms = self.client.get('/'.join([self.uri(term.ontology_name), 'terms', self.term_uri(term.iri), relation]))
        if 'terms' in terms.data:
            # only return ontologies if some exists
            return []
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


Subset = namedtuple("Subset", ["terms"])

Error = namedtuple("Error", ["error", "message", "status", "path", "timestamp"])


class Individual(OlsDto):
    path = 'individuals'
    iri = None
    label = None
    description = []
    synonyms = None
    ontology_name = None
    ontology_prefix = None
    ontology_iri = None
    is_obsoloete = None
    is_defining_ontology = None
    short_form = None
    obo_id = None

    def __repr__(self):
        return '<Individual(label={}, iri={}, ontology_name={}, short_form={}, obo_id={})>'.format(
            self.label, self.ontology_name, self.iri, self.short_form, self.obo_id)


class Property(OlsDto):
    path = 'properties'
    annotation = None
    synonyms = None
    iri = None
    label = None
    description = None
    ontology_name = None
    ontology_prefix = None
    ontology_iri = None
    is_obsolete = None
    is_defining_ontology = None
    has_children = None
    is_root = None
    short_form = None
    obo_id = None

    def __repr__(self):
        return '<Property(label={}, iri={}, ontology_name={}, short_form={}, obo_id={})>'.format(
            self.label, self.ontology_name, self.iri, self.short_form, self.obo_id)
