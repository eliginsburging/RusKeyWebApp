from django.contrib import admin
from .models import Verb, Example, PerformancePerExample

# Register your models here.
admin.site.register(Verb)
admin.site.register(Example)
admin.site.register(PerformancePerExample)
