# -*- coding: utf-8 -*-
from collections.__init__ import OrderedDict

from coreapi import Object

from ebi.ols.api.helpers import Config, OntoAnnotation, Ontology, Term
from ols.api.helpers import Error

__all__ = ['load_data', 'load_ontology']


def convert_keys(data) -> OrderedDict:
    """
    Convert Json like keyx into Python-like keys
    :param data: a OrderedDict or None
    :return: OrderedDict
    """
    if data is None:
        return OrderedDict({})
    return OrderedDict(
        {k.replace("-", "_"): convert_keys(v) if isinstance(v, dict) or isinstance(v, Object) else v
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
    converted = convert_keys(data)
    config = converted.pop("config", None)
    onto_config = load_ontology_config(config)
    ontology = Ontology(**converted, config=onto_config)
    return ontology


def load_term(term_doc) -> Term or Error:
    return load_data(Term, term_doc)
