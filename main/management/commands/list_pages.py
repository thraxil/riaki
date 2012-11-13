from django.core.management.base import BaseCommand
from main.models import get_page


class Command(BaseCommand):
    args = ''
    help = ''

    def handle(self, *args, **options):
        page = get_page("index")
        for link in page._page.get_links():
            if link.get_bucket() == 'riakitag':
                print link.get().get_data()
