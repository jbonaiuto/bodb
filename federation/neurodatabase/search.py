import urllib
import urllib2

def runNeurodatabaseSearch(search_data, userId):
    searchDict={'format':'xml'}
    searcher=NeurodatabaseSearcher(search_data)
    results=[]
    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            searchDict=dispatch(searchDict, userId)

    auth_req = urllib2.Request('http://neurodatabase.org/dataserver/queryInfo.do?queryCompliant=true')
    auth_response = urllib2.urlopen(auth_req)
    cookie = auth_response.headers.get('Set-Cookie')

    # Use the cookie is subsequent requests
    query_req = urllib2.Request('http://neurodatabase.org/dataserver/queryHTMLExec.do', urllib.urlencode( searchDict ) )
    query_req.add_header('cookie', cookie)
    query_response = urllib2.urlopen(query_req)
    data=query_response.read()

    print(data)

class NeurodatabaseSearcher():
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    def search_related_literature_title(self, searchDict, userId):
        if self.related_literature_title:
            searchDict['field(citation$title)']=self.related_literature_title
        return searchDict

    def search_related_literature_author(self, searchDict, userId):
        if self.related_literature_author:
            if self.related_literature_author.index(' ')>-1:
                names=self.related_literature_author.split(' ')
                searchDict['field(contributor$first)']=names[0]
                searchDict['field(contributor$last)']=names[1]
            else:
                searchDict['field(contributor$last)']=self.related_literature_author
        return searchDict

    def search_related_literature_year_min(self, searchDict, userId):
        if self.related_literature_year_min:
            searchDict['field(citation$year)']=self.related_literature_year_min
        return searchDict

    # search by related Literature maximum year
    def search_related_literature_year_max(self, searchDict, userId):
        if self.related_literature_year_max:
            searchDict['field(citation$year)']=self.related_literature_year_max
        return searchDict