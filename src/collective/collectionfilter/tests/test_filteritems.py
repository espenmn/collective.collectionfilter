# -*- coding: utf-8 -*-
"""Setup tests for this package."""
import unittest
from urlparse import urlparse, parse_qs

from plone.app.contenttypes.interfaces import ICollection

from collective.collectionfilter.query import make_query
from collective.collectionfilter.testing import COLLECTIVE_COLLECTIONFILTER_INTEGRATION_TESTING  # noqa
from collective.collectionfilter.filteritems import get_filter_items


def get_data_by_val(result, val):
    for r in result:
        if r['value'] == val:
            return r


class TestFilteritems(unittest.TestCase):

    layer = COLLECTIVE_COLLECTIONFILTER_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.collection = self.portal['testcollection']
        self.collection_uid = self.collection.UID()

    def test_filteritems(self):
        self.assertEqual(len(self.collection.results()), 3)

        result = get_filter_items(
            self.collection_uid, 'Subject', cache_enabled=False)

        self.assertEqual(len(result), 4)
        self.assertEqual(get_data_by_val(result, 'all')['count'], 3)
        self.assertEqual(get_data_by_val(result, 'all')['selected'], True)
        self.assertEqual(get_data_by_val(result, u'Süper')['count'], 2)
        self.assertEqual(get_data_by_val(result, u'Evänt')['count'], 1)
        self.assertEqual(get_data_by_val(result, u'Dokumänt')['count'], 2)

        result = get_filter_items(
            self.collection_uid, 'Subject',
            request_params={'Subject': u'Süper'},
            cache_enabled=False)

        self.assertEqual(len(result), 4)
        self.assertEqual(get_data_by_val(result, u'Süper')['selected'], True)

        result = get_filter_items(
            self.collection_uid, 'Subject',
            request_params={'Subject': u'Dokumänt'},
            cache_enabled=False)

        self.assertEqual(len(result), 4)
        self.assertEqual(
            get_data_by_val(result, u'Dokumänt')['selected'], True)

        # test narrowed down results
        narrowed_down_result = get_filter_items(
            self.collection_uid, 'Subject',
            request_params={'Subject': u'Dokumänt'},
            narrow_down=True,
            show_count=True,
            cache_enabled=False)

        self.assertEqual(
            len(narrowed_down_result), 3,
            msg=u"narrowed result length should be 3")
        self.assertEqual(
            get_data_by_val(narrowed_down_result, u'Dokumänt')['selected'], True,  # noqa
            msg=u"Test that 'Dokumänt' is selected, matching the query")
        self.assertEqual(
            get_data_by_val(narrowed_down_result, u'all')['count'], 3,
            msg=u"Test that there are 3 results if unselected")

    def test_portal_type_filter(self):
        self.assertEqual(len(self.collection.results()), 3)

        result = get_filter_items(
            self.collection_uid, 'portal_type', cache_enabled=False)

        self.assertEqual(len(result), 3)
        self.assertEqual(get_data_by_val(result, 'all')['count'], 3)
        self.assertEqual(get_data_by_val(result, 'all')['selected'], True)
        self.assertEqual(get_data_by_val(result, u'Event')['count'], 1)
        self.assertEqual(get_data_by_val(result, u'Document')['count'], 2)

        result = get_filter_items(
            self.collection_uid, 'portal_type',
            request_params={'portal_type': u'Event'},
            cache_enabled=False)

        self.assertEqual(len(result), 3)
        self.assertEqual(get_data_by_val(result, u'Event')['selected'], True)

        # test narrowed down results
        result = get_filter_items(
            self.collection_uid, 'portal_type',
            request_params={'portal_type': u'Event'},
            narrow_down=True,
            show_count=True,
            cache_enabled=False)

        self.assertEqual(len(result), 2)
        self.assertEqual(
            get_data_by_val(result, u'all')['count'], 3,
            msg=u"Test that the number of results if unselected is 3")

        self.assertEqual(
            get_data_by_val(result, u'Event')['selected'], True,
            msg=u"Test that Event portal_type is selected matching the query")

    def test_and_filter_type(self):
        self.assertEqual(len(self.collection.results()), 3)

        result = get_filter_items(
            self.collection_uid, 'Subject', cache_enabled=False)

        self.assertEqual(len(result), 4)
        self.assertEqual(get_data_by_val(result, 'all')['count'], 3)
        self.assertEqual(get_data_by_val(result, 'all')['selected'], True)
        self.assertEqual(get_data_by_val(result, u'Süper')['count'], 2)
        self.assertEqual(get_data_by_val(result, u'Evänt')['count'], 1)
        self.assertEqual(get_data_by_val(result, u'Dokumänt')['count'], 2)



        def qs(result, index):
            url = get_data_by_val(result, index)['url']
            _,_,_,_,query,_ = urlparse(url)
            result = parse_qs(query)
            del result['collectionfilter']
            # Quick hack to get single values back from being lists
            result.update(dict([(k,v[0]) for k,v in result.items() if len(v) == 1]))
            return result


        # Test url
        self.assertEqual(qs(result, u'Süper'), {'Subject': 'S\xc3\xbcper'})

        catalog_results = ICollection(self.collection).results(
            batch=False,
            brains=True,
            custom_query=make_query(qs(result, u'Süper'))
        )
        self.assertEqual(len(catalog_results), 2)

        result = get_filter_items(
            self.collection_uid, 'Subject',
            request_params={'Subject': u'Süper'},
            filter_type="and",
            cache_enabled=False)



        self.assertEqual(len(result), 4)
        self.assertEqual(get_data_by_val(result, 'all')['count'], 3)

        # TODO: I'm not sure these counts are correct. It should represent how many results you will get if you click so should be smaller than this
        # but I guess you need to turn on narrow down for that?
        self.assertEqual(get_data_by_val(result, u'Süper')['count'], 2)
        self.assertEqual(get_data_by_val(result, u'Evänt')['count'], 1)
        self.assertEqual(get_data_by_val(result, u'Dokumänt')['count'], 2)

        self.assertEqual(get_data_by_val(result, u'Süper')['selected'], True)

        self.assertEqual(qs(result, u'Süper'), {})
        self.assertEqual(qs(result, u'Dokumänt'), {'Subject_op': 'and', 'Subject': ['S\xc3\xbcper', 'Dokum\xc3\xa4nt']})
        self.assertEqual(qs(result, u'Evänt'), {'Subject_op': 'and', 'Subject': ['S\xc3\xbcper', 'Ev\xc3\xa4nt']})

        # Narrow down by 2

        catalog_results = ICollection(self.collection).results(
            batch=False,
            brains=True,
            custom_query=make_query(qs(result, u'Dokumänt'))
        )
        self.assertEqual(len(catalog_results), 1)

        result = get_filter_items(
            self.collection_uid, 'Subject',
            request_params={'Subject': [u'Süper', u'Dokumänt']},
            filter_type="and",
            cache_enabled=False)

        self.assertEqual(len(result), 4)
        self.assertEqual(get_data_by_val(result, 'all')['count'], 3)
        self.assertEqual(get_data_by_val(result, u'Süper')['count'], 2)

        self.assertEqual(get_data_by_val(result, u'Evänt')['count'], 1)
        self.assertEqual(get_data_by_val(result, u'Dokumänt')['count'], 2)

        self.assertEqual(get_data_by_val(result, u'Süper')['selected'], True)
        self.assertEqual(get_data_by_val(result, u'Dokumänt')['selected'], True)

        self.assertEqual(qs(result, u'Süper'), {'Subject': 'Dokum\xc3\xa4nt'})
        self.assertEqual(qs(result, u'Dokumänt'), {'Subject': 'S\xc3\xbcper'})
        self.assertEqual(qs(result, u'Evänt'), {'Subject': ['S\xc3\xbcper', 'Dokum\xc3\xa4nt', 'Ev\xc3\xa4nt'], 'Subject_op': 'and'})


        # Clicking on Event we should get 0 results as none will be in common
        catalog_results = ICollection(self.collection).results(
            batch=False,
            brains=True,
            custom_query=make_query(qs(result, u'Evänt'))
        )
        self.assertEqual(len(catalog_results), 0)
