from django.contrib import admin
# from .models import Rolka, Tkanina, Dziennik, WpisySzwalnia, Log, WpisyMagazyn,ErrorLog
from .models import *

class LogAdmin(admin.ModelAdmin):
    search_fields = ['rolka_id', 'typ', 'dziennik_nr']

class ErrorLogAdmin(admin.ModelAdmin):
    search_fields = ['rolka_id', 'typ']

class PaczkiAdmin(admin.ModelAdmin):
    search_fields = ['dziennik__nr', 'karta', 'pozycja']

class WpisySzwalniaAdmin(admin.ModelAdmin):
    search_fields = ['dziennik__nr', 'tkanina__nazwa', 'TA']

class RolkaAdmin(admin.ModelAdmin):
	search_fields = ['pk', 'barcode', 'tkanina__nazwa', 'dostawca', 'nr_zamowienia']
class Rolka_usunietaAdmin(admin.ModelAdmin):
	search_fields = ['pk', 'barcode']

class Rolka_zliczanaAdmin(admin.ModelAdmin):
	search_fields = ['pk', 'barcode']

class DziennikAdmin(admin.ModelAdmin):
	search_fields = ['nr', 'data']

class TkaninaAdmin(admin.ModelAdmin):
	search_fields = ['nazwa']
class FgkCommentAdmin(admin.ModelAdmin):
	search_fields = ['job_name']
class FgkLineAdmin(admin.ModelAdmin):
	search_fields = ['job_name']
# Register your models here.
admin.site.register(Dziennik, DziennikAdmin)
admin.site.register(Tkanina,TkaninaAdmin)
admin.site.register(Rolka, RolkaAdmin)
admin.site.register(Odpad)
admin.site.register(Paczki, PaczkiAdmin)
admin.site.register(WpisySzwalnia, WpisySzwalniaAdmin)
admin.site.register(WpisyMagazyn)
admin.site.register(WpisyMagazynPowiazania)
admin.site.register(Log, LogAdmin)
admin.site.register(ErrorLog, ErrorLogAdmin)
admin.site.register(Rolka_usunieta, Rolka_usunietaAdmin)
admin.site.register(Rolka_zliczana, Rolka_zliczanaAdmin)
admin.site.register( FgkComment, FgkCommentAdmin)
admin.site.register( FgkLine, FgkLineAdmin)

