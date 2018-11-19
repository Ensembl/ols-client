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
import logging
import re
from collections import namedtuple, OrderedDict

import inflection
from coreapi import Object

from ebi.ols.api.base import ListClientMixin, site

logger = logging.getLogger(__name__)


def underscore(value):
    val = inflection.underscore(value)
    return re.sub('\s+', '_', val)


def convert_keys(data):
    """
    Convert Json like keys into Python-like keys
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


class HasAccessionMixin(object):
    short_form = None
    obo_id = None
    is_obsolete = False
    is_defining_ontology = False
    iri = None

    _accession = None

    @property
    def accession_old(self):
        """
        Return term accession issued from related retrieved data, try to figure out related obo_id if value not
        set in OLS
        :return: str
        """
        if not self.obo_id and self.short_form:
            log = logging.getLogger('ols_errors')
            log.error('[NO_OBO_ID][%s][%s]', self.short_form, self.iri)
            # guess
            sp = self.short_form.split('_')
            if len(sp) == 2:
                self.obo_id = ':'.join(sp)
                return self.obo_id
            else:
                # no '_' character in short_form might ignore the error (may be #Thing)
                logger.warning('Unable to parse %s', self.short_form) if len(sp) == 1 else None
                return False
        return self.obo_id

    @property
    def accession(self):
        if self._accession:
            return self._accession
        if not self.obo_id:
            logger.error('[NO_OBO_ID][%s][%s]', self.short_form, self.iri)
            to_parse = self.short_form or self.iri.rsplit('/', 1)[-1]
            # guess
            sp = to_parse.split('_')
            if len(sp) >= 2:
                left = '_'.join(sp[:-1])
                right = sp[len(sp) - 1]
                accession = ':'.join([left, right])
                logger.debug('Accession sorted out %s', accession)
                self._accession = accession
                return accession
            else:
                # no '_' character in short_form might ignore the error (may be #Thing)
                logger.warning('Unable to parse %s', self.short_form) if len(sp) == 1 else None
                return None
        return self.obo_id

    @accession.setter
    def accession(self, accession):
        self._accession = accession


class OLSHelper(object):
    """
    Base Transfer object, mainly assign dynamically received dict keys to object attributes
    """

    def __init__(self, **kwargs):
        converted = convert_keys(kwargs)
        [self.__setattr__(name, to_python_value(value)) for name, value in converted.items()]

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
        client = ListClientMixin('/'.join([site, 'ontologies/' + self.ontology_id]), Term)
        return client(filters=filters)

    def individuals(self, filters=None):
        """ Links to ontology associated individuals """
        client = ListClientMixin('/'.join([site, 'ontologies/' + self.ontology_id]), Individual)
        return client(filters=filters)

    def properties(self, filters=None):
        """ Links to ontology associated properties"""
        client = ListClientMixin('/'.join([site, 'ontologies/' + self.ontology_id]), Property)
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


class Term(OLSHelper, HasAccessionMixin):
    path = 'terms'

    label = None
    _description = []
    annotation = None
    synonyms = None
    ontology_name = None
    ontology_prefix = None
    ontology_iri = None
    term_replaced_by = None
    has_children = False
    is_root = False
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
            client = ListClientMixin(
                site + '/ontologies/' + self.ontology_name + '/terms/' + ListClientMixin.make_uri(self.iri), Term)
            self._relations_types = [name for name in client.document.links.keys() if name not in ('graph', 'jstree')]
        return self._relations_types

    def load_relation(self, relation):
        client = ListClientMixin(site + '/ontologies/' + self.ontology_name + '/terms/' + ListClientMixin.make_uri(self.iri),
                                 Term)
        return client(action=relation)

    def graph(self):
        raise NotImplementedError('This link process is not implemented yet')

    def jstree(self):
        raise NotImplementedError('This link process is not implemented yet')

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
        """ Returned coma separated list of term subsets """
        return ','.join(
            [subset for subset in sorted(self.in_subset, key=lambda s: s.lower())]) if self.in_subset else ''

    @property
    def name(self):
        return self.label


Subset = namedtuple("Subset", ["terms"])


class Individual(OLSHelper, HasAccessionMixin):
    path = 'individuals'
    label = None
    description = []
    synonyms = None
    ontology_name = None
    ontology_prefix = None
    ontology_iri = None

    def __repr__(self):
        return '<Individual(label={}, iri={}, ontology_name={}, short_form={}, accession={})>'.format(
            self.label, self.ontology_name, self.iri, self.short_form, self.obo_id)


class Property(OLSHelper, HasAccessionMixin):
    path = 'properties'
    annotation = None
    synonyms = None
    label = None
    description = None
    ontology_name = None
    ontology_prefix = None
    ontology_iri = None
    has_children = None
    is_root = None

    def __repr__(self):
        return '<Property(label={}, iri={}, ontology_name={}, short_form={}, obo_id={})>'.format(
            self.label, self.iri, self.ontology_name, self.short_form, self.obo_id)

    @property
    def definition(self):
        return self.description
