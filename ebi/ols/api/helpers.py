# -*- coding: utf-8 -*-

import re
from collections import namedtuple, OrderedDict

import inflection
from coreapi import Object

from ebi.ols.api.base import *


def underscore(value):
    val = inflection.underscore(value)
    return re.sub('\s+', '_', val)


def convert_keys(data) -> OrderedDict:
    """
    Convert Json like keyx into Python-like keys
    :param data: a OrderedDict or None
    :return: OrderedDict
    """
    if data is None:
        return OrderedDict({})
    return OrderedDict(
        {underscore(k): convert_keys(v) if isinstance(v, dict) or isinstance(v, Object) else v for k, v in
         data.items()})


class OLSHelper(object):
    """
    Base Transfer object, mainly assign dynamically received dict keys to object attributes
    """

    def __init__(self, **kwargs) -> None:
        converted = convert_keys(kwargs)
        for name, value in converted.items():
            self.__setattr__(name, value)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class OntologyAnnotation(OLSHelper):
    """
    An ontology annotation item.
    """
    license = None
    creator = []
    rights = []
    format_version = None
    comment = []
    default_namespace = None
    contributor = []


class OntologyConfig(OLSHelper):
    id = None
    version_iri = None
    title = None
    namespace = None
    preferred_prefix = None
    description = None
    homepage = None
    version = None
    mailing_list = None
    creators = []
    annotations = {}
    file_location = None
    reasoner_type = None
    obo_slims = None
    label_property = None
    definition_properties = []
    synonym_properties = []
    hierarchical_properties = []
    base_uris = []
    hidden_properties = []
    internal_metadata_properties = []
    skos = None

    def __init__(self, **kwargs) -> None:
        annotations = OntologyAnnotation(**kwargs.pop("annotations", {}))
        super().__init__(**kwargs, annotations=annotations)

    def __repr__(self):
        return '<OntologyConfig(id={}, iri={}, namespace={}, title={}, version={})>'.format(
            self.id, self.version_iri, self.namespace, self.title, self.version)


class Ontology(OLSHelper):
    """
    An Ontology element from EBI Ontology lookup service
    """
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
    annotations = {}

    def __init__(self, **kwargs) -> None:
        config = OntologyConfig(**kwargs.pop("config", {}))
        super().__init__(**kwargs, config=config)

    def __repr__(self):
        return '<Ontology(ontology_id={}, title={}, namespace={}, updated={})>'.format(
            self.ontology_id, self.config.title, self.config.namespace, self.updated)

    def terms(self, filters=None):
        """ Links to ontology associated terms"""
        client = ListClientMixin('ontologies/' + self.ontology_id, Term)
        return client(filters=filters)

    def individuals(self, filters=None):
        """ Links to ontology associated individuals """
        client = ListClientMixin('ontologies/' + self.ontology_id, Individual)
        return client(filters=filters)

    def properties(self, filters=None):
        """ Links to ontology associated properties"""
        client = ListClientMixin('ontologies/' + self.ontology_id, Property)
        return client(filters=filters)


class OboXref(OLSHelper):
    database = None
    id = None
    description = None
    ur = None


class OboCitation(OLSHelper):
    definition = None
    oboXref = None


class TermAnnotation(OLSHelper):
    database_cross_reference = None
    has_obo_namespace = None
    id = None
    alternative_term = []
    definition_source = []
    editor_preferred_term = []
    example_of_usage = []
    term_editor = []
    term_tracker_item = []


class TermsLink(OLSHelper):
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


class Term(OLSHelper):
    path = 'terms'
    iri = None
    label = None
    description = None
    annotation = None
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

    def __init__(self, **kwargs) -> None:
        annotation = TermAnnotation(**kwargs.pop("annotation", {}))
        super().__init__(**kwargs, annotation=annotation)

    def __repr__(self):
        return '<Term(obo_id={}, name={}, ontology_id={}, subsets={}, short_form={})>'.format(
            self.obo_id, self.label, self.ontology_name, self.in_subset, self.short_form)

    def _load_relation(self, relation):
        client = ListClientMixin('ontologies/' + self.ontology_name + '/terms/' + uri_terms(self.iri),
                                 Term)
        return client(action=relation)

    def ancestors(self):
        return self._load_relation('ancestors')

    def parents(self):
        return self._load_relation('parents')

    def hierarchical_parents(self):
        return self._load_relation('hierarchicalParents')

    def hierarchical_ancestors(self):
        return self._load_relation('hierarchicalAncestors')

    def hierarchical_children(self):
        return self._load_relation('hierarchicalChildren')

    def hierarchical_descendants(self):
        return self._load_relation('hierarchicalDescendants')

    def graphs(self):
        return self._load_relation('graphs')

    def jstree(self):
        return self._load_relation('jstree')


Subset = namedtuple("Subset", ["terms"])


class Individual(OLSHelper):
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


class Property(OLSHelper):
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
