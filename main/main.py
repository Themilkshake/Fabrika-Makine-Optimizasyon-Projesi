import sys
import random
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                            QScrollArea, QMessageBox, QDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPalette, QColor
import numpy as np
from deap import base, creator, tools, algorithms
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import os

# Stil sabitleri
STIL = {
    'BIRINCIL_RENK': '#2196F3',  # Mavi
    'BIRINCIL_KOYU': '#1976D2',   # Koyu mavi
    'BASARI_RENK': '#4CAF50',  # Yeşil
    'BASARI_KOYU': '#45a049',   # Koyu yeşil
    'ARKAPLAN_RENK': '#f5f5f5',      # Açık gri
    'YAZI_RENK': '#333333',    # Koyu gri
    'KENAR_YARICAP': '4px',
    'DOLGU': '5px 15px',
    'YAZI_BOYUT': '12px'
}

# Ortak buton stili
BUTON_STIL = f"""
    QPushButton {{
        background-color: {STIL['BIRINCIL_RENK']};
        color: white;
        padding: {STIL['DOLGU']};
        font-size: {STIL['YAZI_BOYUT']};
        border-radius: {STIL['KENAR_YARICAP']};
        min-height: 30px;
    }}
    QPushButton:hover {{
        background-color: {STIL['BIRINCIL_KOYU']};
    }}
"""

# Giris alani stili
GIRIS_STIL = f"""
    QLineEdit {{
        padding: 5px;
        border: 1px solid #ccc;
        border-radius: {STIL['KENAR_YARICAP']};
        background-color: white;
        font-size: {STIL['YAZI_BOYUT']};
    }}
    QLineEdit:focus {{
        border: 1px solid {STIL['BIRINCIL_RENK']};
    }}
"""

# Etiket stili
ETIKET_STIL = f"""
    QLabel {{
        color: {STIL['YAZI_RENK']};
        font-size: {STIL['YAZI_BOYUT']};
        padding: 2px;
    }}
"""

# Genetik algoritma sınıflarını temizleme fonksiyonu
def genetik_temizle():
    if 'FitnessMin' in creator.__dict__:
        del creator.FitnessMin
    if 'Individual' in creator.__dict__:
        del creator.Individual

class SonucPenceresi(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Optimizasyon Sonuçları")
        self.setGeometry(200, 200, 1000, 800)
        self.parent = parent
        
        # Arka plan rengini ayarla
        self.setStyleSheet(f"background-color: {STIL['ARKAPLAN_RENK']};")
        
        # Ana düzen
        ana_duzen = QVBoxLayout()
        ana_duzen.setSpacing(10)
        ana_duzen.setContentsMargins(15, 15, 15, 15)
        
        # Üst araç çubuğu
        arac_cubugu = QHBoxLayout()
        
        # Tam ekran butonu
        self.tam_ekran_btn = QPushButton("🗖")  # Unicode tam ekran simgesi
        self.tam_ekran_btn.setFixedSize(30, 30)
        self.tam_ekran_btn.setStyleSheet(BUTON_STIL + """
            QPushButton {
                font-size: 16px;
                padding: 0px;
            }
        """)
        self.tam_ekran_btn.clicked.connect(self.tam_ekran_degistir)
        arac_cubugu.addWidget(self.tam_ekran_btn)
        
        arac_cubugu.addStretch()
        ana_duzen.addLayout(arac_cubugu)
        
        # Grafik kapsayıcı
        grafik_kapsayici = QWidget()
        grafik_kapsayici.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            padding: 10px;
        """)
        grafik_duzen = QVBoxLayout(grafik_kapsayici)
        
        # Grafik gösterimi için widget
        self.sekil = plt.figure(figsize=(8, 8))
        self.tuval = FigureCanvas(self.sekil)
        grafik_duzen.addWidget(self.tuval)
        ana_duzen.addWidget(grafik_kapsayici)
        
        # Sonuçlar için kaydırma alanı
        kaydirma = QScrollArea()
        kaydirma.setWidgetResizable(True)
        kaydirma.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                border-radius: 5px;
            }
        """)
        
        self.sonuclar_widget = QWidget()
        self.sonuclar_widget.setStyleSheet(f"background-color: {STIL['ARKAPLAN_RENK']};")
        self.sonuclar_duzen = QVBoxLayout(self.sonuclar_widget)
        kaydirma.setWidget(self.sonuclar_widget)
        ana_duzen.addWidget(kaydirma)
        
        # Alt araç çubuğu için kapsayıcı
        alt_kapsayici = QWidget()
        alt_kapsayici.setFixedHeight(50)
        alt_duzen = QHBoxLayout(alt_kapsayici)
        alt_duzen.setContentsMargins(0, 0, 0, 0)
        
        # Ana Sayfa butonu
        ana_sayfa_buton = QPushButton("Ana Sayfaya Dön")
        ana_sayfa_buton.setStyleSheet(f"""
            QPushButton {{
                background-color: {STIL['BASARI_RENK']};
                color: white;
                padding: {STIL['DOLGU']};
                font-size: {STIL['YAZI_BOYUT']};
                border-radius: {STIL['KENAR_YARICAP']};
                min-height: 30px;
                max-width: 150px;
            }}
            QPushButton:hover {{
                background-color: {STIL['BASARI_KOYU']};
            }}
        """)
        ana_sayfa_buton.clicked.connect(self.ana_sayfaya_don)
        
        alt_duzen.addStretch()
        alt_duzen.addWidget(ana_sayfa_buton)
        alt_duzen.addStretch()
        
        ana_duzen.addWidget(alt_kapsayici)
        
        self.setLayout(ana_duzen)
        self.tam_ekran_mi = False
    
    def tam_ekran_degistir(self):
        if self.tam_ekran_mi:
            self.showNormal()
            self.tam_ekran_btn.setText("🗖")
        else:
            self.showFullScreen()
            self.tam_ekran_btn.setText("🗗")
        self.tam_ekran_mi = not self.tam_ekran_mi
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape and self.tam_ekran_mi:
            self.showNormal()
            self.tam_ekran_btn.setText("🗖")
            self.tam_ekran_mi = False
        else:
            super().keyPressEvent(event)
    
    def ana_sayfaya_don(self):
        if self.parent:
            self.parent.ana_pencere_sifirla()
        self.close()
    
    def sonuclari_goster(self, makine_verisi, en_iyi_cozum, en_iyi_uygunluk, nesiller, min_uygunluk, ort_uygunluk, toplam_makine):
        # Grafikleri temizle
        self.sekil.clear()
        
        # 3 grafik için alt çizim oluştur
        gs = self.sekil.add_gridspec(3, 1, height_ratios=[1, 1, 1], hspace=0.5)
        
        # 1. Grafik: Makine dağılımı
        ax1 = self.sekil.add_subplot(gs[0])
        isimler = [veri['isim'] for veri in makine_verisi]
        sayilar = en_iyi_cozum
        cubuklar1 = ax1.bar(isimler, sayilar)
        ax1.set_title('Optimum Makine Dağılımı', pad=5, fontsize=9)
        ax1.set_xlabel('Makine Türü', fontsize=8)
        ax1.set_ylabel('Makine Sayısı', fontsize=8)
        ax1.tick_params(axis='both', which='major', labelsize=7)
        plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Çubuk değerlerini göster
        for cubuk in cubuklar1:
            yukseklik = cubuk.get_height()
            ax1.text(cubuk.get_x() + cubuk.get_width()/2., yukseklik,
                    f'{int(yukseklik)}',
                    ha='center', va='bottom', fontsize=7)
        
        # 2. Grafik: Genetik algoritma ilerlemesi
        ax2 = self.sekil.add_subplot(gs[1])
        ax2.plot(nesiller, min_uygunluk, 'b-', label='En İyi Uygunluk')
        ax2.plot(nesiller, ort_uygunluk, 'r-', label='Ortalama Uygunluk')
        ax2.set_title('Genetik Algoritma İlerlemesi', pad=5, fontsize=9)
        ax2.set_xlabel('Nesil', fontsize=8)
        ax2.set_ylabel('Uygunluk (Toplam Süre)', fontsize=8)
        ax2.tick_params(axis='both', which='major', labelsize=7)
        ax2.legend(fontsize=7, loc='upper right')
        
        # 3. Grafik: İşlem ve Bekleme Süreleri
        ax3 = self.sekil.add_subplot(gs[2])
        x = np.arange(len(isimler))
        genislik = 0.35
        
        # İşlem süreleri
        islem_sureleri = [veri['islem_suresi'] * sayi for veri, sayi in zip(makine_verisi, en_iyi_cozum)]
        cubuklar2 = ax3.bar(x - genislik/2, islem_sureleri, genislik, label='İşlem Süresi')
        
        # Bekleme süreleri
        bekleme_sureleri = [veri['bekleme_suresi'] * sayi for veri, sayi in zip(makine_verisi, en_iyi_cozum)]
        cubuklar3 = ax3.bar(x + genislik/2, bekleme_sureleri, genislik, label='Bekleme Süresi')
        
        ax3.set_title('Makine Türlerine Göre Toplam Süreler', pad=5, fontsize=9)
        ax3.set_xlabel('Makine Türü', fontsize=8)
        ax3.set_ylabel('Süre (saniye)', fontsize=8)
        ax3.set_xticks(x)
        ax3.set_xticklabels(isimler, rotation=45, ha='right')
        ax3.tick_params(axis='both', which='major', labelsize=7)
        ax3.legend(fontsize=7, loc='upper right')
        
        # Çubuk değerlerini göster
        def etiket_ekle(cubuklar):
            for cubuk in cubuklar:
                yukseklik = cubuk.get_height()
                ax3.text(cubuk.get_x() + cubuk.get_width()/2., yukseklik,
                        f'{yukseklik:.1f}s',
                        ha='center', va='bottom', fontsize=6)
        
        etiket_ekle(cubuklar2)
        etiket_ekle(cubuklar3)
        
        # Grafik düzenini optimize et
        self.sekil.tight_layout()
        self.tuval.draw()
        
        # Önceki sonuçları temizle
        for i in reversed(range(self.sonuclar_duzen.count())): 
            self.sonuclar_duzen.itemAt(i).widget().setParent(None)
        
        # Özet bilgiler
        ozet_widget = QWidget()
        ozet_duzen = QVBoxLayout(ozet_widget)
        
        toplam_makine_etiket = QLabel(f"Toplam Makine Sayısı: {toplam_makine}")
        toplam_makine_etiket.setStyleSheet("font-weight: bold; font-size: 14px;")
        ozet_duzen.addWidget(toplam_makine_etiket)
        
        toplam_sure_etiket = QLabel(f"Toplam Üretim Süresi: {en_iyi_uygunluk:.2f} saniye")
        toplam_sure_etiket.setStyleSheet("font-weight: bold; font-size: 14px;")
        ozet_duzen.addWidget(toplam_sure_etiket)
        
        self.sonuclar_duzen.addWidget(ozet_widget)

class FabrikaOptimizasyonu(QMainWindow):
    def __init__(self):
        super().__init__()
        self.arayuz_olustur()
    
    def arayuz_olustur(self):
        self.setWindowTitle("Fabrika Makine Optimizasyonu")
        self.setGeometry(100, 100, 800, 600)
        
        # Ana widget ve düzen
        self.ana_widget = QWidget()
        self.ana_widget.setStyleSheet(f"background-color: {STIL['ARKAPLAN_RENK']};")
        self.setCentralWidget(self.ana_widget)
        
        self.duzen = QVBoxLayout(self.ana_widget)
        self.duzen.setSpacing(15)
        self.duzen.setContentsMargins(20, 20, 20, 20)
        
        # Giriş kapsayıcı
        giris_kapsayici = QWidget()
        giris_kapsayici.setStyleSheet("""
            background-color: white;
            border-radius: 8px;
            padding: 20px;
        """)
        giris_duzen = QVBoxLayout(giris_kapsayici)
        
        # Makine türü sayısı girişi
        tur_duzen = QHBoxLayout()
        tur_etiket = QLabel("Makine Türü Sayısı:")
        tur_etiket.setStyleSheet(ETIKET_STIL)
        self.tur_giris = QLineEdit()
        self.tur_giris.setStyleSheet(GIRIS_STIL)
        tur_duzen.addWidget(tur_etiket)
        tur_duzen.addWidget(self.tur_giris)
        giris_duzen.addLayout(tur_duzen)
        
        # Toplam makine sayısı girişi
        toplam_makine_duzen = QHBoxLayout()
        toplam_makine_etiket = QLabel("Toplam Makine Sayısı:")
        toplam_makine_etiket.setStyleSheet(ETIKET_STIL)
        self.toplam_makine_giris = QLineEdit()
        self.toplam_makine_giris.setStyleSheet(GIRIS_STIL)
        toplam_makine_duzen.addWidget(toplam_makine_etiket)
        toplam_makine_duzen.addWidget(self.toplam_makine_giris)
        giris_duzen.addLayout(toplam_makine_duzen)
        
        self.duzen.addWidget(giris_kapsayici)
        
        # Devam butonu
        self.devam_btn = QPushButton("Devam")
        self.devam_btn.setStyleSheet(BUTON_STIL)
        self.devam_btn.setFixedWidth(200)
        self.duzen.addWidget(self.devam_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.devam_btn.clicked.connect(self.makine_girisleri_olustur)
        
        # Kaydırma alanı
        self.kaydirma = QScrollArea()
        self.kaydirma.setWidgetResizable(True)
        self.kaydirma.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f1f1f1;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #888;
                border-radius: 5px;
            }
        """)
        
        self.kaydirma_widget = QWidget()
        self.kaydirma_widget.setStyleSheet(f"background-color: {STIL['ARKAPLAN_RENK']};")
        self.kaydirma_duzen = QVBoxLayout(self.kaydirma_widget)
        self.kaydirma_duzen.setSpacing(15)
        self.kaydirma.setWidget(self.kaydirma_widget)
        self.duzen.addWidget(self.kaydirma)
        
        self.makine_girisleri = []
        self.sonuc_penceresi = None
    
    def ana_pencere_sifirla(self):
        # Tüm girdileri temizle
        self.tur_giris.clear()
        self.toplam_makine_giris.clear()
        
        # Makine girişlerini temizle
        for i in reversed(range(self.kaydirma_duzen.count())): 
            widget = self.kaydirma_duzen.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.makine_girisleri.clear()
        
        # Sonuç penceresini temizle
        if self.sonuc_penceresi:
            self.sonuc_penceresi.close()
            self.sonuc_penceresi = None
        
        # Genetik algoritma sınıflarını temizle
        genetik_temizle()
        
        # Matplotlib figürlerini temizle
        plt.close('all')
    
    def makine_girisleri_olustur(self):
        try:
            tur_sayisi = int(self.tur_giris.text())
            toplam_makine = int(self.toplam_makine_giris.text())
            
            if toplam_makine <= 0:
                raise ValueError("Toplam makine sayısı 0'dan büyük olmalıdır!")
            
            # Önceki girişleri temizle
            for i in reversed(range(self.kaydirma_duzen.count())): 
                widget = self.kaydirma_duzen.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
            self.makine_girisleri.clear()
            
            # Her makine türü için giriş oluştur
            for i in range(tur_sayisi):
                # Makine kapsayıcı
                makine_kapsayici = QWidget()
                makine_kapsayici.setStyleSheet("""
                    background-color: white;
                    border-radius: 8px;
                    padding: 15px;
                """)
                tur_duzen = QVBoxLayout(makine_kapsayici)
                
                # Makine türü adı
                isim_duzen = QHBoxLayout()
                isim_etiket = QLabel(f"Makine Türü {i+1} Adı:")
                isim_etiket.setStyleSheet(ETIKET_STIL)
                isim_giris = QLineEdit()
                isim_giris.setStyleSheet(GIRIS_STIL)
                isim_duzen.addWidget(isim_etiket)
                isim_duzen.addWidget(isim_giris)
                tur_duzen.addLayout(isim_duzen)
                
                # İşlem süresi
                islem_duzen = QHBoxLayout()
                islem_etiket = QLabel("İşlem Süresi (saniye):")
                islem_etiket.setStyleSheet(ETIKET_STIL)
                islem_giris = QLineEdit()
                islem_giris.setStyleSheet(GIRIS_STIL)
                islem_duzen.addWidget(islem_etiket)
                islem_duzen.addWidget(islem_giris)
                tur_duzen.addLayout(islem_duzen)
                
                # Bekleme süresi
                bekleme_duzen = QHBoxLayout()
                bekleme_etiket = QLabel("Bekleme Süresi (saniye):")
                bekleme_etiket.setStyleSheet(ETIKET_STIL)
                bekleme_giris = QLineEdit()
                bekleme_giris.setStyleSheet(GIRIS_STIL)
                bekleme_duzen.addWidget(bekleme_etiket)
                bekleme_duzen.addWidget(bekleme_giris)
                tur_duzen.addLayout(bekleme_duzen)
                
                self.kaydirma_duzen.addWidget(makine_kapsayici)
                self.makine_girisleri.append({
                    'isim': isim_giris,
                    'islem': islem_giris,
                    'bekleme': bekleme_giris
                })
            
            # Optimize butonu
            optimize_btn = QPushButton("Optimize Et")
            optimize_btn.setStyleSheet(BUTON_STIL)
            optimize_btn.setFixedWidth(200)
            self.kaydirma_duzen.addWidget(optimize_btn, alignment=Qt.AlignmentFlag.AlignCenter)
            optimize_btn.clicked.connect(self.optimize_et)
            
        except ValueError as e:
            QMessageBox.warning(self, "Hata", str(e) if str(e) != "" else "Lütfen geçerli bir sayı girin!")
    
    def optimize_et(self):
        try:
            # Genetik algoritma sınıflarını temizle
            genetik_temizle()
            
            toplam_makine = int(self.toplam_makine_giris.text())
            
            makine_verisi = []
            for girisler in self.makine_girisleri:
                makine_verisi.append({
                    'isim': girisler['isim'].text(),
                    'islem_suresi': float(girisler['islem'].text()),
                    'bekleme_suresi': float(girisler['bekleme'].text())
                })
            
            # Genetik algoritma parametreleri
            POPULASYON_BOYUTU = 100
            CAPRAZLAMA_OLASILIK = 0.7
            MUTASYON_OLASILIK = 0.2
            MAKS_NESIL = 50
            
            creator.create("UygunlukMin", base.Fitness, weights=(-1.0,))
            creator.create("Birey", list, fitness=creator.UygunlukMin)
            
            arac_kutusu = base.Toolbox()
            
            # Birey oluşturma fonksiyonu
            def birey_olustur():
                # Önce her türe 1 makine ver
                birey = [1 for _ in makine_verisi]
                kalan_makineler = toplam_makine - len(makine_verisi)
                
                if kalan_makineler < 0:
                    raise ValueError(f"Toplam makine sayısı en az {len(makine_verisi)} olmalıdır! (Her tür için en az 1 makine)")
                
                # Kalan makineleri rastgele dağıt
                if kalan_makineler > 0:
                    ekstra = [random.randint(0, kalan_makineler) for _ in makine_verisi]
                    toplam_ekstra = sum(ekstra)
                    if toplam_ekstra > 0:  # 0'a bölme hatasını önle
                        normalize_ekstra = [int(round(x * kalan_makineler / toplam_ekstra)) for x in ekstra]
                        # Son makineyi ayarla
                        normalize_ekstra[-1] = kalan_makineler - sum(normalize_ekstra[:-1])
                        # Her türe ekstra makineleri ekle
                        birey = [taban + ekstra for taban, ekstra in zip(birey, normalize_ekstra)]
                
                return birey
            
            arac_kutusu.register("birey", tools.initIterate, creator.Birey, birey_olustur)
            arac_kutusu.register("populasyon", tools.initRepeat, list, arac_kutusu.birey)
            
            # Uygunluk fonksiyonu
            def degerlendir(birey):
                # Her türden en az 1 makine olmalı
                if any(sayi < 1 for sayi in birey) or sum(birey) != toplam_makine:
                    return float('inf'),
                
                toplam_sure = 0
                for i, sayi in enumerate(birey):
                    islem_suresi = makine_verisi[i]['islem_suresi']
                    bekleme_suresi = makine_verisi[i]['bekleme_suresi']
                    toplam_sure += (islem_suresi + bekleme_suresi) * sayi
                return toplam_sure,
            
            arac_kutusu.register("degerlendir", degerlendir)
            arac_kutusu.register("mate", tools.cxTwoPoint)
            
            # Mutasyon operatörü
            def ozel_mutasyon(birey, olaslik):
                for i in range(len(birey)):
                    if random.random() < olaslik:
                        # Mevcut değeri al
                        mevcut_deger = birey[i]
                        # Değişim miktarını belirle (-2 ile +2 arası)
                        degisim = random.randint(-2, 2)
                        # Yeni değer en az 1 olmalı
                        yeni_deger = max(1, mevcut_deger + degisim)
                        # Değişimi uygula
                        birey[i] = yeni_deger
                
                # Toplam makine sayısını koru
                mevcut_toplam = sum(birey)
                if mevcut_toplam != toplam_makine:
                    # Fazla veya eksik makine sayısını hesapla
                    fark = toplam_makine - mevcut_toplam
                    # Rastgele bir makine türü seç (son tür hariç)
                    ayar_indeks = random.randint(0, len(birey) - 2)
                    # Seçilen türün makine sayısını ayarla (en az 1 olacak şekilde)
                    birey[ayar_indeks] = max(1, birey[ayar_indeks] + fark)
                    
                return birey,
            
            arac_kutusu.register("mutate", ozel_mutasyon, olaslik=0.2)
            arac_kutusu.register("select", tools.selTournament, tournsize=3)
            
            # Genetik algoritma çalıştırma ve nesil verilerini toplama
            try:
                populasyon = arac_kutusu.populasyon(n=POPULASYON_BOYUTU)
                istatistik = tools.Statistics(lambda birey: birey.fitness.values)
                istatistik.register("min", np.min)
                istatistik.register("ort", np.mean)
                
                nesiller = []
                min_uygunluk = []
                ort_uygunluk = []
                
                # Her nesil için istatistikleri toplama
                for nesil in range(MAKS_NESIL):
                    populasyon = algorithms.varAnd(populasyon, arac_kutusu, CAPRAZLAMA_OLASILIK, MUTASYON_OLASILIK)
                    
                    # Uygunluk değerlerini hesaplama
                    uygunluklar = arac_kutusu.map(arac_kutusu.degerlendir, populasyon)
                    for uygunluk, birey in zip(uygunluklar, populasyon):
                        birey.fitness.values = uygunluk
                    
                    # Yeni nesil için seçim
                    populasyon = arac_kutusu.select(populasyon, len(populasyon))
                    
                    # İstatistikleri kaydetme
                    nesil_istatistik = istatistik.compile(populasyon)
                    nesiller.append(nesil)
                    min_uygunluk.append(nesil_istatistik['min'])
                    ort_uygunluk.append(nesil_istatistik['ort'])
                
                en_iyi_birey = tools.selBest(populasyon, k=1)[0]
                en_iyi_uygunluk = en_iyi_birey.fitness.values[0]
                
                if en_iyi_uygunluk == float('inf'):
                    raise ValueError("Uygun çözüm bulunamadı! Lütfen toplam makine sayısını artırın.")
                
                # Sonuçları göster
                if self.sonuc_penceresi is None:
                    self.sonuc_penceresi = SonucPenceresi(self)
                self.sonuc_penceresi.sonuclari_goster(makine_verisi, en_iyi_birey, en_iyi_uygunluk,
                                                nesiller, min_uygunluk, ort_uygunluk, toplam_makine)
                self.sonuc_penceresi.show()
                
            except ValueError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.warning(self, "Hata", "Optimizasyon sırasında bir hata oluştu: " + str(e))
            
        except ValueError:
            QMessageBox.warning(self, "Hata", "Lütfen tüm alanları doğru formatta doldurun!")

if __name__ == '__main__':
    uygulama = QApplication(sys.argv)
    pencere = FabrikaOptimizasyonu()
    pencere.show()
    sys.exit(uygulama.exec())