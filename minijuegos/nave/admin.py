from django import forms
from django.contrib import admin

from .models import AnomaliaAmbigua, NaveEspacial, OpcionMetrica, Requerimiento


class OpcionMetricaInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        total = 0
        correctas = 0
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE', False):
                continue
            texto = form.cleaned_data.get('texto')
            if texto:
                total += 1
                if form.cleaned_data.get('es_correcta'):
                    correctas += 1

        if total > 0:
            if total < 2:
                raise forms.ValidationError("Cada anomalía debe tener al menos 2 opciones de métrica.")
            if correctas != 1:
                raise forms.ValidationError("Cada anomalía debe tener exactamente una opción correcta.")


class OpcionMetricaInline(admin.TabularInline):
    model = OpcionMetrica
    formset = OpcionMetricaInlineFormSet
    extra = 3
    min_num = 2


class RequerimientoInline(admin.TabularInline):
    model = Requerimiento
    extra = 2


class AnomaliaAmbiguaInline(admin.StackedInline):
    model = AnomaliaAmbigua
    extra = 1


@admin.register(NaveEspacial)
class NaveEspacialAdmin(admin.ModelAdmin):
    list_display = ('actividad', 'total_requerimientos', 'total_anomalias')
    inlines = [RequerimientoInline, AnomaliaAmbiguaInline]

    def total_requerimientos(self, obj):
        return obj.requerimientos.count()
    total_requerimientos.short_description = 'Requerimientos'

    def total_anomalias(self, obj):
        return obj.anomalias.count()
    total_anomalias.short_description = 'Anomalías'


@admin.register(Requerimiento)
class RequerimientoAdmin(admin.ModelAdmin):
    list_display = ('texto', 'tipo', 'nave_espacial')
    list_filter = ('tipo', 'nave_espacial')
    search_fields = ('texto', 'explicacion')


@admin.register(AnomaliaAmbigua)
class AnomaliaAmbiguaAdmin(admin.ModelAdmin):
    list_display = ('texto_ambiguo', 'tiempo_limite_seg', 'nave_espacial')
    list_filter = ('nave_espacial',)
    search_fields = ('texto_ambiguo', 'explicacion')
    inlines = [OpcionMetricaInline]


@admin.register(OpcionMetrica)
class OpcionMetricaAdmin(admin.ModelAdmin):
    list_display = ('texto', 'es_correcta', 'anomalia')
    list_filter = ('es_correcta', 'anomalia')
    search_fields = ('texto',)
