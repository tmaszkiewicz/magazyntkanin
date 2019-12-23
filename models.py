from django.db import models
from django.db.models import Sum
from django import forms
from.validators import validate_file_extension
# Create your models here.


STATUS = (
    (0, 'Magazyn'),
    (1, 'Wydany'),
    (2, 'Zakończony')
)

WZ = (
    (0, 'Wydanie wewnętrzne'),
    (1, 'Wymianka'),
    (2, 'Sprzedaż'),
    (3, 'Wzorniki'),    
)

# class Status(models.Model):
# """
# Description: Baza slownikowa dla statusow
# """
# nazwa = models.CharField(max_length=50)

# class Meta:
#     # verbose_name_plural = 'Statusy'


class Dziennik(models.Model):
    """
    Description: Baza dziennikow
    """
    nr = models.IntegerField()
    data = models.DateField(default=None, blank=True, null=True)
    lokalizacja = models.BooleanField(default=False)

    def ilosc_paczek(self):
        return self.paczki_set.all()
    
    def ilosc_paczek_zakonczonych(self):
        return self.paczki_set.filter(zakonczona=True)

    def suma_tkanin(self):
        return self.wpisymagazynpowiazania_set.values('rolka').annotate(total=Sum('rolka__dlugosc')).order_by('total')
    class Meta:
        verbose_name_plural = 'Dzienniki'

    def __str__(self):
        return str(self.nr)


class Tkanina(models.Model):
    """
    Description: Baza z indeksami i nazwami tkanin
    """
    index_sap = models.IntegerField(unique=True)
    nazwa = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = 'Tkaniny'

    def ilosc_na_magazynie(self):
        return self.rolka_set.filter(dlugosc__gt=0).filter(zakonczona=False).aggregate(Sum('dlugosc'))['dlugosc__sum']

    def sztuk(self):
        return self.rolka_set.filter(dlugosc__gt=0).count()

    def __str__(self):
        return str(' / ').join((str(self.index_sap), self.nazwa))


class Rolka(models.Model):
    """
    Description: Baza danych rolek i wszystkie informacje o rolkach
    """
    tkanina = models.ForeignKey(Tkanina)
    status = models.IntegerField(default=0, choices=STATUS)
    wydanie = models.IntegerField(default=0, choices=WZ)
    data_dostawy = models.DateField(default=None, blank=True, null=True)
    lot = models.CharField(max_length=30, blank=True, null=True)
    nr_rolki = models.IntegerField(default=0)
    dlugosc = models.FloatField(default=0)
    szerokosc = models.IntegerField(default=0)
    dlugosc_poczatkowa = models.FloatField(blank=True, null=True)
    barcode = models.BigIntegerField(default=None, null=True, blank=True)
    nr_zamowienia = models.CharField(max_length=50, blank=True, null=True)
    zakonczona = models.BooleanField(default=False)
    wydrukowana = models.BooleanField(default=False)
    do_usuniecia = models.BooleanField(default=False)
    dostawca = models.CharField(max_length=30, blank=True, null=True)
    class Meta:
        verbose_name_plural = 'Rolki'

    def _odpad(self):
        return self.odpad_set.all().aggregate(Sum('ilosc'))['ilosc__sum']

    def w_metrach(self):
        return self.dlugosc

    def w_cm(self):
        return self.dlugosc / 100

    def w_mm(self):
        return self.dlugosc / 1000

    def metry_dla_daty(self):
        return Rolka.objects.filter(data_dostawy=self.data_dostawy,
                                    tkanina=self.tkanina).aggregate(Sum('dlugosc'))['dlugosc__sum']
    
    def suma(self):
        return Rolka.objects.filter(tkanina=self.tkanina, nr_zamowienia=self.nr_zamowienia).aggregate(Sum('dlugosc'))['dlugosc__sum']
    
    def ilosc_belek(self):
        return Rolka.objects.filter(tkanina=self.tkanina, nr_zamowienia=self.nr_zamowienia).order_by('tkanina')

    def kolor(self):
        color = ""
        if self.zakonczona:
            color = "red" 
        return color

    def __str__(self):
        return_string = (str(self.pk),
                         str(self.tkanina),
                         self.lot,
                         str(self.dlugosc))
        # return str('/').join(return_string)
        return str(self.pk) + " / " + str(self.tkanina)


class Rolka_usunieta(models.Model):
    """
    TM 03.01.2019
    Description: Baza danych rolek historycznych, usunietych po inwentaryzacjach
    """
    tkanina = models.ForeignKey(Tkanina)
    status = models.IntegerField(default=0, choices=STATUS)
    wydanie = models.IntegerField(default=0, choices=WZ)
    data_dostawy = models.DateField(default=None, blank=True, null=True)
    lot = models.CharField(max_length=30, blank=True, null=True)
    nr_rolki = models.IntegerField(default=0)
    dlugosc = models.FloatField(default=0)
    szerokosc = models.IntegerField(default=0)
    dlugosc_poczatkowa = models.FloatField(blank=True, null=True)
    barcode = models.BigIntegerField(default=None, null=True, blank=True)
    nr_zamowienia = models.CharField(max_length=50, blank=True, null=True)
    zakonczona = models.BooleanField(default=False)
    wydrukowana = models.BooleanField(default=False)
    do_usuniecia = models.BooleanField(default=False)
    dostawca = models.CharField(max_length=30, blank=True, null=True)
    class Meta:
        verbose_name_plural = 'Rolki usuniete'

    def _odpad(self):
        return self.odpad_set.all().aggregate(Sum('ilosc'))['ilosc__sum']

    def w_metrach(self):
        return self.dlugosc

    def w_cm(self):
        return self.dlugosc / 100

    def w_mm(self):
        return self.dlugosc / 1000

    def metry_dla_daty(self):
        return Rolka.objects.filter(data_dostawy=self.data_dostawy,
                                    tkanina=self.tkanina).aggregate(Sum('dlugosc'))['dlugosc__sum']
    
    def suma(self):
        return Rolka.objects.filter(tkanina=self.tkanina, nr_zamowienia=self.nr_zamowienia).aggregate(Sum('dlugosc'))['dlugosc__sum']
    
    def ilosc_belek(self):
        return Rolka.objects.filter(tkanina=self.tkanina, nr_zamowienia=self.nr_zamowienia).order_by('tkanina')

    def kolor(self):
        color = ""
        if self.zakonczona:
            color = "red" 
        return color


    def __str__(self):
        return_string = (str(self.pk),
                         str(self.tkanina),
                         self.lot,
                         str(self.dlugosc))
        # return str('/').join(return_string)
        return str(self.pk) + " / " + str(self.tkanina)



class Rolka_zliczana(models.Model):
    """
    TM 13.02.2019
    Description: Rolka tymczasowa, do zliczania bez inwentaryzacji
    """
    tkanina = models.ForeignKey(Tkanina)
    status = models.IntegerField(default=0, choices=STATUS)
    wydanie = models.IntegerField(default=0, choices=WZ)
    data_dostawy = models.DateField(default=None, blank=True, null=True)
    lot = models.CharField(max_length=30, blank=True, null=True)
    nr_rolki = models.IntegerField(default=0)
    dlugosc = models.FloatField(default=0)
    szerokosc = models.IntegerField(default=0)
    dlugosc_poczatkowa = models.FloatField(blank=True, null=True)
    barcode = models.BigIntegerField(default=None, null=True, blank=True)
    nr_zamowienia = models.CharField(max_length=50, blank=True, null=True)
    zakonczona = models.BooleanField(default=False)
    wydrukowana = models.BooleanField(default=False)
    do_usuniecia = models.BooleanField(default=False)
    dostawca = models.CharField(max_length=30, blank=True, null=True)
    class Meta:
        verbose_name_plural = 'Rolki zliczane'

    def _odpad(self):
        return self.odpad_set.all().aggregate(Sum('ilosc'))['ilosc__sum']

    def w_metrach(self):
        return self.dlugosc

    def w_cm(self):
        return self.dlugosc / 100

    def w_mm(self):
        return self.dlugosc / 1000

    def metry_dla_daty(self):
        return Rolka.objects.filter(data_dostawy=self.data_dostawy,
                                    tkanina=self.tkanina).aggregate(Sum('dlugosc'))['dlugosc__sum']
    
    def suma(self):
        return Rolka.objects.filter(tkanina=self.tkanina, nr_zamowienia=self.nr_zamowienia).aggregate(Sum('dlugosc'))['dlugosc__sum']
    
    def ilosc_belek(self):
        return Rolka.objects.filter(tkanina=self.tkanina, nr_zamowienia=self.nr_zamowienia).order_by('tkanina')

    def kolor(self):
        color = ""
        if self.zakonczona:
            color = "red" 
        return color


    def __str__(self):
        return_string = (str(self.pk),
                         str(self.tkanina),
                         self.lot,
                         str(self.dlugosc))
        # return str('/').join(return_string)
        return str(self.pk) + " / " + str(self.tkanina)

class Paczki(models.Model):
    """
    Description: Informacje dotyczace odpadow tkaniny
    """
    dziennik = models.ForeignKey(Dziennik)
    karta = models.CharField(max_length=50)
    pozycja = models.CharField(max_length=50)
    zakonczona = models.BooleanField(default=False)
    tkanina = models.CharField(max_length=50, default="")
    data_utworzenia = models.DateTimeField(blank=True, null=True, default=None)

    def kolor(self):
        if self.zakonczona == True:
            return "color: #cf3438"

    def ilosc(self):
        return Paczki.objects.filter(dziennik=self.dziennik, pozycja=self.pozycja).count()
    
    def ilosc_zakoczonych(self):
        return Paczki.objects.filter(dziennik=self.dziennik, pozycja=self.pozycja, zakonczona=True).count()

    class Meta:
        verbose_name = "Paczki"
        verbose_name_plural = "Paczki"

    def __str__(self):
        # return "{0} / {1} / {3}".format(self.dziennik.nr, self.karta, self.pozycja)
        return "{0} / {1} / {2}".format(self.dziennik.nr, self.karta, self.pozycja)


class Odpad(models.Model):
    """
    Description: Informacje dotyczace odpadow tkaniny
    """
    rolka = models.ForeignKey(Rolka)
    ilosc = models.FloatField(default=0)

    class Meta:
        verbose_name = "Odpad"
        verbose_name_plural = "Odpady"

    def __str__(self):
        return "{0} / {1}".format(self.rolka.pk, str(self.ilosc))


class Stoff(models.Model):
    """
    Description: Informacje dotyczace funkcji Stoff tkaniny
    """
    rolka = models.ForeignKey(Rolka)
    dziennik = models.ForeignKey(Dziennik, default=None, null=True, blank=True)
    pozycja = models.IntegerField()
    ilosc = models.FloatField(default=0)

    class Meta:
        verbose_name = "Stoff"
        verbose_name_plural = "Stoffy"

    def __str__(self):
        return "{0} / {1}".format(self.rolka.pk, str(self.ilosc))


class WpisySzwalnia(models.Model):
    """
    Description: Wpisy dzinnika
    """
    dziennik = models.ForeignKey(Dziennik)
    tkanina = models.ForeignKey(Tkanina)
    pozycja = models.IntegerField()
    TA = models.IntegerField()
    ilosc = models.IntegerField()
    tura = models.IntegerField()
    ukonczone = models.BooleanField(default=False)

    def kolorowanie_tabeli(self):
        if self.pozycja % 2 == 0:
            return 'lightgray'
        else:
            return ''

    class Meta:
        verbose_name_plural = 'Wpisy dziennika - Szwalnia'

    def __str__(self):
        return " / ".join((str(self.dziennik), str(self.tkanina), str(self.pozycja), str(self.TA)))


class WpisyMagazyn(models.Model):
    """
    Description: Wpisy dzinnika
    """
    dziennik = models.ForeignKey(Dziennik)
    tkanina = models.ForeignKey(Tkanina)
    ilosc = models.FloatField(default=0)

    def pozostalo_metrow(self):
        rolki = WpisyMagazynPowiazania.objects.filter(
            dziennik=self.dziennik, rolka__tkanina=self.tkanina, aktywne=True)
        dlugosc = self.ilosc
        for each in rolki:
            dlugosc -= each.rolka.w_metrach()
        return dlugosc

    def powiazania_wg_tkaniny(self):
        rolki = WpisyMagazynPowiazania.objects.filter(
            dziennik=self.dziennik, rolka__tkanina=self.tkanina, aktywne=True)
        return rolki

    def historia(self):
        rolki = WpisyMagazynPowiazania.objects.filter(
            dziennik=self.dziennik, rolka__tkanina=self.tkanina).order_by('rolka__nr_rolki')
        wpisy = []            
        for each in rolki:
            info = {}
            info['rolka'] = each.rolka
            # info['log'] = Log.objects.filter(dziennik_nr=self.dziennik.nr, rolka_id=each.rolka.pk, typ="WPIS_MAGAZYN_DODANIE")
            info['log'] = Log.objects.filter(dziennik_nr=self.dziennik.nr, rolka_id=each.rolka.pk, typ="WPIS_MAGAZYN_DODANIE").last()
            wpisy.append(info)
        return wpisy


    def zwroty(self):
        rolki = WpisyMagazynPowiazania.objects.filter(
            dziennik=self.dziennik, rolka__tkanina=self.tkanina, data_zwrotu__isnull=False)
        return rolki

    def css_color(self):
        if self.pozostalo_metrow() < 0:
            return "#dff0d8"
        else:
            return "#FFFFFF"

    class Meta:
        verbose_name_plural = 'Wpisy dziennika - Magazyn'

    def __str__(self):
        return " / ".join((str(self.dziennik), str(self.tkanina), str(self.ilosc) + "m"))


class WpisyMagazynPowiazania(models.Model):
    dziennik = models.ForeignKey(Dziennik)
    rolka = models.ForeignKey(Rolka)
    aktywne = models.BooleanField(default=False)
    data_wydania = models.DateTimeField(auto_now_add=True)
    data_zwrotu = models.DateTimeField(blank=True, null=True, default=None)

    class Meta:
        verbose_name = "Powiazanie z magazynem"
        verbose_name_plural = "Powiazania magazynowe"

    def __str__(self):
        return " / ".join((str(x) for x in (self.rolka, self.aktywne)))


class Log(models.Model):
    """
    Description: Opis wszystkich dzialan
    """
    dziennik_nr = models.IntegerField(default=None, null=True)
    wpis_szwalnia_id = models.IntegerField(default=None, null=True)
    rolka_id = models.IntegerField(default=None, null=True)
    index_tkaniny = models.IntegerField(default=None, null=True)
    dlugosc_rolki = models.FloatField(default=None, null=True)
    nr_fgk = models.CharField(max_length=30)
    dlugosc_elementu = models.FloatField(default=None, null=True)
    typ = models.CharField(default=True, max_length=50)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Logi'

    def __str__(self):
        return "{0} / {1} / {2}".format(self.rolka_id, self.typ, self.timestamp.strftime("%d-%m-%Y %H:%M:%S"))


class TkaninyXlsx(models.Model):
        description = models.CharField(max_length=255, blank=True)
    #os.path.join('.', 'magazyntkanin', 'pliki', 'euro')
        document = models.FileField(upload_to='magazyntkanin/pliki/euro', validators=[validate_file_extension])
        uploaded_at = models.DateTimeField(auto_now_add=True)
        data_dostawy = models.DateField(default=None, blank=True, null=True)

class FgkComment(models.Model):
        job_name  = models.CharField(max_length=255, blank=True)
        job_comm  = models.CharField(max_length=255, blank=True)
        job_mrklen = models.CharField(max_length=255, blank=True)
        job_mrkwidth = models.CharField(max_length=255, blank=True)
        job_eff = models.CharField(max_length=255, blank=True)
        job_partqnt = models.CharField(max_length=255, blank=True)
        job_cr_date = models.CharField(max_length=255, blank=True)
        job_mrknotchqty = models.CharField(max_length=255, blank=True)
        job_cutt= models.CharField(max_length=255, blank=True)
        
        
class FgkLine(models.Model):
        job_name  = models.CharField(max_length=255, blank=True)
        part  = models.CharField(max_length=255, blank=True)
        count = models.CharField(max_length=255, blank=True)
        
        class Meta:
            verbose_name_plural = 'FgkLines'

        def __str__(self):
            return "{0} / {1} / {2}".format(self.job_name, self.part, self.count)

# -------------- FORMS --------------
class RolkaForm(forms.ModelForm):
    class Meta:
        model = Rolka
        labels = {
            "dlugosc": "Dlugość (Mb)",
            "szerokosc": "Szerokosc (mm)",
        }
        fields = ('data_dostawy',
                  'lot',
                  'nr_rolki',
                  'szerokosc',
                  'dlugosc',
                  'barcode',
                  'nr_zamowienia'
                  )
        # fields = ('__all__')

class RolkaForm_all(forms.ModelForm):
    class Meta:
        model = Rolka
        labels = {
            "dlugosc": "Dlugość (Mb)",
            "szerokosc": "Szerokosc (mm)",
        }
        fields = ('__all__')

class TkaninaForm(forms.ModelForm):
    class Meta:
        model = Tkanina
        labels = {
            "index_sap": "Indeks SAP",
            "nazwa": "Nazwa",
        }
        fields = ('index_sap',
                  'nazwa',
                  )
# fields = ('__all__')

class XlsBrowserForm(forms.ModelForm):
    class Meta:
        model = TkaninyXlsx
        fields = ('description',
                  'document',
                  'data_dostawy',
                  )


class FgkLineForm(forms.ModelForm):
    class Meta:
        model = FgkLine
        fields = ('job_name',
                  'part',
                  'count',
                  )
class ErrorLog(models.Model):
    error = models.CharField(max_length=250)
    post = models.CharField(max_length=500)
    funkcja = models.CharField(max_length=70)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Log"
        verbose_name_plural = "Logs"

    def __str__(self):
        return "{0} / {1}".format(self.data, self.error)

