import operator
from bodb.models import Document, SSR
from bodb.search.document import DocumentSearch
from registration.models import User

def runSSRSearch(search_data, userId):
    filters=[]

    op=operator.or_
    if search_data['search_options']=='all':
        op=operator.and_

    # create SSR search
    searcher=DocumentSearch(search_data)

    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            filters.append(dispatch(userId))

    # restrict to user's own entries or those of other users that are not drafts
    if User.objects.filter(id=userId):
        user=User.objects.get(id=userId)
    else:
        user=User.get_anonymous()

    q = reduce(op,filters) & Document.get_security_q(user)

    # get results
    if q and len(q):
        results = SSR.objects.filter(q).select_related('collator').distinct()
    else:
        results = SSR.objects.all().select_related('collator')
    return results.order_by('title')