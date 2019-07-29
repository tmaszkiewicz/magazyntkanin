"""TKANINY URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from . import views
from django.contrib.auth import views as auth_views
from django.conf.urls import url, include
# APP_NAME = 'magazyntkanin'

urlpatterns = [
    # url(r'^magazyn/(?P<dziennik>[0-9]+)/(?P<typ>[a-z]+)/$', views.podaj_dzienniki, name='podaj_dzienniki'),
    # url(r'^test/$', views.test, name='test'),
    url(r'^$', views.index, name='index'),
    url('accounts/', include('django.contrib.auth.urls')),
    url(r'^login/$', views.user_login, name='login'),
    url(r'^l_check/(?P<nr_rolki>[0-9]+)/$', views.l_check, name='l_check'),
    url(r'^test/ulotka$', views.ulotka, name='ulotka'),
    url(r'^test/obiegowka_full/(?P<nr_rolki>[0-9]+)$', views.obiegowka_full, name='obiegowka_full'),    
    url(r'^test/obiegowka/(?P<nr_rolki>[0-9]+)/$', views.obiegowka, name='obiegowka'),
    url(r'^magazyn/szablon/$', views.szablon_a4, name='szablon_a4'),
    url(r'^drukuj/$', views.drukuj_etykiety, name='drukuj_etykiety'),
    url(r'^drukuj/(?P<nr_rolki>[0-9]+)/$', views.drukuj_etykiete, name='drukuj_etykiete'),
    url(r'^dzienniki/$', views.wyszukaj_dziennik, name='wyszukaj_dziennik'),
    url(r'^dzienniki/(?P<dzial>[a-z]+)/(?P<dziennik>[0-9]+)/$', views.Wyswietl_dziennik, name='wyswietl_dziennik'),
    url(r'^edytuj/(?P<nr_rolki>[0-9]+)/$', views.edytuj_rolke, name='edytuj_rolke'),
    # url(r'^edytuj/(?P<nr_rolki>[0-9]+)/all/$', views.edytuj_rolke, name='edytuj_rolke'),
    url(r'^edytuj/krojownia/(?P<nr_rolki>[0-9]+)/(?P<user>.+)/$', views.edytuj_rolke_, name='edytuj_rolke'),
    url(r'^edytuj/krojownia/(?P<nr_rolki>[0-9]+)/all/$', views.edytuj_rolke, name='edytuj_rolke'),
    url(r'^import_pdf/$', views.import_pdf, name='import_pdf'),
    url(r'^import_t/$', views.import_tkanin, name='import_tkaniny'),
    url(r'^import_z/$', views.import_zamowienia, name='import_zamowienia'),
    url(r'^import_zdown/$', views.import_zamowienia_pobierz, name='import_zamowienia_pobierz'),
    url(r'^krojownia/$', views.krojownia_index, name='krojownia_index'),
    url(r'^krojownia/raporty/$', views.krojownia_raport, name='krojownia_raport'),
    url(r'^krojownia/dziennik/$', views.krojownia_status, name='krojownia_status'),
    # url(r'^krojownia/dzienniki/$', views.krojownia_dzienniki_widok, name='krojownia_dzienniki_widok'),
    url(r'^krojownia/paczki/$', views.krojownia_paczki, name='krojownia_paczki'),
    url(r'^krojownia/obiegowki/$', views.krojownia_obiegowki, name='krojownia_obiegowki'),
    url(r'^krojownia/status/$', views.krojownia_status, name='krojownia_status'),
    url(r'^krojownia/edytuj/$', views.krojowania_edycja, name='krojowania_edycja'),
    url(r'^krojownia/status/(?P<nr_dziennika>[0-9]+)/$', views.status_dziennika, name='status_dziennika'),
    url(r'^magazyn/$', views.magazyn_index, name='magazyn_index'),
    url(r'^magazyn/dziennik/$', views.podaj_dzienniki, name='podaj_dzienniki'),
    url(r'^magazyn/generator/$', views.generator_etykiet, name='generator'),
    url(r'^magazyn/raporty/$', views.raporty, name='raport'),
    url(r'^magazyn/sap_generator/(?P<nr_dziennika>[0-9]+)$', views.sap_generator, name='sap_generator'),
    url(r'^magazyn/raporty/zamowienia/(?P<zamowienie>.+)/$', views.raporty_zamowienie, name='raporty_zamowienie'),
    url(r'^magazyn/raporty_a/(?P<dziennik>[0-9]+)/$', views.raport_a, name='raport_a'),
    url(r'^magazyn/stan/$', views.stan_magazynowy, name='stan_magazynowy'),
    url(r'^magazyn/tkaniny/$', views.tkaniny, name='tkaniny'),
    url(r'^magazyn/inwentura/$', views.magazyn_inwentura, name='inwentura'),
    url(r'^magazyn/inwentura_g/$', views.magazyn_inwentura_grupowana, name='inwentura_g'),
    url(r'^magazyn/inwentura_r/$', views.magazyn_inwentura_rep, name='inwentura_r'),
    url(r'^magazyn/inwentura_c/$', views.czysc_po_inw, name='inwentura_c'),
    url(r'^magazyn/sprzedaz_r/$', views.magazyn_sprzedaz_rep, name='sprzedaz_rep'),
    url(r'^magazyn/inwentura_usun/$', views.inw_do_usuniecia, name='inwentura_usun'),
    url(r'^magazyn/zerowe_do_usuniecia/$', views.zerowe_do_usuniecia, name='zerowe_do_usuniecia'),
    url(r'^magazyn/do_usuniecia/$', views.do_usuniecia, name='do_usuniecia'),
    url(r'^magazyn/inwentura_usun_finalnie/$', views.inw_usuwamy, name='inwentura_usun_finalnie'),
    url(r'^magazyn/archiwizuj_inwenture/$', views.archiwizuj_inwenture, name='archiwizuj_inwenture'),
    url(r'^magazyn/inw_pdf/$', views.raport_inw, name='inw_pdf'),
    url(r'^planowanie/$', views.panel_planowania, name='panel_planowania'),
    url(r'^planowanie/ajax/$', views.planowanie_ajax, name='planowanie_ajax'),
    url(r'^planowanie/drukowanie/$', views.Wyswietl_dziennik_planowanie, name='Wyswietl_dziennik_planowanie'),
    url(r'^poka/$', views.poka, name='poka'),
    url(r'^magazyn/statystyki/rolka/(?P<rolka>[0-9]+)/$', views.statystyki_rolka, name='statystyki_rolka'),
    url(r'^magazyn/statystyki/tkanina/(?P<tkanina>[0-9]+)/$', views.statystyki_tkanina, name='statystyki_tkanina'),
    url(r'^krojownia/statystyki/rolka/(?P<rolka>[0-9]+)/$', views.statystyki_rolka, name='statystyki_rolka'),
    url(r'^krojownia/statystyki/tkanina/(?P<tkanina>[0-9]+)/$', views.statystyki_tkanina, name='statystyki_tkanina'),
    # url(r'^(?P<dzial>[a-z]+)/statystyki/rolka/(?P<rolka>[0-9]+)/$', views.statystyki_rolka, name='statystyki_rolka'),
    # url(r'^(?P<dzial>[a-z]+)/statystyki/tkanina/(?P<tkanina>[0-9]+)/$', views.statystyki_tkanina, name='statystyki_tkanina'),
    url(r'^scanner/dodanie_dziennika/$', views.dodanie_dziennika, name='dodanie_dziennika'),
    url(r'^scanner/drukuj_barcode/$', views.drukuj_barcode, name='drukuj_barcode'),
    url(r'^scanner/dziennik/$', views.sprawdz_dziennik, name='sprawdz_dziennik'),
    url(r'^scanner/edytuj/$', views.edytuj, name='s_edytuj'),
    url(r'^scanner/inwentura/$', views.inwentura, name='s_inwentura'),
    url(r'^scanner/info/$', views.informacje, name='informacje'),
    url(r'^scanner/infov2/$', views.informacje_v2, name='informacje_v2'),
    url(r'^scanner/infotm/$', views.informacje_tm_test, name='informacje_tm_test'),
    url(r'^scanner/nesting/$', views.nesting, name='nesting'),
    url(r'^scanner/nl/$', views.nl, name='nl'),
    url(r'^scanner/nowa_rolka/$', views.nowa_rolka, name='nowa_rolka'),
    url(r'^scanner/odpad/$', views.odpad, name='odpad'),
    url(r'^scanner/sprawdz_wpis/$', views.sprawdz_wpis, name='sprawdz_wpis'),
    url(r'^scanner/stoff/$', views.stoff, name='stoff'),
    url(r'^scanner/wpis/$', views.wpis, name='wpis'),
    url(r'^scanner/wpis_k/$', views.wpis_k, name='wpis_k'),
    url(r'^scanner/wycofanie_dziennika/$', views.wycofanie_dziennika, name='wycofanie_dziennika'),
    url(r'^scanner/wydanie_magazyn/$', views.przekaz_tkanine, name='przekaz_tkanine'),
    url(r'^scanner/wymianka/$', views.wymianka, name='wymianka'),
    url(r'^scanner/znajdz_barcode/$', views.znajdz_barcode, name='znajdz_barcode'),
    url(r'^scanner/znajdz_bar_dziennik/$', views.znajdz_bar_dziennik, name='znajdz_bar_dziennik'),
    url(r'^scanner/zwrot_magazyn/$', views.odbierz_tkanine, name='odbierz_tkanine'),
    url(r'^scanner/log/$', views.log_info, name='log_info'),
    url(r'^scanner/log_full/$', views.log_info_full, name='log_info_full'),
    url(r'^magazyn/tkaniny/(?P<nr_tkaniny>[0-9]+)/$', views.tkaniny_edit, name='tkaniny_edit'),
    url(r'^magazyn/tkaniny/new/$', views.tkaniny_new, name='tkaniny_new'),
    url(r'^magazyn/drukuj_etykiety_test/$', views.drukuj_etykiety_test, name='drukuj_etykiety_test'),
    url(r'^scanner/magazyn_wymianki/$', views.magazyn_wymianki, name='magazyn_wymianki'),
    url(r'^magazyn/czysc_zliczanie/$', views.czysc_zliczanie, name='czysc_zliczanie'),
]
