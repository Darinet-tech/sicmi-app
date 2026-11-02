from django.contrib import admin
from .models import PlanAnual, AccionPlan, TareaTecnica, Croquis, PlanFirma, HistorialPlan


class AccionInline(admin.TabularInline):
    model = AccionPlan
    extra = 0


@admin.register(PlanAnual)
class PlanAnualAdmin(admin.ModelAdmin):
    list_display = ('anio', 'uo', 'estado')
    list_filter = ('uo', 'estado')
    inlines = [AccionInline]


admin.site.register(TareaTecnica)
admin.site.register(Croquis)
admin.site.register(PlanFirma)
admin.site.register(HistorialPlan)