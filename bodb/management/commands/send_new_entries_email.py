from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.mail import send_mail
from bodb.models import Model, BOP, SED, SSR
from datetime import date, timedelta, datetime

class Command(BaseCommand):
    
    def handle(self, *args, **options):
                
        message = "this is a very, very basic newsletter for new entries that will provide full urls when run from the server.\n"
        message += "clearly it needs more love.\n"
        
        #bops = BOP.objects.filter(draft=0, public=1, creation_time__gte=datetime.now()-timedelta(days=14)).order_by('-creation_time')
        bops = BOP.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]
        message += "New BOPs\n\n"
        for bop in bops:
            message += bop.title + ' (' + settings.URL_BASE + bop.get_absolute_url() + ')\n'
            message += bop.get_collator_str() + '\n'
            message += bop.brief_description + '\n\n'
            
        #models = Model.objects.filter(draft=0, public=1, creation_time__gte=datetime.now()-timedelta(days=14)).order_by('-creation_time')
        models = Model.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]
        message += "\nNew Models\n\n"
        for model in models:
            message += model.title + ' (' + settings.URL_BASE + model.get_absolute_url() + ')\n'
            message += model.get_collator_str() + '\n'
            message += model.brief_description + '\n\n'
            
        #seds = SED.objects.filter(draft=0, public=1, creation_time__gte=datetime.now()-timedelta(days=14)).order_by('-creation_time')
        seds = SED.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]
        message += "\nNew SEDs\n\n"
        for sed in seds:
            message += sed.title + ' (' + settings.URL_BASE + sed.get_absolute_url() + ')\n'
            message += sed.get_collator_str() + '\n'
            message += sed.brief_description + '\n\n'
            
        #ssrs = SSR.objects.filter(draft=0, public=1, creation_time__gte=datetime.now()-timedelta(days=14)).order_by('-creation_time')
        ssrs = SSR.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]
        message += "\nNew SSRs\n\n"
        for ssr in ssrs:
            message += ssr.title + ' (' + settings.URL_BASE + ssr.get_absolute_url() + ')\n'
            message += ssr.get_collator_str() + '\n'
            message += ssr.brief_description + '\n\n'
        
        send_mail("new entries", message, settings.DEFAULT_FROM_EMAIL, ['mwinter@unboundedpress.org'])
