import urllib
import urllib2

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
    #searchString='<edsp_query debug="true"><from id="g1" gId="c19"/><select><col id="c0" cId="g1.112" name="Model Type"/><col id="c1" cId="g1.oname" name="Name"/><col id="c2" cId="g1.oid" name="Object.ID"/><col id="c3" cId="g1.24" name="Notes"/></select><conditions><cond id="n0" cId="g1.112" value="Network"/></conditions><expression value=""/></edsp_query>'
    #result = urllib.urlopen('http://senselab.med.yale.edu/ModelDB/eavXDSearch.aspx', searchString)
    #request = urllib2.Request('http://senselab.med.yale.edu/ModelDB/eavXDSearch.aspx', data=searchString)
    #data = urllib2.urlopen(request).read().strip()
    search_dict={'__EVENTTARGET': '',
                 '__EVENTARGUMENT':'',
                 '__LASTFOCUS':'',
                 '__VIEWSTATE':'/wEPDwULLTEzNzQ2NjMwMTkPZBYCZg9kFgICAw9kFgRmDw8WBB4JQmFja0NvbG9yDB4EXyFTQgIIZBYCAgEPDxYCHgRUZXh0BQZQdWJsaWNkZAIBD2QWBgIDDw8WAh4HVmlzaWJsZWdkFggCAQ8QDxYGHg1EYXRhVGV4dEZpZWxkBQdDYXB0aW9uHg5EYXRhVmFsdWVGaWVsZAUCSWQeC18hRGF0YUJvdW5kZ2QQFRwdMiBPYmplY3RzIFJlbGF0aW9uc2hpcCAoZWRnZSkUQWx0ZXJuYXRlIE1vZGVsIEZpbGUbQ2FtZSB0byBNb2RlbERCIGJlY2F1c2Ugd2FzBENlbGwJQ2hhcmFjdGVyDUNvbGxhYm9yYXRpb24JQ29tcG9uZW50E0NvbXB1dGF0aW9uYWwgbW9kZWwNR2FwIEp1bmN0aW9ucwlHZW5lIE5hbWULR2VuZSBzcGVjaWULSW1wbGVtZW50ZXIHSm91cm5hbA1Mb2NhbCBDb250YWN0C01vZGVsIFRvcGljCk1vZGVsIFR5cGUUTW9kZWxpbmcgQXBwbGljYXRpb24NT250b2xvZ3kgdGVybQVQYXBlcgxQYXBlciBBdXRob3ILUGFwZXIgVXNhZ2UbUHJvdmVuYW5jZS1EYXRlIG1hZGUgcHVibGljDFJlbGF0aW9uc2hpcAxSdW4gQ3VyYXRpb24MU1FMIHByb2dyYW1zBlNwZWNpZQZTdGF0dXMNVHJlZSBvciBncmFwaBUcAzEyNQI5MgMxMjgCOTcDMTE3Ajg3AzE1OQIxOQMxNDIDMTI2AzEzNgI5MQMxMTgCODgCMzkCMzgCMzYDMTIyAjQyAjQ0AzEzNQMxMjcDMTI0AzE1NwI3MwMxMzcCODkDMTE5FCsDHGdnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2dnZ2cWAQIHZAIDDw8WBB8ACXfMzP8fAQIIZGQCBw8PFgQfAAl3zMz/HwECCGRkAgsPDxYCHgtOYXZpZ2F0ZVVybAUdLi9lYXZYRFNlYXJjaC5hc3B4P2RiPTImY2w9MTlkZAIFDw8WAh8DaGQWBAIFDzwrABEBARAWABYAFgBkAgkPPCsAEQEBEBYAFgAWAGQCBw8PFgIfAmVkZBgDBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WEAUmY3RsMDAkQ29udGVudFBsYWNlSG9sZGVyMSRja2JTZWxlY3RBbGwFIGN0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkZmRfb2lkBSFjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJGZkX25hbWUFIGN0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkZmRfYTI0BSBjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJGZkX2EyNQUhY3RsMDAkQ29udGVudFBsYWNlSG9sZGVyMSRmZF9hNDE0BSBjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJGZkX2EyNwUgY3RsMDAkQ29udGVudFBsYWNlSG9sZGVyMSRmZF9hMjYFIWN0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkZmRfYTExMgUhY3RsMDAkQ29udGVudFBsYWNlSG9sZGVyMSRmZF9hMTEzBSFjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJGZkX2ExMTQFIWN0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkZmRfYTQ3NgUhY3RsMDAkQ29udGVudFBsYWNlSG9sZGVyMSRmZF9hNDcxBSFjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJGZkX2E0NjkFIWN0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkZmRfYTI5OQUgY3RsMDAkQ29udGVudFBsYWNlSG9sZGVyMSRmZF9hMjgFKWN0bDAwJENvbnRlbnRQbGFjZUhvbGRlcjEkR3JpZFZpZXdfcmVzdWx0D2dkBSNjdGwwMCRDb250ZW50UGxhY2VIb2xkZXIxJEdyaWRWaWV3MQ9nZMdi47hdNxT51NzubeqUmWmqxHdKRCQTaJbYFSVv8bwm',
                 '__EVENTVALIDATION':'/wEWPALu2qO/AwLinKf2DwLSoL3SAQL188WbAwKz+LHmBQL18+mbAwKEkv24DQL68+mbAwKO0Y/TCwLt86GYAwK9nJ4SAqm5n88HAqm5k88HAvXzwZsDArP4veYFAvrzrZgDAu/zoZgDAu/zrZgDAu/z9ZsDAr2c5hIC7vPFmwMC7vP9mwMC0qCx0gEChJLxuA0C98/b+AsChJLtuA0C6/P5mwMChJL1uA0C+vOhmAMCjtGf0wsC/MjhlAEC977UpQICh82B9gkCh82dyQcC+qug9wcC+quMnA8C+quo7wwCt8LurwUCt8Kq3AgC+qvk5Q0C+qvQpQ4C+qv4wAYC+qu8ygUC7IaV8AYC7IbRnAoC7YaV8AYC7YbRnAoC5oaV8AYC5obRnAoCucKW5gYCucKCpgcCvMKW5gYCvMKCpgcCtMKqwQ8CtMLuyg4C/u+SrAsC/u/O2A4C+quwsQ8C+qvEpwEC8a/roQsESpQ5PfnLlb73z2q0+oQEg20jncYy+4608iWZDV5f4w==',
                 'ctl00_ContentPlaceHolder1_ddl_class': '19',
                 'ctl00_ContentPlaceHolder1_fd_oid': 'on',
                 'ctl00_ContentPlaceHolder1_fd_name': 'on',
                 #'ctl00_ContentPlaceHolder1_fc_name':'',
                'ctl00_ContentPlaceHolder1_fc_a25': 'Neocortical basket cell'
    }
    result = urllib.urlopen('http://senselab.med.yale.edu/ModelDB/eavRAMCDandXsearch.aspx', urllib.urlencode( search_dict ) )
    data=result.read()
#    search_string='Neocortical basket cell'
#    result=urllib.urlopen('http://senselab.med.yale.edu/ModelDB/eavRAMCDandXSearch.aspx?g=%s' % search_string.replace(' ','+'))
#    data=result.read()
    print(data)

class ModelDBSearcher():
    def __init__(self, search_data):
        self.__dict__.update(search_data)
