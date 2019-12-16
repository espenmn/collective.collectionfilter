# -*- coding: utf-8 -*-
from collective.collectionfilter.interfaces import IGroupByCriteria
from collective.collectionfilter.utils import safe_decode
from collective.collectionfilter.vocabularies import EMPTY_MARKER
from collective.collectionfilter.vocabularies import GEOLOC_IDX
from collective.collectionfilter.vocabularies import TEXT_IDX
from logging import getLogger
from zope.component import getUtility
import plone.api


logger = getLogger('collective.collectionfilter')
MULTISPACE = u'\u3000'
BAD_CHARS = ('?', '-', '+', '*', MULTISPACE)


def quote_unsafe_chars(s):
    # We need to quote parentheses when searching text indices
    if '(' in s:
        s = s.replace('(', '"("')
    if ')' in s:
        s = s.replace(')', '")"')
    if MULTISPACE in s:
        s = s.replace(MULTISPACE, ' ')
    return s


def quote_keywords(term):
    # The terms and, or and not must be wrapped in quotes to avoid
    # being parsed as logical query atoms.
    if term.lower() in ('and', 'or', 'not'):
        term = '"%s"' % term
    return term


def sanitise_search_query(query):
    for char in BAD_CHARS:
        query = query.replace(char, u" ")
    clean_query = [quote_keywords(token) for token in query.split()]
    clean_query = quote_unsafe_chars(clean_query)
    return u" ".join(clean_query)


def make_query(params_dict):
    """Make a query from a dictionary of parameters, like a request form.
    """
    query_dict = {}
    groupby_criteria = getUtility(IGroupByCriteria).groupby
    for val in groupby_criteria.values():
        idx = val['index']
        if idx in params_dict:
            crit = params_dict.get(idx) or EMPTY_MARKER

            idx_mod = val.get('index_modifier', None)
            crit = idx_mod(crit) if idx_mod else safe_decode(crit)

            # filter operator
            op = params_dict.get(idx + '_op', None)
            if op is None:
                # add filter query
                query_dict[idx] = {'query': crit}
            else:
                if op not in ['and', 'or']:
                    op = 'or'
                # add filter query
                query_dict[idx] = {'operator': op, 'query': crit}

    for idx in GEOLOC_IDX:
        if idx in params_dict:
            # lat/lng query has to be float values
            try:
                query_dict[idx] = dict(
                    query=[
                        float(params_dict[idx]['query'][0]),
                        float(params_dict[idx]['query'][1]),
                    ],
                    range=params_dict[idx]['range'])
            except (ValueError, TypeError):
                logger.warning(
                    "Could not apply lat/lng values to filter: %s",
                    params_dict[idx])

    if TEXT_IDX in params_dict and params_dict.get(TEXT_IDX):
        safe_text = safe_decode(params_dict.get(TEXT_IDX))
        clean_searchable_text = sanitise_search_query(safe_text)
        query_dict[TEXT_IDX] = clean_searchable_text

    # Filter by path if passed in
    if 'path' in params_dict:
        additional_paths = params_dict['path'].split('/')
        query_dict['path'] = {'query': '/'.join(
            list(plone.api.portal.get().getPhysicalPath()) + additional_paths)}

    return query_dict
