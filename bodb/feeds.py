from django.contrib.syndication.views import Feed
from bodb.models import Model, BOP, SED, SSR

class LatestModels(Feed):
    """
    Lists the five most recently added Models
    """
    title = "BODB newest models"
    link = "/model/"
    description = "Updates on the latest models added to BODB"

    def items(self):
        return Model.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.brief_description


class LatestBOPs(Feed):
    """
    Lists the five most recently aded BOPs
    """
    title = "BODB newest BOPs"
    link = "/bop/"
    description = "Updates on the latest brain operating principles added to BODB"

    def items(self):
        return BOP.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.brief_description


class LatestSEDs(Feed):
    """
    Lists the five most recently added SEDs
    """
    title = "BODB newest SEDs"
    link = "/sed/"
    description = "Updates on the latest summaries of experimental data added to BODB"

    def items(self):
        return SED.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.brief_description


class LatestSSRs(Feed):
    """
    Lists the five most recently added SSRs
    """
    title = "BODB newest SSRs"
    link = "/ssr/"
    description = "Updates on the latest summaries of simulation results added to BODB"

    def items(self):
        return SSR.objects.filter(draft=0, public=1).order_by('-creation_time')[:5]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.brief_description