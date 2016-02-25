from django.core.cache import cache
from django.template.loader import render_to_string
from django.views.generic.edit import BaseUpdateView
import os
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import View, DeleteView, TemplateView
from bodb.forms.literature import JournalForm, BookForm, ChapterForm, ConferenceForm, ThesisForm, UnpublishedForm, LiteratureAuthorFormSet
from bodb.models import LiteratureAuthor, Author, Journal, Book, Chapter, Conference, Thesis, Unpublished, BOP, Model, BrainRegion, SED, Literature, BrainImagingSED, SEDCoord, ConnectivitySED, ERPSED, reference_export, ERPComponent, WorkspaceActivityItem
from bodb.views.main import set_context_workspace, get_active_workspace, get_profile
from bodb.views.model import CreateModelView
from guardian.mixins import PermissionRequiredMixin, LoginRequiredMixin
from uscbp import settings
from uscbp.views import JSONResponseMixin

class EditLiteratureMixin():
    template_name = 'bodb/literature/literature_detail.html'

    def get_instances(self,request,id,literatureType):
        return None,None,None,None,None,None,LiteratureAuthor.objects.none(),LiteratureAuthor.objects.none(),\
               LiteratureAuthor.objects.none(),LiteratureAuthor.objects.none(),LiteratureAuthor.objects.none(),\
               LiteratureAuthor.objects.none()

    def process_literature(self, request, type, form, authorFormSet):

        if form.is_valid() and authorFormSet.is_valid():
            lit=form.save(commit=False)
            lit.collator=request.user
            lit.save()

            # save each author, add to journal if not removed, save journal
            for authorForm in authorFormSet.forms:
                if not authorForm in authorFormSet.deleted_forms:
                    lit_author=authorForm.save(commit=False)
                    author=Author(first_name=authorForm.cleaned_data['author_first_name'],
                        middle_name=authorForm.cleaned_data['author_middle_name'],
                        last_name=authorForm.cleaned_data['author_last_name'], alias=authorForm.cleaned_data['author_alias'],
                        email=authorForm.cleaned_data['author_email'],homepage=authorForm.cleaned_data['author_homepage'])
                    if 'author' in authorForm.cleaned_data and authorForm.cleaned_data['author'] is not None:
                        author=authorForm.cleaned_data['author']
                        author.first_name=authorForm.cleaned_data['author_first_name']
                        author.middle_name=authorForm.cleaned_data['author_middle_name']
                        author.last_name=authorForm.cleaned_data['author_last_name']
                        author.alias=authorForm.cleaned_data['author_alias']
                        author.email=authorForm.cleaned_data['author_email']
                        author.homepage=authorForm.cleaned_data['author_homepage']
                    author.save()
                    lit_author.author=author
                    lit_author.save()
                    lit.authors.add(lit_author)

            lit.save()

            return lit.id
        return None

    def get(self, request, *args, **kwargs):
        id = self.kwargs.get('pk', None)
        literatureType=request.GET.get('literatureType','journal')

        journal,book,chapter,conference,thesis,unpublished,journal_authors,book_authors,chapter_authors,\
            conference_authors,thesis_authors,unpublished_authors=self.get_instances(request,id,literatureType)

        journal_form = JournalForm(instance=journal)
        book_form = BookForm(instance=book)
        chapter_form = ChapterForm(instance=chapter)
        conference_form = ConferenceForm(instance=conference)
        thesis_form = ThesisForm(instance=thesis)
        unpublished_form = UnpublishedForm(instance=unpublished)

        journal_author_formset = LiteratureAuthorFormSet(queryset=journal_authors, prefix='journal_author')
        book_author_formset = LiteratureAuthorFormSet(queryset=book_authors, prefix='book_author')
        chapter_author_formset = LiteratureAuthorFormSet(queryset=chapter_authors, prefix='chapter_author')
        conference_author_formset = LiteratureAuthorFormSet(queryset=conference_authors, prefix='conference_author')
        thesis_author_formset = LiteratureAuthorFormSet(queryset=thesis_authors, prefix='thesis_author')
        unpublished_author_formset = LiteratureAuthorFormSet(queryset=unpublished_authors, prefix='unpublished_author')

        context={
            'helpPage': self.helpPage,
            'journal_form': journal_form,
            'journal_author_formset': journal_author_formset,
            'book_form': book_form,
            'book_author_formset': book_author_formset,
            'chapter_form': chapter_form,
            'chapter_author_formset': chapter_author_formset,
            'conference_form': conference_form,
            'conference_author_formset': conference_author_formset,
            'thesis_form': thesis_form,
            'thesis_author_formset': thesis_author_formset,
            'unpublished_form': unpublished_form,
            'unpublished_author_formset': unpublished_author_formset,
            'literatureType':literatureType,
            'ispopup': ('_popup' in request.GET)}
        context=set_context_workspace(context, self.request)

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        literatureType=request.POST['literature_type']
        id = self.kwargs.get('pk', None)

        journal,book,chapter,conference,thesis,unpublished,journal_authors,book_authors,chapter_authors,\
        conference_authors,thesis_authors,unpublished_authors=self.get_instances(request,id,literatureType)

        journal_form = JournalForm(request.POST, instance=journal)
        book_form = BookForm(request.POST, instance=book)
        chapter_form = ChapterForm(request.POST, instance=chapter)
        conference_form = ConferenceForm(request.POST, instance=conference)
        thesis_form = ThesisForm(request.POST, instance=thesis)
        unpublished_form = UnpublishedForm(request.POST, instance=unpublished)

        journal_author_formset = LiteratureAuthorFormSet(queryset=journal_authors, prefix='journal_author')
        book_author_formset = LiteratureAuthorFormSet(queryset=book_authors, prefix='book_author')
        chapter_author_formset = LiteratureAuthorFormSet(queryset=chapter_authors, prefix='chapter_author')
        conference_author_formset = LiteratureAuthorFormSet(queryset=conference_authors, prefix='conference_author')
        thesis_author_formset = LiteratureAuthorFormSet(queryset=thesis_authors, prefix='thesis_author')
        unpublished_author_formset = LiteratureAuthorFormSet(queryset=unpublished_authors, prefix='unpublished_author')

        if literatureType=='journal':
            journal_author_formset = LiteratureAuthorFormSet(request.POST, queryset=journal_authors,
                prefix='journal_author')
            id=self.process_literature(request, 'journal', journal_form, journal_author_formset)
        elif literatureType=='book':
            book_author_formset = LiteratureAuthorFormSet(request.POST, queryset=book_authors,
                prefix='book_author')
            id=self.process_literature(request, 'book', book_form, book_author_formset)
        elif literatureType=='chapter':
            chapter_author_formset = LiteratureAuthorFormSet(request.POST, queryset=chapter_authors,
                prefix='chapter_author')
            id=self.process_literature(request, 'chapter', chapter_form, chapter_author_formset)
        elif literatureType=='conference':
            conference_author_formset = LiteratureAuthorFormSet(request.POST, queryset=conference_authors,
                prefix='conference_author')
            id=self.process_literature(request, 'conference', conference_form, conference_author_formset)
        elif literatureType=='thesis':
            thesis_author_formset = LiteratureAuthorFormSet(request.POST, queryset=thesis_authors,
                prefix='thesis_author')
            id=self.process_literature(request, 'thesis', thesis_form, thesis_author_formset)
        elif literatureType=='unpublished':
            unpublished_author_formset = LiteratureAuthorFormSet(request.POST, queryset=unpublished_authors,
                prefix='unpublished_author')
            id=self.process_literature(request, 'unpublished', unpublished_form, unpublished_author_formset)

        if id is not None:
            href='/bodb/literature/%d/?literatureType=%s' % (id,literatureType)
            if '_popup' in request.GET:
                href+='&_popup=%s' % request.GET['_popup']
            return HttpResponseRedirect(href)

        context={
            'helpPage': self.helpPage,
            'journal_form': journal_form,
            'journal_author_formset': journal_author_formset,
            'book_form': book_form,
            'book_author_formset': book_author_formset,
            'chapter_form': chapter_form,
            'chapter_author_formset': chapter_author_formset,
            'conference_form': conference_form,
            'conference_author_formset': conference_author_formset,
            'thesis_form': thesis_form,
            'thesis_author_formset': thesis_author_formset,
            'unpublished_form': unpublished_form,
            'unpublished_author_formset': unpublished_author_formset,
            'literatureType':literatureType
        }
        context=set_context_workspace(context, self.request)

        return render(request, self.template_name, context)


class CreateLiteratureView(EditLiteratureMixin,PermissionRequiredMixin,View):
    helpPage='insert_data.html#insert-literature'
    permission_required='bodb.add_literature'


class UpdateLiteratureView(EditLiteratureMixin,PermissionRequiredMixin,View):
    helpPage='insert_data.html#insert-literature'
    permission_required='bodb.change_literature'

    def get_instances(self,request,id,literatureType):
        # create new literature objects
        journal=Journal(collator=request.user)
        journal_authors=LiteratureAuthor.objects.none()
        book=Book(collator=request.user)
        book_authors=LiteratureAuthor.objects.none()
        chapter=Chapter(collator=request.user)
        chapter_authors=LiteratureAuthor.objects.none()
        conference=Conference(collator=request.user)
        conference_authors=LiteratureAuthor.objects.none()
        thesis=Thesis(collator=request.user)
        thesis_authors=LiteratureAuthor.objects.none()
        unpublished=Unpublished(collator=request.user)
        unpublished_authors=LiteratureAuthor.objects.none()

        # load Literature object
        if literatureType=='journal':
            journal=get_object_or_404(Journal.objects.select_related('collator').prefetch_related('authors__author'), id=id)
            journal_authors=journal.authors.all()
        elif literatureType=='book':
            book=get_object_or_404(Book.objects.select_related('collator').prefetch_related('authors__author'), id=id)
            book_authors=book.authors.all()
        elif literatureType=='chapter':
            chapter=get_object_or_404(Chapter.objects.select_related('collator').prefetch_related('authors__author'), id=id)
            chapter_authors=chapter.authors.all()
        elif literatureType=='conference':
            conference=get_object_or_404(Conference.objects.select_related('collator').prefetch_related('authors__author'), id=id)
            conference_authors=conference.authors.all()
        elif literatureType=='thesis':
            thesis=get_object_or_404(Thesis.objects.select_related('collator').prefetch_related('authors__author'), id=id)
            thesis_authors=thesis.authors.all()
        elif literatureType=='unpublished':
            unpublished=get_object_or_404(Unpublished.objects.select_related('collator').prefetch_related('authors__author'), id=id)
            unpublished_authors=unpublished.authors.all()

        return journal,book,chapter,conference,thesis,unpublished,journal_authors,book_authors,chapter_authors,\
               conference_authors,thesis_authors,unpublished_authors

class LiteraturePubmedView(View):

    def get(self, request, *args, **kwargs):
        literature=Literature.objects.filter(pubmed_id=self.kwargs.get('id', None))[0]
        return redirect(literature.get_absolute_url())


class LiteratureDetailView(TemplateView):
    template_name = 'bodb/literature/literature_view.html'

    def get_context_data(self, **kwargs):
        context=super(LiteratureDetailView,self).get_context_data(**kwargs)
        context=set_context_workspace(context, self.request)
        id = self.kwargs.get('pk', None)

        try:
            literature=Journal.objects.select_related('collator').prefetch_related('authors__author').get(id=id)
            literatureType='journal'
        except (Journal.DoesNotExist, Journal.MultipleObjectsReturned), err:
            try:
                literature=Book.objects.select_related('collator').prefetch_related('authors__author').get(id=id)
                literatureType='book'
            except (Book.DoesNotExist, Book.MultipleObjectsReturned), err:
                try:
                    literature=Chapter.objects.select_related('collator').prefetch_related('authors__author').get(id=id)
                    literatureType='chapter'
                except (Chapter.DoesNotExist, Chapter.MultipleObjectsReturned), err:
                    try:
                        literature=Conference.objects.select_related('collator').prefetch_related('authors__author').get(id=id)
                        literatureType='conference'
                    except (Conference.DoesNotExist, Conference.MultipleObjectsReturned), err:
                        try:
                            literature=Thesis.objects.select_related('collator').prefetch_related('authors__author').get(id=id)
                            literatureType='thesis'
                        except (Thesis.DoesNotExist, Thesis.MultipleObjectsReturned), err:
                            try:
                                literature=Unpublished.objects.select_related('collator').prefetch_related('authors__author').get(id=id)
                                literatureType='unpublished'
                            except (Unpublished.DoesNotExist, Unpublished.MultipleObjectsReturned), err:
                                literature=None
                                literatureType=''

        if literature is None:
            raise Http404
        brain_regions=BrainRegion.objects.filter(nomenclature__lit=literature).select_related('nomenclature','parent_region').prefetch_related('nomenclature__species').order_by('name')

        user=self.request.user
        context['helpPage']='view_entry.html'
        context['literature']=literature
        context['url']=literature.html_url_string()
        context['literatureType']=literatureType
        context['brain_regions']=BrainRegion.get_region_list(brain_regions,context['workspace_regions'],
            context['fav_regions'])
        context['ispopup']=('_popup' in self.request.GET)
        context['connectionGraphId']='connectivitySEDDiagram'
        context['erpGraphId']='erpSEDDiagram'
        context['bopGraphId']='bopRelationshipDiagram'
        context['modelGraphId']='modelRelationshipDiagram'

        models=Model.get_literature_models(literature, user)
        context['models']=Model.get_model_list(models, context['workspace_models'], context['fav_docs'],
            context['subscriptions'])
        context['model_seds']=Model.get_sed_map(models, user)

        bops=BOP.get_literature_bops(literature, user)
        context['bops']=BOP.get_bop_list(bops, context['workspace_bops'], context['fav_docs'], context['subscriptions'])
        context['bop_relationships']=BOP.get_bop_relationships(bops, user)

        generic_seds=SED.get_literature_seds(literature, user)
        context['generic_seds']=SED.get_sed_list(generic_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])

        imaging_seds=BrainImagingSED.get_literature_seds(literature, user)
        coords=[SEDCoord.objects.filter(sed=sed).select_related('coord') for sed in imaging_seds]
        context['imaging_seds']=SED.get_sed_list(imaging_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        if user.is_authenticated() and not user.is_anonymous():
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords,
                context['selected_sed_coords'].values_list('sed_coordinate__id',flat=True))
        else:
            context['imaging_seds']=BrainImagingSED.augment_sed_list(context['imaging_seds'],coords, [])

        conn_seds=ConnectivitySED.get_literature_seds(literature,user)
        context['connectivity_seds']=SED.get_sed_list(conn_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['connectivity_sed_regions']=ConnectivitySED.get_region_map(conn_seds)

        erp_seds=ERPSED.get_literature_seds(literature, user)
        components=[ERPComponent.objects.filter(erp_sed=erp_sed).select_related('electrode_cap','electrode_position__position_system') for erp_sed in erp_seds]
        context['erp_seds']=SED.get_sed_list(erp_seds, context['workspace_seds'], context['fav_docs'],
            context['subscriptions'])
        context['erp_seds']=ERPSED.augment_sed_list(context['erp_seds'],components)

        context['is_favorite']=literature.id in context['fav_lit']
        context['subscribed_to_collator']=(literature.collator.id,'All') in context['subscriptions']
        context['selected']=literature.id in context['workspace_literature']

        return context


class DeleteLiteratureView(PermissionRequiredMixin,DeleteView):
    model=Literature
    success_url = '/bodb/index.html'
    permission_required = 'bodb.delete_literature'


class ExportLiteratureView(JSONResponseMixin, BaseUpdateView):
    model=Literature

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            # get list of ids
            ids=self.request.POST.getlist('ids[]')
            # get export format
            format = self.request.POST['format']
            # export references
            file_name='literature-%s.%s' % (self.request.user.username,format)
            path=os.path.join(settings.MEDIA_ROOT, 'export', file_name)
            reference_export(format, Literature.objects.filter(id__in=ids), path)
            context={
                'file_name':file_name
            }
        return context


class ToggleSelectLiteratureView(LoginRequiredMixin,JSONResponseMixin,BaseUpdateView):
    model = Literature

    def get_context_data(self, **kwargs):
        context={'msg':u'No POST data sent.' }
        if self.request.is_ajax():
            lit=Literature.objects.get(id=self.kwargs.get('pk', None))

            active_workspace=get_active_workspace(get_profile(self.request),self.request)

            context={
                'literature_id':lit.id,
                'workspace': active_workspace.title
            }

            activity=WorkspaceActivityItem(workspace=active_workspace, user=self.request.user)
            remove=False
            if 'select' in self.request.POST:
                remove=self.request.POST['select']=='false'
            else:
                remove=lit in active_workspace.related_literature.all()
            if remove:
                active_workspace.related_literature.remove(lit)
                context['selected']=False
                activity.text='%s removed the literature: <a href="%s">%s</a> from the workspace' % \
                              (self.request.user.username, lit.get_absolute_url(), lit.__unicode__())
            else:
                active_workspace.related_literature.add(lit)
                context['selected']=True
                activity.text='%s added the literature: <a href="%s">%s</a> to the workspace' % \
                              (self.request.user.username, lit.get_absolute_url(), lit.__unicode__())
            activity.save()
            active_workspace.save()
            cache.set('%d.active_workspace' % self.request.user.id, active_workspace)

        return context


def exportPubmedResources():
    objList=''
    pubmed_ids=[]
    for literature in Literature.objects.all().exclude(pubmed_id=''):
        related_brain_regions=BrainRegion.objects.filter(nomenclature__lit=literature)
        related_bops=BOP.objects.filter(literature=literature,public=1)
        related_models=Model.objects.filter(literature=literature,public=1)
        related_seds=SED.objects.filter(literature=literature,public=1)
        if related_brain_regions or related_bops or related_models or related_seds:
            if not literature.pubmed_id in pubmed_ids:
                pubmed_ids.append(literature.pubmed_id)
    for pubmed_id in pubmed_ids:
        objList+='<ObjId>'+pubmed_id+'</ObjId>\n'
    str=render_to_string('pubmed/pubmed_bodb_resources.xml',{'objList': objList})
    FILE=open(settings.MEDIA_ROOT+'/pubmed/resources.xml','w')
    FILE.write(str)
    FILE.close()

