# -*- coding: utf-8 -*-
from .query import make_query


def set_content_filter(context, event):
    """Set the content filter dictionary on the request, built from request
    parameters to narrow the results of the collection.
    """
    req = event.request
    if 'collectionfilter' not in req.form:
        return
    del req.form['collectionfilter']
    print(
        "CALLED set_content_filter URL: %s, ACTUAL_URL: %s" % (
            req['URL'], req['ACTUAL_URL']
        )
    )
    content_filter = make_query(req.form)
    event.request['contentFilter'] = content_filter
