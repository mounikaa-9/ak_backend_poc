from django.core.management.base import BaseCommand
from heatmaps.utils import save_heatmaps_from_response
import json

class Command(BaseCommand):
    help = "Saves heatmaps from satellite response"

    def add_arguments(self, parser):
        parser.add_argument('json_path', type=str)

    def handle(self, *args, **options):
        json_path = options['json_path']
        with open(json_path) as f:
            field_data = json.load(f)
        save_heatmaps_from_response(field_data)
