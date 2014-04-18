from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.mail import send_mail
from bodb.models import Model, BOP, SED, SSR
from datetime import date, timedelta, datetime
from django.contrib.auth.models import User, Permission

class Command(BaseCommand):
    
    def handle(self, *args, **options):
        
        how_many_days = datetime.now()-timedelta(days=int(args[0]))
                
        message = "this is a list of the new entries created in the past " + args[0] + " days .\n"
        
        #bops = BOP.objects.filter(draft=0, public=1, creation_time__gte=datetime.now()-timedelta(days=14)).order_by('-creation_time')
        bops = BOP.objects.filter(creation_time__gte=how_many_days, draft=0, public=1).order_by('-creation_time')
        message += "New BOPs\n\n"
        for bop in bops:
            message += bop.title + ' (' + settings.URL_BASE + bop.get_absolute_url() + ')\n'
            message += bop.get_collator_str() + '\n'
            message += bop.brief_description + '\n\n'
            
        #models = Model.objects.filter(draft=0, public=1, creation_time__gte=datetime.now()-timedelta(days=14)).order_by('-creation_time')
        models = Model.objects.filter(creation_time__gte=how_many_days, draft=0, public=1).order_by('-creation_time')
        message += "\nNew Models\n\n"
        for model in models:
            message += model.title + ' (' + settings.URL_BASE + model.get_absolute_url() + ')\n'
            message += model.get_collator_str() + '\n'
            message += model.brief_description + '\n\n'
            
        #seds = SED.objects.filter(draft=0, public=1, creation_time__gte=datetime.now()-timedelta(days=14)).order_by('-creation_time')
        seds = SED.objects.filter(creation_time__gte=how_many_days, draft=0, public=1).order_by('-creation_time')
        message += "\nNew SEDs\n\n"
        for sed in seds:
            message += sed.title + ' (' + settings.URL_BASE + sed.get_absolute_url() + ')\n'
            message += sed.get_collator_str() + '\n'
            message += sed.brief_description + '\n\n'
            
        #ssrs = SSR.objects.filter(draft=0, public=1, creation_time__gte=datetime.now()-timedelta(days=14)).order_by('-creation_time')
        ssrs = SSR.objects.filter(creation_time__gte=how_many_days, draft=0, public=1).order_by('-creation_time')
        message += "\nNew SSRs\n\n"
        for ssr in ssrs:
            message += ssr.title + ' (' + settings.URL_BASE + ssr.get_absolute_url() + ')\n'
            message += ssr.get_collator_str() + '\n'
            message += ssr.brief_description + '\n\n'
        
        superusers=User.objects.filter(is_superuser=True)
        
        send_mail("new entries", message, settings.DEFAULT_FROM_EMAIL, [u.email for u in superusers])
