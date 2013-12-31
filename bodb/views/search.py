import datetime
from Bio import Entrez
Entrez.email = 'uscbrainproject@gmail.com'
from django.views.generic.edit import FormView
from brede.search import runBredeSearch
from cocomac.search import runCoCoMacSearch
from bodb.forms import AllSearchForm, BOPSearchForm, SEDSearchForm, LiteratureSearchForm, BrainRegionSearchForm, ModelSearchForm, SSRSearchForm, PubmedSearchForm
from bodb.models import BOP, SED, Literature, Journal, Book, Chapter, Thesis, Conference, Unpublished, BrainRegion, Model, SSR, PubMedResult, ERPSED, BrainImagingSED, SelectedSEDCoord, ConnectivitySED
from bodb.search import runBOPSearch, runSEDSearch, runLiteratureSearch, runBrainRegionSearch, runModelSearch, runSSRSearch, runSEDCoordSearch

class SearchView(FormView):
    form_class = AllSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(SearchView,self).get_context_data(**kwargs)
        context['helpPage']='BODB-Search'
        context['showTabs']=True
        context['ispopup']=('_popup' in self.request.GET)
        context['bop_search_form']=BOPSearchForm(self.request.POST or None,prefix='bop')
        context['model_search_form']=ModelSearchForm(self.request.POST or None,prefix='model')
        context['sed_search_form']=SEDSearchForm(self.request.POST or None,prefix='sed')
        context['ssr_search_form']=SSRSearchForm(self.request.POST or None,prefix='ssr')
        context['literature_search_form']=LiteratureSearchForm(self.request.POST or None,prefix='literature')
        context['brain_region_search_form']=BrainRegionSearchForm(self.request.POST or None,prefix='brain_region')
        context['searchType']=self.request.POST.get('searchType','all')
        context['allConnectionGraphId']='allConnectivitySEDDiagram'
        context['sedConnectionGraphId']='sedConnectivitySEDDiagram'
        context['allBopGraphId']='allBOPRelationshipDiagram'
        context['bopBOPGraphId']='bopRelationshipDiagram'
        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        bop_form = context['bop_search_form']
        model_form = context['model_search_form']
        sed_form = context['sed_search_form']
        ssr_form = context['ssr_search_form']
        literature_form = context['literature_search_form']
        brain_region_form = context['brain_region_search_form']

        user=self.request.user

        sedCoords=[]
        literatures=[]
        bopObjs=BOP.objects.none()
        modelObjs=Model.objects.none()
        genericObjs=[]
        connectivityObjs=[]
        erpObjs=[]
        imagingObjs=[]
        ssrObjs=SSR.objects.none()
        brain_regions=BrainRegion.objects.none()

        searchType=self.request.POST['searchType']
        if searchType=='bops' and bop_form.is_valid():
            bopObjs=runBOPSearch(bop_form.cleaned_data, user.id)
        elif searchType=='models' and model_form.is_valid():
            modelObjs=runModelSearch(model_form.cleaned_data, user.id)
        elif searchType=='seds' and sed_form.is_valid():
            sedObjs=runSEDSearch(sed_form.cleaned_data, user.id)
            for idx,sedObj in enumerate(sedObjs):
                if sedObj.type=='event related potential':
                    erpObjs.append(ERPSED.objects.get(id=sedObj.id))
                elif sedObj.type=='brain imaging':
                    imagingObjs.append(BrainImagingSED.objects.get(id=sedObj.id))
                elif sedObj.type=='connectivity':
                    connectivityObjs.append(ConnectivitySED.objects.get(id=sedObj.id))
                elif sedObj.type=='generic':
                    genericObjs.append(sedObj)
            connSEDs=runCoCoMacSearch(sed_form.cleaned_data, user.id)
            for connSED in connSEDs:
                connectivityObjs.append(connSED)
            imagingSEDs=runBredeSearch(sed_form.cleaned_data, user.id)
            for imagingSED in imagingSEDs:
                imagingObjs.append(imagingSED)
            sedCoords=runSEDCoordSearch(imagingObjs, sed_form.cleaned_data, user.id)
        elif searchType=='ssrs' and ssr_form.is_valid():
            ssrObjs=runSSRSearch(ssr_form.cleaned_data, user.id)
        elif searchType=='literature'and literature_form.is_valid():
            literatures=list(runLiteratureSearch(literature_form.cleaned_data, user.id))
            literatures.sort(key=Literature.author_names)
        elif searchType=='brain_regions' and brain_region_form.is_valid():
            brain_regions=runBrainRegionSearch(brain_region_form.cleaned_data)
        else:
            bopObjs=runBOPSearch(form.cleaned_data, user.id)
            modelObjs=runModelSearch(form.cleaned_data, user.id)
            sedObjs=runSEDSearch(form.cleaned_data, user.id)
            for idx,sedObj in enumerate(sedObjs):
                if sedObj.type=='event related potential':
                    erpObjs.append(ERPSED.objects.get(id=sedObj.id))
                elif sedObj.type=='brain imaging':
                    imagingObjs.append(BrainImagingSED.objects.get(id=sedObj.id))
                elif sedObj.type=='connectivity':
                    connectivityObjs.append(ConnectivitySED.objects.get(id=sedObj.id))
                elif sedObj.type=='generic':
                    genericObjs.append(sedObj)
            connSEDs=runCoCoMacSearch(form.cleaned_data, user.id)
            for connSED in connSEDs:
                connectivityObjs.append(connSED)
            imagingSEDs=runBredeSearch(form.cleaned_data, user.id)
            for imagingSED in imagingSEDs:
                imagingObjs.append(imagingSED)
            sedCoords=runSEDCoordSearch(imagingObjs, form.cleaned_data, user.id)
            ssrObjs=runSSRSearch(form.cleaned_data, user.id)
            literatures=list(runLiteratureSearch(form.cleaned_data, user.id))
            literatures.sort(key=Literature.author_names)
            brain_regions=runBrainRegionSearch(form.cleaned_data)

        context['bops']=BOP.get_bop_list(bopObjs, user)
        context['models']=Model.get_model_list(modelObjs, user)
        context['generic_seds']=SED.get_sed_list(genericObjs, user)
        context['erp_seds']=SED.get_sed_list(erpObjs, user)
        context['connectivity_seds']=SED.get_sed_list(connectivityObjs, user)
        coords=[sedCoords[sed.id] for sed in imagingObjs]
        context['imaging_seds']=SED.get_sed_list(imagingObjs, user)
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'], coords)
        context['ssrs']=SSR.get_ssr_list(ssrObjs, user)

        # first request for search page - start with all record search
        context['literatures']=literatures
        context['brain_regions']=brain_regions

        return self.render_to_response(context)


class BOPSearchView(FormView):
    form_class=BOPSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(BOPSearchView,self).get_context_data(**kwargs)
        context['bop_search_form']=context.get('form')
        context['bopGraphId']='bopRelationshipDiagram'
        context['searchType']='bops'
        context['searchLabel']='Brain Operating Principles (BOPs)'
        context['exclude']=None
        if 'exclude' in self.request.GET:
            context['exclude']=self.request.GET['exclude']
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        user=self.request.user

        bopObjs=runBOPSearch(form.cleaned_data, user.id)

        bops_to_return=[]
        for bop in bopObjs:
            if context['exclude'] is None or not bop.id==context['exclude']:
                bops_to_return.append(bop)
        context['bops']=BOP.get_bop_list(bops_to_return, user)

        return self.render_to_response(context)


class BrainRegionSearchView(FormView):
    form_class=BrainRegionSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(BrainRegionSearchView,self).get_context_data(**kwargs)
        context['brain_region_search_form']=context.get('form')
        context['searchType']='brain_regions'
        context['searchLabel']='Brain Regions'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        if 'fieldName' in self.request.GET:
            context['fieldName']=self.request.GET['fieldName']
        return context

    def form_valid(self, form):
        brain_regions=runBrainRegionSearch(form.cleaned_data)

        # first request for search page - start with all record search
        context=self.get_context_data(form=form)
        context['brain_regions']=brain_regions
        return self.render_to_response(context)


class LiteratureSearchView(FormView):
    form_class=LiteratureSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(LiteratureSearchView,self).get_context_data(**kwargs)
        context['literature_search_form']=context.get('form')
        context['searchType']='literature'
        context['searchLabel']='Literature'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        return context

    def form_valid(self, form):
        literatures=list(runLiteratureSearch(form.cleaned_data, self.request.user.id))
        literatures.sort(key=Literature.author_names)

        for idx,literature in enumerate(literatures):
            if Journal.objects.filter(id=literature.id):
                literatures[idx]=Journal.objects.get(id=literature.id)
            elif Book.objects.filter(id=literature.id):
                literatures[idx]=Book.objects.get(id=literature.id)
            elif Chapter.objects.filter(id=literature.id):
                literatures[idx]=Chapter.objects.get(id=literature.id)
            elif Thesis.objects.filter(id=literature.id):
                literatures[idx]=Thesis.objects.get(id=literature.id)
            elif Conference.objects.filter(id=literature.id):
                literatures[idx]=Conference.objects.get(id=literature.id)
            elif Unpublished.objects.filter(id=literature.id):
                literatures[idx]=Unpublished.objects.get(id=literature.id)

        # first request for search page - start with all record search
        context=self.get_context_data(form=form)
        context['literatures']=literatures
        return self.render_to_response(context)


class ModelSearchView(FormView):
    form_class=ModelSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(ModelSearchView,self).get_context_data(**kwargs)
        context['sed_search_form']=context.get('form')
        context['searchType']='models'
        context['searchLabel']='Models'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        user=self.request.user

        modelObjs=runModelSearch(form.cleaned_data, user.id)
        context['models']=Model.get_model_list(modelObjs, user)

        return self.render_to_response(context)


class SEDSearchView(FormView):
    form_class=SEDSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(SEDSearchView,self).get_context_data(**kwargs)
        context['sed_search_form']=context.get('form')
        context['searchType']='seds'
        context['searchLabel']='Summaries of Experimental Data (SEDs)'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        context['type']=self.request.GET.get('type',None)
        context['connectionGraphId']='connectivitySEDDiagram'
        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        user=self.request.user

        genericObjs=[]
        connectivityObjs=[]
        erpObjs=[]
        imagingObjs=[]

        sedObjs=runSEDSearch(form.cleaned_data, user.id)
        for idx,sedObj in enumerate(sedObjs):
            if sedObj.type=='event related potential':
                erpObjs.append(ERPSED.objects.get(id=sedObj.id))
            elif sedObj.type=='brain imaging':
                imagingObjs.append(BrainImagingSED.objects.get(id=sedObj.id))
            elif sedObj.type=='connectivity':
                connectivityObjs.append(ConnectivitySED.objects.get(id=sedObj.id))
            elif sedObj.type=='generic':
                genericObjs.append(sedObj)
        connSEDs=runCoCoMacSearch(form.cleaned_data, user.id)
        for connSED in connSEDs:
            connectivityObjs.append(connSED)
        imagingSEDs=runBredeSearch(form.cleaned_data, user.id)
        for imagingSED in imagingSEDs:
            imagingObjs.append(imagingSED)
        sedCoords=runSEDCoordSearch(imagingObjs, form.cleaned_data, user.id)

        # load selected sed ids
        context['generic_seds']=SED.get_sed_list(genericObjs,user)
        context['erp_seds']=SED.get_sed_list(erpObjs,user)
        context['connectivity_seds']=SED.get_sed_list(connectivityObjs,user)
        coords=[sedCoords[sed.id] for sed in imagingObjs]
        context['imaging_seds']=SED.get_sed_list(imagingObjs,user)
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords)

        return self.render_to_response(context)


class PubmedSearchView(FormView):
    form_class=PubmedSearchForm
    template_name='bodb/search/search_pubmed.html'
    initial = {'start':0}
    # get 10 results at a time
    number=10

    def get_context_data(self, **kwargs):
        context = super(PubmedSearchView,self).get_context_data(**kwargs)
        context['helpPage']='BODB-Insert-Literature#PubMed_Search'
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        context=self.get_context_data()

        # get search phrase
        searchPhrase=''
        if len(form.cleaned_data['all']):
            searchPhrase+='%s[tiab]' % form.cleaned_data['all']
        if len(form.cleaned_data['journal']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            searchPhrase+='%s[ta]' % form.cleaned_data['journal']
        if len(form.cleaned_data['volume']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            searchPhrase+='%s[vi]' % form.cleaned_data['volume']
        if len(form.cleaned_data['authors']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            searchPhrase+='%s[au]' % form.cleaned_data['authors']
        if len(form.cleaned_data['issue']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            searchPhrase+='%s[ip]' % form.cleaned_data['issue']
        if len(form.cleaned_data['title']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            searchPhrase+='%s[ti]' % form.cleaned_data['title']
        minDate='1900'
        if len(form.cleaned_data['min_year']):
            minDate=form.cleaned_data['min_year']
        maxDate=str(datetime.datetime.now().year+1)
        if len(form.cleaned_data['max_year']):
            maxDate=form.cleaned_data['max_year']

        # get starting record
        start=int(form.cleaned_data['start'])

        # starting record of the previous page of results
        lastStart=start-self.number
        if lastStart<0:
            lastStart=0

        # total number of results (can be more than 10)
        total=0

        # if there is a search phrase
        search_results=[]
        if len(searchPhrase)>0:
            # get IDs of pubmed articles matching the search phrase
            id_handle=Entrez.esearch(db="pubmed", term=searchPhrase, retmax=self.number, retstart=start, mindate=minDate,
                maxdate=maxDate)
            id_records=Entrez.read(id_handle)
            # get the total number of results
            total=int(id_records['Count'])
            if total>0 and len(id_records['IdList']):
                # get the pubmed article associated with each ID
                article_handles=Entrez.esummary(db="pubmed", id=','.join(id_records['IdList']))
                article_records=Entrez.read(article_handles)
                # read each result
                for article_record in article_records:
                    # create a pubmedresult object
                    pm_result=PubMedResult()
                    pm_result.pubmedId=str(article_record['Id'])
                    if len(Literature.objects.filter(pubmed_id=pm_result.pubmedId)):
                        pm_result.exists=True
                    if 'AuthorList' in article_record:
                        pm_result.authors_display=", ".join(article_record['AuthorList'])
                        pm_result.authors=", ".join(article_record['AuthorList']).replace('\'', '\\\'')
                    if 'PubDate' in article_record:
                        pm_result.year=article_record['PubDate'].split(' ')[0]
                    if 'Title' in article_record:
                        pm_result.title_display=article_record['Title']
                        pm_result.title=article_record['Title'].replace('\'', '\\\'')
                    if 'Source' in article_record:
                        pm_result.journal_display=article_record['Source']
                        pm_result.journal=article_record['Source'].replace('\'', '\\\'')
                    if 'Volume' in article_record:
                        pm_result.volume=article_record['Volume']
                    if 'Issue' in article_record:
                        pm_result.issue=article_record['Issue']
                    if 'Pages' in article_record:
                        pm_result.pages=article_record['Pages']
                    if 'LangList' in article_record:
                        pm_result.language=", ".join(article_record['LangList'])
                    pm_result.url='http://www.ncbi.nlm.nih.gov/pubmed/'+article_record['Id']
                    search_results.append(pm_result)

        # calculate start and end index
        startIdx=start+1
        endIdx=start+len(search_results)

        # whether or not there are any more results to get (after this request)
        has_more=False
        if total>endIdx:
            has_more=True

        # return results and query terms to pubmed search template
        context['search_results']=search_results
        context['startIdx']=startIdx
        context['endIdx']=endIdx
        context['next_start']=str(start+self.number)
        context['last_start']=lastStart
        context['has_more']=has_more
        context['total']=total
        context['form']=form
        return self.render_to_response(context)




