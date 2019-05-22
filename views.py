from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Q
from .forms import LoginForm
from django.utils import timezone
import django.core.exceptions
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout 
from . import functions
import os
import re
from datetime import datetime
import json
from subprocess import call

# Modele
from .models import *

# Formy
from .models import RolkaForm
from .models import TkaninaForm

#Utils

def logowanie_bledu(request, error):
    ErrorLog.objects.create(error=error, post=request.POST, funkcja=request.get_full_path())
    return True


# === Glowne funkcje ===
def index(request):
    return HttpResponse('Done')

def ulotka(request):
    if functions.zmiany_w_karcie() == False:
        return  HttpResponse('Blad generowania dokumentu {0}'.format(functions.zmiany_w_karcie()))
    if functions.zamien_wzornik_na_pdf() == False:
        return HttpResponse("Blad zamiany na PDF")
    else:
         return HttpResponse("Konwersja PDF wykonana")

def sprawdz_dzial(request):
    if re.search('krojownia', request.path):
        return 'krojownia'
    return 'magazyn'

def edytuj_rolke_(request, nr_rolki,user):
    rolka = Rolka.objects.get(pk=nr_rolki)
    rolka_old =rolka.dlugosc
    print(user)
    return edytuj_rolke(request,nr_rolki,rolka_old,user)
    
def edytuj_rolke(request, nr_rolki,rolka_old,user):
    if request.method == 'POST':
        print(request.user)
        rolka = Rolka.objects.get(pk=nr_rolki)
        form = RolkaForm(request.POST, instance=rolka)
        # if re.search(r'all', request.path):
        #     form = RolkaForm_all(request.POST, instance=rolka)        
        if form.is_valid():         
            print(form.cleaned_data['dlugosc'])

            if not form.cleaned_data['dlugosc'] == rolka_old:

                created, log = Log.objects.get_or_create(rolka_id=rolka.pk,
                                                        index_tkaniny=rolka.tkanina.index_sap,
                                                        dlugosc_rolki=rolka_old,
                                                        dlugosc_elementu=form.cleaned_data['dlugosc'],
                                                        nr_fgk=user,
                                                        typ='EDYCJA_KOMPUTER')            
            form.save()              
            return render(request, 'magazyntkanin/edytuj.html', {'form': form, 'nr': nr_rolki, 'dzial': sprawdz_dzial(request)})
        else:
            return render(request, 'magazyntkanin/edytuj.html', {'form': form, 'nr': nr_rolki,'dzial': sprawdz_dzial(request)})
    rolka = Rolka.objects.get(pk=nr_rolki)
    form = RolkaForm(instance=rolka)
    # if re.search(r'all', request.path):
    #     form = RolkaForm_all(instance=rolka)            
    return render(request, 'magazyntkanin/edytuj.html', {'form': form, 'nr': nr_rolki, 'dzial': sprawdz_dzial(request)})

def obiegowka(request, nr_rolki):
    rolka = Rolka.objects.get(pk=nr_rolki)
    functions.generuj_obigowke(
        id=rolka.id,
        index=rolka.tkanina.index_sap,
        nazwa_tkaniny=rolka.tkanina.nazwa,
        dlugosc=rolka.dlugosc,
        szerokosc=rolka.szerokosc,
        lot=rolka.lot,
        rolka=rolka.nr_rolki,
        data_zamowienia=rolka.data_dostawy,
        qr_draw=True
    )

def obiegowka_full(request, nr_rolki):
    rolka = Rolka.objects.get(pk=nr_rolki)
    
    #functions.generuj_obigowke(
    functions.generuj_obiegowke_v1(
        id=rolka.id,
        index=rolka.tkanina.index_sap,
        nazwa_tkaniny=rolka.tkanina.nazwa,
        dlugosc=rolka.dlugosc,
        szerokosc=rolka.szerokosc,
        lot=rolka.lot,
        rolka=rolka.nr_rolki,
        data_zamowienia=rolka.data_dostawy,
        qr_draw=True,
        full=True
    )
    with open("tmp/obiegowka.pdf", 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline;filename=hello.pdf'
        return response
    pdf.closed
    return True

def raport_inw(request):
    #functions.generuj_rap_inwentury2()
    with open("tmp/inv.pdf", 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline;filename=hello.pdf'
        return response
    pdf.closed
    return True
def szablon_a4(request):
    if request.POST:
        _nr_sap = request.POST.get('nr_sap')
        t = Tkanina.objects.get(index_sap=_nr_sap)
        if request.POST.get('wszystkie'):
            functions.tkaniny_A4_barcode(t.nazwa, t.index_sap, wszystkie_=True)
        else:
            functions.tkaniny_A4_barcode(t.nazwa, t.index_sap)
        with open("tmp/tabela.pdf", 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'inline;filename=hello.pdf'
            return response
        pdf.closed
    else:
        wszystkie = Tkanina.objects.all()
        return render(request, 'magazyntkanin/generator_a4.html', {'wszystkie': wszystkie})

def wyszukaj_dziennik(request):
    if request.POST:
        try:
            data = request.POST['data_dziennika']
            dziennik = request.POST['nr_dziennika']
            if not dziennik == '':
                dzienniki = Dziennik.objects.filter(nr=dziennik)
                return render(request, 'magazyntkanin/dzienniki.html', {'dzienniki': dzienniki, 'data': data})
            else:
                dzienniki = Dziennik.objects.filter(data=data)
                return render(request, 'magazyntkanin/dzienniki.html', {'dzienniki': dzienniki, 'data': data})
        except Exception as e:
            print(e)
            return render(request, 'magazyntkanin/dzienniki.html', {'error': 'Niepoprawne dane'})
    else:
        return render(request, 'magazyntkanin/dzienniki.html', {})

def Wyswietl_dziennik(request, dziennik, dzial):
    path = os.path.join('.', 'dzienniki', dzial)
    path += "/" + dziennik + '.pdf'
    with open(path, 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline;filename=hello.pdf'
        return response
    pdf.closed

def Wyswietl_dziennik_planowanie(request):
    with open('tmp/output_marge.pdf', 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'inline;filename=hello.pdf'
        return response
    pdf.closed

def magazyn_index(request):
    context = {}
    context['dzial'] = sprawdz_dzial(request)
    return render(request, 'magazyntkanin/magazyn_index.html', context)

def podaj_dzienniki(request):
    ostatni = Log.objects.filter(typ="WPIS_MAGAZYN_DODANIE").last()
    if request.GET:
        nr_dziennika = request.GET['dziennik']
        radio = request.GET['radio']
        if nr_dziennika == '':
            return render(request, 'magazyntkanin/powiazania.html', {'error': 'Niepoprawny numer'})
        if WpisyMagazyn.objects.filter(dziennik__nr=nr_dziennika).exists():
            if radio == 'wydane':
                dziennik_magazyn = WpisyMagazyn.objects.filter(
                    dziennik__nr=nr_dziennika).order_by('tkanina__index_sap')
            elif radio == 'zwroty':
                dziennik_magazyn = WpisyMagazyn.objects.filter(
                    dziennik__nr=nr_dziennika).order_by('tkanina__index_sap')
                return render(request, 'magazyntkanin/powiazania.html', {'zwroty': True, 'dzienniki': dziennik_magazyn, 'ostatni': ostatni})
        else:
            return render(request, 'magazyntkanin/powiazania.html', {'error': 'Podany dziennik nie istnieje'})
        return render(request, 'magazyntkanin/powiazania.html', {'dzienniki': dziennik_magazyn, 'ostatni': ostatni})
    return render(request, 'magazyntkanin/powiazania.html', {'radio': True, 'ostatni': ostatni})

def magazyn_inwentura(request):
    url = "magazyntkanin/inwentura.html"
    inw = Log.objects.filter(typ='INWENTURA')
    context = {
    }
    context['inw']=inw
    return render(request, url, context)
def czysc_po_inw(request):
    RolkiZinwentaryzowane = []
    RolkiNieInwentura = []
    licznik=0
    rolki = Rolka.objects.all()
    for i in rolki:
        iLogs = Log.objects.filter(rolka_id=i.nr_rolki)
        if iLogs.filter(typ='INWENTURA')!=None:
            licznik+=licznik
            RolkiZinwentaryzowane.append(i.nr_rolki)
        else:
            RolkiNieInwentura.append(i.nr_rolki)
        
            #tmp = iLogs.filter(typ='INWENTURA')
    
            #print(tmp)
            
        #    for k in tmp:
        #        print(k)
                #k.typ = 'INWENTURA1'
                #k.save()

            
    return HttpResponse(licznik)


def magazyn_sprzedaz_rep(request):
    from operator import itemgetter
    url = "magazyntkanin/sprzedaz_rep.html"
    context = {
    }
    if request.GET:
        
        nazwa_tkaniny = request.GET.get('nazwa_tkaniny')
        index_tkaniny = request.GET.get('index_tkaniny')
        rolka_id = request.GET.get('rolka_id')
        data = request.GET.get('data')
        print(data)
        if nazwa_tkaniny:
            try:
                index_tkaniny = Tkanina.objects.filter(nazwa__startswith=nazwa_tkaniny)[0].index_sap
            except:
                uone

        sp3=[]
        if index_tkaniny:
           sprzedaz = Log.objects.filter(typ="WYDANIE_MAG_SPRZEDAŻ").filter(index_tkaniny=index_tkaniny).order_by('rolka_id','-timestamp') # .distinct('rolka_id')a
        elif rolka_id:
           sprzedaz = Log.objects.filter(typ="WYDANIE_MAG_SPRZEDAŻ").filter(rolka_id=rolka_id).order_by('rolka_id','-timestamp') # .distinct('rolka_id')
        elif data:
           #sprzedaz = Log.objects.filter(typ="WYDANIE_MAG_SPRZEDAŻ").filter(timestamp__startswith=data).order_by('rolka_id','-timestamp') # .distinct('rolka_id')
           sprzedaz = Log.objects.filter(typ="WYDANIE_MAG_SPRZEDAŻ").filter(timestamp__gt=data).order_by('rolka_id','-timestamp') # .distinct('rolka_id')
           #sprzedaz = Log.objects.filter(typ="WYDANIE_MAG_SPRZEDAŻ").filter(timestamp.strftime("%Y-%m-%d")="2019-01-30").order_by('rolka_id','-timestamp') # .distinct('rolka_id')
        else:
             sprzedaz = Log.objects.filter(typ="WYDANIE_MAG_SPRZEDAŻ").order_by('rolka_id','-timestamp')

        for i in sprzedaz:
            sp2={}
            sp2['nazwa_tkaniny']=Tkanina.objects.filter(index_sap=i.index_tkaniny)[0].nazwa
            sp2['rolka_id']=i.rolka_id
            sp2['index_tkaniny']=i.index_tkaniny
            sp2['dlugosc_rolki']=i.dlugosc_rolki
            sp2['dlugosc_elementu']=i.dlugosc_elementu
            sp2['typ']=i.typ
            sp2['timestamp']=i.timestamp
            sp2['isPrinted']=True
            sp3.append(sp2)
        context['sprzedaz'] = sp3
        context['data'] = data

    #if request.GET:
    #    None
    return render(request,url,context)
def do_wywalenia(x):
    try:
        if Rolka.objects.get(pk=x).do_usuniecia:
            return True
    except:
        return False
    

def magazyn_inwentura_grupowana(request):
    from operator import itemgetter
    #url = "magazyntkanin/inwentura_grupowana.html"
    url = "magazyntkanin/inwentura_rep.html"
    context = {
    }

    if request.GET:
        nazwa_tkaniny = request.GET.get('nazwa_tkaniny')
        index_tkaniny = request.GET.get('index_tkaniny')
        status = request.GET.get('status')
        

        if nazwa_tkaniny:
            try:
                index_tkaniny = Tkanina.objects.filter(nazwa__startswith=nazwa_tkaniny)[0].index_sap
            except:
                None
           

        if index_tkaniny:
            if ( status!='' and int(status)<2) or status=='':
                inw = Log.objects.filter(index_tkaniny__startswith=index_tkaniny).order_by('rolka_id','-timestamp').distinct('rolka_id')
                typ_inwentury="INWENTURA"
            elif int(status)==2:

                inw_ = Log.objects.filter(index_tkaniny__startswith=index_tkaniny).order_by('rolka_id','-timestamp').distinct('rolka_id')

                inw = list(filter(lambda x: do_wywalenia(x.rolka_id),inw_))

                typ_inwentury="INWENTURA"
            elif int(status)==3:
                typ_inwentury="ZLICZANIE"
                inw3 = []
                for  inw_ in Rolka_zliczana.objects.filter(tkanina__index_sap__startswith=index_tkaniny):
                    inw2={}
                    inw2['rolka_id'] = inw_.pk
                    inw2['index_tkaniny'] = inw_.tkanina.index_sap
                    inw2['dlugosc_elementu'] = inw_.dlugosc
                    inw2['typ']=typ_inwentury
                    inw2['nazwa_tkaniny']=inw_.tkanina.nazwa
                    inw2['dlugosc_rolki']=inw_.dlugosc
                    inw3.append(inw2)

                #context['inw'] = inw3
                #return render(request, url, context)

                

            elif int(status)==4:
                typ_inwentury="INWENTURA_22122018"
                inw = Log.objects.filter(index_tkaniny__startswith=index_tkaniny,typ=typ_inwentury).order_by('rolka_id','-timestamp').distinct('rolka_id')
            elif int(status)==5:
                typ_inwentury="INWENTURA_06022019"
                inw = Log.objects.filter(index_tkaniny__startswith=index_tkaniny,typ=typ_inwentury).order_by('rolka_id','-timestamp').distinct('rolka_id')
    
        else:
            if (status!='' and  int(status)<2) or status=='':
                typ_inwentury="INWENTURA"
                inw = Log.objects.order_by('rolka_id','-timestamp').distinct('rolka_id')
            elif int(status)==2:

                inw_ = Log.objects.filter(index_tkaniny__startswith=index_tkaniny).order_by('rolka_id','-timestamp').distinct('rolka_id')

                inw = list(filter(lambda x: do_wywalenia(x.rolka_id),inw_))
                typ_inwentury="INWENTURA"
            elif int(status)==3:
                typ_inwentury="ZLICZANIE"
                inw3 = []
                for  inw_ in Rolka_zliczana.objects.filter(tkanina__index_sap__startswith=index_tkaniny):
                    inw2={}
                    inw2['rolka_id'] = inw_.pk
                    inw2['index_tkaniny'] = inw_.tkanina.index_sap
                    inw2['dlugosc_elementu'] = inw_.dlugosc # dlugosc rolki, i elementu jako dlugosc przed i po w tym wypadku takie same
                    inw2['typ']=typ_inwentury
                    inw2['nazwa_tkaniny']=inw_.tkanina.nazwa
                    inw2['dlugosc_rolki']=inw_.dlugosc  # w tym przypadku interesuje nas długość "po", nie ewidencjonujemy zmian, wiec i w dlugosc_elementu i w dlugosc_rolki  tu i tu mamy dlugosc rolko
                    inw3.append(inw2)

                #context['inw'] = inw3
                #return render(request, url, context)
                
            elif int(status)==4:
                typ_inwentury="INWENTURA_22122018"
                inw = Log.objects.filter(typ=typ_inwentury).order_by('rolka_id','-timestamp').distinct('rolka_id')
            elif int(status)==5:
                typ_inwentury="INWENTURA_06022019"
                inw = Log.objects.filter(typ=typ_inwentury).order_by('rolka_id','-timestamp').distinct('rolka_id')

        ind_old=0
        if (status=='' or int(status)!=3):
            inw3=[]
            for i in inw:
                if Rolka.objects.filter(pk=i.rolka_id).exists():
                    
                    inw2={}
                    inw2['nazwa_tkaniny']=Tkanina.objects.filter(index_sap=i.index_tkaniny)[0].nazwa
                    inw2['rolka_id']=i.rolka_id
                    inw2['index_tkaniny']=i.index_tkaniny
                    inw2['dlugosc_rolki']=i.dlugosc_rolki
                    inw2['dlugosc_elementu']=i.dlugosc_elementu
                    inw2['typ']=i.typ
                    inw2['timestamp']=i.timestamp
                    inw2['isPrinted']=True
                    inw2['suma_po_rolkach']=Rolka.objects.filter(tkanina__index_sap=i.index_tkaniny).aggregate(Sum('dlugosc'))
                    #print(Rolka.objects.filter(tkanina__index_sap=12641),"23333")
                    inw3.append(inw2)
        # GDZIES TU SIE NIE TWORZY inw3, generalnnie nie wpada w sytuacji brak statusu i i nie ma wtedy inw3, jak dodać, oto zadanie na poniedzialek!!!!!!!
        inw3 = sorted(inw3, key=itemgetter('index_tkaniny'))
        
        dlPerIndeks = 0
        dlPerIndeks_inw = 0
        #ZLICZAMY DLUGOSC INDEKSU 
        for i in inw3:
            if ind_old != i['index_tkaniny']:
                
                dlPerIndeks_inw = 0
                i['isPrinted']=True
                
                if i['dlugosc_elementu']!=None:
                    dlPerIndeks = i['dlugosc_elementu']
                    if i['typ']==typ_inwentury:
                        dlPerIndeks_inw = i['dlugosc_elementu']
                    
                else:
                    dlPerIndeks=0
                    dlPerIndeks_inw = 0
                i['dlPerIndeks']=dlPerIndeks
                
                i['dlPerIndeks_inw']=dlPerIndeks_inw
            else:
                i['isPrinted']=False
                #print(i['dlugosc_elementu'],dlPerIndeks)
                if i['dlugosc_elementu']!=None:
                    dlPerIndeks += i['dlugosc_elementu']
                    if i['typ']==typ_inwentury:
                        dlPerIndeks_inw += i['dlugosc_elementu']
                
                i['dlPerIndeks']=round(dlPerIndeks,2)
                i['dlPerIndeks_inw']=round(dlPerIndeks_inw,2)
                
            ind_old=i['index_tkaniny']
            #przeniesc do czesci ze zmiana ind_old
            ilosc_= Tkanina.objects.get(index_sap=ind_old).ilosc_na_magazynie()
            for j in filter(lambda x: x['index_tkaniny'] == ind_old, inw3):

                # Nastepny wiersz  należaloby zoptymalizowac, bo zjada mnostwo czasu !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                #j['dlPerIndeks']=Tkanina.objects.get(index_sap=j['index_tkaniny']).ilosc_na_magazynie() ### NA RAZIE NA SZTYWNO, POTEM DODAJ ZLICZANIE
                #j['dlPerIndeks']=Tkanina.objects.get(index_sap=ind_old).ilosc_na_magazynie() ### NA RAZIE NA SZTYWNO, POTEM DODAJ ZLICZANIE
                j['dlPerIndeks']=round(ilosc_,1)
                #j['dlPerIndeks']=Tkanina.objects.filter(index_sap=ind_old).aggregate(Sum('dlugosc')) ### NA RAZIE NA SZTYWNO, POTEM DODAJ ZLICZANIE
                

                # wlasnie ten powyzej !!!!!!!
                j['dlPerIndeks_inw']=round(dlPerIndeks_inw,2)
            
        
    #SPRAWDZIC POSZCZEGOLNE WARIANTY - DZIALA INWENTURA ARCH, NIE WIADOMO JAK Z BIEZACA INW. i POZOSTALE


        if status:
            ind_o = 0
            if int(status)<1:
                inw3 = [x for x in inw3 if x['typ'] != typ_inwentury ]
            else:
                inw3 = [x for x in inw3 if x['typ'] == typ_inwentury ]

            for k in inw3:
                if ind_o != k['index_tkaniny']:
                    k['isPrinted']=True
                else:
                     k['isPrinted']=False
                ind_o=k['index_tkaniny']


        #if index_tkaniny:
            #inw3 = [x for x in inw3 if x['index_tkaniny'] ==  int(index_tkaniny) ]
        
        functions.generuj_raport_inwentury2(inw3)
        functions.generuj_raport_xls(inw3)
        functions.generuj_xls_porownanie_sap(inw3)

        context['inw'] = inw3
        context['status'] = status
        return render(request, url, context)
    return render(request, url, context)




def magazyn_inwentura_rep(request):
    #url = 'magazyntkanin/raporty.html
    url = "magazyntkanin/inwentura_rep.html"
    context = {

    }
    if request.GET:
        rolka = request.GET.get('rolka')
        q = Rolka.objects.all()
        if rolka:
            q = q.filter(pk__icontains=rolka)
        zamowienie = request.GET.get('zamowienie')
        if zamowienie:
            q = q.filter(nr_zamowienia__icontains=zamowienie)
        status = request.GET.get('status')
        if status:
            q = q.filter(status=status)
        tkanina = request.GET.get('tkanina')
        if tkanina:
            q = q.filter(tkanina__index_sap__icontains=tkanina)
        wydanie = request.GET.get('wydanie')
        if wydanie:
            q = q.filter(wydanie=wydanie)
        q = q.order_by('-pk')
        dlugosc = request.GET.get('dlugosc')
        if dlugosc:
            dlugosc_radio = request.GET.get('dlugosc_radio', None)
            if dlugosc_radio == 'lt':
                q = q.filter(dlugosc__lt=dlugosc)
                q = q.order_by('dlugosc')
            else:
                q = q.filter(dlugosc__gt=dlugosc)
                q = q.order_by('-dlugosc')
        data_dostawy = request.GET.get('data_dostawy')
        if data_dostawy:
            data_radio = request.GET.get('data_radio', 'eq')
            if data_radio == 'lt':
                q = q.filter(data_dostawy__lt=data_dostawy)
                q = q.order_by('data_dostawy')
            elif data_radio == 'gt':
                q = q.filter(data_dostawy__gt=data_dostawy)
                q = q.order_by('-data_dostawy')
            else:
                q = q.filter(data_dostawy__startswith=data_dostawy)
        if q.count() > 1000:
            context['error'] = "Powyżej 1000 wpisów! Wyszukaj bardziej szczegółowo."
            return render(request, url, context)
        context['wpisy'] = q
        return render(request, url, context)
    return render(request, url, context)
def inw_do_usuniecia(request):
    #Nadaje status do usuniecia dla niezinwentaryzowanych rolek
    #Poki co trzeba wstawic date konca ponizej
    #kolejnosc 
    #1 ) http://jan-svr-docker:8000/magazyn/inwentura_usun/ (views.inw_do_usuniecia)
    #2 ) http://jan-svr-docker:8000/magazyn/inwentura_usun_finalnie/ (views.inw_usuwamy) 
    #3 ) http://jan-svr-docker:8000/magazyn/archiwizuj_inwenture/ (views.archiwizuj_inwenture)
    rolki= []
    dd= datetime.strptime("2019-02-06 00:00:01.78200", "%Y-%m-%d %H:%M:%S.%f").date()
    for i in Rolka.objects.all():   # DLA PELNEJ INWENTURY
    ##for i in Rolka.objects.filter(tkanina__index_sap=12641):  # DLA INWENTURY TKANINY
        
    
        if  Log.objects.filter(rolka_id=i.pk,typ='INWENTURA'): # dodatkowo warunek na INWENTURE
            rolki.append(i.pk)
            i.do_usuniecia=False
            i.save()
        else:
            try:
                if i.data_dostawy>=dd:
                    i.do_usuniecia=False
                else:
                    i.do_usuniecia=True
                i.save()
            except:
                None

    return HttpResponse(rolki)

def inw_usuwamy(request):
    #kopia = Rolka_usunieta - usunąc filtr na pk
    for i in Rolka.objects.filter(do_usuniecia=True):
        Rolka_usunieta.objects.get_or_create(pk=i.pk,tkanina=i.tkanina,status=i.status,data_dostawy=i.data_dostawy,nr_rolki=i.nr_rolki,dlugosc=i.dlugosc,szerokosc=i.szerokosc,dlugosc_poczatkowa=i.dlugosc_poczatkowa,barcode=i.barcode,nr_zamowienia=i.nr_zamowienia,zakonczona=i.zakonczona,wydrukowana=i.wydrukowana,do_usuniecia=i.do_usuniecia)
    Rolka.objects.filter(do_usuniecia=True).delete()

    return HttpResponse("OK")
def archiwizuj_inwenture(request):
    for i in Log.objects.filter(typ='INWENTURA'):
        i.typ='INWENTURA_06022019'
        i.save()
    #for i in Log.objects.filter(typ='INWENTURA_22122019'):
    #    i.typ='INWENTURA_22122018'
    #    i.save()
    return HttpResponse("OK")
def panel_planowania(request):
    if request.POST:
        if request.POST['generuj']:
            krojownia, magazyn, error = functions.Zarzadzenie_dziennikami()
            ilosc = {'krojownia': len(krojownia),
                     'magazyn': len(magazyn),
                     'error': len(error)}
            condata = {'ilosc': ilosc}
            return render(request, 'magazyntkanin/planowanie.html', condata)
    else:
        return render(request, 'magazyntkanin/planowanie.html', {})

def raporty_temp(request):
    user_logout(request)
    url = "magazyntkanin/test.html"
    context = {

    }
    if request.GET:
        dziennik = request.GET.get('dziennik')
        rolka = request.GET.get('rolka')
        zamowienie = request.GET.get('zamowienie')
        if dziennik:
            try:
                dziennik = Dziennik.objects.get(nr=dziennik)
                wpisy = Log.objects.filter(
                    dziennik_nr=dziennik.nr).order_by('-timestamp')
                niezakonczone = WpisySzwalnia.objects.filter(dziennik=dziennik, ukonczone=False).count()
                return render(request, 'magazyntkanin/krojownia_raporty.html', {'wpisy': wpisy, 'dziennik': niezakonczone})
            except Exception as e:
                return render(request, 'magazyntkanin/krojownia_raporty.html', {'errors': 'Brak podanego dziennika'})
        if request.GET['rolka']:
            rolka = request.GET['rolka']
            try:
                rolka = Rolka.objects.get(pk=rolka)
                wpisy = Log.objects.filter(
                    rolka_id=rolka.pk).order_by('-timestamp')
                return render(request, 'magazyntkanin/krojownia_raporty.html', {'wpisy': wpisy, 'rolka': rolka})
            except Exception as e:
                return render(request, 'magazyntkanin/krojownia_raporty.html', {'errors': 'Brak podanej rolki'})
        if not request.GET['rolka'] and not request.GET['dziennik']:
            wpisy = Log.objects.all().order_by('-timestamp')
            return render(request, 'magazyntkanin/krojownia_raporty.html', {'wpisy': wpisy})
    return render(request, 'magazyntkanin/krojownia_raporty.html')
    return render(request, url_name, context)

def raporty(request):
    url = 'magazyntkanin/raporty.html'
    context = {

    }
    if request.GET:
        rolka = request.GET.get('rolka')
        q = Rolka.objects.all()
        if rolka:
            q = q.filter(pk__icontains=rolka)
        zamowienie = request.GET.get('zamowienie')
        if zamowienie:
            q = q.filter(nr_zamowienia__icontains=zamowienie)
        status = request.GET.get('status')
        if status:
            q = q.filter(status=status)
        tkanina = request.GET.get('tkanina')
        if tkanina:
            q = q.filter(tkanina__index_sap__icontains=tkanina)
        wydanie = request.GET.get('wydanie')
        if wydanie:
            q = q.filter(wydanie=wydanie)
            
        q = q.order_by('-pk')
        dlugosc = request.GET.get('dlugosc')
        if dlugosc:
            dlugosc_radio = request.GET.get('dlugosc_radio', None)
            if dlugosc_radio == 'lt':
                q = q.filter(dlugosc__lt=dlugosc)
                q = q.order_by('dlugosc')
            else:
                q = q.filter(dlugosc__gt=dlugosc)
                q = q.order_by('-dlugosc')
        data_dostawy = request.GET.get('data_dostawy')
        if data_dostawy:
            data_radio = request.GET.get('data_radio', 'eq')
            if data_radio == 'lt':
                q = q.filter(data_dostawy__lt=data_dostawy)
                q = q.order_by('data_dostawy')
            elif data_radio == 'gt':
                q = q.filter(data_dostawy__gt=data_dostawy)
                q = q.order_by('-data_dostawy')
            else:
                q = q.filter(data_dostawy__startswith=data_dostawy)
        if q.count() > 1000:
            context['error'] = "Powyżej 1000 wpisów! Wyszukaj bardziej szczegółowo."
            return render(request, url, context)
        context['wpisy'] = q
        return render(request, url, context)
    return render(request, url, context)

def sap_generator(request, nr_dziennika):
    url = 'magazyntkanin/sap.html'
    dziennik = Dziennik.objects.get(nr=nr_dziennika)
    a = dziennik.wpisymagazynpowiazania_set.all().order_by('rolka__tkanina__index_sap')
    test_arrayu = []
    dodane = []
    dodane_rolki = []
    for each in a:
        suma_tkaniny = 0
        if each.rolka.tkanina in dodane:
            continue
        else:
            tkanina = each.rolka.tkanina
            for each in a:
                if tkanina == each.rolka.tkanina:
                    if not each.rolka.id in dodane_rolki:
                        dlugosc_w_momencie = Log.objects.filter(rolka_id=each.rolka.id, typ='WPIS_MAGAZYN_DODANIE', dziennik_nr=nr_dziennika).last().dlugosc_rolki
                        dodane_rolki.append(each.rolka.id)
                        suma_tkaniny += dlugosc_w_momencie
            test_arrayu.append({'tkanina': tkanina.index_sap, 'suma': suma_tkaniny})
            dodane.append(tkanina)
    context = {
        'wpisy': test_arrayu,
        'nr_dziennika': nr_dziennika,
    }
    return render(request, url, context)

def test_statystki(rolka):
    log = Log.objects.filter(rolka_id=rolka)
    log_magazynowy = log.filter(
        Q(typ="WPIS_MAGAZYN_WYDANIE") |
        Q(typ="EDYCJA") |
        Q(typ="EDYCJA_KOMPUTER") |
        Q(typ="WPIS_MAGAZYN_WYCOFANIE") |
        Q(typ="WPIS_MAGAZYN_DODANIE") |
        Q(typ="INWENTURA") |
        Q(typ="INWENTURA_22122019") |
        Q(typ="INWENTURA_06022019") |
        Q(typ="WPIS_MAGAZYN_ZWROT")).order_by('-timestamp')

    log_fgk = log.filter(
        Q(typ="ODPAD") |
        Q(typ="WYMIANKA") |
        Q(typ="WYMIANKA_O") |
        Q(typ="FGK_laczone") |
        Q(typ="FGK_laczone_poza") |
        Q(typ="FGK") |
        Q(typ="FGK_poza") |
        Q(typ="STOFF_WEW") |
        Q(typ__startswith="WYDANIE_MAG_")).order_by('-timestamp')

    return log_magazynowy, log_fgk

def statystyki_rolka(request, rolka):
    url = 'magazyntkanin/statystyki_rolka.html'
    rolka = Rolka.objects.get(pk=rolka)
    context = {
        "rolka": rolka,
    }
    log_magazynowy, log_fgk = test_statystki(rolka.pk)
    context['log_m'] = log_magazynowy
    context['log_fgk'] = log_fgk
    return render(request, url, context)

def statystyki_tkanina(request, tkanina):
    url = 'magazyntkanin/statystyki_tkanina.html'
    context = {}
    tkanina = Tkanina.objects.get(index_sap=tkanina)
    wszystkie_rolki = tkanina.rolka_set.all().order_by('-data_dostawy')
    dlugosci = Rolka.objects.filter(status=0, tkanina=tkanina).aggregate(Sum('dlugosc'))
    wydane = wszystkie_rolki.filter(status=1).count()
    zerowe = wszystkie_rolki.filter(dlugosc=0).count()
    zakonczona = wszystkie_rolki.filter(zakonczona=True).count()
    na_magazynie = wszystkie_rolki.exclude(status=1).exclude(zakonczona=True).count()
    context['rolka'] = wszystkie_rolki
    context['na_magazynie'] = na_magazynie
    context['zerowe'] = zerowe
    context['zakonczona'] = zakonczona
    context['wydane'] = wydane
    context['dlugosci'] = dlugosci
    context['tkanina'] = tkanina
    return render(request, url, context)

def raporty_dziennik(request):
    url = ""
    context = {

    }
    if request.GET:
        dziennik = request.GET.get('dziennik')
        if dziennik:
            d = Log.objects.filter(
                    dziennik_nr__icontains=dziennik).order_by('-timestamp')
            context['wpisy'] = d
            context['dziennik'] = True
            return render(request, url, context)
    return render(request, url, context)

def raporty_zamowienie(request, zamowienie):
    url = "magazyntkanin/raporty_zamowienie.html"
    wpisy = Rolka.objects.filter(nr_zamowienia=zamowienie).order_by('tkanina')
    context = {
        "wpisy": wpisy,
    }
    context['zamowienie'] = zamowienie
    return render(request, url, context)

def raporty_(request):
    if request.GET:
        dziennik = request.GET.get('dziennik') if request.GET.get('dziennik') else None
        rolka = request.GET.get('rolka') if request.GET.get('rolka') else None
        zamowienie = request.GET.get('zamowienie') if request.GET.get('zamowienie') else None
        if dziennik:
            try:
                dziennik = Dziennik.objects.get(nr=dziennik)
                wpisy = Log.objects.filter(
                    dziennik_nr=dziennik.nr).order_by('-timestamp')
                return render(request, 'magazyntkanin/raporty.html', {'wpisy': wpisy})
            except Exception as e:
                return render(request, 'magazyntkanin/raporty.html', {'errors': 'Brak podanego dziennika'})
        if rolka:
            try:
                rolka = Rolka.objects.get(pk=rolka)
                wpisy = Log.objects.filter(
                    rolka_id=rolka.pk).order_by('-timestamp')
                print(rolka, wpisy)
                return render(request, 'magazyntkanin/raporty.html', {'wpisy': wpisy, 'rolka': True})
            except Exception as e:
                return render(request, 'magazyntkanin/raporty.html', {'errors': e})
        if zamowienie:
            rolka = Rolka.objects.filter(nr_zamowienia=zamowienie).order_by('tkanina__nazwa')
            if rolka.count() > 0:
                return render(request, 'magazyntkanin/raporty.html', {'rol': rolka, 'zamowienie': True})
            else:
                return render(request, 'magazyntkanin/raporty.html', {'errors': 'Brak podanego zamowienia'})
        if not request.GET['rolka'] and not request.GET['dziennik']:
            wpisy = Log.objects.all().order_by('-timestamp')
            return render(request, 'magazyntkanin/raporty.html', {'wpisy': wpisy})
    return render(request, 'magazyntkanin/raporty.html')

def raport_a(request, dziennik):
    dziennik = Dziennik.objects.get(nr=dziennik)
    wpisy = Log.objects.filter(dziennik_nr=dziennik.nr)
    log = WpisyMagazyn.objects.filter(dziennik=dziennik)
    context = {'log': log,
                'wpisy': wpisy,
                'dziennik': dziennik}
    return render(request, 'magazyntkanin/raport_a.html', context)

# === AJAX response ===
def planowanie_ajax(request):
    if request.GET['generuj'] == 'true':
        krojowania, magazyn, errors, brak_danych = functions.Zarzadzenie_dziennikami()
        braki_krojownia, braki_magazyn = functions.roznice_w_plikach()
        context = {'status': {'krojownia': len(krojowania),
                              'magazyn': len(magazyn),
                              'errors': len(errors),
                              'brak_danych': brak_danych},
                   'braki': {'krojownia': list(braki_krojownia),
                             'magazyn': list(braki_magazyn)}}
        return JsonResponse(context)
    if request.GET['drukuj']:
        dane = []
        errors = []
        brak_danych = None
        od = request.GET['od']
        do = request.GET['do']
        if not od == '':
            od = int(od)
            if not do == '':
                do = int(do)
                dzienniki = Dziennik.objects.filter(nr__gt=od, nr__lt=do)
                for each in range(od, do + 1):
                    if not Dziennik.objects.filter(nr=each).exists():
                        errors.append(each)
                    else:
                        dane.append(each)
                functions.pdf_merger(dane)
            else:
                if Dziennik.objects.filter(nr=od).exists():
                    dane.append(Dziennik.objects.filter(nr=od).first().nr)
                else:
                    errors.append('Brak dziennika')
                functions.pdf_merger(dane)
        return JsonResponse({'errors': sorted(errors, reverse=True), 'dane': sorted(dane, reverse=True), 'brak_danych': brak_danych})

# === Krojownia ===
def status_dziennika(request, nr_dziennika):
    #host=HttpRequest.get_host()
    print("status_dziennika")
    #print(host,"status_dziennika")
    if re.match(r'status', request.get_full_path()):
        wpisy = Dziennik.wpisyszwalnia_set.all()
    else:
        wpisy = WpisySzwalnia.objects.filter(
            dziennik__nr=nr_dziennika, ukonczone=False)
    wpisy = wpisy.order_by('pozycja')    
    user_logout(request)
    return render(request, 'magazyntkanin/status_dz.html', {'wpisy': wpisy})

def krojownia_index(request):
    url_name = 'magazyntkanin/base_k.html'
    context = {

    }
    return render(request, url_name, context)

def krojownia_status(request):
    host=request.META['REMOTE_ADDR']

    print("krojownia_status")
    print(host,"krojownia_status")

    if re.search(r'dziennik', request.path) or host=='192.168.43.31':
        url_name = 'magazyntkanin/krojownia_dziennik_widok.html'
    else:
        url_name = 'magazyntkanin/krojownia_status.html'
    context = {}

    user_logout(request)
    if request.GET:
        dziennik = request.GET.get('dziennik', "")
        if dziennik == "":
            context['errors'] = "Podaj jakis numer"
        else:
            try:
                dziennik = Dziennik.objects.get(nr=dziennik)
            except Exception as e:
                context['errors'] = "Podany dziennik nie istnieje w bazie danych: {e}"
                return render(request, url_name, context)
            wpisy = dziennik.wpisyszwalnia_set.all()
            # wpisy = WpisySzwalnia.objects.filter(dziennik__nr=dziennik, ukonczone=False)
            if wpisy.count() > 0:
                wpisy = wpisy.order_by('pozycja')
                context['wpisy'] = wpisy
                context['OK'] = True
            else:
                context['errors'] = "Podany numer nie istnieje"
    return render(request, url_name, context)

def krojownia_paczki(request, *args, **kwargs):
    user_logout(request)
    if all:
        query = Paczki.objects.all().order_by('-dziennik__nr', '-data_utworzenia')[:50]
    query = Paczki.objects.all().order_by('-dziennik__nr', '-data_utworzenia')[:50]
    # query = Paczki.objects.filter(zakonczona=True).order_by('-dziennik__nr', '-data_utworzenia',)[:50]
    url_name = 'magazyntkanin/krojownia_paczki.html'
    context = {
        'paczki': query,
    }
    return render(request, url_name, context)

@login_required(login_url='/login/') #-- logowanie odkomentowac 
def krojowania_edycja(request):
    url = 'magazyntkanin/krojownia_edycja.html'
    user = request.user

    context = {}
    if request.GET:
        rolka = request.GET.get('rolka')
        rolka = Rolka.objects.filter(pk=rolka)
        if rolka.exists():
            
            url = 'magazyntkanin/statystyki_rolka.html'
            rolka = Rolka.objects.get(pk=rolka)
            context = {
                "rolka": rolka,
            }
            log_magazynowy, log_fgk = test_statystki(rolka.pk)
            context['log_m'] = log_magazynowy
            context['log_fgk'] = log_fgk
            context['dzial'] = 'krojownia'
            context['user'] = user
            user_logout(request)
            return render(request, url, context)
        else:
            context['rolka'] = rolka
    return render(request, url, context)

def krojownia_raport(request):
    user_logout(request)

    url_name = 'magazyntkanin/base_k.html'
    context = {

    }
    if request.GET:
        if request.GET['dziennik']:
            dziennik = request.GET['dziennik']
            try:
                dziennik = Dziennik.objects.get(nr=dziennik)
                wpisy = Log.objects.filter(
                    dziennik_nr=dziennik.nr).order_by('-timestamp')
                niezakonczone = WpisySzwalnia.objects.filter(dziennik=dziennik, ukonczone=False).count()
                return render(request, 'magazyntkanin/krojownia_raporty.html', {'wpisy': wpisy, 'dziennik': niezakonczone})
            except Exception as e:
                return render(request, 'magazyntkanin/krojownia_raporty.html', {'errors': 'Brak podanego dziennika'})
        if request.GET['rolka']:
            rolka = request.GET['rolka']
            try:
                rolka = Rolka.objects.get(pk=rolka)
                wpisy = Log.objects.filter(
                    rolka_id=rolka.pk).order_by('-timestamp')
                return render(request, 'magazyntkanin/krojownia_raporty.html', {'wpisy': wpisy, 'rolka': rolka})
            except Exception as e:
                return render(request, 'magazyntkanin/krojownia_raporty.html', {'errors': 'Brak podanej rolki'})
        if not request.GET['rolka'] and not request.GET['dziennik']:
            wpisy = Log.objects.all().order_by('-timestamp')
            return render(request, 'magazyntkanin/krojownia_raporty.html', {'wpisy': wpisy})
    return render(request, 'magazyntkanin/krojownia_raporty.html')
    return render(request, url_name, context)

def krojownia_obiegowki(request):
    url = "magazyntkanin/obiegowki.html"
    context = {

    }
    logout(request)
    if request.GET:
        nr_rolki = request.GET.get('rolka', None)
        try:
            rolka = Rolka.objects.get(pk=nr_rolki)
        except Rolka.DoesNotExist:
            context['error'] = 'Podana rolka nie istnieje w bazie danych'
            return render(request, url, context)
        return obiegowka_full(request, nr_rolki)
    return render(request, url, context)

def user_login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect('/krojownia/')
    form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})

def l_check(request,nr_rolki):
    print("d11111")
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = data['user']
            password = data['password']
            user_check = authenticate(username=user, password=password)
            if user_check:
                if user_check.is_active:
                    login(request, user_check)
                    return HttpResponseRedirect('/krojownia/edytuj')
            else:
                return render(request, 'registration/login.html', {'form': form, 'error': 'Logowanie nie poprawne'})
    return render(request, 'registration/login.html', {'form': form, 'error': 'Logowanie nie poprawne'})      

@login_required
def user_logout(request):
    logout(request)
    return HttpResponseRedirect('/krojownia/')

# === import danych ===
def import_tkanin(request):
    path = os.path.join('magazyntkanin', 'pliki', 'tkaniny.csv')
    return HttpResponse(functions.importBazyTkanin(path))

def import_zamowienia(request):
    # path = os.path.join('magazyntkanin', 'pliki', 'delivery_test.csv')
    return HttpResponse(functions.Tworzenie_CSV())
    # return HttpResponse(functions.Import_euro(path))

def import_zamowienia_pobierz(request):
    if request.method == 'POST':
        form = XlsBrowserForm(request.POST, request.FILES)
        if form.is_valid():
            MyTkaninyXlsx = TkaninyXlsx()
            MyTkaninyXlsx.description = form.cleaned_data["description"]
            MyTkaninyXlsx.document = form.cleaned_data["document"]
            MyTkaninyXlsx.data_dostawy = form.cleaned_data["data_dostawy"]

            MyTkaninyXlsx.save()
            functions.Tworzenie_CSV(data_dostawy=MyTkaninyXlsx.data_dostawy)
    else:
        form = XlsBrowserForm()

    return render(request,'magazyntkanin/import_eurotex.html',locals())

def import_pdf(request):
    krojownia, magazyn, error, brak_danych = functions.Zarzadzenie_dziennikami()
    return HttpResponse(import_pdf)

# === testowe ===
def ajax_test(request):
    if request.GET['pk']:
        pk = request.GET['pk']
        return HttpResponse(Rolka.objects.get(pk=int(pk)))

def poka(request):
    wpisy = Dziennik.wpisyszwalnia_set.all()
    dane = {
        'wpisy': wpisy
    }
    return render(request, 'magazyntkanin/dane.html', dane)

def stan_magazynowy(request):
    tkaniny = Rolka.objects.all().distinct(
        'tkanina__nazwa').order_by('tkanina__nazwa')
    if request.POST:
        tkanina = request.POST['tkanina']
        rolki = Rolka.objects.filter(
            tkanina__index_sap=tkanina, dlugosc__gt=0).order_by('data_dostawy')
        return render(request, 'magazyntkanin/stan_magazynowy.html', {'tkaniny': tkaniny, 'rolki': rolki})
    return render(request, 'magazyntkanin/stan_magazynowy.html', {'tkaniny': tkaniny})

def test_MDB_Query(request, NL=False):
    scan = request.POST['scan']
    if NL:
        wynik = functions.Tworzenie_zapytania(nr=scan + "-NL")
    else:
        wynik = functions.Tworzenie_zapytania(nr=scan)
    nazwa, komentarz, dlugosc = (wynik[0], wynik[3], float(wynik[5]) / 1000)
    ret = " -------- ".join((nazwa, komentarz, dlugosc))
    return HttpResponse(ret)

def fuzzy_check(komentarz, rolka):
    from fuzzywuzzy import fuzz
    regex_paczka_string = r'^(\d{1,2})[ ]*[xX][ ]*(\d+)[ ]*[xX]*(\d+)[ Xx]*(.+) X'
    re_wynik = re.match(regex_paczka_string, komentarz)
    if re_wynik:
        pozycja = re_wynik.group(1)
        dziennik = re_wynik.group(2)
        nazwa_tkaniny = re_wynik.group(3)
        print(re_wynik.group())
        wybrana_tkanina = rolka.tkanina.nazwa    
        ratio = fuzz.ratio(wybrana_tkanina, nazwa_tkaniny)
        return ratio
    else:
        return "Niepoprawne dane"

# === Generowanie etykiet ===
def generator_etykiet(request, **kwargs):
    wszystkie = Tkanina.objects.all().order_by('nazwa')
    context = {'wszystkie': wszystkie}
    return render(request, 'magazyntkanin/generator_tkanin.html', context)

def drukuj_etykiety(request):
    if request.method == 'GET':
        data_przyjecia = request.GET['data-przyjecia']
        if data_przyjecia == '':
            return HttpResponse('Wprowadz date')
        mass = request.GET.get('mass')
        if mass:
            data_przyjecia = request.GET.get('data-przyjecia')
            zamowienie = request.GET.get('zamowienie') if request.GET.get('zamowienie') else None
            if data_przyjecia == "":
                return HttpResponse('Wprowadz date')
            linie = mass.split('\n')
            bledne = []
            for linia in linie:
                linia = linia.split(',')
                nr_sap = linia[0]
                tkanina = Tkanina.objects.filter(index_sap=nr_sap)
                if not tkanina.exists():
                    bledne.append(nr_sap)
            if len(bledne) > 0:
                return HttpResponse("Nie odnaleziono tkanin {0}".format(bledne))
            for linia in linie:
                linia = linia.split(',')
                if len(linia) == 2:
                    nr_sap = linia[0]
                    ilosc = linia[1]
                    barcodes = []
                    tkanina = Tkanina.objects.get(index_sap=nr_sap)
                    nazwa = tkanina.nazwa
                    for e in range(int(ilosc)):
                        r = Rolka.objects.create(
                            tkanina=tkanina, data_dostawy=data_przyjecia, nr_zamowienia=zamowienie)
                        barcodes.append(str(r.pk))
                    functions.generuj_etykiete_tkaniny_podwojna(
                        nazwa, barcode=barcodes, data_dostawy=data_przyjecia)
                    call(['/etc/init.d/cups start'], shell=True)
                    #call(['lp tmp/etykieta_podwojna.pdf'], shell=True)
                    call(['lp -o Resolution=300dpi -o PageSize=w144h216 tmp/etykieta_podwojna.pdf'], shell=True)
                else:
                    return HttpResponse("Nieprawidłowe dane")
            return HttpResponse("Wydrukowano")
        tkanina = Tkanina.objects.get(index_sap=request.GET['nr_sap'])
        nazwa = tkanina.nazwa
        if request.GET['ilosc']:
            ilosc = request.GET['ilosc']
        else:
            ilosc = 1
        barcodes = []
        for e in range(int(ilosc)):
            r = Rolka.objects.create(
                tkanina=tkanina, data_dostawy=data_przyjecia)
            barcodes.append(str(r.pk))
        functions.generuj_etykiete_tkaniny_podwojna(
            nazwa, barcode=barcodes, data_dostawy=data_przyjecia)
        call(['/etc/init.d/cups start'], shell=True)
        # call(['ls /etc/cups/'], shell=True)
        call(['lp -o Resolution=300dpi -o PageSize=w144h216 tmp/etykieta_podwojna.pdf'], shell=True)
        return HttpResponse('Wydrukowano {0} etykiet {1}'.format(ilosc, tkanina.nazwa))
    else:
        return HttpResponse('Niepoprawne dane')

def drukuj_etykiety_test(request):
    if request.method == 'GET':
        #data_przyjecia = request.GET['data-przyjecia']
        data_przyjecia = '2018-11-21'
        if data_przyjecia == '':
            return HttpResponse('Wprowadz date')
        mass = request.GET.get('mass')
        if mass:
            data_przyjecia = request.GET.get('data-przyjecia')
            zamowienie = request.GET.get('zamowienie') if request.GET.get('zamowienie') else None
            if data_przyjecia == "":
                return HttpResponse('Wprowadz date')
            linie = mass.split('\n')
            bledne = []
            for linia in linie:
                linia = linia.split(',')
                nr_sap = '14447' #  14447 / SALSA BEERE
                #nr_sap = linia[0]
                tkanina = Tkanina.objects.filter(index_sap=nr_sap)
                if not tkanina.exists():
                    bledne.append(nr_sap)
            if len(bledne) > 0:
                return HttpResponse("Nie odnaleziono tkanin {0}".format(bledne))
            for linia in linie:
                linia = linia.split(',')
                if len(linia) == 2:
                    nr_sap = linia[0]
                    ilosc = linia[1]
                    barcodes = []
                    tkanina = Tkanina.objects.get(index_sap=nr_sap)
                    nazwa = tkanina.nazwa
                    for e in range(int(ilosc)):
                        u = Rolka.objects.create(
                            tkanina=tkanina, data_dostawy=data_przyjecia, nr_zamowienia=zamowienie)
                        barcodes.append(str(r.pk))
                    functions.generuj_etykiete_tkaniny_podwojna(
                        nazwa, barcode=barcodes, data_dostawy=data_przyjecia)
                    #call(['/etc/init.d/cups start'], shell=True)
                    #call(['lp tmp/etykieta_podwojna.pdf'], shell=True)
                else:
                    return HttpResponse("Nieprawidłowe dane")
            return HttpResponse("Wydrukowano")

        tkanina = Tkanina.objects.get(index_sap='14447')
        nazwa = tkanina.nazwa
        ilosc = 1
        barcodes = []
        for e in range(int(ilosc)):
            r = Rolka.objects.create(
                tkanina=tkanina, data_dostawy=data_przyjecia)
            barcodes.append(str(r.pk))
        functions.generuj_etykiete_tkaniny_podwojna(
            nazwa, barcode=barcodes, data_dostawy=data_przyjecia)
        #call(['/etc/init.d/cups start'], shell=True)
        # call(['ls /etc/cups/'], shell=True)
        #call(['lp tmp/etykieta.pdf'], shell=True)
        return HttpResponse('Wydrukowano {0} etykiet {1}'.format(ilosc, tkanina.nazwa))
    else:
        return HttpResponse('Niepoprawne dane')

def drukuj_etykiete(request, nr_rolki):
    try:
        int(nr_rolki)
        rolka = Rolka.objects.get(pk=nr_rolki)
        L = rolka.lot
        if not L:
            L = ''
        R = rolka.nr_rolki
        if not R:
            R = ''
        M = rolka.dlugosc
        if not M:
            M = ''
        szerokosc = rolka.szerokosc
        if szerokosc == 0:
            szerokosc = ''
        data_dostawy = rolka.data_dostawy.strftime("%d/%m/%Y")
        if not data_dostawy:
            data_dostawy = ''
        nazwa_tkaniny = rolka.tkanina.nazwa
        barcode = [str(rolka.pk)]
        functions.generuj_etykiete_tkaniny_podwojna(nazwa_tkaniny, barcode, str(
            L), str(R), data_dostawy, str(M), szerokosc)
        with open('tmp/etykieta_podwojna.pdf', 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'filename=etykieta_podwojna.pdf'
            return response
        pdf.closed
    except Exception as e:
        raise e
        return HttpResponse('Niepoprawny numer rolki')

# === Skaner CK3X ===
@csrf_exempt
def dodanie_dziennika(request):
    try:
        dziennik = Dziennik.objects.get(nr=request.POST['nr_dziennika'])
        rolka = Rolka.objects.get(pk=request.POST['rolka_id'])
        if WpisyMagazyn.objects.filter(dziennik=dziennik, tkanina=rolka.tkanina).exists():
            created, wpis = WpisyMagazynPowiazania.objects.get_or_create(
                dziennik=dziennik, rolka=rolka, aktywne=True)
            if not created:
                return HttpResponse('Podany wpis już istnieje')
            created, log = Log.objects.get_or_create(dziennik_nr=dziennik.nr,
                                                     rolka_id=rolka.pk,
                                                     index_tkaniny=rolka.tkanina.index_sap,
                                                     dlugosc_rolki=rolka.dlugosc,
                                                     typ='WPIS_MAGAZYN_DODANIE')
            return HttpResponse('Tkanian {0} dodana do dziennika {1}'.format(rolka.pk, dziennik.nr))
        else:
            return HttpResponse('Na dzienniku nie ma tkaniny - {0}'.format(rolka.tkanina.nazwa))
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse('Błedny numer tkaniny lub dziennika')

@csrf_exempt
def wycofanie_dziennika(request):
    try:
        dziennik = Dziennik.objects.get(nr=request.POST['nr_dziennika'])
        rolka = Rolka.objects.get(pk=request.POST['rolka_id'])
        created, log = Log.objects.get_or_create(dziennik_nr=dziennik.nr,
                                                 rolka_id=rolka.pk,
                                                 index_tkaniny=rolka.tkanina.index_sap,
                                                 dlugosc_rolki=rolka.dlugosc,
                                                 typ='WPIS_MAGAZYN_WYCOFANIE')
        wpisy = WpisyMagazynPowiazania.objects.get(
            dziennik=dziennik, rolka=rolka, aktywne=True)
        wpisy.data_zwrotu = timezone.now()
        wpisy.aktywne = False
        wpisy.save()
        return HttpResponse('Tkanian {0} została usunieta z dziennika {1}'.format(rolka.pk, dziennik.nr))
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse('Nie znaleziono podanej kombinacji')

@csrf_exempt
def nl(request):
    try:
        rolka = Rolka.objects.get(pk=request.POST['id_rolki'])
        karta_fgk = request.POST['karta_fgk']
        fgk_result = functions.Tworzenie_zapytania(karta_fgk + "-NL")
        dlugosc_do_wyciecia = (float(fgk_result[5]) / 1000)
        if rolka.dlugosc < dlugosc_do_wyciecia:
            return HttpResponse("Za mało tkaniny")
        if fgk_result:
            Log.objects.create(rolka_id=rolka.pk,
                               index_tkaniny=rolka.tkanina.index_sap,
                               dlugosc_rolki=rolka.dlugosc,
                               nr_fgk=karta_fgk,
                               dlugosc_elementu=dlugosc_do_wyciecia,
                               typ='NL')
            rolka.dlugosc = rolka.dlugosc - dlugosc_do_wyciecia
            rolka.save()
        return HttpResponse("Wpis NL dodany poprawnie - dlugosc {0} mb".format(dlugosc_do_wyciecia))
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("Brak NL dla karty")

@csrf_exempt
def przekaz_tkanine(request):

    if request.POST['barcode'] == "9999999" and request.POST['nr_dziennika'] == "9999999":
        print("aaaaa")
        return HttpResponse("Tkanina wydana") 
    try:
        rolka = Rolka.objects.get(pk=request.POST['barcode'])
        szerokosc = request.POST['szerokosc']
        dziennik_nr = request.POST['nr_dziennika']
        dlugosc = request.POST['dlugosc']
        print(rolka,dziennik_nr)

        if rolka.dlugosc == 0:
            return HttpResponse("Rolka ma 0 dlugosc! Edytuj przed dodaniem")
        if szerokosc == '':
            if rolka.szerokosc == 0:
                return HttpResponse("szerokosc")
        else:
            try:
                szerokosc = int(szerokosc)
                rolka.szerokosc = szerokosc
                rolka.save()
            except Exception as e:
                ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
                raise e
        if not dlugosc == '':
            try:
                rolka.dlugosc = float(dlugosc.replace(',', '.'))
                rolka.save()
            except Exception as e:
                message = "Podana długość jest nieprawidłowa"
                logowanie_bledu(request, message)
                print(message, request.POST)
        try:
            dziennik = Dziennik.objects.get(nr=int(dziennik_nr))
            if WpisyMagazyn.objects.filter(dziennik=dziennik, tkanina=rolka.tkanina).exists():
                created, wpis = WpisyMagazynPowiazania.objects.get_or_create(
                    dziennik=dziennik, rolka=rolka, aktywne=True)
                if not created:
                    return HttpResponse('Podany wpis już istnieje')
                created, log = Log.objects.get_or_create(dziennik_nr=dziennik.nr,
                                                         rolka_id=rolka.pk,
                                                         index_tkaniny=rolka.tkanina.index_sap,
                                                         dlugosc_rolki=rolka.dlugosc,
                                                         typ='WPIS_MAGAZYN_DODANIE')
            else:
                return HttpResponse('Na dzienniku nie ma tkaniny - {0}'.format(rolka.tkanina.nazwa))
            if rolka.status == 1:
                return HttpResponse("Rolka jest już wydana")
            if rolka.wpisymagazynpowiazania_set.filter(aktywne=True).count() > 0:
                rolka.status = 1
                created, log = Log.objects.get_or_create(rolka_id=rolka.pk,
                                                         index_tkaniny=rolka.tkanina.index_sap,
                                                         dlugosc_rolki=rolka.dlugosc,
                                                         typ='WPIS_MAGAZYN_WYDANIE')
                rolka.save()
                return HttpResponse("Tkanina wydana")
            else:
                return HttpResponse("Tkanina nie przypisana do dziennika")
        except Exception as e:
            print(e)
            ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
            return HttpResponse("Niepoprawna wartość szerokości")
    except Exception as e:
        print(e)
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse(e)

@csrf_exempt
def odbierz_tkanine(request):
    if request.POST['barcode'] == "9999999" and request.POST['nr_dziennika'] == "9999999":
        print("Odbior")
        return HttpResponse("Tkanina wydana") 
    try:
        rolka = Rolka.objects.get(pk=request.POST['barcode'])
        if rolka.status == 1:
            rolka.status = 0
            rolka.save()
            for each in rolka.wpisymagazynpowiazania_set.filter(data_zwrotu__isnull=True):
                each.aktywne = False
                each.data_zwrotu = timezone.now()
                each.save()
                created, log = Log.objects.get_or_create(dziennik_nr=each.dziennik.nr,
                                                         rolka_id=rolka.pk,
                                                         index_tkaniny=rolka.tkanina.index_sap,
                                                         dlugosc_rolki=rolka.dlugosc,
                                                         typ='WPIS_MAGAZYN_WYCOFANIE')
            created, log = Log.objects.get_or_create(rolka_id=rolka.pk,
                                                     index_tkaniny=rolka.tkanina.index_sap,
                                                     dlugosc_rolki=rolka.dlugosc,
                                                     typ='WPIS_MAGAZYN_ZWROT')
            return HttpResponse("edytuj")
        else:
            return HttpResponse("Tkanina nie wydana z magazyny lub zakonczona")
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse(e)

@csrf_exempt
def odpad(request):
    try:
        rolka = Rolka.objects.get(pk=request.POST['id_rolki'])
        dlugosc = request.POST['dlugosc']
        dlugosc = float(dlugosc.replace(',', '.'))
        if dlugosc > rolka.dlugosc:
            return HttpResponse("Podana rolka nie ma tyle długości".format(rolka.pk))
        Odpad.objects.create(rolka=rolka, ilosc=dlugosc)
        created, log = Log.objects.get_or_create(rolka_id=rolka.pk,
                                                 index_tkaniny=rolka.tkanina.index_sap,
                                                 dlugosc_rolki=rolka.dlugosc,
                                                 dlugosc_elementu=dlugosc,
                                                 typ='ODPAD')
        rolka.dlugosc -= dlugosc
        rolka.save()
        return HttpResponse("Dodano odpad do rolki {0}".format(rolka.pk))
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("Error")

@csrf_exempt
def wymianka(request):
    rolka = request.POST['id_rolki']
    karta_fgk = request.POST['karta_fgk']
    odpad = request.POST['odpad']
    odpad = True if odpad == 'True' else False
    rolka = Rolka.objects.get(pk=rolka)
    wynik_sql = functions.Tworzenie_zapytania(karta_fgk)
    dlugosc_do_wyciecia = round((float(wynik_sql[5]) / 1000), 2)
    try:
        if not odpad:
            if (rolka.dlugosc - dlugosc_do_wyciecia) >= 0:
                rolka.dlugosc = rolka.dlugosc - dlugosc_do_wyciecia
                rolka.save()
            else:
                return HttpResponse("Tkanina nie ma tyle metrów")
            created, log = Log.objects.get_or_create(rolka_id=rolka.pk,
                                                     index_tkaniny=rolka.tkanina.index_sap,
                                                     dlugosc_rolki=rolka.dlugosc,
                                                     dlugosc_elementu=dlugosc_do_wyciecia,
                                                     nr_fgk=karta_fgk,
                                                     typ='WYMIANKA')
            return HttpResponse("Karta 'wymiany' dodana dla {0}".format(rolka.pk))
        else:
            if (rolka._odpad() - dlugosc_do_wyciecia) >= 0:
                minusowy_odpad = -1 * dlugosc_do_wyciecia
                odpad = Odpad.objects.create(rolka=rolka, ilosc=minusowy_odpad)
                odpad.save()
                return HttpResponse("Pomniejszono odpad o {0} mb".format(dlugosc_do_wyciecia))
            else:
                return HttpResponse("Tkanina nie ma tyle metrów")
            created, log = Log.objects.get_or_create(rolka_id=rolka.pk,
                                                     index_tkaniny=rolka.tkanina.index_sap,
                                                     dlugosc_rolki=rolka.dlugosc,
                                                     dlugosc_elementu=dlugosc_do_wyciecia,
                                                     nr_fgk=karta_fgk,
                                                     typ='WYMIANKA_O')
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("Tkanina za krotka")
    return HttpResponse("Error")

@csrf_exempt
def informacje(request):
    pk = request.POST['barcode']
    try:
        rolka = Rolka.objects.get(pk=pk)
        return_arr = []
        status = ['Magazyn', 'Wydana', 'Zakonczna']
        infor_tupple = (rolka.lot,
                        rolka.nr_rolki,
                        rolka.dlugosc_poczatkowa,
                        rolka.dlugosc,
                        rolka.tkanina.nazwa,
                        rolka.data_dostawy if rolka.data_dostawy is not None else "Brak",
                        rolka.odpad_set.all().aggregate(Sum('ilosc'))['ilosc__sum'] if not rolka.odpad_set.all(
                        ).aggregate(Sum('ilosc'))['ilosc__sum'] is None else 0,
                        status[rolka.status],
                        rolka.szerokosc,
                        )
        return_a = "|".join(str(x) for x in infor_tupple)
        if rolka.wpisymagazynpowiazania_set.filter(aktywne=True).count() > 0:
            return_b = "|".join(
                str(x.dziennik.nr) for x in rolka.wpisymagazynpowiazania_set.filter(aktywne=True))
        else:
            return_b = ""
        return HttpResponse(return_a + ";" + return_b)
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("False")

@csrf_exempt
def informacje_tm_test(request):
    pk = request.POST['barcode']
    try:
        rolka = Rolka.objects.get(pk=pk)
        return_arr = []
        status = ['Magazyn', 'Wydana', 'Zakonczna']
        infor_tupple = (rolka.lot,
                        rolka.nr_rolki,
                        rolka.dlugosc_poczatkowa,
                        rolka.dlugosc,
                        rolka.tkanina.nazwa,
                        rolka.data_dostawy if rolka.data_dostawy is not None else "Brak",
                        rolka.odpad_set.all().aggregate(Sum('ilosc'))['ilosc__sum'] if not rolka.odpad_set.all(
                        ).aggregate(Sum('ilosc'))['ilosc__sum'] is None else 0,
                        status[rolka.status],
                        rolka.szerokosc,
                        )
        return_a = "|".join(str(x) for x in infor_tupple)
        print(return_a)
        if rolka.wpisymagazynpowiazania_set.filter(aktywne=True).count() > 0:
            return_b = "|".join(
                str(x.dziennik.nr) for x in rolka.wpisymagazynpowiazania_set.filter(aktywne=True))
        else:
            return_b = ""
        print(return_a, return_b)
        return HttpResponse(return_a + ";" + return_b)
    except Exception as e:
        print(request.__dir__())
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("False"+"#"+str(e))

@csrf_exempt
def sprawdz_wpis(request):
    rolka = request.POST['id_rolki']
    dziennik = request.POST['nr_dziennika']
    try:
        rolka = Rolka.objects.get(pk=rolka)
        dziennik = Dziennik.objects.get(nr=dziennik)
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("False")
    if not WpisyMagazynPowiazania.objects.filter(dziennik=dziennik, rolka=rolka, aktywne=True).exists():
        return HttpResponse("dziennik")
    else:
        return HttpResponse("OK")

@csrf_exempt
def nesting(request):
    try:
        rolka = Rolka.objects.get(pk=request.POST['id_rolki'])
        podpowiedzi = WpisyMagazynPowiazania.objects.filter(
            rolka__tkanina=rolka.tkanina, aktywne=True).exclude(rolka__pk=rolka.pk)
        if len(podpowiedzi) == 0:
            return HttpResponse("Brak podobnych tkanin")
        wynik_array = []
        for each in podpowiedzi:
            wynik_array.append(
                "{0} - {1} - {2} mb".format(each.dziennik.nr, each.rolka.pk, each.rolka.dlugosc))
        wynik = "\n".join(wynik_array)
        return HttpResponse(wynik)
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("#".join("Fasle", str(e)))

@csrf_exempt
def wpis_k(request):
    rolka = request.POST['id_rolki']
    rolka2 = request.POST['id_rolki2']
    dziennik = request.POST['nr_dziennika']
    karta_fgk = request.POST['karta_fgk']
    poza_dziennikiem = True if request.POST['poza_dziennikiem'] == 'True' else False
    wynik_sql = functions.Tworzenie_zapytania(karta_fgk)
    paczka_flag = False
    try:
        ilosc_do_wyciecia_str = round((float(wynik_sql[5]) / 1000), 1)
    except Exception as e:
        message = "Niepoprawna wartosc w komentarzu (e:0)"
        print(message, request.POST, sep = " // ")
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse(message)
    try:
        rolka = Rolka.objects.get(pk=rolka)
        rolka2 = Rolka.objects.get(pk=rolka2)
        dziennik = Dziennik.objects.get(nr=dziennik)
    except Exception as e:
        message = 'Wskazana druga rolka nie istnieje!'
        logowanie_bledu(request, e)
        return HttpResponse(message)
    komentarz = wynik_sql[3].strip()
    regex_pozycja = re.search(r'^(\d{1,2})', komentarz)
    if regex_pozycja:
        pozycja = int(regex_pozycja.group(1))
    else:
        message = "Bledny komentarz karty (e:25)"            
        print(message, request.POST, rolka, komentarz, sep = " // ")
        return HttpResponse(message)        
    regex_paczka_string = r'^\d{1,2}[ ]*[xX][ ]*(\d+)[ ]*[xX]*' + str(dziennik.nr) + r' (.+) X'
    regex_paczka = re.search(regex_paczka_string, komentarz)
    if regex_paczka:
        print("1")
        paczka_flag = True
    if rolka.tkanina == rolka2.tkanina:
        ilosc_pozostala = ilosc_do_wyciecia_str - rolka.dlugosc
        wpis = WpisySzwalnia.objects.get(dziennik=dziennik,
                                         pozycja=pozycja, tkanina=rolka.tkanina, ukonczone=False)
        if (rolka2.dlugosc - ilosc_pozostala) >= 0:
            rolka2.dlugosc -= ilosc_pozostala
        else:
            message = "Podana rolka jest za krótka! Brakuje {0} mb".format(abs(round((rolka2.dlugosc - ilosc_pozostala), 4)))
            print(message, request.POST, sep=" // ")
            return HttpResponse(message)
        typ = "FGK_laczone" if poza_dziennikiem == False else "FGK_laczone_poza"
        created, log = Log.objects.get_or_create(dziennik_nr=dziennik.nr,
                                                 wpis_szwalnia_id=wpis.pk,
                                                 rolka_id=rolka.pk,
                                                 index_tkaniny=rolka.tkanina.index_sap,
                                                 dlugosc_rolki=rolka.dlugosc,
                                                 dlugosc_elementu=rolka.dlugosc,
                                                 nr_fgk=karta_fgk,
                                                 typ=typ)
        created, log = Log.objects.get_or_create(dziennik_nr=dziennik.nr,
                                                 wpis_szwalnia_id=wpis.pk,
                                                 rolka_id=rolka2.pk,
                                                 index_tkaniny=rolka2.tkanina.index_sap,
                                                 dlugosc_rolki=rolka2.dlugosc,
                                                 dlugosc_elementu=ilosc_pozostala,
                                                 nr_fgk=karta_fgk,
                                                 typ=typ)
        rolka.dlugosc = 0
        rolka.zakonczona = True
        for each in rolka.wpisymagazynpowiazania_set.filter(aktywne=True):
            each.aktywne = False
            each.data_zwrotu = timezone.now()
        rolka.status = 2
        if paczka_flag:
            paczka = dziennik.paczki_set.filter(
                karta=karta_fgk, zakonczona=False, tkanina=rolka.tkanina.nazwa)
            if paczka.exists():
                podana_paczka = paczka.filter(karta=karta_fgk).first()
                podana_paczka.zakonczona = True
                podana_paczka.save()
                if dziennik.paczki_set.filter(zakonczona=False, pozycja=pozycja).count() == 0:
                    wpis.ukonczone = True
                    wpis.save()
            else:
                message = ""
                print(message, request.POST, wpis, paczka, sep = " // ")
                return HttpResponse("Podana paczka już została dodana!")
        else:
            wpis.ukonczone = True
            wpis.save()
        rolka.save()
        rolka2.save()
        return HttpResponse("OK")
    else:
        message = ""
        print(message, request.POST, rolka2, rolka, wpis, sep = " // ")
        return HttpResponse("Podane rolki są innego typu!")

@csrf_exempt
def wpis(request):
    rolka = request.POST['id_rolki']
    dziennik = request.POST['nr_dziennika']
    karta_fgk = request.POST['karta_fgk']
    paczka_flag = False
    poza_dziennikiem = True if request.POST['poza_dziennikiem'] == 'True' else False
    try:
        rolka = Rolka.objects.get(pk=rolka)
        tkanina = rolka.tkanina
    except Exception as e:
        message = "Podana tkanina nie istnieje (e:1)"
        print(message, request.POST, sep = " // ")
        return HttpResponse(message)
    if rolka.status == 0:
        message = "Podana tkanina nie została wydana z magazyny (e:2)"
        print(message, request.POST, rolka, rolka.status, sep = " // ")
        return HttpResponse(message)
    elif rolka.status == 2:
        message = "Tkanina oznaczona jako zakończona (e:3)"
        print(message, request.POST, rolka, rolka.get_status_display(), sep = " // ")
        return HttpResponse(message)
    dziennik = Dziennik.objects.get(nr=dziennik)
    wynik_sql = functions.Tworzenie_zapytania(karta_fgk)
    if wynik_sql:
        ilosc_do_wyciecia_str = round((float(wynik_sql[5]) / 1000), 1)
        komentarz = wynik_sql[3].strip()
        regex_paczka_string = r'^\d{1,2}[ ]*[xX][ ]*(\d+)[ ]*[xX]*' + str(dziennik.nr) + r' (.+) X'    
        regex_pozycja = re.search(r'^(\d{1,2})', komentarz)
        regex_paczka = re.search(regex_paczka_string, komentarz)     
        if regex_pozycja:
            pozycja = int(regex_pozycja.group(1))
        else:
            message = "Bledny komentarz karty (e:25)"            
            print(message, request.POST, rolka, komentarz, sep = " // ")
            return HttpResponse(message)
        if regex_paczka:
            #print(f"Ratio:{fuzzy_check(komentarz, rolka)}\n{rolka.tkanina.nazwa}\n{komentarz}") #Tester FuzzyWuzzy
            regex_komentarz = re.search(r'(^\d{1,2}[ ]*[xX][ ]*\d+[ ]*[xX]*' + str(dziennik.nr) + r' .+) X', komentarz)
            print(komentarz)
            paczki = functions.zapytanie_paczki(regex_komentarz.group(1).strip())            
            ilosc_paczek = int(regex_paczka.group(1))
            regex_tkanina = Tkanina.objects.filter(nazwa=regex_paczka.group(2).strip())
            if not len(paczki) == ilosc_paczek:
                print(request.POST, komentarz, sep = " // ")
                print(f"{karta_fgk} - Ilość wpisów bazie FGK nie równa komentarzowi FGK - {len(paczki)} : Komentarz - {ilosc_paczek}")
            if not regex_tkanina.exists():
                print(request.POST, komentarz, sep = " // ")
                print(f"{karta_fgk} - Podana w komentarzu tkanina {regex_paczka.group(2).strip()} nie odnaleziona w bazie danych")
                return HttpResponse("Podana w komentarzu nazwa tkaniny nie istnieje w bazie SAP!")
            regex_tkanina = regex_tkanina.first()
            for each in paczki:
                linia = each.split('\t')
                karta_fgk_temp = linia[0]
                _paczka, utworzona_paczka = Paczki.objects.get_or_create(dziennik=dziennik,
                                                                karta=karta_fgk_temp,
                                                                pozycja=pozycja,
                                                                tkanina=regex_tkanina.nazwa)
                if utworzona_paczka:
                    _paczka.data_utworzenia = timezone.now()
                    _paczka.save()
            paczka_flag = True
    else:
        message = "Nie odnaleziono wpisu (e:15)"
        print(message, request.POST)
        return HttpResponse(message)
    try:
        wpis = WpisySzwalnia.objects.get(dziennik=dziennik,
                                        pozycja=pozycja,
                                        tkanina=tkanina)
    except Exception as e:
        message = "Podany wpis nie istnieje w wewnetrznej (e:88)"
        print(message, request.POST, sep=' // ')
        return HttpResponse(message)        
    if wpis.ukonczone == True:
        message = "Wpis został już zakończony! (e:12)"
        print(message, request.POST, wpis, wpis.ukonczone, sep = " // ")
        return HttpResponse(message)
    if rolka.dlugosc < ilosc_do_wyciecia_str:
        message = "Łaczenie rolki (e:14)"
        print(message, request.POST, wpis, wpis.ukonczone, rolka, rolka.dlugosc, sep = " // ")
        return HttpResponse('rolka')
    if paczka_flag:        
        paczka = dziennik.paczki_set.filter(
            karta=karta_fgk, zakonczona=False)        
        if paczka.exists():
            podana_paczka = paczka.filter(karta=karta_fgk).first()
            podana_paczka.zakonczona = True
            podana_paczka.save()              
            pozostala_ilosc = dziennik.paczki_set.filter(zakonczona=False, pozycja=pozycja, tkanina=regex_tkanina.nazwa).count()  
            if pozostala_ilosc == 0:
                wpis.ukonczone = True
                wpis.save()
        else:
            message = "Podana paczka już została dodana! (e:20)"
            print(message, request.POST, paczka, pozostala_ilosc)
            return HttpResponse(message)
    else:
        wpis.ukonczone = True
        wpis.save()
    typ = "FGK" if poza_dziennikiem == False else "FGK_poza"
    created, log = Log.objects.get_or_create(dziennik_nr=dziennik.nr,
                                                wpis_szwalnia_id=wpis.pk,
                                                rolka_id=rolka.pk,
                                                index_tkaniny=rolka.tkanina.index_sap,
                                                dlugosc_rolki=rolka.dlugosc,
                                                dlugosc_elementu=ilosc_do_wyciecia_str,
                                                nr_fgk=karta_fgk,
                                                typ=typ)
    rolka.dlugosc = rolka.dlugosc - ilosc_do_wyciecia_str
    rolka.save()
    return HttpResponse("Poprawnie odjeto {0} mb tkaniny\nPozostało na rolce - {1} mb".format(ilosc_do_wyciecia_str, round(rolka.dlugosc,3)))
    # except Exception as e:
    #     message = "Podana kombinacja nie istnieje (e:60)"
    #     print(message, request.POST, rolka.tkanina.nazwa, wpis.id, wpis, e)
    #     return HttpResponse(message)
    # return HttpResponse("Error")

@csrf_exempt
def sprawdz_dziennik(request):
    dziennik = Dziennik.objects.get(nr=request.POST['nr_dziennika'])
    try:
        return HttpResponse(dziennik)
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("#".join("False", str(e)))

@csrf_exempt
def znajdz_barcode(request):
    try:
        barcode = request.POST['barcode']
        rolka = Rolka.objects.get(pk=barcode)
        str_return = [str(x) for x in
                    (rolka.pk,
                    rolka.tkanina.index_sap,
                    rolka.dlugosc,
                    rolka.lot,
                    rolka.nr_rolki,
                    rolka.data_dostawy,
                    rolka.szerokosc,
                    rolka.tkanina.nazwa,
                    rolka.nr_zamowienia,
                    rolka.dostawca)]   # dodany dostawca 21052019
        for i, x in enumerate(str_return):
            if x == "None":
                str_return[i] = ""
        print("Test edycji:", request.POST)
        return HttpResponse(",". join(str_return))
    except Exception as e:
        message = "Nie odnaleziono kodu rolki (e:23)"
        print(message, request.POST, e)
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("Error")
    return HttpResponse("")

@csrf_exempt
def drukuj_barcode(request):
    try:
        barcode = request.POST['barcode']
        barcode = int(barcode)
        if Rolka.objects.filter(barcode=barcode).exists():
            rolka = Rolka.objects.get(barcode=barcode)
            functions.generuj_obigowke(
                id=rolka.id,
                index=rolka.tkanina.index_sap,
                nazwa_tkaniny=rolka.tkanina.nazwa,
                dlugosc=rolka.dlugosc,
                szerokosc=rolka.szerokosc,
                lot=rolka.lot,
                rolka=rolka.nr_rolki,
                data_zamowienia=rolka.data_dostawy,
                qr_draw=True
            )

            functions.Bezposredni_wydruk(rolka)

            rolka.wydrukowana = True
            rolka.save()
            return HttpResponse('Etykieta ' + str(rolka.pk) + ' wydrukowana!')
        elif Rolka.objects.filter(pk=barcode).exists():
            print("Wydruk ze skanera")
            rolka_pk = Rolka.objects.get(pk=barcode)
            functions.Bezposredni_wydruk(rolka_pk)
            rolka_pk.wydrukowana = True
            rolka_pk.save()
            return HttpResponse('Etykieta ' + str(rolka_pk.pk) + ' wydrukowana!')
        else:
            return HttpResponse('Brak podanego identyfikatora')
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())

        #functions.generuj_obigowke('','',rolka.tkanina,rolka.lot,'',rolka.data_dostawy,rolka.szerokosc,rolka.dlugosc,True)
        functions.generuj_obigowke()
        return HttpResponse('Brak podanek identyfikatora')

@csrf_exempt
def edytuj(request):
    pk = request.POST['pk']
    lot = request.POST['lot']
    nr_rolki = request.POST['nr_rolki']
    dlugosc = request.POST['dlugosc']
    print(dlugosc,"123123123")
    szerokosc = request.POST['szerokosc']
    zamowienia = request.POST.get('zamowienie') # 21052019 TM byc moze do zmiany bez get i [] 
    #zamowienia = request.POST['zamowienie'] #< ---- na to
    data_direct = request.POST['data_dostawy'].replace('/', '-')
    dostawca = request.POST['dostawca']
    print(dlugosc)
    try:
        dlugosc = float(dlugosc.replace(',', '.'))
    except ValueError as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("Niepoprawne dane")
    
    print("dupa")
    nr_rolki = 0 if nr_rolki == "" else nr_rolki
    dlugosc = 0 if dlugosc == "" else dlugosc
    log = 0 if lot == "" else lot
    try:
        data_dostawy = datetime.strptime(
            data_direct.split()[0], '%y-%m-%d').date()
    except ValueError:
        data_dostawy = datetime.strptime(
            data_direct.split()[0], '%d.%m.%Y').date()
    rolka = Rolka.objects.get(pk=pk)
    if rolka:
        try:
            created, log = Log.objects.get_or_create(rolka_id=rolka.pk,
                                                     index_tkaniny=rolka.tkanina.index_sap,
                                                     dlugosc_rolki=rolka.dlugosc,
                                                     dlugosc_elementu=dlugosc,
                                                     typ='EDYCJA')
            rolka.dlugosc = dlugosc
            rolka.lot = lot
            rolka.nr_rolki = nr_rolki
            rolka.data_dostawy = data_dostawy
            rolka.szerokosc = szerokosc
            rolka.nr_zamowienia = zamowienia
            rolka.dostawca = dostawca # 21052019 TM
            rolka.save()
            return HttpResponse('Zapisano!')
        except Exception as e:
            ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
            return HttpResponse("Niepoprawne dane")

@csrf_exempt
def inwentura(request):
    pk = request.POST['pk']
    lot = request.POST['lot']
    nr_rolki = request.POST['nr_rolki']
    dlugosc = request.POST['dlugosc']
    szerokosc = request.POST['szerokosc']
    zamowienia = request.POST.get('zamowienie')
    data_direct = request.POST['data_dostawy'].replace('/', '-')
    typ_inwentury = request.POST['typ_inwentury']

    if typ_inwentury!="ZLICZANIE":
        typ_inwentury = "INWENTURA"

        
    try:
        dlugosc = float(dlugosc.replace(',', '.'))
    except ValueError as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("Niepoprawne dane")
    nr_rolki = 0 if nr_rolki == "" else nr_rolki
    print(dlugosc)
    dlugosc = 0 if dlugosc == "" else dlugosc
    log = 0 if lot == "" else lot
    #try:
    #    data_dostawy = datetime.strptime(
    #        data_direct.split()[0], '%y-%m-%d').date()
    #except ValueError:
    #    data_dostawy = datetime.strptime(
    #        data_direct.split()[0], '%d.%m.%Y').date()
    #        data_direct.split()[0], '%Y.%m.%d').date()
    rolka = Rolka.objects.get(pk=pk)
    if rolka:
        #try:
        if typ_inwentury == "INWENTURA":
            created, log = Log.objects.get_or_create(rolka_id=rolka.pk,
                                                     index_tkaniny=rolka.tkanina.index_sap,
                                                     dlugosc_rolki=rolka.dlugosc,
                                                     dlugosc_elementu=dlugosc,
                                                     typ='INWENTURA')
            #WAZNE - przy nastepnej inwenturze sprawdz, czy typ inwentury nie lapie literowki i czy wchodzi do
            # warunku

        else:
            #Rolka_zliczana.objects.get_or_create(tkanina_id=rolka.tkanina.pk)
            try:
                rolka_z = Rolka_zliczana.objects.get(pk=rolka.pk)
            except:
                print("Roleczka {}".format(rolka))
                print("tu jestem") 
                rolka_z = Rolka_zliczana.objects.create(pk=rolka.pk,
                                                   tkanina_id=rolka.tkanina.pk,
                                                    status=rolka.status,
                                                    data_dostawy=rolka.data_dostawy,
                                                    lot=rolka.lot,
                                                    nr_rolki=rolka.nr_rolki,
                                                    dlugosc=dlugosc,
                                                    szerokosc=rolka.szerokosc,
                                                    dlugosc_poczatkowa=rolka.dlugosc_poczatkowa,
                                                    barcode=rolka.barcode,
                                                    nr_zamowienia=rolka.nr_zamowienia,
                                                    zakonczona=rolka.zakonczona,
                                                    wydrukowana=rolka.wydrukowana,
                                                    do_usuniecia=rolka.do_usuniecia)
        
            
            if rolka:
                print(rolka_z)
                   
                rolka_z.dlugosc=dlugosc
                rolka_z.save()
        rolka.dlugosc = dlugosc
        rolka.lot = lot
        rolka.nr_rolki = nr_rolki
        #rolka.data_dostawy = data_dostawy
        rolka.szerokosc = szerokosc
        rolka.nr_zamowienia = zamowienia
        rolka.save()
        return HttpResponse('Zapisano!')
        #except Exception as e:
        #    ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        #    return HttpResponse("Niepoprawne dane")

@csrf_exempt
def proponuj(request):
    rolka = request.POST['id_rolki']
    dziennik = request.POST['dziennik']
    rolka = Rolka.objects.get(pk=rolka)
    dziennik = Dziennik.objects.get(nr=dziennik)
    z_dziennika = WpisyMagazynPowiazania.objects.filter(dziennik=dziennik,
                                                        rolka__tkanina=rolka.tkanina,
                                                        aktywne=True)
    rolki_z_dziennika = [each.rolka.nr_rolki for each in z_dziennika]
    zestaw_a = ",".join(each.rolka.nr_rolki)
    poza_dziennikiem = WpisyMagazynPowiazania.objects.filter(
        rolka__tkanina=rolka.tkanina, aktywne=True)

@csrf_exempt
def stoff(request):
    try:
        rolka = Rolka.objects.get(pk=request.POST['id_rolki'])
        pozycja = request.POST.get('pozycja')
        dziennik = Dziennik.objects.get(nr=request.POST['dziennik'])
        dlugosc = request.POST.get('dlugosc')
        dlugosc = float(dlugosc.replace(',', '.'))
        typ = 'STOFF'
        if dlugosc > rolka.dlugosc:
            return HttpResponse("Podana rolka nie ma tyle długości ({0})".format(rolka.dlugosc))
        wpis = WpisySzwalnia.objects.get(dziennik=dziennik, pozycja=pozycja, tkanina=rolka.tkanina)
        if not wpis.tkanina == rolka.tkanina:
            return HttpResponse("Niepoprawna tkanina: Podane - {0} / Powinno byc {1}".format(wpis.tkanina.nazwa, rolka.tkanina.nazwa))
        created, stoff = Stoff.objects.get_or_create(rolka=rolka, ilosc=dlugosc, dziennik=dziennik, pozycja=pozycja)
        if not created:
            return HttpResponse("Error! Sprawdz poprawność pozycji, wpis już ukończony")
        if wpis.ukonczone == False:
            wpis.ukonczone = True
            wpis.save()
        else:
            typ = 'STOFF_WEW'
        created, log = Log.objects.get_or_create(rolka_id=rolka.pk,
                                                 dziennik_nr = dziennik.nr,
                                                 index_tkaniny=rolka.tkanina.index_sap,
                                                 dlugosc_rolki=rolka.dlugosc,
                                                 dlugosc_elementu=dlugosc,
                                                 typ=typ)
        rolka.dlugosc -= dlugosc
        rolka.save()
        return HttpResponse("Dodano nowy wpis stoff dla rolki {0}".format(rolka.pk))
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse("Error: " + e)

@csrf_exempt
def nowa_rolka(request):
    lot = request.POST['lot']
    nr_rolki = request.POST['nr_rolki']
    dlugosc = request.POST['dlugosc']
    dlugosc = float(dlugosc.replace(',', '.'))
    zamowienie = request.POST.get('zamowienie')
    print(request.POST)
    data_dostawy = datetime.strptime(
        request.POST['data_dostawy'].split()[0], '%y-%m-%d').date()
    if lot == '' or nr_rolki == '' or dlugosc == '':
        return HttpResponse('Niepoprane dane')
    try:
        tkanina = Tkanina.objects.get(index_sap=request.POST['index_sap'])
    except Exception as e:
        return HttpResponse('Podana tkanina nie istnieje')
    try:
        rolka = Rolka.objects.create(lot=lot,
                                     nr_rolki=nr_rolki,
                                     tkanina=tkanina,
                                     dlugosc=dlugosc,
                                     data_dostawy=data_dostawy,
                                     nr_zamowienia=zamowienie)
        functions.Bezposredni_wydruk(rolka)
        return HttpResponse('Etykieta wydrukowana')
    except Exception as e:
        ErrorLog.objects.create(error=e, post=request.POST, funkcja=request.get_full_path())
        return HttpResponse('Error')

@csrf_exempt
def tkaniny(request):
	tkanina = Tkanina.objects.order_by('-index_sap')
	return render(request, 'magazyntkanin/tkaniny.html', {'tkanina': tkanina})

@csrf_exempt
def tkaniny_edit(request, nr_tkaniny):
    if request.method == 'POST':
        tkanina = Tkanina.objects.get(pk=nr_tkaniny)
        form = TkaninaForm(request.POST, instance=tkanina)
        if form.is_valid():
            form.save()
            return render(request, 'magazyntkanin/tkaniny_edit.html', {'form': form, 'nr': nr_tkaniny})
        else:
            return render(request, 'magazyntkanin/tkaniny_edit.html', {'form': form, 'nr': nr_tkaniny})
    tkanina = Tkanina.objects.get(pk=nr_tkaniny)
    form = TkaninaForm(instance=tkanina)
    return render(request, 'magazyntkanin/tkaniny_edit.html', {'form': form, 'nr': nr_tkaniny})

@csrf_exempt
def tkaniny_new(request):
    if request.method == "POST":
        form = TkaninaForm(request.POST)
        if form.is_valid():
            vtdata = form.save(commit=False)

            vtdata.save()
            return redirect('magazyntkanin/tkaniny.html')
    else:
        form = TkaninaForm()
    return render(request, 'magazyntkanin/tkaniny_new.html', {'form': form})

@csrf_exempt
def magazyn_wymianki(request):
    if request.method == 'POST':
        import json
        # data = json.loads(request.body.decode("utf-8"))
        data = request.POST
        rolka = data['rolka']
        check = data.get('check')
        try:
            rolka = Rolka.objects.get(pk=rolka)
        except Exception as e:
            message = "Podana rolka nie istnieje (e:34)"            
            print(message, request.body.decode("utf-8"), e)           
            return HttpResponse(message)
        if rolka.zakonczona or rolka.dlugosc == 0:
            message = "Rolka jest zakończona lub ma 0 dł. (e:37)"
            print(message, request.body.decode("utf-8"))           
            return HttpResponse(message)
        if check == 'True':
            return HttpResponse(rolka.dlugosc)
        dlugosc = data.get('dlugosc')
        calosc = data.get('all')
        status = int(data.get('status'))                    
        if calosc == 'True':
            dlugosc = rolka.dlugosc
            rolka.zakonczona = True      
            rolka.status = status
        try:                
            dlugosc = float(dlugosc)                
            if dlugosc > rolka.dlugosc:
                message = f"Rolka za krótka - posiada tylko {rolka.dlugosc} mb (e:20)"
                print(message, request.body.decode("utf-8"))
                return HttpResponse(message)    
        except Exception as e:
            message = f"Niepoprawna długość (e:20)\n{e}"            
            print(message, request.body.decode("utf-8"), e)
            return HttpResponse(message)
        rolka.dlugosc = rolka.dlugosc - dlugosc
        typ = 'WYDANIE_MAG_' + WZ[status][1].upper()
        try:
            rolka.save()
            created, log = Log.objects.get_or_create(rolka_id = rolka.pk,
                                                    index_tkaniny = rolka.tkanina.index_sap,
                                                    dlugosc_rolki = rolka.dlugosc,
                                                    dlugosc_elementu = dlugosc,
                                                    typ = typ)            
        except Exception as e:                    
            message = "Zapisanie danych niepoprawne (e:39)"
            print(message, request.body.decode("utf-8"), e)
            return HttpResponse(message)
        return HttpResponse(f'{rolka.tkanina.nazwa} wydana poprawnie {dlugosc} mb - {typ.split("_")[-1]}')        
    return HttpResponse("Brak danych")

@csrf_exempt
def log_info(request):
    if request.method == 'POST':
        rolka_id = request.POST.get('rolka_id')
        rolka = Rolka.objects.filter(pk=rolka_id)
        if rolka.exists():
            return_string = ""
            data = []
            wpisy = Log.objects.filter(rolka_id=rolka_id, typ__startswith="FGK").order_by('-timestamp')
            print(wpisy,sep='\n')
            for each in wpisy:
                data.append([each.timestamp.strftime('%d-%m-%Y'), each.nr_fgk, each.dlugosc_elementu, round(each.dlugosc_rolki-each.dlugosc_elementu, 2)])
            for each in data:
                line = f'{each[0]} // {each[1]}\n{each[2]}mb// {each[3]}mb'
                return_string = return_string + line + '\n------------\n'
        return HttpResponse(return_string)
    return HttpResponse("")

def czysc_zliczanie(request):
    url='magazyntkanin/inwentura_rep.html'
    context = {
    }
    rolka = Rolka_zliczana.objects.all()   
    if request.method == 'GET':
        for i in rolka:
            if request.GET.get(str(i.pk))=="on":
                Rolka_zliczana.objects.filter(pk=i.pk).delete()
                

    return render(request,url,context)
