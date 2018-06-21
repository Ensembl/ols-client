# -*- coding: utf-8 -*-
from coreapi import Document


def has_next(document: Document) -> bool:
    return 'next' in document.links


def has_first(document: Document) -> bool:
    return 'first' in document.links


def has_last(document: Document) -> bool:
    return 'last' in document.links


def has_prev(document: Document) -> bool:
    return 'prev' in document.links
