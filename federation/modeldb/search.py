import urllib

def runModelDBSearch(search_data, userId):
    searchString=''
    searcher=ModelDBSearcher(search_data)
    results=[]
    # construct search query
#    for key in search_data.iterkeys():
#        # if the searcher can search by this field
#        if hasattr(searcher, 'search_%s' % key):
#            # add field to query
#            dispatch=getattr(searcher, 'search_%s' % key)
#            searchString=dispatch(searchString)
    searchString='<edsp_query debug="false"><from id="g1" gId="c19"/><select><col id="c0" cId="g1.112" name="Model Type"/><col id="c1" cId="g1.oname" name="Name"/><col id="c2" cId="g1.oid" name="Object.ID"/><col id="c3" cId="g1.24" name="Notes"/></select><conditions><cond id="n0" cId="g1.112" value="Network"/></conditions><expression value=""/></edsp_query>'
    result = urllib.urlopen('http://senselab.med.yale.edu/ModelDB/eavXDSearch.aspx', urllib.urlencode( {'request':searchString} ) )
    data=result.read()
    print(data)

class ModelDBSearcher():
    def __init__(self, search_data):
        self.__dict__.update(search_data)
