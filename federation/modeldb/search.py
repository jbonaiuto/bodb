from StringIO import StringIO
from lxml import etree
import re
import urllib
from bodb.models import ModelDBResult, Model, importPubmedLiterature

def runModelDBSearch(search_data, userId):
    searchString=''
    searcher=ModelDBSearcher(search_data)
    results=[]
    # construct search query
    for key in search_data.iterkeys():
        # if the searcher can search by this field
        if hasattr(searcher, 'search_%s' % key):
            # add field to query
            dispatch=getattr(searcher, 'search_%s' % key)
            searchString=dispatch(searchString, userId)

    parser=etree.HTMLParser()

    query_data=urllib.urlopen('http://senselab.med.yale.edu/ModelDB/eavRAMCDandXSearch.aspx?g=%s' % searchString).read()
    query_tree=etree.parse(StringIO(query_data),parser)
    result_nodes=query_tree.xpath("//tr[@class='search1']")
    for result_node in result_nodes:
        link_node=result_node.xpath('./td/a')[0]
        link=link_node.attrib['href']
        result=ModelDBResult()
        result.accession_number=link[link.index('=')+1:]
        result.title=link_node.text
        result.exists=Model.objects.filter(modeldb_accession_number=int(result.accession_number)).exists()

        model_data=urllib.urlopen('http://senselab.med.yale.edu/ModelDB/ShowModel.asp?model=%s' % result.accession_number).read()
        model_tree=etree.parse(StringIO(model_data),parser)
        desc_node=model_tree.xpath("//form[@name='form0']/table/tr[3]/td")[0]
        result.description="".join([x for x in desc_node.itertext()])
        result.description=re.sub('\s+',' ',result.description).strip()

        concept_node=model_tree.xpath("//td[contains(text(),'Model Concept(s):')]")[0]
        keyword_node=concept_node.getparent().xpath('./td')[1]
        result.keywords="".join([x for x in keyword_node.itertext()])
        result.keywords=re.sub('\s+', ' ', result.keywords).strip()

        pubmed_nodes=model_tree.xpath("//a[contains(text(),'PubMed')]")
        if len(pubmed_nodes):
            pubmed_link=pubmed_nodes[0].attrib['href']
            pubmed_id=pubmed_link[pubmed_link.index('list_uids=')+10:pubmed_link.index('&dopt')]
            result.literature=importPubmedLiterature(pubmed_id)

            for ordered_author in result.literature.authors.all():
                if len(result.authors)>0:
                    result.authors+=', '
                result.authors+='%s %s' % (ordered_author.author.last_name,ordered_author.author.first_name)
        results.append(result)
    return results


class ModelDBSearcher():
    def __init__(self, search_data):
        self.__dict__.update(search_data)

    def search_keywords(self, search_string, userId):
        if self.keywords:
            search_string='%s ' % self.keywords.replace(' ','+')
        return search_string
