import os
import json
from datetime import datetime
from django.db import transaction
from heatmaps.models import Heatmap
from users.models import Farm