# -*- coding: utf-8 -*-
"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""
import re
from collections import namedtuple, OrderedDict

import inflection
from coreapi import Object

from ebi.ols.api.base import *


def underscore(value):
    val = inflection.underscore(value)
    return re.sub('\s+', '_', val)


def convert_keys(data):
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


def to_python_value(value):
    type_value = type(value)
    if type_value is bool:
        return value
    elif type_value is 'str':
        if value in ('true', 'True', '1'):
            return True
        elif value in ('0', 'false', 'False'):
            return False
    return value


class OLSHelper(object):
    """
    Base Transfer object, mainly assign dynamically received dict keys to object attributes
    """

    def __init__(self, **kwargs):
        converted = convert_keys(kwargs)
        for name, value in converted.items():
            # print(name, value, to_python_value(value))
            self.__setattr__(name, to_python_value(value))

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

    def __init__(self, **kwargs):
        annotations = OntologyAnnotation(**kwargs.pop("annotations", {}))
        super().__init__(annotations=annotations, **kwargs)

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
    _version = None
    number_of_terms = None
    number_of_properties = None
    number_of_individuals = None
    config = None
    annotations = {}

    def __init__(self, **kwargs):
        config = OntologyConfig(**kwargs.pop("config", {}))
        super().__init__(config=config, **kwargs)

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

    @property
    def namespace(self):
        return self.config.namespace

    @property
    def title(self):
        return self.config.title

    @property
    def version(self):
        return self._version if self._version else self.config.version

    @version.setter
    def version(self, version):
        self._version = version

    @namespace.setter
    def namespace(self, namespace):
        if self.config.annotations.default_namespace:
            self.config.annotations.default_namespace[0] = namespace
        else:
            self.config.namespace = namespace


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
    has_obo_namespace = []
    has_alternative_id = []
    id = []
    alternative_term = []
    definition_source = []
    editor_preferred_term = []
    example_of_usage = []
    term_editor = []
    term_tracker_item = []

    def __repr__(self):
        return '<Term(id={}, has_obo_name_space={}, alternative_term={}, alt_id={})>'.format(
            self.id, self.has_obo_namespace, self.alternative_term, self.has_alternative_id)


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
    _description = []
    annotation = None
    synonyms = None
    ontology_name = None
    ontology_prefix = None
    ontology_iri = None
    is_obsolete = False
    term_replaced_by = None
    is_defining_ontology = False
    has_children = False
    is_root = False
    short_form = None
    obo_id = None
    in_subset = None
    obo_definition_citation = None
    obo_xref = None
    obo_synonym = None

    def __init__(self, **kwargs):
        annotation = TermAnnotation(**kwargs.pop("annotation", {}))
        super().__init__(annotation=annotation, **kwargs)
        self._relations_types = None

    def __repr__(self):
        return '<Term(obo_id={}, name={}, ontology_id={}, namespace={} subsets={}, short_form={})>'.format(
            self.obo_id, self.label, self.ontology_name, self.obo_name_space, self.in_subset, self.short_form)

    @property
    def relations_types(self):
        if self._relations_types is None:
            client = ListClientMixin('ontologies/' + self.ontology_name + '/terms/' + uri_terms(self.iri), Term)
            self._relations_types = [name for name in client.document.links.keys() if name not in ('graph', 'jstree')]
        return self._relations_types

    def load_relation(self, relation):
        client = ListClientMixin('ontologies/' + self.ontology_name + '/terms/' + uri_terms(self.iri), Term)
        return client(action=relation)

    def children(self):
        return self.load_relation('children') if self.has_children else []

    def descendants(self):
        return self.load_relation('descendants')

    def ancestors(self):
        return self.load_relation('ancestors')

    def parents(self):
        return self.load_relation('parents')

    def hierarchical_parents(self):
        return self.load_relation('hierarchicalParents')

    def hierarchical_ancestors(self):
        return self.load_relation('hierarchicalAncestors')

    def hierarchical_children(self):
        return self.load_relation('hierarchicalChildren')

    def hierarchical_descendants(self):
        return self.load_relation('hierarchicalDescendants')

    def graph(self):
        return self.load_relation('graph')

    def jstree(self):
        return self.load_relation('jstree')

    @property
    def obo_name_space(self):
        # print(self.annotation)
        if self.annotation.has_obo_namespace:
            return self.annotation.has_obo_namespace[0]
        else:
            return self.ontology_name

    @property
    def description(self):
        return self._description[0] if len(self._description) > 0 else ''

    @description.setter
    def description(self, value):
        if value is None:
            value = [self.label]
        self._description = value

    @property
    def subsets(self):
        return ','.join(
            [subset for subset in sorted(self.in_subset, key=lambda s: s.lower())]) if self.in_subset else ''

    @property
    def accession(self):
        return self.obo_id

    @property
    def name(self):
        return self.label


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
            self.label, self.iri, self.ontology_name, self.short_form, self.obo_id)

    @property
    def definition(self):
        return self.description