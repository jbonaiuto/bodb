import datetime
from Bio import Entrez
Entrez.email = 'uscbrainproject@gmail.com'
from bodb.search.user import runUserSearch
from registration.models import User
from bodb.search.atlas import runBrainRegionSearch
from bodb.search.bop import runBOPSearch
from bodb.search.literature import runLiteratureSearch
from bodb.search.model import runModelSearch
from bodb.search.sed import runSEDSearch, runSEDCoordSearch
from bodb.search.ssr import runSSRSearch
from federation.modeldb.search import runModelDBSearch
from django.views.generic.edit import FormView
from federation.brede.search import runBredeSearch
from federation.cocomac.search import runCoCoMacSearch
from bodb.forms.search import AllSearchForm, BOPSearchForm, SEDSearchForm, LiteratureSearchForm, BrainRegionSearchForm, ModelSearchForm, DocumentSearchForm, PubmedSearchForm, ModelDBSearchForm, UserSearchForm
from bodb.models import BOP, SED, Literature, BrainRegion, Model, SSR, PubMedResult, ERPSED, BrainImagingSED, ConnectivitySED, SelectedSEDCoord, ERPComponent, BodbProfile

class SearchView(FormView):
    form_class = AllSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(SearchView,self).get_context_data(**kwargs)
        context['helpPage']='search_data.html'
        context['showTabs']=True
        context['ispopup']=('_popup' in self.request.GET)
        context['bop_search_form']=BOPSearchForm(self.request.POST or None,prefix='bop')
        context['model_search_form']=ModelSearchForm(self.request.POST or None,prefix='model')
        context['sed_search_form']=SEDSearchForm(self.request.POST or None,prefix='sed')
        context['ssr_search_form']=DocumentSearchForm(self.request.POST or None,prefix='ssr')
        context['literature_search_form']=LiteratureSearchForm(self.request.POST or None,prefix='literature')
        context['brain_region_search_form']=BrainRegionSearchForm(self.request.POST or None,prefix='brain_region')
        context['user_search_form']=UserSearchForm(self.request.POST or None,prefix='user')
        context['searchType']=self.request.POST.get('searchType','all')
        context['allConnectionGraphId']='allConnectivitySEDDiagram'
        context['allErpGraphId']='allErpSEDDiagram'
        context['sedConnectionGraphId']='sedConnectivitySEDDiagram'
        context['sedErpGraphId']='sedErpSEDDiagram'
        context['allBopGraphId']='allBOPRelationshipDiagram'
        context['bopBOPGraphId']='bopRelationshipDiagram'
        context['allModelGraphId']='allModelRelationshipDiagram'
        context['modelModelGraphId']='modelRelationshipDiagram'
        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        bop_form = context['bop_search_form']
        model_form = context['model_search_form']
        sed_form = context['sed_search_form']
        ssr_form = context['ssr_search_form']
        literature_form = context['literature_search_form']
        brain_region_form = context['brain_region_search_form']
        user_form=context['user_search_form']

        user=self.request.user

        genericSEDs=[]
        connectivitySEDs=[]
        erpSEDs=[]
        imagingSEDs=[]
        sedCoords=[]

        literature=Literature.objects.none()
        bops=BOP.objects.none()
        models=Model.objects.none()
        ssrs=SSR.objects.none()
        brain_regions=BrainRegion.objects.none()
        users=User.objects.none()

        searchType=self.request.POST['searchType']
        if searchType=='bops' and bop_form.is_valid():
            bops=runBOPSearch(bop_form.cleaned_data, user.id)
        elif searchType=='models' and model_form.is_valid():
            models=runModelSearch(model_form.cleaned_data, user.id)
        elif searchType=='seds' and sed_form.is_valid():
            seds=runSEDSearch(sed_form.cleaned_data, user.id)
            for idx,sedObj in enumerate(seds):
                if sedObj.type=='event related potential':
                    erpSEDs.append(ERPSED.objects.get(id=sedObj.id))
                elif sedObj.type=='brain imaging':
                    imagingSEDs.append(BrainImagingSED.objects.get(id=sedObj.id))
                elif sedObj.type=='connectivity':
                    connectivitySEDs.append(ConnectivitySED.objects.get(id=sedObj.id))
                elif sedObj.type=='generic':
                    genericSEDs.append(sedObj)
            cococmacConnSEDs=runCoCoMacSearch(sed_form.cleaned_data, user.id)
            for connSED in cococmacConnSEDs:
                connectivitySEDs.append(connSED)
            bredeImagingSEDs=runBredeSearch(sed_form.cleaned_data, user.id)
            for imagingSED in bredeImagingSEDs:
                imagingSEDs.append(imagingSED)
            sedCoords=runSEDCoordSearch(imagingSEDs, sed_form.cleaned_data, user.id)
        elif searchType=='ssrs' and ssr_form.is_valid():
            ssrs=runSSRSearch(ssr_form.cleaned_data, user.id)
        elif searchType=='literature'and literature_form.is_valid():
            literature=runLiteratureSearch(literature_form.cleaned_data, user.id)
        elif searchType=='brain_regions' and brain_region_form.is_valid():
            brain_regions=runBrainRegionSearch(brain_region_form.cleaned_data)
        elif searchType=='users' and user_form.is_valid():
            users=runUserSearch(user_form.cleaned_data, user.id)
        else:
            bops=runBOPSearch(form.cleaned_data, user.id)
            models=runModelSearch(form.cleaned_data, user.id)
            seds=runSEDSearch(form.cleaned_data, user.id)
            for idx,sedObj in enumerate(seds):
                if sedObj.type=='event related potential':
                    erpSEDs.append(ERPSED.objects.get(id=sedObj.id))
                elif sedObj.type=='brain imaging':
                    imagingSEDs.append(BrainImagingSED.objects.get(id=sedObj.id))
                elif sedObj.type=='connectivity':
                    connectivitySEDs.append(ConnectivitySED.objects.get(id=sedObj.id))
                elif sedObj.type=='generic':
                    genericSEDs.append(sedObj)
            cocomacConnSEDs=runCoCoMacSearch(form.cleaned_data, user.id)
            for connSED in cocomacConnSEDs:
                connectivitySEDs.append(connSED)
            bredeImagingSEDs=runBredeSearch(form.cleaned_data, user.id)
            for imagingSED in bredeImagingSEDs:
                imagingSEDs.append(imagingSED)
            sedCoords=runSEDCoordSearch(imagingSEDs, form.cleaned_data, user.id)
            ssrs=runSSRSearch(form.cleaned_data, user.id)
            literature=runLiteratureSearch(form.cleaned_data, user.id)
            brain_regions=runBrainRegionSearch(form.cleaned_data)
            users=runUserSearch(form.cleaned_data, user.id)

        context['bops']=BOP.get_bop_list(bops, user)
        context['models']=Model.get_model_list(models, user)
        context['generic_seds']=SED.get_sed_list(genericSEDs, user)
        context['erp_seds']=SED.get_sed_list(erpSEDs, user)
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],
            [ERPComponent.objects.filter(erp_sed=erp_sed) for erp_sed in erpSEDs])
        context['connectivity_seds']=SED.get_sed_list(connectivitySEDs, user)
        context['imaging_seds']=SED.get_sed_list(imagingSEDs, user)
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],
            [sedCoords[sed.id] for sed in imagingSEDs])
        context['ssrs']=SSR.get_ssr_list(ssrs, user)
        context['literatures']=literature
        context['brain_regions']=brain_regions
        context['users']=BodbProfile.get_user_list(users,user)
        context['can_add_entry']=False
        context['can_remove_entry']=False
        context['selected_coord_ids']=[]
        if user.is_authenticated() and not user.is_anonymous():
            active_workspace=user.get_profile().active_workspace
            context['can_add_entry']=user.has_perm('add_entry',active_workspace)
            context['can_remove_entry']=user.has_perm('remove_entry',active_workspace)

            selected_coords=SelectedSEDCoord.objects.filter(selected=True, user__id=user.id)
            for coord in selected_coords:
                context['selected_coord_ids'].append(coord.sed_coordinate.id)

        return self.render_to_response(context)


class BOPSearchView(FormView):
    form_class=BOPSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(BOPSearchView,self).get_context_data(**kwargs)
        context['helpPage']='search_data.html#bops'
        context['bop_search_form']=context.get('form')
        context['bopGraphId']='bopRelationshipDiagram'
        context['searchType']='bops'
        context['searchLabel']='Brain Operating Principles (BOPs)'
        context['exclude']=self.request.GET.get('exclude',None)
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        user=self.request.user

        bops=runBOPSearch(form.cleaned_data, user.id, exclude=context['exclude'])

        context['bops']=BOP.get_bop_list(bops, user)

        user=self.request.user
        context['can_add_entry']=False
        context['can_remove_entry']=False
        if user.is_authenticated() and not user.is_anonymous():
            active_workspace=user.get_profile().active_workspace
            context['can_add_entry']=user.has_perm('add_entry',active_workspace)
            context['can_remove_entry']=user.has_perm('remove_entry',active_workspace)

        return self.render_to_response(context)


class BrainRegionSearchView(FormView):
    form_class=BrainRegionSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(BrainRegionSearchView,self).get_context_data(**kwargs)
        context['helpPage']='search_data.html#brain-regions'
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
        user=self.request.user
        context['can_add_entry']=False
        context['can_remove_entry']=False
        if user.is_authenticated() and not user.is_anonymous():
            active_workspace=user.get_profile().active_workspace
            context['can_add_entry']=user.has_perm('add_entry',active_workspace)
            context['can_remove_entry']=user.has_perm('remove_entry',active_workspace)
        return self.render_to_response(context)


class LiteratureSearchView(FormView):
    form_class=LiteratureSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(LiteratureSearchView,self).get_context_data(**kwargs)
        context['helpPage']='search_data.html#literature'
        context['literature_search_form']=context.get('form')
        context['searchType']='literature'
        context['searchLabel']='Literature'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        return context

    def form_valid(self, form):
        literatures=runLiteratureSearch(form.cleaned_data, self.request.user.id)

        # first request for search page - start with all record search
        context=self.get_context_data(form=form)
        context['literatures']=literatures
        user=self.request.user
        context['can_add_entry']=False
        context['can_remove_entry']=False
        if user.is_authenticated() and not user.is_anonymous():
            active_workspace=user.get_profile().active_workspace
            context['can_add_entry']=user.has_perm('add_entry',active_workspace)
            context['can_remove_entry']=user.has_perm('remove_entry',active_workspace)
        return self.render_to_response(context)


class ModelSearchView(FormView):
    form_class=ModelSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(ModelSearchView,self).get_context_data(**kwargs)
        context['helpPage']='search_data.html#models'
        context['model_search_form']=context.get('form')
        context['searchType']='models'
        context['searchLabel']='Models'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        context['exclude']=self.request.GET.get('exclude',None)
        context['modelGraphId']='modelRelationshipDiagram'
        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        user=self.request.user

        models=runModelSearch(form.cleaned_data, user.id, exclude=context['exclude'])
        context['models']=Model.get_model_list(models, user)

        user=self.request.user
        context['can_add_entry']=False
        context['can_remove_entry']=False
        if user.is_authenticated() and not user.is_anonymous():
            active_workspace=user.get_profile().active_workspace
            context['can_add_entry']=user.has_perm('add_entry',active_workspace)
            context['can_remove_entry']=user.has_perm('remove_entry',active_workspace)

        return self.render_to_response(context)


class SEDSearchView(FormView):
    form_class=SEDSearchForm
    template_name='bodb/search/search.html'

    def get_context_data(self, **kwargs):
        context = super(SEDSearchView,self).get_context_data(**kwargs)
        context['helpPage']='search_data.html#summary-of-experimental-data'
        context['sed_search_form']=context.get('form')
        context['searchType']='seds'
        context['searchLabel']='Summaries of Experimental Data (SEDs)'
        context['ispopup']=('_popup' in self.request.GET)
        context['multiple']=('_multiple' in self.request.GET)
        context['type']=self.request.GET.get('type',None)
        context['connectionGraphId']='connectivitySEDDiagram'
        context['erpGraphId']='erpSEDDiagram'
        return context

    def form_valid(self, form):
        context=self.get_context_data(form=form)
        user=self.request.user

        genericSEDs=[]
        connectivitySEDs=[]
        erpSEDs=[]
        imagingSEDs=[]

        seds=runSEDSearch(form.cleaned_data, user.id)
        for idx,sedObj in enumerate(seds):
            if sedObj.type=='event related potential':
                erpSEDs.append(ERPSED.objects.get(id=sedObj.id))
            elif sedObj.type=='brain imaging':
                imagingSEDs.append(BrainImagingSED.objects.get(id=sedObj.id))
            elif sedObj.type=='connectivity':
                connectivitySEDs.append(ConnectivitySED.objects.get(id=sedObj.id))
            elif sedObj.type=='generic':
                genericSEDs.append(sedObj)
        cocomacConnSEDs=runCoCoMacSearch(form.cleaned_data, user.id)
        for connSED in cocomacConnSEDs:
            connectivitySEDs.append(connSED)
        bredeImagingSEDs=runBredeSearch(form.cleaned_data, user.id)
        for imagingSED in bredeImagingSEDs:
            imagingSEDs.append(imagingSED)
        sedCoords=runSEDCoordSearch(imagingSEDs, form.cleaned_data, user.id)

        # load selected sed ids
        context['generic_seds']=SED.get_sed_list(genericSEDs,user)
        context['erp_seds']=SED.get_sed_list(erpSEDs, user)
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],
            [ERPComponent.objects.filter(erp_sed=erp_sed) for erp_sed in erpSEDs])
        context['connectivity_seds']=SED.get_sed_list(connectivitySEDs,user)
        context['imaging_seds']=SED.get_sed_list(imagingSEDs,user)
        context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],
            [sedCoords[sed.id] for sed in imagingSEDs])
        context['can_add_entry']=False
        context['can_remove_entry']=False
        context['selected_coord_ids']=[]
        if user.is_authenticated() and not user.is_anonymous():
            active_workspace=user.get_profile().active_workspace
            context['can_add_entry']=user.has_perm('add_entry',active_workspace)
            context['can_remove_entry']=user.has_perm('remove_entry',active_workspace)

            selected_coords=SelectedSEDCoord.objects.filter(selected=True, user__id=user.id)
            for coord in selected_coords:
                context['selected_coord_ids'].append(coord.sed_coordinate.id)

        return self.render_to_response(context)


class ModelDBSearchView(FormView):
    form_class=ModelDBSearchForm
    template_name = 'bodb/search/search_modeldb.html'

    def get_context_data(self, **kwargs):
        context=super(ModelDBSearchView,self).get_context_data(**kwargs)
        context['helpPage']='BODB-Insert-Model#ModelDB_Search'
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        context=self.get_context_data()

        searchData={'keywords': form.cleaned_data['all']}
        results=runModelDBSearch(searchData, self.request.user.id)
        context['search_results']=results
        context['form']=form
        return self.render_to_response(context)


stop_words=['a', 'about', 'again', 'all', 'almost', 'also', 'although', 'always', 'among', 'an', 'and', 'another',
            'any', 'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'between', 'both', 'but', 'by', 'can',
            'could', 'did', 'do', 'does', 'done', 'due', 'during', 'each', 'either', 'enough', 'especially', 'etc',
            'for', 'found', 'from', 'further', 'had', 'has', 'have', 'having', 'here', 'how', 'however', 'i', 'if',
            'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'kg', 'km', 'made', 'mainly', 'make', 'may', 'mg',
            'might', 'ml', 'mm', 'most', 'mostly', 'must', 'nearly', 'neither', 'no', 'nor', 'obtained', 'of', 'often',
            'on', 'our', 'overall', 'perhaps', 'pmid', 'quite', 'rather', 'really', 'regarding', 'seem', 'seen',
            'several', 'should', 'show', 'showed', 'shown', 'shows', 'significantly', 'since', 'so', 'some', 'such',
            'than', 'that', 'the', 'their', 'theirs', 'them', 'then', 'there', 'therefore', 'these', 'they', 'this',
            'those', 'through', 'thus', 'to', 'upon', 'use', 'used', 'using', 'various', 'very', 'was', 'we', 'were',
            'what', 'when', 'which', 'while', 'with', 'within', 'without', 'would']


class PubmedSearchView(FormView):
    form_class=PubmedSearchForm
    template_name='bodb/search/search_pubmed.html'
    initial = {'start':0}
    # get 10 results at a time
    number=10

    def get_context_data(self, **kwargs):
        context = super(PubmedSearchView,self).get_context_data(**kwargs)
        context['helpPage']='insert_data.html#pubmed-search'
        context['ispopup']=('_popup' in self.request.GET)
        return context

    def form_valid(self, form):
        context=self.get_context_data()

        # get search phrase
        searchPhrase=''
        if len(form.cleaned_data['all']):
            for i,word in enumerate(form.cleaned_data['all'].split()):
                if not word in stop_words:
                    if i>0:
                        searchPhrase+='+AND+'
                    searchPhrase+='%s[tiab]' % word.replace(':','')
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
            for i,word in enumerate(form.cleaned_data['authors'].split()):
                if i>0:
                    searchPhrase+='+AND+'
                searchPhrase+='%s[au]' % word
        if len(form.cleaned_data['issue']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            searchPhrase+='%s[ip]' % form.cleaned_data['issue']
        if len(form.cleaned_data['title']):
            if len(searchPhrase):
                searchPhrase+='+AND+'
            for i,word in enumerate(form.cleaned_data['title'].split()):
                if not word in stop_words:
                    if i>0:
                        searchPhrase+='+AND+'
                    searchPhrase+='%s[Title]' % word.replace(':','')
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




