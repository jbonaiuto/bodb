from django import template
from django.db import models
from django.db.models import Count, Q
from django.core.exceptions import FieldError
import math
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


        q=Q()
        if isinstance(user,User) and user.is_authenticated() and not user.is_anonymous():
            if not user.is_superuser:
                own_entry_q=Q(collator__id=user.id)
                public_q=Q(public=1)
                group_q=Q(Q(draft=0) & Q(collator__groups__in=list(user.groups.all())))
                q=own_entry_q | public_q | group_q
        else:
            q=Q(public=1)

        # filter tagged items        
        if applabel:
            queryset = TaggedItem.objects.filter(content_type__app_label=applabel.lower())
        if model:
            queryset = queryset.filter(content_type__model=model.lower())
        if len(q):
            queryset=queryset.filter(object_id__in=Document.objects.filter(q).values_list('id',flat=True))

        # get tags
        tag_ids = queryset.values_list('tag_id', flat=True)
        queryset = Tag.objects.filter(id__in=tag_ids)

    # Retain compatibility with older versions of Django taggit
    # a version check (for example taggit.VERSION <= (0,8,0)) does NOT
    # work because of the version (0,8,0) of the current dev version of django-taggit
    try:
        return queryset.annotate(num_times=Count('taggeditem_items'))
    except FieldError:
        return queryset.annotate(num_times=Count('taggit_taggeditem_items'))

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
    queryset = get_queryset(user, forvar)
    num_times = queryset.values_list('num_times', flat=True)
    if(len(num_times) == 0):
        context[asvar] = queryset
        return ''
    weight_fun = get_weight_fun(2, 24, min(num_times), max(num_times))
    queryset = queryset.order_by('name')
    tags=[]
    for tag in queryset:
        weight=weight_fun(tag.num_times)
        if weight>=8:
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
