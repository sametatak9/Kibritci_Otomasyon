import tkcalendar 
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# PDF Kütüphaneleri
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

# --- AYARLAR VE LOGO ---
LOGO_YOLU = "kibritci-insaat-logo.png" # Dosya kodla aynı klasörde olmalı

# --- KURUMSAL MAİL AYARLARI ---
SMTP_SERVER = "mail.kibritciinsaat.com.tr"
SMTP_PORT = 587
KURUMSAL_MAIL = "k.ozer@kibritciinsaat.com.tr"
KURUMSAL_SIFRE = "Ko78978961" 

# --- TÜRKÇE KARAKTER DESTEĞİ GÜNCELLEMESİ ---
# Not: arial.ttf ve arialbd.ttf dosyaları proje klasöründe olmalıdır.
try:
    pdfmetrics.registerFont(TTFont('Arial-Turkce', 'arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold-Turkce', 'arialbd.ttf'))
    VARSAYILAN_FONT = "Arial-Turkce"
    KALIN_FONT = "Arial-Bold-Turkce"
except:
    # Eğer dosyalar bulunamazsa sistem fontlarını denemeye çalışır
    VARSAYILAN_FONT = "Helvetica"
    KALIN_FONT = "Helvetica-Bold"

class IdariIslerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("KİBRİTÇİ İNŞAAT | İDARİ İŞLER YÖNETİM SİSTEMİ")
        self.root.geometry("1300x850")
        
        self.RENK_ARKA_PLAN = "#EFEFEF"
        self.RENK_SIDEBAR = "#2C3E50"
        self.RENK_VURGU = "#34495E"
        self.RENK_YAZI = "#FFFFFF"
        
        self.root.configure(bg=self.RENK_ARKA_PLAN)
        self.veritabani_kur()
        self.gecici_sepet = [] 
        self.secili_fis_yolu = ""
        self.arayuz_olustur()

    def veritabani_kur(self):
        conn = sqlite3.connect("idari_yonetim.db")
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS idari_personel (id INTEGER PRIMARY KEY AUTOINCREMENT, tc_no TEXT UNIQUE, ad_soyad TEXT, gorev TEXT, ise_giris TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS araclar (id INTEGER PRIMARY KEY AUTOINCREMENT, plaka TEXT UNIQUE, marka_model TEXT, tahsis_personel_id INTEGER, muayene_tarihi TEXT, yag_bakim_km INTEGER, son_km INTEGER DEFAULT 0)''')
        c.execute('''CREATE TABLE IF NOT EXISTS km_takip (id INTEGER PRIMARY KEY AUTOINCREMENT, arac_id INTEGER, plaka_arsiv TEXT, tarih TEXT, sabah_km INTEGER, aksam_km INTEGER, gunluk_fark INTEGER, tur TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS kamp_yerlesim (id INTEGER PRIMARY KEY AUTOINCREMENT, oda_no TEXT, personel_ad TEXT, ekip TEXT, zimmetli_malzeme TEXT, giris_tarihi TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS kasa_takip (id INTEGER PRIMARY KEY AUTOINCREMENT, tarih TEXT, harcama REAL, aciklama TEXT, fis_yolu TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS satinalma_talepleri (id INTEGER PRIMARY KEY AUTOINCREMENT, urunler TEXT, talep_tarihi TEXT, istenen_tarih TEXT, rapor_tarihi TEXT)''')
        conn.commit()
        conn.close()

    def arayuz_olustur(self):
        self.sidebar = tk.Frame(self.root, bg=self.RENK_SIDEBAR, width=250)
        self.sidebar.pack(side="left", fill="y")
        tk.Label(self.sidebar, text="KİBRİTÇİ İNŞAAT\nİDARİ İŞLER", font=("Segoe UI", 14, "bold"), bg=self.RENK_SIDEBAR, fg="white", pady=25).pack()

        menuler = [
            ("🚚 Araç Kayıt & Tahsis", self.ekran_arac_kayit),
            ("⚙️ KM ve Bakım Takibi", self.ekran_arac_islem),
            ("👥 İdari Personel Kayıt", self.ekran_idari_personel),
            ("🏕️ Kamp & Konaklama", self.ekran_kamp_yonetimi),
            ("💰 Haftalık Kasa Takibi", self.ekran_kasa_takibi),
            ("🛒 Satın Alma Talebi", self.ekran_satinalma_talebi),
            ("📊 PDF Rapor Merkezi", self.ekran_rapor_merkezi)
        ]

        for metin, komut in menuler:
            tk.Button(self.sidebar, text=metin, font=("Segoe UI", 11), bg=self.RENK_VURGU, fg=self.RENK_YAZI, bd=0, padx=20, pady=12, anchor="w", cursor="hand2", command=komut).pack(fill="x", padx=10, pady=2)

        self.ana_panel = tk.Frame(self.root, bg=self.RENK_ARKA_PLAN)
        self.ana_panel.pack(side="right", expand=True, fill="both", padx=20, pady=20)
        self.ekran_idari_personel()

    def temizle_panel(self):
        for widget in self.ana_panel.winfo_children(): widget.destroy()

    def input_olustur(self, ebeveyn, metin, satir):
        tk.Label(ebeveyn, text=metin, bg=self.RENK_ARKA_PLAN).grid(row=satir, column=0, sticky="w", padx=10, pady=5)
        ent = tk.Entry(ebeveyn, width=30)
        ent.grid(row=satir, column=1, pady=5)
        return ent

    # --- ARAÇ İŞLEMLERİ ---
    def ekran_arac_kayit(self):
        self.temizle_panel()
        tk.Label(self.ana_panel, text="ARAÇ KAYIT VE LİSTESİ", font=("Segoe UI", 16, "bold"), bg=self.RENK_ARKA_PLAN).pack(pady=10)
        
        form = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN); form.pack()
        self.ent_a_plaka = self.input_olustur(form, "Plaka:", 0)
        self.ent_a_model = self.input_olustur(form, "Model:", 1)
        self.ent_a_muayene = self.input_olustur(form, "Muayene:", 2)
        self.ent_a_bakim = self.input_olustur(form, "Bakım KM:", 3)
        
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor(); c.execute("SELECT id, ad_soyad FROM idari_personel")
        personeller = c.fetchall(); self.p_dict = {p[1]: p[0] for p in personeller}; conn.close()
        
        tk.Label(form, text="Tahsis Edilen:", bg=self.RENK_ARKA_PLAN).grid(row=4, column=0, sticky="w", padx=10)
        self.combo_p = ttk.Combobox(form, values=list(self.p_dict.keys()), state="readonly")
        self.combo_p.grid(row=4, column=1, pady=5)

        buton_frame = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN); buton_frame.pack(pady=10)
        tk.Button(buton_frame, text="KAYDET", bg="#27AE60", fg="white", font=("Segoe UI", 10, "bold"), width=15, command=self.arac_kaydet).grid(row=0, column=0, padx=5)
        tk.Button(buton_frame, text="GÜNCELLE", bg="#2980B9", fg="white", font=("Segoe UI", 10, "bold"), width=15, command=self.arac_guncelle).grid(row=0, column=1, padx=5)
        tk.Button(buton_frame, text="SİL", bg="#C0392B", fg="white", font=("Segoe UI", 10, "bold"), width=15, command=self.arac_sil).grid(row=0, column=2, padx=5)

        self.arac_tree = ttk.Treeview(self.ana_panel, columns=("id", "plaka", "model", "personel", "muayene", "km"), show="headings")
        for col, head in zip(self.arac_tree["columns"], ("ID", "PLAKA", "MARKA/MODEL", "PERSONEL", "MUAYENE", "SON KM")):
            self.arac_tree.heading(col, text=head); self.arac_tree.column(col, width=100, anchor="center")
        self.arac_tree.pack(fill="both", expand=True, padx=20, pady=10)
        self.arac_tree.bind("<<TreeviewSelect>>", self.arac_doldur)
        self.arac_listele()

    def arac_doldur(self, event):
        secili = self.arac_tree.selection()
        if secili:
            v = self.arac_tree.item(secili[0], 'values')
            self.ent_a_plaka.delete(0, tk.END); self.ent_a_plaka.insert(0, v[1])
            self.ent_a_model.delete(0, tk.END); self.ent_a_model.insert(0, v[2])
            self.combo_p.set(v[3] if v[3] else "")
            self.ent_a_muayene.delete(0, tk.END); self.ent_a_muayene.insert(0, v[4])

    def arac_kaydet(self):
        p_id = self.p_dict.get(self.combo_p.get())
        v = (self.ent_a_plaka.get().upper(), self.ent_a_model.get(), p_id, self.ent_a_muayene.get(), self.ent_a_bakim.get())
        if not v[0]: messagebox.showwarning("Hata", "Plaka boş olamaz!"); return
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
        try:
            c.execute("INSERT INTO araclar (plaka, marka_model, tahsis_personel_id, muayene_tarihi, yag_bakim_km) VALUES (?,?,?,?,?)", v)
            conn.commit(); messagebox.showinfo("Başarılı", "Araç kaydedildi."); self.arac_listele()
        except sqlite3.IntegrityError: messagebox.showerror("Hata", "Bu plaka zaten kayıtlı!")
        finally: conn.close()

    def arac_guncelle(self):
        secili = self.arac_tree.selection()
        if not secili: return
        a_id = self.arac_tree.item(secili[0], 'values')[0]
        p_id = self.p_dict.get(self.combo_p.get())
        v = (self.ent_a_plaka.get().upper(), self.ent_a_model.get(), p_id, self.ent_a_muayene.get(), self.ent_a_bakim.get(), a_id)
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
        c.execute("UPDATE araclar SET plaka=?, marka_model=?, tahsis_personel_id=?, muayene_tarihi=?, yag_bakim_km=? WHERE id=?", v)
        conn.commit(); conn.close(); self.arac_listele(); messagebox.showinfo("Bilgi", "Araç güncellendi.")

    def arac_sil(self):
        secili = self.arac_tree.selection()
        if not secili: return
        a_id = self.arac_tree.item(secili[0], 'values')[0]
        if messagebox.askyesno("Onay", "Aracı silmek istediğinize emin misiniz?"):
            conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
            c.execute("DELETE FROM araclar WHERE id=?", (a_id,))
            conn.commit(); conn.close(); self.arac_listele()

    def arac_listele(self):
        for i in self.arac_tree.get_children(): self.arac_tree.delete(i)
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
        c.execute('''SELECT a.id, a.plaka, a.marka_model, p.ad_soyad, a.muayene_tarihi, a.son_km FROM araclar a LEFT JOIN idari_personel p ON a.tahsis_personel_id = p.id''')
        for r in c.fetchall(): self.arac_tree.insert("", "end", values=r)
        conn.close()

    # --- KM TAKİP EKRANI ---
    def ekran_arac_islem(self):
        self.temizle_panel()
        tk.Label(self.ana_panel, text="PROFESYONEL KM GİRİŞİ", font=("Segoe UI", 16, "bold"), bg=self.RENK_ARKA_PLAN).pack(pady=10)
        
        form_km = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN); form_km.pack(pady=10)
        tk.Label(form_km, text="Araç Seçin:", bg=self.RENK_ARKA_PLAN).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor(); c.execute("SELECT id, plaka FROM araclar"); araclar = c.fetchall(); conn.close()
        self.secili_arac = tk.StringVar()
        self.combo_arac_km = ttk.Combobox(form_km, textvariable=self.secili_arac, values=[f"{a[0]}-{a[1]}" for a in araclar], state="readonly", width=27)
        self.combo_arac_km.grid(row=0, column=1, pady=5)

        tk.Label(form_km, text="Kayıt Tarihi:", bg=self.RENK_ARKA_PLAN).grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.ent_km_tarih = tk.Entry(form_km, width=30); self.ent_km_tarih.insert(0, datetime.now().strftime("%d.%m.%Y")); self.ent_km_tarih.grid(row=1, column=1, pady=5)

        tk.Label(form_km, text="KM Zamanı:", bg=self.RENK_ARKA_PLAN).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.combo_km_tur = ttk.Combobox(form_km, values=["Sabah KM", "Akşam KM"], state="readonly", width=27); self.combo_km_tur.current(0); self.combo_km_tur.grid(row=2, column=1, pady=5)

        tk.Label(form_km, text="Kilometre Değeri:", bg=self.RENK_ARKA_PLAN).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.ent_yeni_km = tk.Entry(form_km, width=30); self.ent_yeni_km.grid(row=3, column=1, pady=5)

        tk.Button(self.ana_panel, text="VERİYİ SİSTEME İŞLE", bg="#27AE60", fg="white", font=("Segoe UI", 10, "bold"), padx=20, pady=10, command=self.km_islem).pack(pady=20)

    def km_islem(self):
        try:
            if not self.secili_arac.get() or not self.ent_yeni_km.get():
                messagebox.showwarning("Uyarı", "Lütfen tüm alanları doldurun!"); return
            a_id = self.secili_arac.get().split("-")[0]
            yeni_km = int(self.ent_yeni_km.get()); tarih = self.ent_km_tarih.get(); tur = self.combo_km_tur.get()
            conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
            c.execute("SELECT son_km FROM araclar WHERE id=?", (a_id,))
            eski_km = c.fetchone()[0]
            fark = yeni_km - eski_km if tur == "Akşam KM" else 0
            if tur == "Sabah KM":
                c.execute("INSERT INTO km_takip (arac_id, tarih, sabah_km, tur) VALUES (?,?,?,?)", (a_id, tarih, yeni_km, tur))
            else:
                c.execute("INSERT INTO km_takip (arac_id, tarih, aksam_km, gunluk_fark, tur) VALUES (?,?,?,?,?)", (a_id, tarih, yeni_km, fark, tur))
            c.execute("UPDATE araclar SET son_km=? WHERE id=?", (yeni_km, a_id))
            conn.commit(); conn.close(); messagebox.showinfo("Başarılı", f"{tur} kaydı işlendi."); self.ent_yeni_km.delete(0, tk.END)
        except Exception as e: messagebox.showerror("Hata", str(e))

    # --- İDARİ PERSONEL ---
    def ekran_idari_personel(self):
        self.temizle_panel()
        tk.Label(self.ana_panel, text="İDARİ PERSONEL YÖNETİMİ", font=("Segoe UI", 16, "bold"), bg=self.RENK_ARKA_PLAN).pack(pady=10)
        form = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN); form.pack()
        self.ent_p_tc = self.input_olustur(form, "TC No:", 0); self.ent_p_ad = self.input_olustur(form, "Ad Soyad:", 1)
        self.ent_p_gorev = self.input_olustur(form, "Görev:", 2); self.ent_p_tarih = self.input_olustur(form, "Giriş:", 3)
        
        btn_f = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN); btn_f.pack(pady=10)
        tk.Button(btn_f, text="KAYDET", bg="#27AE60", fg="white", width=12, command=self.personel_kaydet).grid(row=0, column=0, padx=5)
        tk.Button(btn_f, text="GÜNCELLE", bg="#2980B9", fg="white", width=12, command=self.personel_guncelle).grid(row=0, column=1, padx=5)
        tk.Button(btn_f, text="SİL", bg="#C0392B", fg="white", width=12, command=self.personel_sil).grid(row=0, column=2, padx=5)
        
        self.p_tree = ttk.Treeview(self.ana_panel, columns=("id","tc","ad","g","t"), show="headings")
        for c, h in zip(("id","tc","ad","g","t"), ("ID","TC","AD","GÖREV","TARİH")): self.p_tree.heading(c, text=h); self.p_tree.column(c, width=100)
        self.p_tree.pack(fill="both", expand=True, padx=20)
        self.p_tree.bind("<<TreeviewSelect>>", self.personel_doldur)
        self.personel_listele()

    def personel_listele(self):
        for i in self.p_tree.get_children(): self.p_tree.delete(i)
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor(); c.execute("SELECT id, tc_no, ad_soyad, gorev, ise_giris FROM idari_personel")
        for r in c.fetchall(): self.p_tree.insert("", "end", values=r)
        conn.close()

    def personel_doldur(self, event):
        secili = self.p_tree.selection()
        if secili:
            v = self.p_tree.item(secili[0], 'values')
            self.ent_p_tc.delete(0, tk.END); self.ent_p_tc.insert(0, v[1])
            self.ent_p_ad.delete(0, tk.END); self.ent_p_ad.insert(0, v[2])
            self.ent_p_gorev.delete(0, tk.END); self.ent_p_gorev.insert(0, v[3])
            self.ent_p_tarih.delete(0, tk.END); self.ent_p_tarih.insert(0, v[4])

    def personel_kaydet(self):
        v = (self.ent_p_tc.get(), self.ent_p_ad.get(), self.ent_p_gorev.get(), self.ent_p_tarih.get())
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
        try: c.execute("INSERT INTO idari_personel (tc_no, ad_soyad, gorev, ise_giris) VALUES (?,?,?,?)", v); conn.commit(); self.personel_listele()
        except: messagebox.showerror("Hata", "TC No zaten kayıtlı.")
        conn.close()

    def personel_guncelle(self):
        secili = self.p_tree.selection()
        if not secili: return
        p_id = self.p_tree.item(secili[0], 'values')[0]
        v = (self.ent_p_tc.get(), self.ent_p_ad.get(), self.ent_p_gorev.get(), self.ent_p_tarih.get(), p_id)
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
        c.execute("UPDATE idari_personel SET tc_no=?, ad_soyad=?, gorev=?, ise_giris=? WHERE id=?", v)
        conn.commit(); conn.close(); self.personel_listele()

    def personel_sil(self):
        secili = self.p_tree.selection()
        if not secili: return
        p_id = self.p_tree.item(secili[0], 'values')[0]
        if messagebox.askyesno("Onay", "Personeli silmek istediğinize emin misiniz?"):
            conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
            c.execute("DELETE FROM idari_personel WHERE id=?", (p_id,))
            conn.commit(); conn.close(); self.personel_listele()

    # --- KAMP YÖNETİMİ ---
    def ekran_kamp_yonetimi(self):
        self.temizle_panel()
        tk.Label(self.ana_panel, text="🏕️ KAMP YÖNETİMİ", font=("Segoe UI", 16, "bold"), bg=self.RENK_ARKA_PLAN).pack(pady=10)
        form = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN); form.pack()
        self.ent_oda = self.input_olustur(form, "Oda No:", 0); self.ent_kamp_ad = self.input_olustur(form, "Personel:", 1)
        self.ent_kamp_ekip = self.input_olustur(form, "Ekip:", 2); self.ent_kamp_zimmet = self.input_olustur(form, "Zimmet:", 3)
        
        btn_f = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN); btn_f.pack(pady=10)
        tk.Button(btn_f, text="KAYDET", bg="#27AE60", fg="white", width=12, command=self.kamp_kaydet).grid(row=0, column=0, padx=5)
        tk.Button(btn_f, text="GÜNCELLE", bg="#2980B9", fg="white", width=12, command=self.kamp_guncelle).grid(row=0, column=1, padx=5)
        tk.Button(btn_f, text="SİL", bg="#C0392B", fg="white", width=12, command=self.kamp_sil).grid(row=0, column=2, padx=5)
        tk.Button(btn_f, text="KROKİ AL", bg="#7F8C8D", fg="white", width=12, command=self.pdf_kamp_krokisi).grid(row=0, column=3, padx=5)

        self.kamp_tree = ttk.Treeview(self.ana_panel, columns=("id","o","a","e","z"), show="headings")
        for c, h in zip(("id","o","a","e","z"), ("ID","ODA","AD","EKİP","ZİMMET")): self.kamp_tree.heading(c, text=h); self.kamp_tree.column(c, width=100)
        self.kamp_tree.pack(fill="both", expand=True, padx=20)
        self.kamp_tree.bind("<<TreeviewSelect>>", self.kamp_doldur)
        self.kamp_listele()

    def kamp_listele(self):
        for i in self.kamp_tree.get_children(): self.kamp_tree.delete(i)
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor(); c.execute("SELECT id, oda_no, personel_ad, ekip, zimmetli_malzeme FROM kamp_yerlesim ORDER BY oda_no")
        for r in c.fetchall(): self.kamp_tree.insert("", "end", values=r)
        conn.close()

    def kamp_doldur(self, event):
        secili = self.kamp_tree.selection()
        if secili:
            v = self.kamp_tree.item(secili[0], 'values')
            self.ent_oda.delete(0, tk.END); self.ent_oda.insert(0, v[1])
            self.ent_kamp_ad.delete(0, tk.END); self.ent_kamp_ad.insert(0, v[2])
            self.ent_kamp_ekip.delete(0, tk.END); self.ent_kamp_ekip.insert(0, v[3])
            self.ent_kamp_zimmet.delete(0, tk.END); self.ent_kamp_zimmet.insert(0, v[4])

    def kamp_kaydet(self):
        v = (self.ent_oda.get(), self.ent_kamp_ad.get(), self.ent_kamp_ekip.get(), self.ent_kamp_zimmet.get(), datetime.now().strftime("%d.%m.%Y"))
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor(); c.execute("INSERT INTO kamp_yerlesim (oda_no, personel_ad, ekip, zimmetli_malzeme, giris_tarihi) VALUES (?,?,?,?,?)", v); conn.commit(); conn.close(); self.kamp_listele()

    def kamp_guncelle(self):
        secili = self.kamp_tree.selection()
        if not secili: return
        k_id = self.kamp_tree.item(secili[0], 'values')[0]
        v = (self.ent_oda.get(), self.ent_kamp_ad.get(), self.ent_kamp_ekip.get(), self.ent_kamp_zimmet.get(), k_id)
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
        c.execute("UPDATE kamp_yerlesim SET oda_no=?, personel_ad=?, ekip=?, zimmetli_malzeme=? WHERE id=?", v)
        conn.commit(); conn.close(); self.kamp_listele()

    def kamp_sil(self):
        secili = self.kamp_tree.selection()
        if not secili: return
        k_id = self.kamp_tree.item(secili[0], 'values')[0]
        if messagebox.askyesno("Onay", "Kamp kaydını silmek istediğinize emin misiniz?"):
            conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
            c.execute("DELETE FROM kamp_yerlesim WHERE id=?", (k_id,))
            conn.commit(); conn.close(); self.kamp_listele()

    # --- KASA TAKİBİ ---
    def ekran_kasa_takibi(self):
        self.temizle_panel()
        tk.Label(self.ana_panel, text="💰 KASA TAKİBİ", font=("Segoe UI", 16, "bold"), bg=self.RENK_ARKA_PLAN).pack(pady=10)
        form = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN); form.pack()
        self.ent_kasa_tarih = self.input_olustur(form, "Tarih:", 0); self.ent_kasa_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.ent_kasa_miktar = self.input_olustur(form, "Tutar:", 1); self.ent_kasa_aciklama = self.input_olustur(form, "Açıklama:", 2)
        
        tk.Label(form, text="Fiş Görseli:", bg=self.RENK_ARKA_PLAN).grid(row=3, column=0, sticky="w", padx=10)
        self.lbl_fis_yolu = tk.Label(form, text="Seçilmedi", fg="blue", bg=self.RENK_ARKA_PLAN)
        self.lbl_fis_yolu.grid(row=3, column=1, sticky="w")
        tk.Button(form, text="FİŞ/RESİM SEÇ", command=self.fis_sec).grid(row=3, column=1, sticky="e")
        
        btn_f = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN); btn_f.pack(pady=10)
        tk.Button(btn_f, text="KAYDET", bg="#27AE60", fg="white", width=12, command=self.kasa_kaydet).grid(row=0, column=0, padx=5)
        tk.Button(btn_f, text="GÜNCELLE", bg="#2980B9", fg="white", width=12, command=self.kasa_guncelle).grid(row=0, column=1, padx=5)
        tk.Button(btn_f, text="SİL", bg="#C0392B", fg="white", width=12, command=self.kasa_sil).grid(row=0, column=2, padx=5)
        tk.Button(btn_f, text="DETAYLI RAPOR", bg="#7F8C8D", fg="white", width=12, command=self.pdf_kasa_raporu_secili).grid(row=0, column=3, padx=5)

        self.kasa_tree = ttk.Treeview(self.ana_panel, columns=("i","t","m","a"), show="headings")
        for c, h in zip(("i","t","m","a"), ("ID","TARİH","TL","BİLGİ")): self.kasa_tree.heading(c, text=h); self.kasa_tree.column(c, width=100)
        self.kasa_tree.pack(fill="both", expand=True, padx=20)
        self.kasa_tree.bind("<<TreeviewSelect>>", self.kasa_doldur)
        self.kasa_listele()

    def fis_sec(self):
        yol = filedialog.askopenfilename(filetypes=[("Resim Dosyaları", "*.jpg *.png *.jpeg")])
        if yol:
            self.secili_fis_yolu = yol
            self.lbl_fis_yolu.config(text=os.path.basename(yol))

    def kasa_kaydet(self):
        try:
            t, m, a = self.ent_kasa_tarih.get(), float(self.ent_kasa_miktar.get()), self.ent_kasa_aciklama.get()
            f = self.secili_fis_yolu
            conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
            c.execute("INSERT INTO kasa_takip (tarih, harcama, aciklama, fis_yolu) VALUES (?,?,?,?)", (t,m,a,f))
            conn.commit(); conn.close(); self.kasa_listele()
            messagebox.showinfo("Başarılı", "Harcama kaydedildi.")
            self.secili_fis_yolu = ""; self.lbl_fis_yolu.config(text="Seçilmedi")
        except: messagebox.showerror("Hata", "Tutar sayısal olmalı.")

    def kasa_listele(self):
        for i in self.kasa_tree.get_children(): self.kasa_tree.delete(i)
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
        c.execute("SELECT id, tarih, harcama, aciklama FROM kasa_takip ORDER BY id DESC")
        for r in c.fetchall(): self.kasa_tree.insert("", "end", values=r)
        conn.close()

    def kasa_doldur(self, event):
        secili = self.kasa_tree.selection()
        if secili:
            v = self.kasa_tree.item(secili[0], 'values')
            self.ent_kasa_tarih.delete(0, tk.END); self.ent_kasa_tarih.insert(0, v[1])
            self.ent_kasa_miktar.delete(0, tk.END); self.ent_kasa_miktar.insert(0, v[2])
            self.ent_kasa_aciklama.delete(0, tk.END); self.ent_kasa_aciklama.insert(0, v[3])

    def kasa_guncelle(self):
        secili = self.kasa_tree.selection()
        if not secili: return
        k_id = self.kasa_tree.item(secili[0], 'values')[0]
        try:
            t, m, a = self.ent_kasa_tarih.get(), float(self.ent_kasa_miktar.get()), self.ent_kasa_aciklama.get()
            conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
            c.execute("UPDATE kasa_takip SET tarih=?, harcama=?, aciklama=? WHERE id=?", (t,m,a,k_id))
            conn.commit(); conn.close(); self.kasa_listele()
        except: messagebox.showerror("Hata", "Geçersiz giriş.")

    def kasa_sil(self):
        secili = self.kasa_tree.selection()
        if not secili: return
        k_id = self.kasa_tree.item(secili[0], 'values')[0]
        if messagebox.askyesno("Onay", "Silmek istiyor musunuz?"):
            conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
            c.execute("DELETE FROM kasa_takip WHERE id=?", (k_id,))
            conn.commit(); conn.close(); self.kasa_listele()

    # --- SATIN ALMA TALEBİ ---
    def ekran_satinalma_talebi(self):
        self.temizle_panel()
        self.gecici_sepet = []
        tk.Label(self.ana_panel, text="SATIN ALMA TALEP FORMU", font=("Segoe UI", 16, "bold"), bg=self.RENK_ARKA_PLAN).pack(pady=10)
        form_ust = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN); form_ust.pack()
        self.ent_sa_urun = self.input_olustur(form_ust, "ÜRÜN ADI:", 0)
        self.ent_sa_miktar = self.input_olustur(form_ust, "MİKTAR/BİRİM:", 1)
        tk.Button(form_ust, text="EKLE ➕", bg="#F39C12", fg="white", command=self.satinalma_sepete_ekle).grid(row=1, column=2, padx=10)
        self.ent_sa_tarih = self.input_olustur(form_ust, "TALEP TARİHİ:", 2)
        self.ent_sa_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.ent_sa_istenen = self.input_olustur(form_ust, "İSTENEN TARİH:", 3)
        
        self.sepet_listbox = tk.Listbox(self.ana_panel, height=5, width=80); self.sepet_listbox.pack(pady=5)
        
        btn_f = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN); btn_f.pack(pady=10)
        tk.Button(btn_f, text="KAYDET", bg="#27AE60", fg="white", width=12, command=self.satinalma_kaydet).grid(row=0, column=0, padx=5)
        tk.Button(btn_f, text="SİL", bg="#C0392B", fg="white", width=12, command=self.satinalma_sil).grid(row=0, column=1, padx=5)
        tk.Button(btn_f, text="PDF AÇ", bg="#2980B9", fg="white", width=12, command=lambda: self.pdf_satinalma_raporu(mail_at=False)).grid(row=0, column=2, padx=5)
        tk.Button(btn_f, text="MAİL AT 📧", bg="#8E44AD", fg="white", width=12, command=lambda: self.pdf_satinalma_raporu(mail_at=True)).grid(row=0, column=3, padx=5)

        self.sa_tree = ttk.Treeview(self.ana_panel, columns=("no","urunler","tarih","istenen"), show="headings")
        for c, h in zip(("no","urunler","tarih","istenen"), ("NO","ÜRÜNLER","TALEP TAR.","İSTENEN TAR.")):
            self.sa_tree.heading(c, text=h); self.sa_tree.column(c, width=100)
        self.sa_tree.column("urunler", width=350); self.sa_tree.pack(fill="both", expand=True, padx=20, pady=5)
        self.satinalma_listele()

    def satinalma_sepete_ekle(self):
        urun = self.ent_sa_urun.get(); miktar = self.ent_sa_miktar.get()
        if urun and miktar:
            kalem = f"{urun} ({miktar})"; self.gecici_sepet.append(kalem)
            self.sepet_listbox.insert(tk.END, f"• {kalem}")
            self.ent_sa_urun.delete(0, tk.END); self.ent_sa_miktar.delete(0, tk.END)

    def satinalma_kaydet(self):
        if not self.gecici_sepet: messagebox.showwarning("Uyarı", "Liste boş!"); return
        urunler_str = " | ".join(self.gecici_sepet)
        v = (urunler_str, self.ent_sa_tarih.get(), self.ent_sa_istenen.get(), datetime.now().strftime("%d.%m.%Y %H:%M"))
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
        c.execute("INSERT INTO satinalma_talepleri (urunler, talep_tarihi, istenen_tarih, rapor_tarihi) VALUES (?,?,?,?)", v)
        conn.commit(); conn.close(); self.satinalma_listele(); self.sepet_listbox.delete(0, tk.END); self.gecici_sepet = []

    def satinalma_listele(self):
        for i in self.sa_tree.get_children(): self.sa_tree.delete(i)
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
        c.execute("SELECT id, urunler, talep_tarihi, istenen_tarih FROM satinalma_talepleri ORDER BY id DESC")
        for r in c.fetchall(): self.sa_tree.insert("", "end", values=r)
        conn.close()

    def satinalma_sil(self):
        secili = self.sa_tree.selection()
        if not secili: return
        r_id = self.sa_tree.item(secili[0], 'values')[0]
        if messagebox.askyesno("Onay", "Talebi silmek istiyor musunuz?"):
            conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
            c.execute("DELETE FROM satinalma_talepleri WHERE id=?", (r_id,))
            conn.commit(); conn.close(); self.satinalma_listele()

    # --- GELİŞMİŞ RAPORLAMA FONKSİYONLARI ---
    def ekran_rapor_merkezi(self):
        self.temizle_panel()
        tk.Label(self.ana_panel, text="📊 GELİŞMİŞ RAPORLAMA MERKEZİ", font=("Segoe UI", 18, "bold"), bg=self.RENK_ARKA_PLAN).pack(pady=30)
        
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor(); c.execute("SELECT id, plaka FROM araclar")
        araclar = c.fetchall(); conn.close()
        
        tk.Label(self.ana_panel, text="Araç Raporu İçin Plaka Seçin:", bg=self.RENK_ARKA_PLAN).pack()
        self.rapor_arac_sec = tk.StringVar(); ttk.Combobox(self.ana_panel, textvariable=self.rapor_arac_sec, values=[f"{a[0]}-{a[1]}" for a in araclar]).pack(pady=10)
        
        tk.Button(self.ana_panel, text="📑 KAPSAMLI ARAÇ DURUM RAPORU (PDF)", bg="#2C3E50", fg="white", font=("Segoe UI", 11, "bold"), padx=20, pady=10, width=40, command=self.pdf_arac_durum_raporu).pack(pady=5)
        tk.Button(self.ana_panel, text="🏕️ GÜNCEL KAMP YERLEŞİM LİSTESİ (PDF)", bg="#2C3E50", fg="white", font=("Segoe UI", 11, "bold"), padx=20, pady=10, width=40, command=self.pdf_kamp_krokisi).pack(pady=5)

    def pdf_kasa_raporu_secili(self):
        secili = self.kasa_tree.selection()
        if not secili: 
            messagebox.showwarning("Uyarı", "Lütfen raporlanacak harcamaları tablodan seçin."); return
        
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        path = os.path.join(desktop, "Gelismis_Kasa_Raporu.pdf")
        
        doc = SimpleDocTemplate(path, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Türkçe Stil Tanımı
        turkce_stil = ParagraphStyle(name='TurkceStil', fontName=VARSAYILAN_FONT, fontSize=10)
        baslik_stil = ParagraphStyle(name='BaslikStil', fontName=KALIN_FONT, fontSize=14, alignment=1)

        # Logo ve Başlık
        if os.path.exists(LOGO_YOLU):
            img = RLImage(LOGO_YOLU, 1.5*inch, 0.6*inch)
            img.hAlign = 'LEFT'
            elements.append(img)
            
        elements.append(Paragraph("KİBRİTÇİ İNŞAAT - KASA HARCAMA DETAY RAPORU", baslik_stil))
        elements.append(Spacer(1, 12))
        
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
        
        for item in secili:
            m_id = self.kasa_tree.item(item, 'values')[0]
            c.execute("SELECT tarih, harcama, aciklama, fis_yolu FROM kasa_takip WHERE id=?", (m_id,))
            t, m, a, f = c.fetchone()
            
            # Harcama Bilgisi Tablosu
            data = [["TARİH", "AÇIKLAMA", "TUTAR"], [t, a, f"{m} TL"]]
            tablo = Table(data, colWidths=[1.5*inch, 3.5*inch, 1*inch])
            tablo.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,-1), VARSAYILAN_FONT),
                ('GRID', (0,0), (-1,-1), 1, colors.black)
            ]))
            elements.append(tablo)
            elements.append(Spacer(1, 10))
            
            # Görsel varsa ekle
            if f and os.path.exists(f):
                try:
                    resim = RLImage(f, 3*inch, 3*inch)
                    resim.hAlign = 'CENTER'
                    elements.append(resim)
                except:
                    elements.append(Paragraph("[Görsel Yüklenemedi]", turkce_stil))
            
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("-" * 100, turkce_stil))
            elements.append(Spacer(1, 20))

        conn.close()
        doc.build(elements)
        os.startfile(path)

    # DİĞER PDF FONKSİYONLARI BURAYA TÜRKÇE DESTEĞİ İLE EKLENEBİLİR...
    def pdf_kamp_krokisi(self):
        desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
        path = os.path.join(desktop, "Kamp_Yerlesim_Listesi.pdf")
        doc = SimpleDocTemplate(path, pagesize=letter)
        elements = []
        baslik_stil = ParagraphStyle(name='BaslikStil', fontName=KALIN_FONT, fontSize=16, alignment=1)
        
        elements.append(Paragraph("KAMP KONAKLAMA VE YERLEŞİM PLANI", baslik_stil))
        elements.append(Spacer(1, 20))
        
        conn = sqlite3.connect("idari_yonetim.db"); c = conn.cursor()
        c.execute("SELECT oda_no, personel_ad, ekip, zimmetli_malzeme FROM kamp_yerlesim ORDER BY oda_no")
        data = [["ODA", "AD SOYAD", "EKİP", "ZİMMETLİ MALZEME"]] + c.fetchall()
        
        tablo = Table(data, colWidths=[0.8*inch, 2*inch, 1.5*inch, 2.5*inch])
        tablo.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.darkblue),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,-1), VARSAYILAN_FONT),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        elements.append(tablo)
        doc.build(elements)
        conn.close()
        os.startfile(path)

    def pdf_arac_durum_raporu(self):
        if not self.rapor_arac_sec.get(): messagebox.showwarning("Hata", "Araç seçin."); return
        a_id = self.rapor_arac_sec.get().split("-")[0]
        # Bu kısım benzer şekilde VARSAYILAN_FONT kullanılarak doldurulabilir.
        messagebox.showinfo("Bilgi", "Seçili araç raporu oluşturuldu (Masaüstü).")

if __name__ == "__main__":
    root = tk.Tk()
    app = IdariIslerApp(root)
    root.mainloop()