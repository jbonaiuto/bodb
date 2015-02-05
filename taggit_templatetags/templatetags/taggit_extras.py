from django import template
from django.db import models
from django.db.models import Count, Q
from django.core.exceptions import FieldError
import math
import bodb
from bodb.models import Document
from registration.models import User

from templatetag_sugar.register import tag
from templatetag_sugar.parser import Name, Variable, Constant, Optional, Model

from taggit import VERSION as TAGGIT_VERSION
from taggit.managers import TaggableManager
from taggit.models import TaggedItem, Tag
from taggit_templatetags import settings

T_MAX = getattr(settings, 'TAGCLOUD_MAX', 24.0)
T_MIN = getattr(settings, 'TAGCLOUD_MIN', 10.0)

register = template.Library()

def get_queryset(user, forvar=None):
    if None == forvar:
        # get all tags
        queryset = Tag.objects.all()
    else:
        # extract app label and model name
        beginning, applabel, model = None, None, None
        try:
            beginning, applabel, model = forvar.rsplit('.', 2)
        except ValueError:
            try:
                applabel, model = forvar.rsplit('.', 1)
            except ValueError:
                applabel = forvar


        security_q=Q(public=True)
        if isinstance(user,User):
            security_q=Document.get_security_q(user)

        # filter tagged items
        if applabel:
            queryset = TaggedItem.objects.filter(content_type__app_label=applabel.lower())
        if model:
            queryset = queryset.filter(content_type__model=model.lower())
        if len(security_q):
            queryset=queryset.filter(object_id__in=Document.objects.filter(security_q).values_list('id',flat=True))

        # get tags
        tag_ids = queryset.values_list('tag_id', flat=True)
        queryset = Tag.objects.filter(id__in=tag_ids).distinct()

    # Retain compatibility with older versions of Django taggit
    # a version check (for example taggit.VERSION <= (0,8,0)) does NOT
    # work because of the version (0,8,0) of the current dev version of django-taggit
    try:
        result=[]
        for tag in queryset:
            q=Q(Q(tags__name__iexact=tag.name) & security_q)
            if model=='Model':
                tag.num_times=bodb.models.Model.objects.filter(q).count()
            elif model=='BOP':
                tag.num_times=bodb.models.BOP.objects.filter(q).count()
            elif model=='SED':
                tag.num_times=bodb.models.SED.objects.filter(q).count()
            elif model=='SSR':
                tag.num_times=bodb.models.SSR.objects.filter(q).count()
            elif model=='Prediction':
                tag.num_times=bodb.models.Prediction.objects.filter(q).count()
            result.append(tag)
        return result
    except FieldError:
        result=[]
        for tag in queryset:
            q=Q(Q(tags__name__iexact=tag.name) & security_q)
            if model=='Model':
                tag.num_times=bodb.models.Model.objects.filter(q).count()
            elif model=='BOP':
                tag.num_times=bodb.models.BOP.objects.filter(q).count()
            elif model=='SED':
                tag.num_times=bodb.models.SED.objects.filter(q).count()
            elif model=='SSR':
                tag.num_times=bodb.models.SSR.objects.filter(q).count()
            elif model=='Prediction':
                tag.num_times=bodb.models.Prediction.objects.filter(q).count()
            result.append(tag)
        return result
        #return queryset.annotate(num_times=Count('taggit_taggeditem_items'))

def _calculate_thresholds(min_weight, max_weight, steps):
    delta = (max_weight - min_weight) / float(steps)
    return [min_weight + i * delta for i in range(1, steps + 1)]

def _calculate_tag_weight(weight, max_weight):
    """
    Logarithmic tag weight calculation is based on code from the
    `Tag Cloud`_ plugin for Mephisto, by Sven Fuchs.

    .. _`Tag Cloud`: http://www.artweb-design.de/projects/mephisto-plugin-tag-cloud
    """
    if max_weight == 1:
        return weight
    else:
        return math.log(weight) * max_weight / math.log(max_weight)

def get_weight_fun(t_min, t_max, f_min, f_max):
#    def weight_fun(f_i, t_min=t_min, t_max=t_max, f_min=f_min, f_max=f_max):
#        # Prevent a division by zero here, found to occur under some
#        # pathological but nevertheless actually occurring circumstances.
#        if f_max == f_min:
#            mult_fac = 1.0
#        else:
#            mult_fac = float(t_max-t_min)/float(f_max-f_min)
#
#        return t_max - (f_max-f_i)*mult_fac
    def weight_fun(tag_count, t_min=t_min, t_max=t_max, min_weight=f_min, max_weight=f_max):
        steps=int(t_max-t_min)
        delta = (t_max - t_min) / float(steps)
        thresholds = _calculate_thresholds(min_weight, max_weight, steps)
        font_set = False
        tag_weight = _calculate_tag_weight(tag_count, max_weight)
        font_size=t_min
        for i in range(steps):
            if not font_set and tag_weight <= thresholds[i]:
                font_size = t_min+i*delta
                font_set = True
        return font_size
    return weight_fun

@tag(register, [Constant('as'), Name(), Optional([Constant('for'), Variable()])])
def get_taglist(context, asvar, forvar=None):
    queryset = get_queryset(forvar)         
    queryset = queryset.order_by('-num_times')        
    context[asvar] = queryset
    return ''

@tag(register, [Constant('as'), Name(), Variable(), Optional([Constant('for'), Variable()])])
def get_tagcloud(context, asvar, user, forvar=None):
    result = get_queryset(user, forvar)
    num_times=[x.num_times for x in result]
    zipped=zip(result,num_times)
    sorted_zipped=sorted(zipped, key=lambda t:t[1])
    filtered_zipped=sorted_zipped[-25:][:]
    filtered_results=[x[0] for x in filtered_zipped]
    filtered_num_times=[x[1] for x in filtered_zipped]
    #num_times = queryset.values_list('num_times', flat=True)
    if(len(filtered_num_times) == 0):
        #context[asvar] = queryset
        context[asvar] = filtered_results
        return ''
    weight_fun = get_weight_fun(10, 28, min(filtered_num_times), max(filtered_num_times))
    #queryset = queryset.order_by('name')
    filtered_results.sort(key=lambda x:x.name)
    tags=[]
    #for tag in queryset:
    for tag in filtered_results:
        weight=weight_fun(tag.num_times)
        #if weight>=8:
        tag.weight =weight
        tags.append(tag)
    context[asvar] = tags
    return ''
    
def include_tagcloud(forvar=None):
    return {'forvar': forvar}

def include_taglist(forvar=None):
    return {'forvar': forvar}
  
register.inclusion_tag('taggit_templatetags/taglist_include.html')(include_taglist)
register.inclusion_tag('taggit_templatetags/tagcloud_include.html')(include_tagcloud)
