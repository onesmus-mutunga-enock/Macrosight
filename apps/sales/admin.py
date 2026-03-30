from django.contrib import admin
from django.db import models as _db_models
from . import models as _models

for attr in dir(_models):
    obj = getattr(_models, attr)
    try:
        if isinstance(obj, type) and issubclass(obj, _db_models.Model):
            admin.site.register(obj)
    except Exception:
        pass
