from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.core.mail import send_mail
from bodb.models import Model, BOP, SED, SSR
from datetime import date, timedelta, datetime

class Command(BaseCommand):
    
    def handle(self, *args, **options):
                
        message = "this is a very, very basic newsletter for new entries that will provide full urls when run from the server.\n"
        message += "clearly it needs more love.\n"
        
        #bops = BOP.objects.filter(draft=0, public=1, creation_time__gte=datetime.now()-timedelta(days=30)).order_by('-creation_time')[:5]
        bops = BOP.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]
        message += "new BOPs\n"
        for bop in bops:
            message += bop.get_absolute_url() + '\n'
            
        models = Model.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]
        message += "\nnew Models\n"
        for model in models:
            message += model.get_absolute_url() + '\n'
            
        seds = SED.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]
        message += "\nnew SEDs\n"
        for sed in seds:
            message += sed.get_absolute_url() + '\n'
            
        ssrs = SSR.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]
        message += "\nnew SSRs\n"
        for ssr in ssrs:
            message += ssr.get_absolute_url() + '\n'
        
        send_mail("new entries", message, settings.DEFAULT_FROM_EMAIL, ['mwinter@unboundedpress.org, jbonaiuto@gmail.com, arbib@usc.edu'])
