# -*- coding: utf-8 -*-
import time
from collections.__init__ import OrderedDict

from coreapi import Document, Object

from ebi.ols.api.helpers import Config, OntoAnnotation, Ontology, Error, Term
from ols.api.exceptions import BadParameter
from ols.api.helpers import Error

__all__ = ['load_ontologies', 'load_ontology']


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


def load_ontologies(ontologies) -> [Ontology] or Error:
    """
    From received Document with list of ontologies Document return a list of Ontology objects
    :param ontologies: Document
    :return: [Ontology] or Error
    """
    if 'ontologies' not in ontologies:
        return Error("No Ontologies", "No ontology provided", 400, None, None)
    else:
        return [load_ontology(onto) for onto in ontologies['ontologies']]


def load_term(term_doc) -> Term or Error:
    return load_data(Term, term_doc)


def load_terms(terms) -> [Term] or Error:
    if 'terms' not in terms:
        return Error("No Term", "No term provided", 400, None, None)
    else:
        return [load_term(term) for term in terms['terms']]
    pass


class ListMixin(object):
    client = None
    current = None

    def __init__(self, client, current) -> None:
        super().__init__()
        self.client = client
        self.current = current

    def next(self) -> Document or Error:
        if self.has_next:
            self.current = self.client.action(self.current, ['next'])
            return self._load_objects(self.current)
        raise BadParameter(Error(error="Bad Request", message="No next item", status=400,
                                 path=None, timestamp=time.time()))

    def prev(self) -> Document:
        if self.has_prev:
            return self.client.action(self.current, ['prev'])
        raise BadParameter(Error(error="Bad Request", message="No next item", status=400,
                                 path=None, timestamp=time.time()))

    def last(self) -> Document:
        if self.has_last:
            return self.client.action(self.current, ['last'])
        raise BadParameter(Error(error="Bad Request", message="No next item", status=400,
                                 path=None, timestamp=time.time()))

    def first(self) -> Document:
        if self.has_first:
            return self.client.action(self.current, ['first'])
        raise BadParameter(error="Bad Request", message="No first item", status=400,
                           path='ontologies', timestamp=time.time())

    @property
    def has_next(self) -> bool:
        return 'next' in self.current.links

    @property
    def has_first(self) -> bool:
        return 'first' in self.current.links

    @property
    def has_last(self) -> bool:
        return 'last' in self.current.links

    @property
    def has_prev(self) -> bool:
        return 'prev' in self.current.links

    @property
    def total_pages(self) -> int:
        return self.current.data['page']['totalPages']

    @property
    def size(self) -> int:
        return self.current.data['page']['size']

    @property
    def __len__(self):
        return self.current.data['page']['totalElements']

    def _load_objects(self, document: Document):
        raise NotImplementedError()

    def _load_object(self, document):
        raise NotImplementedError()


class OntologyList(ListMixin):

    def _load_objects(self, document: Document):
        return load_ontologies(document.data)

    def _load_object(self, document):
        return load_ontology(document)
