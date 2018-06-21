# -*- coding: utf-8 -*-

from collections import namedtuple, OrderedDict
from coreapi.document import Object
import warnings

class BaseDto(object):

    def __init__(self, **kwargs) -> None:
        super().__init__()
        for name, value in kwargs.items():
            self.__setattr__(name, value)


class OntoAnnotation(BaseDto):
    license = None
    creator = None
    rights = None
    format_version = None
    comment = None
    default_namespac = None


class Config(BaseDto):
    id = None
    versionIri = None
    title = None
    namespace = None
    preferredPrefix = None
    description = None
    homepage = None
    version = None
    mailingList = None
    creators = None
    annotations = None
    fileLocation = None
    reasonerType = None
    oboSlims = None
    labelProperty = None
    definitionProperties = None
    synonymProperties = None
    hierarchicalProperties = None
    baseUris = None
    hiddenProperties = None
    internalMetadataProperties = None
    skos = None


class Ontology(BaseDto):
    ontologyId = None
    loaded = None
    updated = None
    status = None
    message = None
    version = None
    numberOfTerms = None
    numberOfProperties = None
    numberOfIndividuals = None
    config = None


class OntologyLink(BaseDto):
    self = None
    terms = None
    properties = None
    individual = None


class OboXref(BaseDto):
    database = None
    id = None
    description = None
    ur = None


class OboCitation(BaseDto):
    definition = None
    oboXref = None


class TermAnnotation(BaseDto):
    database_cross_reference = None
    has_obo_namespace = None
    i = None


class TermsLink(BaseDto):
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


class Term(BaseDto):
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


Subset = namedtuple("Subset", ["terms"])

Error = namedtuple("Error", ["error", "message", "status", "path", "timestamp"])
# TODO add all required DTO objects to trasnfer


def _convert_keys(data) -> OrderedDict:
    """
    Convert Json like keyx into Python-like keys
    :param data: a OrderedDict or None
    :return: OrderedDict
    """
    if data is None:
        return OrderedDict({})
    return OrderedDict(
        {k.replace("-", "_"): _convert_keys(v) if isinstance(v, dict) or isinstance(v, Object) else v
         for k, v in data.items()})


def load_data(cls, data):
    """
    Load data into related class (assuming it's one of the namedtuple for ontologies, and no inner tuple to load)
    :param cls: the destination namedtuple
    :param data: the initial OrderedDIct
    :return: namedtuple
    """
    return cls(**data)


def load_ontology_config(data) -> Config:
    """
    Load Config object
:param data: an OrderedDict received
:return: Config namedtuple
    """
    onto_annotations = OntoAnnotation(**data.pop("annotations", None))
    return Config(**data, annotations=onto_annotations)


def load_ontology(data) -> Ontology:
    """
    Load an Ontology object
:param data: an Document received
:return: Ontology namedtuple
    """
    converted = _convert_keys(data)
    config = converted.pop("config", None)
    onto_config = load_ontology_config(config)
    ontology = Ontology(**converted, config=onto_config)
    return ontology


def load_ontologies_list(data) -> [Ontology] or Error:
    """
    From received Document with list of ontologies Document return a list of Ontology objects
    :param data: Document
    :return: [Ontology] or Error
    """
    if 'ontologies' not in data:
        return Error("No Ontologies", "No ontology provided", 500, None, None)
    else:
        return [load_ontology(onto) for onto in data['ontologies']]
