# -*- coding: utf-8 -*-

from collections import namedtuple


class OlsDto(object):
    """
    Base Transfer object, mainly assign dynamically received dict keys to object attributes
    """
    api_client = None

    def __init__(self, **kwargs) -> None:
        super().__init__()
        for name, value in kwargs.items():
            self.__setattr__(name, value)

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


class Ontology(OlsDto):
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
