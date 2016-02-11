import ftplib
from django.core.mail import send_mail
from django.core.management import BaseCommand
from bodb.views.literature import exportPubmedResources
from uscbp import settings

class Command(BaseCommand):

    def handle(self, *args, **options):
        exportPubmedResources()
        session = ftplib.FTP('ftp-private.ncbi.nlm.nih.gov','bodb',settings.LINKOUT_PASSWORD)
        file = open(settings.MEDIA_ROOT+'/pubmed/resources.xml','rb')                  # file to send
        session.storbinary('STOR holdings/resources.xml', file)     # send the file
        file.close()                                    # close file and FTP
        session.quit()

        message='The resources file for the BODB database have been updated'
        send_mail("New resources file", message, settings.EMAIL_HOST_USER, ['linkout@ncbi.nlm.nih.gov'])
