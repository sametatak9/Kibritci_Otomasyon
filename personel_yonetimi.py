import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime
import os
import calendar

# PDF Raporlama ve Font Desteği
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A3, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# --- TÜRKÇE KARAKTER DESTEĞİ ---
try:
    pdfmetrics.registerFont(TTFont('Arial', 'arial.ttf'))
    pdfmetrics.registerFont(TTFont('Arial-Bold', 'arialbd.ttf'))
    ANAFONT = "Arial"
    ANAFONT_BOLD = "Arial-Bold"
except:
    ANAFONT = "Helvetica"
    ANAFONT_BOLD = "Helvetica-Bold"

class AnaProgram:
    def __init__(self, root):
        self.root = root
        self.root.title("KİBRİTÇİ İNŞAAT | YÖNETİM PANELİ v3.2")
        self.root.geometry("1400x900")
        
        # --- PROFESYONEL RENK PALETİ ---
        self.RENK_ARKA_PLAN = "#F8F9FA"  
        self.RENK_SIDEBAR = "#343A40"    
        self.RENK_AKTIF_MENU = "#495057" 
        self.RENK_VURGU = "#6C757D"      
        self.RENK_METIN = "#212529"      
        self.RENK_BEYAZ = "#FFFFFF"

        self.root.configure(bg=self.RENK_ARKA_PLAN)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        self.style.configure("Treeview", 
                             background=self.RENK_BEYAZ, 
                             foreground=self.RENK_METIN, 
                             rowheight=38, 
                             font=("Segoe UI", 10),
                             borderwidth=0)
        self.style.map("Treeview", background=[('selected', '#DEE2E6')], foreground=[('selected', '#000000')])
        self.style.configure("Treeview.Heading", 
                             background="#E9ECEF", 
                             foreground=self.RENK_METIN, 
                             relief="flat", 
                             font=("Segoe UI", 10, "bold"))

        self.veritabani_hazirla()
        
        self.sidebar = tk.Frame(self.root, bg=self.RENK_SIDEBAR, width=260)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        header_frame = tk.Frame(self.sidebar, bg=self.RENK_SIDEBAR, pady=40)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text="KİBRİTÇİ", font=("Segoe UI", 20, "bold"), bg=self.RENK_SIDEBAR, fg=self.RENK_BEYAZ).pack()
        tk.Label(header_frame, text="İNŞAAT A.Ş.", font=("Segoe UI", 9), bg=self.RENK_SIDEBAR, fg="#ADB5BD").pack()

        self.menu_buttons = []
        menu_items = [
            ("🏠  GENEL ÖZET", self.ana_sayfa_goster),
            ("👤  PERSONEL KAYIT", self.personel_kayit_goster),
            ("📅  GÜNLÜK PUANTAJ", self.gunluk_puantaj_goster),
            ("⏱️  MESAİ İŞLEMLERİ", self.mesai_girisi_goster),
            ("🚪  İŞTEN ÇIKIŞ", self.isten_cikis_goster),
            ("📊  HAKEDİŞ & RAPOR", self.raporlama_merkezi_goster)
        ]

        for text, command in menu_items:
            btn = tk.Button(self.sidebar, text=text, font=("Segoe UI", 10), bg=self.RENK_SIDEBAR, 
                           fg="#CED4DA", bd=0, padx=25, pady=15, anchor="w", cursor="hand2", 
                           command=command, activebackground=self.RENK_AKTIF_MENU, activeforeground="white")
            btn.pack(fill="x")
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.RENK_AKTIF_MENU, fg="white"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.RENK_SIDEBAR, fg="#CED4DA"))
            self.menu_buttons.append(btn)

        self.ana_panel = tk.Frame(self.root, bg=self.RENK_ARKA_PLAN)
        self.ana_panel.pack(side="right", expand=True, fill="both")
        
        self.ana_sayfa_goster()

    def veritabani_hazirla(self):
        conn = sqlite3.connect("sistem.db")
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM personel")
        mevcut_sayi = c.fetchone()[0]
        
        if mevcut_sayi == 0:
            c.execute("DROP TABLE IF EXISTS personel")
            c.execute("DROP TABLE IF EXISTS puantaj")
            c.execute("DROP TABLE IF EXISTS mesai")
            conn.commit()

        c.execute('''CREATE TABLE IF NOT EXISTS personel (id INTEGER PRIMARY KEY AUTOINCREMENT, tc TEXT, ad_soyad TEXT, iban TEXT, tel TEXT, gorev TEXT, maas REAL, giris_tarihi TEXT, durum TEXT DEFAULT 'Aktif', cikis_tarihi TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS puantaj (id INTEGER PRIMARY KEY AUTOINCREMENT, personel_id INTEGER, tarih TEXT, durum TEXT, UNIQUE(personel_id, tarih))''')
        c.execute('''CREATE TABLE IF NOT EXISTS mesai (id INTEGER PRIMARY KEY AUTOINCREMENT, personel_id INTEGER, tarih TEXT, gercek_saat REAL, hesaplanan_saat REAL)''')
        
        yeni_personeller = [
            ("39236078996", "MUTLU ŞİMŞEK", "TR67 0006 2001 0670 0006 6565 28", "FORMEN", 60000),
            ("39236078996", "ŞAHİN ŞAHİNOĞLU", "TR38 0006 2000 7610 0006 6916 57", "USTA", 60000),
            ("15334919072", "YASİN EFE", "TR78 0006 2001 2280 0006 6918 03", "USTA", 60000),
            ("27619711622", "YUNUS POLAT", "TR11 0006 2000 7880 0006 8037 52", "USTA", 60000),
            ("24679132374", "VEYSİ DOĞAN", "TR88 0006 2000 0860 0006 6487 36", "USTA", 60000),
            ("35992773274", "İSMAİL MALKOÇ", "TR47 0006 2000 0450 0006 9017 82", "D.İŞÇİ", 30000),
            ("13475773928", "MUHAMMED ÇELİK", "TR23 0006 2000 5120 0006 8605 94", "ŞENÖR", 30000),
            ("13571731824", "YUSUF ALİ ŞİŞİK", "TR45 0006 2000 7200 0006 6326 63", "D.İŞÇİ", 30000),
            ("10404040632", "ENES BULUT", "TR80 0006 2000 1580 0006 9494 14", "D.İŞÇİ", 30000),
            ("13031265102", "EMRAH VANER", "TR65 0006 2001 0170 0006 6707 82", "D.İŞÇİ", 30000),
            ("13001266122", "EYÜP VANER", "TR39 0006 2000 0840 0006 9705 04", "D.İŞÇİ", 30000),
            ("39439385082", "ABDURRAHMAN ÇİTO", "TR87 0006 2000 7910 0006 6283 51", "D.İŞÇİ", 30000),
            ("11537315208", "ALİ SAMET VANER", "TR60 0006 2001 0730 0006 6418 80", "D.İŞÇİ", 30000),
            ("41197589510", "HARUN ADIYAMAN", "TR30 0006 2000 7580 0006 6013 15", "D.İŞÇİ", 30000),
            ("44581050658", "FURKAN HİÇDÖNMEZ", "TR29 0006 2000 4590 0006 8744 28", "D.İŞÇİ", 30000),
            ("35371280324", "TANER AKTAŞ", "MERKEZDE VAR", "D.İŞÇİ", 30000),
            ("35371280324", "MEHMET TURHAN", "TR51 0006 2000 4750 0006 8081 86", "D.İŞÇİ", 30000),
            ("19394598222", "SEDAT ÇİTANAK", "TR75 0006 2000 7880 0006 8022 12", "D.İŞÇİ", 30000),
            ("48244468460", "MEVLÜT SEFA BÜLBÜL", "TR45 0006 2000 6340 0006 6512 32", "D.İŞÇİ", 30000),
            ("18020099010", "RECEP SOLAK", "TR65 0006 2000 6950 0006 8677 50", "D.İŞÇİ", 30000),
            ("24427885460", "MUSA MULLAOĞLU", "TR92 0006 2000 7910 0006 6135 17", "D.İŞÇİ", 30000),
            ("21367053096", "HAKAN ZORLU", "TR15 0006 2000 4460 0006 6103 23", "D.İŞÇİ", 30000),
            ("27044064232", "OLCAY AYDIN", "TR12 0006 2000 6300 0006 6479 66", "D.İŞÇİ", 30000),
            ("25927366886", "TAHSİN OTHAN", "-", "TESİSATÇI", 45000),
            ("34708074766", "MEDETULLAH DEMİR", "-", "TESİSATÇI", 45000),
            ("48199183968", "FIRAT SAYGIN(PELEN)", "TR94 0006 2001 2400 0006 6092 96", "D.İŞÇİ", 30000),
            ("10600584138", "TUNCAY KOTAN", "TR92 0006 2000 5990 0006 8757 95", "D.İŞÇİ", 30000),
            ("12248183346", "SERVET ÖZKALŞIN", "TR95 0006 2001 3020 0006 6091 62", "D.İŞÇİ", 30000),
            ("37963213734", "METİN ASLANER", "TR36 0006 2001 2770 0006 6192 73", "D.İŞÇİ", 30000),
            ("21313220060", "MEHMET POLAT", "TR38 0006 2000 7880 0005 9980 69", "D.İŞÇİ", 30000),
            ("13012496860", "MEVLAN SARI", "TR32 0006 2000 7880 0005 9980 80", "D.İŞÇİ", 30000),
            ("10693575938", "SAMET SARI", "TR23 0006 2000 5320 0006 6265 30", "D.İŞÇİ", 30000),
            ("15970398620", "ARDA SARI", "TR90 0006 2001 0820 0006 8506 21", "D.İŞÇİ", 30000),
            ("64789111210", "İSMAİL SEVGİLİ", "TR05 0006 2001 0450 0006 6902 49", "D.İŞÇİ", 30000),
            ("67495253090", "AZİZ GÜLER", "TR16 0006 2000 4290 0006 6316 33", "D.İŞÇİ", 30000),
            ("11761726382", "HÜSEYİN SAMET ATAK", "TR93 0006 2000 8480 0006 6266 00", "D.İŞÇİ", 30000),
            ("11923533183", "ÖMER SARI", "TR59 0006 2000 7880 0005 9980 79", "USTA", 60000),
            ("10114593688", "MUHAMMED ALTINTAŞ", "TR57 0006 2000 0930 0006 6263 67", "USTA", 60000),
            ("25118600980", "CEVDET ÜLEZ", "TR65 0006 2001 2810 0006 6639 33", "MERMERCİ", 45000),
            ("17486855598", "İSLAM ÜLEZ", "TR11 0006 2000 7880 0005 9983 61", "MERMERCİ", 45000),
            ("10724831422", "DOĞUŞ İRGİ", "TR91 0006 2001 5270 0006 6411 86", "D.İŞÇİ", 30000),
            ("69061214672", "HAMZA TOĞMUŞ", "TR47 0006 2000 7880 0005 9981 01", "D.İŞÇİ", 30000),
            ("12286547544", "İBRAHİM TUNÇ", "TR11 0006 2001 1060 0006 6886 47", "D.İŞÇİ", 30000),
            ("36067388898", "ADEM ÇAĞLAR", "TR56 0006 2000 5440 0006 8171 60", "D.İŞÇİ", 30000),
            ("45187803556", "EMRE PEKMEZ", "TR95 0006 2000 5990 0006 8796 21", "D.İŞÇİ", 30000),
            ("24721130976", "KASIM DOĞAN", "TR83 0006 2000 3450 0006 9773 31", "USTA", 60000),
            ("68383235884", "ERCAN AYBUĞA", "TR37 0006 2001 5930 0006 6794 64", "D.İŞÇİ", 30000),
            ("13948465336", "MAHMUT SARI", "-", "USTA", 60000),
            ("25798081178", "NUSRET AKGÜL", "-", "D.İŞÇİ", 30000),
            ("19549814900", "MEHMET EMİN ASLAN", "-", "D.İŞÇİ", 30000)
        ]

        tarih_simdi = datetime.datetime.now().strftime("%Y-%m-%d")
        for tc, ad, iban, gorev, maas in yeni_personeller:
            c.execute("SELECT id FROM personel WHERE ad_soyad = ?", (ad,))
            if not c.fetchone():
                c.execute("INSERT INTO personel (tc, ad_soyad, iban, gorev, maas, giris_tarihi, durum) VALUES (?,?,?,?,?,?, 'Aktif')",
                          (tc, ad.upper(), iban, gorev, maas, tarih_simdi))
        
        conn.commit()
        conn.close()

    def panel_temizle(self):
        for widget in self.ana_panel.winfo_children(): widget.destroy()

    def baslik_ekle(self, metin):
        f = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN, pady=30)
        f.pack(fill="x", padx=40)
        tk.Label(f, text=metin, font=("Segoe UI", 18, "bold"), bg=self.RENK_ARKA_PLAN, fg="#343A40").pack(side="left")
        tk.Frame(self.ana_panel, bg="#DEE2E6", height=1).pack(fill="x", padx=40, pady=(0,20))

    def ana_sayfa_goster(self):
        self.panel_temizle()
        self.baslik_ekle("ŞANTİYE DURUM ÖZETİ")
        
        stats_frame = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN)
        stats_frame.pack(fill="x", padx=40, pady=10)
        
        conn = sqlite3.connect("sistem.db"); c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM personel WHERE durum='Aktif'")
        aktif = c.fetchone()[0]
        
        bugun = datetime.datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM puantaj WHERE tarih=? AND (durum='GELDİ' OR durum='YARIM GÜN')", (bugun,))
        gunluk_aktif = c.fetchone()[0]

        c.execute("SELECT SUM(maas) FROM personel WHERE durum='Aktif'")
        toplam_maliyet = c.fetchone()[0] or 0
        
        simdi = datetime.datetime.now()
        ay_filtresi = simdi.strftime("%Y-%m") + "%"
        c.execute("SELECT durum FROM puantaj WHERE tarih LIKE ?", (ay_filtresi,))
        puantaj_kayitlari = c.fetchall()
        toplam_gun = sum(1 if d[0] in ["GELDİ", "İZİNLİ", "RAPORLU"] else 0.5 if d[0] == "YARIM GÜN" else 0 for d in puantaj_kayitlari)
        
        hesaplanan_toplam = toplam_gun * 1200 
        conn.close()
        
        kartlar = [
            ("TOPLAM PERSONEL", str(aktif), "#495057", "👥"), 
            ("BUGÜN ÇALIŞAN", str(gunluk_aktif), "#007BFF", "👷"),
            ("AYLIK MAAŞ YÜKÜ", f"{toplam_maliyet:,.0f} ₺", "#6C757D", "💰"), 
            ("TAHMİNİ HAKEDİŞ TOPLAMI", f"{hesaplanan_toplam:,.0f} ₺", "#28A745", "📊")
        ]
        
        for baslik, deger, renk, ikon in kartlar:
            k = tk.Frame(stats_frame, bg=self.RENK_BEYAZ, padx=25, pady=25, highlightbackground="#E9ECEF", highlightthickness=1)
            k.pack(side="left", padx=(0, 20), expand=True, fill="both")
            
            top_row = tk.Frame(k, bg=self.RENK_BEYAZ)
            top_row.pack(fill="x")
            tk.Label(top_row, text=ikon, font=("Segoe UI", 14), bg=self.RENK_BEYAZ, fg=renk).pack(side="left")
            tk.Label(top_row, text=baslik, font=("Segoe UI", 9, "bold"), bg=self.RENK_BEYAZ, fg="#6C757D").pack(side="left", padx=10)
            
            tk.Label(k, text=deger, font=("Segoe UI", 20, "bold"), bg=self.RENK_BEYAZ, fg="#212529").pack(anchor="w", pady=(15,0))

    def personel_kayit_goster(self):
        self.panel_temizle()
        self.baslik_ekle("YENİ PERSONEL KAYDI")
        
        container = tk.Frame(self.ana_panel, bg=self.RENK_BEYAZ, padx=50, pady=40, highlightbackground="#E9ECEF", highlightthickness=1)
        container.pack(pady=10)
        
        self.entries = {}
        fields = ["ID", "TC No", "Adı Soyadı", "IBAN", "Telefon", "Görevi", "Maaş", "Giriş Tarihi"]
        
        for i, field in enumerate(fields):
            row, col = divmod(i, 2)
            f_frame = tk.Frame(container, bg=self.RENK_BEYAZ)
            f_frame.grid(row=row, column=col, padx=25, pady=15, sticky="w")
            
            tk.Label(f_frame, text=field.upper(), bg=self.RENK_BEYAZ, fg=self.RENK_VURGU, font=("Segoe UI", 8, "bold")).pack(anchor="w")
            ent = tk.Entry(f_frame, width=35, bg="#F8F9FA", fg=self.RENK_METIN, bd=1, relief="solid", font=("Segoe UI", 11))
            ent.pack(pady=(5,0), ipady=8)
            self.entries[field] = ent
            
        self.entries["Giriş Tarihi"].insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        
        tk.Button(container, text="SİSTEME KAYDET", bg=self.RENK_SIDEBAR, fg="white", 
                  font=("Segoe UI", 10, "bold"), bd=0, padx=60, pady=15, 
                  cursor="hand2", command=self.personel_kaydet).grid(row=4, column=0, columnspan=2, pady=40)

    def personel_kaydet(self):
        d = self.entries
        try:
            conn = sqlite3.connect("sistem.db"); c = conn.cursor()
            c.execute("INSERT INTO personel (tc, ad_soyad, iban, tel, gorev, maas, giris_tarihi, durum) VALUES (?,?,?,?,?,?,?, 'Aktif')",
                      (d["TC No"].get(), d["Adı Soyadı"].get().upper(), d["IBAN"].get(), d["Telefon"].get(), d["Görevi"].get().upper(), d["Maaş"].get(), d["Giriş Tarihi"].get()))
            conn.commit(); conn.close(); messagebox.showinfo("BAŞARILI", "Personel kaydı oluşturuldu."); self.ana_sayfa_goster()
        except Exception as e: messagebox.showerror("HATA", "Bilgileri kontrol edin: " + str(e))

    def gunluk_puantaj_goster(self):
        self.panel_temizle()
        self.baslik_ekle("GÜNLÜK PUANTAJ ÇİZELGESİ")
        
        ust_bar = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN)
        ust_bar.pack(fill="x", padx=40, pady=10)
        
        tk.Label(ust_bar, text="📅 TARİH:", font=("Segoe UI", 9, "bold"), bg=self.RENK_ARKA_PLAN).pack(side="left")
        self.p_tarih = tk.Entry(ust_bar, width=12, bg="white", bd=1, relief="solid", font=("Segoe UI", 10))
        self.p_tarih.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        self.p_tarih.pack(side="left", padx=10, ipady=4)
        
        tk.Button(ust_bar, text="LİSTELE", bg=self.RENK_VURGU, fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=15, command=self.puantaj_listele).pack(side="left", padx=5)
        
        # --- ARAMA KUTUSU (YENİ) ---
        tk.Label(ust_bar, text="🔍 ARA:", font=("Segoe UI", 9, "bold"), bg=self.RENK_ARKA_PLAN).pack(side="left", padx=(20,5))
        self.p_ara = tk.Entry(ust_bar, width=15, bg="white", bd=1, relief="solid", font=("Segoe UI", 10))
        self.p_ara.pack(side="left", padx=5, ipady=4)
        self.p_ara.bind("<KeyRelease>", lambda e: self.puantaj_listele())

        tk.Frame(ust_bar, width=2, bg="#DEE2E6").pack(side="left", fill="y", padx=20)
        
        tk.Label(ust_bar, text="DURUM:", font=("Segoe UI", 9, "bold"), bg=self.RENK_ARKA_PLAN).pack(side="left")
        self.yoklama_combo = ttk.Combobox(ust_bar, values=["GELDİ", "YOK", "İZİNLİ", "RAPORLU", "YARIM GÜN"], state="readonly", width=12)
        self.yoklama_combo.current(0); self.yoklama_combo.pack(side="left", padx=10, ipady=3)
        
        tk.Button(ust_bar, text="SEÇİLİYE İŞLE", bg=self.RENK_SIDEBAR, fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=15, pady=5, command=lambda: self.puantaj_islem("kaydet")).pack(side="left", padx=5)
        
        # --- KAYDET BUTONU (YENİ) ---
        tk.Button(ust_bar, text="💾 TÜMÜNÜ KAYDET", bg="#28A745", fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=20, pady=5, command=self.puantaj_toplu_kaydet).pack(side="left", padx=5)
        tk.Button(ust_bar, text="SİL", bg="#DC3545", fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=15, command=self.puantaj_sil).pack(side="left", padx=5)

        self.p_tree = ttk.Treeview(self.ana_panel, columns=("ID", "AD SOYAD", "GÖREV", "DURUM"), show="headings", selectmode="extended")
        for col in ("ID", "AD SOYAD", "GÖREV", "DURUM"): 
            self.p_tree.heading(col, text=col); self.p_tree.column(col, anchor="center")
        self.p_tree.pack(fill="both", expand=True, padx=40, pady=20)
        self.puantaj_listele()

    def puantaj_listele(self):
        for i in self.p_tree.get_children(): self.p_tree.delete(i)
        secili_tarih = self.p_tarih.get()
        arama_kelimesi = self.p_ara.get().upper()
        conn = sqlite3.connect("sistem.db"); c = conn.cursor()
        
        # DÜZELTME: Sütun adını 'giris_tarihi' yaptık ve tarih kontrolü ekledik
        sorgu = "SELECT id, ad_soyad, gorev FROM personel WHERE durum='Aktif' AND giris_tarihi <= ?"
        parametreler = [secili_tarih]
        
        if arama_kelimesi:
            sorgu += " AND ad_soyad LIKE ?"
            parametreler.append(f"%{arama_kelimesi}%")
            
        c.execute(sorgu, parametreler)
        personeller = c.fetchall()
        for p in personeller:
            c.execute("SELECT durum FROM puantaj WHERE personel_id=? AND tarih=?", (p[0], secili_tarih))
            st = c.fetchone()
            self.p_tree.insert("", "end", values=(p[0], p[1], p[2], st[0] if st else "---"))
        conn.close()

    def puantaj_islem(self, islem_tipi):
        sel = self.p_tree.selection()
        if not sel:
            messagebox.showwarning("UYARI", "Personel seçmelisiniz."); return
        tarih = self.p_tarih.get(); durum = self.yoklama_combo.get()
        conn = sqlite3.connect("sistem.db"); c = conn.cursor()
        for i in sel:
            p_id = self.p_tree.item(i)["values"][0]
            c.execute("INSERT OR REPLACE INTO puantaj (personel_id, tarih, durum) VALUES (?,?,?)", (p_id, tarih, durum))
        conn.commit(); conn.close(); self.puantaj_listele()

    def puantaj_toplu_kaydet(self):
        tarih = self.p_tarih.get()
        conn = sqlite3.connect("sistem.db"); c = conn.cursor()
        count = 0
        for i in self.p_tree.get_children():
            v = self.p_tree.item(i)["values"]
            if v[3] != "---":
                c.execute("INSERT OR REPLACE INTO puantaj (personel_id, tarih, durum) VALUES (?,?,?)", (v[0], tarih, v[3]))
                count += 1
        conn.commit(); conn.close()
        messagebox.showinfo("KAYIT", f"{count} personelin puantajı başarıyla kaydedildi.")

    def puantaj_sil(self):
        sel = self.p_tree.selection()
        if not sel:
            messagebox.showwarning("UYARI", "Silmek için personel seçmelisiniz."); return
        if messagebox.askyesno("ONAY", "Seçili personellerin bu tarihteki yoklama kaydı silinecek. Emin misiniz?"):
            tarih = self.p_tarih.get()
            conn = sqlite3.connect("sistem.db"); c = conn.cursor()
            for i in sel:
                p_id = self.p_tree.item(i)["values"][0]
                c.execute("DELETE FROM puantaj WHERE personel_id=? AND tarih=?", (p_id, tarih))
            conn.commit(); conn.close(); self.puantaj_listele()

    def mesai_girisi_goster(self):
        self.panel_temizle()
        self.baslik_ekle("MESAİ KAYIT PANELİ")
        ust_bar = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN)
        ust_bar.pack(fill="x", padx=40, pady=10)
        
        tk.Label(ust_bar, text="TARİH:", bg=self.RENK_ARKA_PLAN, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        self.m_tarih = tk.Entry(ust_bar, width=12, bg="white", bd=1, relief="solid", font=("Segoe UI", 10))
        self.m_tarih.insert(0, datetime.datetime.now().strftime("%Y-%m-%d"))
        self.m_tarih.pack(side="left", padx=5, ipady=4)
        
        tk.Button(ust_bar, text="LİSTELE", bg=self.RENK_VURGU, fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=15, command=self.mesai_listele).pack(side="left", padx=5)
        
        # --- ARAMA KUTUSU (YENİ) ---
        tk.Label(ust_bar, text="🔍 ARA:", font=("Segoe UI", 9, "bold"), bg=self.RENK_ARKA_PLAN).pack(side="left", padx=(15,5))
        self.m_ara = tk.Entry(ust_bar, width=12, bg="white", bd=1, relief="solid", font=("Segoe UI", 10))
        self.m_ara.pack(side="left", padx=5, ipady=4)
        self.m_ara.bind("<KeyRelease>", lambda e: self.mesai_listele())

        tk.Label(ust_bar, text="SAAT:", bg=self.RENK_ARKA_PLAN, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(15,5))
        self.m_saat = tk.Entry(ust_bar, width=5, bg="white", bd=1, relief="solid", font=("Segoe UI", 10))
        self.m_saat.insert(0, "1.0")
        self.m_saat.pack(side="left", padx=5, ipady=4)
        
        tk.Button(ust_bar, text="SEÇİLİYE EKLE", bg=self.RENK_SIDEBAR, fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=15, pady=5, command=self.mesai_kaydet).pack(side="left", padx=10)
        
        # --- KAYDET BUTONU (YENİ) ---
        tk.Button(ust_bar, text="💾 TÜMÜNÜ KAYDET", bg="#28A745", fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=15, pady=5, command=self.mesai_toplu_kaydet).pack(side="left", padx=5)
        tk.Button(ust_bar, text="SİL", bg="#DC3545", fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=5, command=self.mesai_sil).pack(side="left", padx=5)

        cols = ("ID", "AD SOYAD", "GÖREV", "GÜNLÜK TOPLAM MESAİ")
        self.m_tree = ttk.Treeview(self.ana_panel, columns=cols, show="headings", selectmode="extended")
        for col in cols:
            self.m_tree.heading(col, text=col); self.m_tree.column(col, anchor="center")
        self.m_tree.pack(fill="both", expand=True, padx=40, pady=20)
        self.mesai_listele()

    def mesai_listele(self):
        for i in self.m_tree.get_children(): self.m_tree.delete(i)
        tarih = self.m_tarih.get()
        arama = self.m_ara.get().upper()
        conn = sqlite3.connect("sistem.db"); c = conn.cursor()
        
        # DÜZELTME: Sütun adını 'giris_tarihi' yaptık ve tarih kontrolü ekledik
        sorgu = "SELECT id, ad_soyad, gorev FROM personel WHERE durum='Aktif' AND giris_tarihi <= ?"
        parametreler = [tarih]
        
        if arama:
            sorgu += " AND ad_soyad LIKE ?"
            parametreler.append(f"%{arama}%")
            
        c.execute(sorgu, parametreler)
        personeller = c.fetchall()
        for p in personeller:
            c.execute("SELECT SUM(gercek_saat) FROM mesai WHERE personel_id=? AND tarih=?", (p[0], tarih))
            mesai_toplam = c.fetchone()[0]
            self.m_tree.insert("", "end", values=(p[0], p[1], p[2], f"{mesai_toplam} Saat" if mesai_toplam else "---"))
        conn.close()

    def mesai_kaydet(self):
        sel = self.m_tree.selection()
        if not sel:
            messagebox.showwarning("UYARI", "Personel seçmelisiniz."); return
        try:
            saat = float(self.m_saat.get().replace(",", "."))
            tarih = self.m_tarih.get()
            conn = sqlite3.connect("sistem.db"); c = conn.cursor()
            for i in sel:
                p_id = self.m_tree.item(i)["values"][0]
                c.execute("INSERT INTO mesai (personel_id, tarih, gercek_saat, hesaplanan_saat) VALUES (?,?,?,?)", (p_id, tarih, saat, saat * 1.5))
            conn.commit(); conn.close()
            self.mesai_listele()
        except: messagebox.showerror("HATA", "Geçersiz saat formatı.")

    def mesai_toplu_kaydet(self):
        # Mesai zaten "Mesai Ekle" denildiğinde veritabanına yazılıyor, 
        # buradaki buton kullanıcıya güven vermek ve listeyi yenilemek içindir.
        self.mesai_listele()
        messagebox.showinfo("BİLGİ", "Tüm mesai kayıtları veritabanında güncellendi.")

    def mesai_sil(self):
        sel = self.m_tree.selection()
        if not sel: return
        tarih = self.m_tarih.get()
        conn = sqlite3.connect("sistem.db"); c = conn.cursor()
        for i in sel:
            p_id = self.m_tree.item(i)["values"][0]
            c.execute("DELETE FROM mesai WHERE personel_id=? AND tarih=?", (p_id, tarih))
        conn.commit(); conn.close(); self.mesai_listele()

    def isten_cikis_goster(self):
        self.panel_temizle()
        self.baslik_ekle("PERSONEL ÇIKIŞ İŞLEMİ")
        f = tk.Frame(self.ana_panel, bg="white", padx=50, pady=50, highlightbackground="#E9ECEF", highlightthickness=1); f.pack(pady=20)
        conn = sqlite3.connect("sistem.db"); c = conn.cursor()
        c.execute("SELECT id, ad_soyad FROM personel WHERE durum='Aktif'")
        plist = [f"{r[0]} | {r[1]}" for r in c.fetchall()]; conn.close()
        tk.Label(f, text="ÇIKIŞ YAPACAK PERSONELİ SEÇİN", font=("Segoe UI", 9, "bold"), bg="white", fg=self.RENK_VURGU).pack(pady=(0,10))
        self.c_combo = ttk.Combobox(f, values=plist, width=45); self.c_combo.pack(pady=20, ipady=5)
        tk.Button(f, text="KAYDI ARŞİVLE VE ÇIKIŞ VER", bg="#DC3545", fg="white", font=("Segoe UI", 10, "bold"), bd=0, padx=40, pady=12, command=self.cikis_yap).pack()

    def cikis_yap(self):
        if not self.c_combo.get(): return
        p_id = self.c_combo.get().split(" | ")[0]
        conn = sqlite3.connect("sistem.db"); c = conn.cursor()
        c.execute("UPDATE personel SET durum='Pasif', cikis_tarihi=? WHERE id=?", (datetime.datetime.now().strftime("%Y-%m-%d"), p_id))
        conn.commit(); conn.close(); messagebox.showinfo("BİLGİ", "Personel kaydı arşivlendi."); self.ana_sayfa_goster()

    def raporlama_merkezi_goster(self):
        self.panel_temizle()
        self.baslik_ekle("HAKEDİŞ VE RAPORLAMA")
        ust = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN)
        ust.pack(fill="x", padx=40, pady=10)
        
        tk.Label(ust, text="AY (MM):", bg=self.RENK_ARKA_PLAN, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        self.r_ay = tk.Entry(ust, width=5, bg="white", bd=1, relief="solid", font=("Segoe UI", 10))
        self.r_ay.insert(0, datetime.datetime.now().strftime("%m")); self.r_ay.pack(side="left", padx=5, ipady=5)
        
        tk.Label(ust, text="YIL (YYYY):", bg=self.RENK_ARKA_PLAN, font=("Segoe UI", 9, "bold")).pack(side="left", padx=5)
        self.r_yil = tk.Entry(ust, width=8, bg="white", bd=1, relief="solid", font=("Segoe UI", 10))
        self.r_yil.insert(0, "2026"); self.r_yil.pack(side="left", padx=5, ipady=5)
        
        tk.Button(ust, text="HESAPLA", bg=self.RENK_SIDEBAR, fg="white", bd=0, padx=25, pady=6, font=("Segoe UI", 9, "bold"), command=self.rapor_getir).pack(side="left", padx=15)

        buton_frame = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN)
        buton_frame.pack(fill="x", padx=40, pady=10)

        btns = [
            ("📄 MAAŞ HAKEDİŞ", "#343A40", self.pdf_maas_hakedis_olustur),
            ("📋 FORMEN PUANTAJ", "#28A745", self.pdf_formen_ozel_puantaj_olustur),
            ("📊 AYLIK DETAYLI ÖZET", "#17A2B8", self.pdf_aylik_ozet_a3_olustur),
            ("⭐ KİBAR RAPORLA", "#6C757D", self.kibar_raporla_olustur) 
        ]
        for t, r, c in btns:
            tk.Button(buton_frame, text=t, bg=r, fg="white", bd=0, padx=20, pady=10, font=("Segoe UI", 9, "bold"), command=c).pack(side="left", padx=5)

        cols = ("ID", "AD SOYAD", "MAAŞ", "GÜN", "HAKEDİŞ", "MESAİ TL", "TOPLAM")
        self.r_tree = ttk.Treeview(self.ana_panel, columns=cols, show="headings")
        for col in cols: 
            self.r_tree.heading(col, text=col); self.r_tree.column(col, anchor="center", width=120)
        self.r_tree.pack(fill="both", expand=True, padx=40, pady=20)

        onay_container = tk.Frame(self.ana_panel, bg="#F1F3F5", height=100)
        onay_container.pack(fill="x", side="bottom", padx=40, pady=20)
        for o in ["ŞANTİYE ŞEFİ", "PROJE MÜDÜRÜ", "MUHASEBE ONAY", "MERKEZ ONAY"]:
            f = tk.Frame(onay_container, bg="#F1F3F5", highlightbackground="#DEE2E6", highlightthickness=1)
            f.pack(side="left", expand=True, fill="both", padx=5, pady=5)
            tk.Label(f, text=o, bg="#F1F3F5", font=("Segoe UI", 8, "bold"), fg="#495057").pack(pady=2)
            tk.Label(f, text="\n..........\nİMZA", bg="#F1F3F5", font=("Segoe UI", 7), fg="#ADB5BD").pack()

    def rapor_getir(self):
        for i in self.r_tree.get_children(): self.r_tree.delete(i)
        ay = self.r_ay.get(); yil = self.r_yil.get()
        tarih_filtresi = f"{yil}-{ay}%"
        conn = sqlite3.connect("sistem.db"); c = conn.cursor()
        c.execute("SELECT id, ad_soyad, maas FROM personel WHERE durum = 'Aktif'")
        personeller = c.fetchall()
        for p_id, ad, maas in personeller:
            c.execute("SELECT durum FROM puantaj WHERE personel_id=? AND tarih LIKE ?", (p_id, tarih_filtresi))
            kayitlar = c.fetchall()
            if not kayitlar: continue
            gun_toplam = sum(1 if d[0] in ["GELDİ", "İZİNLİ", "RAPORLU"] else 0.5 if d[0]=="YARIM GÜN" else 0 for d in kayitlar)
            gunluk = maas / 30
            hakedis = gunluk * gun_toplam
            c.execute("SELECT SUM(hesaplanan_saat) FROM mesai WHERE personel_id=? AND tarih LIKE ?", (p_id, tarih_filtresi))
            m_saat = c.fetchone()[0] or 0
            m_tl = m_saat * (gunluk / 8)
            toplam = hakedis + m_tl
            self.r_tree.insert("", "end", values=(p_id, ad, f"{maas:.0f}", gun_toplam, f"{hakedis:.2f}", f"{m_tl:.2f}", f"{toplam:.2f}"))
        conn.close()

    def pdf_olustur_ve_ac(self, dosya_adi, doc_obj, elements):
        try:
            doc_obj.build(elements)
            os.startfile(dosya_adi)
        except Exception as e: messagebox.showerror("HATA", f"PDF Hatası: {str(e)}")

    def kibar_raporla_olustur(self):
        if not self.r_tree.get_children(): 
            messagebox.showwarning("UYARI", "Önce HESAPLA butonuna basarak listeyi tazeleyin."); return
        ay, yil = self.r_ay.get(), self.r_yil.get()
        dosya = f"Kibar_Raporu_{yil}_{ay}.pdf"
        doc = SimpleDocTemplate(dosya, pagesize=A4)
        elements = []
        elements.append(Paragraph(f"KİBRİTÇİ İNŞAAT - KİBAR HAKEDİŞ RAPORU", ParagraphStyle('T', fontName=ANAFONT_BOLD, fontSize=16, alignment=1, spaceAfter=10)))
        elements.append(Paragraph(f"Dönem: {ay} / {yil}", ParagraphStyle('S', fontName=ANAFONT, fontSize=12, alignment=1, spaceAfter=20)))
        data = [["ID", "PERSONEL AD SOYAD", "GELDİĞİ GÜN", "BİRİM YEVMİYE", "TOPLAM TUTAR"]]
        genel_toplam = 0
        for row in self.r_tree.get_children():
            v = self.r_tree.item(row)["values"]
            p_id, ad, maas, gun = v[0], v[1], float(v[2]), float(v[3])
            yevmiye = maas / 30
            tutar = gun * 200
            genel_toplam += tutar
            data.append([p_id, ad, f"{gun}", f"{yevmiye:,.0f} TL", f"{tutar:,.2f} TL"])
        data.append(["", "", "", "GENEL TOPLAM:", f"{genel_toplam:,.2f} TL"])
        t = Table(data, colWidths=[40, 220, 80, 80, 100])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.darkgrey),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,-1),ANAFONT),('FONTNAME',(0,0),(-1,0),ANAFONT_BOLD),('GRID',(0,0),(-1,-1),0.5,colors.black)]))
        elements.append(t)
        self.pdf_olustur_ve_ac(dosya, doc, elements)

    def pdf_maas_hakedis_olustur(self):
        if not self.r_tree.get_children(): return
        ay, yil = self.r_ay.get(), self.r_yil.get()
        dosya = f"Maas_Hakedis_{yil}_{ay}.pdf"
        doc = SimpleDocTemplate(dosya, pagesize=landscape(A4))
        elements = []
        elements.append(Paragraph(f"KİBRİTÇİ İNŞAAT - {yil} / {ay} MAAŞ HAKEDİŞ ÇİZELGESİ", ParagraphStyle('T', fontName=ANAFONT_BOLD, fontSize=14, alignment=1, spaceAfter=20)))
        data = [["ID", "AD SOYAD", "MAAŞ", "GÜN", "HAKEDİŞ", "MESAİ TL", "TOPLAM"]]
        for row in self.r_tree.get_children(): data.append(self.r_tree.item(row)["values"])
        t = Table(data, repeatRows=1, colWidths=[40, 180, 80, 60, 80, 80, 100])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.grey),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('ALIGN',(0,0),(-1,-1),'CENTER'),('FONTNAME',(0,0),(-1,-1),ANAFONT),('GRID',(0,0),(-1,-1),0.5,colors.black)]))
        elements.append(t)
        self.pdf_olustur_ve_ac(dosya, doc, elements)
    def personel_kayit_goster(self):
        self.panel_temizle()
        self.baslik_ekle("PERSONEL YÖNETİMİ (KAYIT & GÜNCELLEME)")
        
        ana_container = tk.Frame(self.ana_panel, bg=self.RENK_ARKA_PLAN)
        ana_container.pack(fill="both", expand=True, padx=40)

        # 1. ÖNCE LİSTE (TREEVIEW) OLUŞTURULMALI
        sag_frame = tk.Frame(ana_container, bg=self.RENK_ARKA_PLAN)
        sag_frame.pack(side="right", fill="both", expand=True, padx=(20,0), pady=10)
        
        cols = ("ID", "TC", "AD SOYAD", "GÖREV")
        self.p_yonetim_tree = ttk.Treeview(sag_frame, columns=cols, show="headings")
        for col in cols:
            self.p_yonetim_tree.heading(col, text=col)
            self.p_yonetim_tree.column(col, width=100, anchor="center")
        
        self.p_yonetim_tree.pack(fill="both", expand=True)
        self.p_yonetim_tree.bind("<<TreeviewSelect>>", self.personel_form_doldur)

        # 2. SONRA FORM (SOL TARAF) OLUŞTURULMALI
        sol_frame = tk.Frame(ana_container, bg=self.RENK_BEYAZ, padx=20, pady=20, highlightbackground="#E9ECEF", highlightthickness=1)
        sol_frame.pack(side="left", fill="y", pady=10)
        
        self.entries = {}
        fields = ["ID", "TC No", "Adı Soyadı", "IBAN", "Telefon", "Görevi", "Maaş", "Giriş Tarihi"]
        
        for i, field in enumerate(fields):
            f_frame = tk.Frame(sol_frame, bg=self.RENK_BEYAZ)
            f_frame.pack(fill="x", pady=5)
            tk.Label(f_frame, text=field.upper(), bg=self.RENK_BEYAZ, fg=self.RENK_VURGU, font=("Segoe UI", 8, "bold")).pack(anchor="w")
            ent = tk.Entry(f_frame, width=30, bg="#F8F9FA", fg=self.RENK_METIN, bd=1, relief="solid", font=("Segoe UI", 10))
            ent.pack(pady=(2,0), ipady=5)
            self.entries[field] = ent
            if field == "ID": ent.config(state="readonly")
            
        btn_frame = tk.Frame(sol_frame, bg=self.RENK_BEYAZ)
        btn_frame.pack(fill="x", pady=20)
        tk.Button(btn_frame, text="YENİ KAYIT", bg="#28A745", fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=20, pady=10, command=self.personel_kaydet).pack(side="left", padx=5)
        tk.Button(btn_frame, text="GÜNCELLE", bg=self.RENK_SIDEBAR, fg="white", font=("Segoe UI", 9, "bold"), bd=0, padx=20, pady=10, command=self.personel_guncelle).pack(side="left", padx=5)

        # 3. EN SON VERİLERİ ÇAĞIR (Artık p_yonetim_tree hazır olduğu için hata vermez)
        self.personel_mini_listele()

    def personel_mini_listele(self):
        for i in self.p_yonetim_tree.get_children(): self.p_yonetim_tree.delete(i)
        conn = sqlite3.connect("sistem.db")
        c = conn.cursor()
        c.execute("SELECT id, tc, ad_soyad, gorev FROM personel WHERE durum='Aktif'")
        for p in c.fetchall(): self.p_yonetim_tree.insert("", "end", values=p)
        conn.close()

    def personel_form_doldur(self, event):
        sel = self.p_yonetim_tree.selection()
        if not sel: return
        
        # Treeview'dan seçilen satırdaki ID'yi al (ilk sütun ID olmalı)
        values = self.p_yonetim_tree.item(sel[0])["values"]
        p_id = values[0]
        
        conn = sqlite3.connect("sistem.db")
        c = conn.cursor()
        # Sütun sırasını tam olarak fields listesiyle eşleştiriyoruz:
        c.execute("SELECT id, tc, ad_soyad, iban, tel, gorev, maas, giris_tarihi FROM personel WHERE id=?", (p_id,))
        p = c.fetchone()
        conn.close()
        
        if p:
            # Formdaki alan adları (Sıralama yukarıdaki SQL sorgusuyla birebir aynı olmalı)
            fields = ["ID", "TC No", "Adı Soyadı", "IBAN", "Telefon", "Görevi", "Maaş", "Giriş Tarihi"]
            
            for i, field in enumerate(fields):
                # Önce kutuyu yazılabilir yap, temizle, veriyi bas, sonra ID ise tekrar kilitle
                self.entries[field].config(state="normal")
                self.entries[field].delete(0, tk.END)
                
                # Eğer veritabanından gelen veri None ise boşluk bırak, hata almamak için kontrol ekledik
                veri = p[i] if p[i] is not None else ""
                self.entries[field].insert(0, veri)
                
                if field == "ID":
                    self.entries[field].config(state="readonly")

    def personel_guncelle(self):
        d = self.entries
        p_id = d["ID"].get()
        if not p_id:
            messagebox.showwarning("UYARI", "Lütfen listeden bir personel seçin."); return
            
        try:
            conn = sqlite3.connect("sistem.db")
            c = conn.cursor()
            c.execute("""UPDATE personel SET tc=?, ad_soyad=?, iban=?, tel=?, gorev=?, maas=?, giris_tarihi=? WHERE id=?""",
                      (d["TC No"].get(), d["Adı Soyadı"].get().upper(), d["IBAN"].get(), d["Telefon"].get(), 
                       d["Görevi"].get().upper(), d["Maaş"].get(), d["Giriş Tarihi"].get(), p_id))
            conn.commit()
            conn.close()
            messagebox.showinfo("BAŞARILI", "Personel bilgileri güncellendi.")
            self.personel_mini_listele()
        except Exception as e:
            messagebox.showerror("HATA", "Güncelleme yapılamadı: " + str(e))
    def pdf_formen_ozel_puantaj_olustur(self):
        try:
            ay = self.r_ay.get(); yil = self.r_yil.get()
            dosya_adi = f"Formen_Saha_Yoklama_{yil}_{ay}.pdf"
            c = canvas.Canvas(dosya_adi, pagesize=landscape(A3))
            genislik, yukseklik = landscape(A3)
            c.setFont(ANAFONT_BOLD, 18); c.drawCentredString(genislik/2, yukseklik - 40, f"KİBRİTÇİ İNŞAAT - SAHA YOKLAMA LİSTESİ ({ay}/{yil})")
            x_bas, y_mevcut, h_w, h_h = 30, yukseklik - 80, 25, 25
            c.setFont(ANAFONT_BOLD, 8); c.rect(x_bas, y_mevcut, 150, 20); c.drawString(x_bas + 5, y_mevcut + 7, "PERSONEL AD SOYAD")
            gun_sayisi = calendar.monthrange(int(yil), int(ay))[1]
            for g in range(1, gun_sayisi + 1):
                c.rect(x_bas + 150 + (g-1)*h_w, y_mevcut, h_w, 20)
                c.drawCentredString(x_bas + 150 + (g-1)*h_w + h_w/2, y_mevcut + 7, str(g))
            y_mevcut -= h_h
            conn = sqlite3.connect("sistem.db"); cur = conn.cursor()
            cur.execute("SELECT ad_soyad FROM personel WHERE durum='Aktif' ORDER BY ad_soyad ASC")
            personeller = cur.fetchall()
            c.setFont(ANAFONT, 9)
            for p in personeller:
                c.rect(x_bas, y_mevcut, 150, h_h); c.drawString(x_bas + 5, y_mevcut + 7, str(p[0]))
                for g in range(1, gun_sayisi + 1): c.rect(x_bas + 150 + (g-1)*h_w, y_mevcut, h_w, h_h)
                y_mevcut -= h_h
                if y_mevcut < 50: c.showPage(); c.setPageSize(landscape(A3)); y_mevcut = yukseklik - 50
            conn.close(); c.save(); os.startfile(dosya_adi)
        except Exception as e: messagebox.showerror("Hata", str(e))
    def pdf_aylik_ozet_a3_olustur(self):
        try:
            ay, yil = self.r_ay.get(), self.r_yil.get()
            dosya_adi = f"Aylik_Ozet_Rapor_{yil}_{ay}.pdf"
            c = canvas.Canvas(dosya_adi, pagesize=landscape(A3))
            genislik, yukseklik = landscape(A3)
            c.setFont(ANAFONT_BOLD, 16); c.drawCentredString(genislik/2, yukseklik - 40, f"KİBRİTÇİ İNŞAAT - {yil}/{ay} PERSONEL YOKLAMA VE MESAİ ÇİZELGESİ")
            x_start, y_konum, hucre_w, hucre_h = 30, yukseklik - 80, 26, 32
            c.setFont(ANAFONT_BOLD, 8); c.rect(x_start, y_konum, 120, 20); c.drawString(x_start + 5, y_konum + 7, "PERSONEL AD SOYAD")
            gun_sayisi = calendar.monthrange(int(yil), int(ay))[1]
            for g in range(1, gun_sayisi + 1):
                c.rect(x_start + 120 + (g-1)*hucre_w, y_konum, hucre_w, 20)
                c.drawCentredString(x_start + 120 + (g-1)*hucre_w + hucre_w/2, y_konum + 7, str(g))
            c.rect(x_start + 120 + gun_sayisi*hucre_w, y_konum, 45, 20); c.drawString(x_start + 120 + gun_sayisi*hucre_w + 5, y_konum + 7, "TOPLAM")
            conn = sqlite3.connect("sistem.db"); cur = conn.cursor()
            y_konum -= hucre_h
            for row in self.r_tree.get_children():
                v = self.r_tree.item(row)["values"]; p_id, p_ad = v[0], v[1]
                c.rect(x_start, y_konum, 120, hucre_h); c.setFont(ANAFONT, 8); c.drawString(x_start + 5, y_konum + 12, str(p_ad))
                aylik_mesai = 0
                for g in range(1, gun_sayisi + 1):
                    tarih = f"{yil}-{ay.zfill(2)}-{str(g).zfill(2)}"
                    cur.execute("SELECT durum FROM puantaj WHERE personel_id=? AND tarih=?", (p_id, tarih))
                    dur = cur.fetchone()
                    cur.execute("SELECT SUM(gercek_saat) FROM mesai WHERE personel_id=? AND tarih=?", (p_id, tarih))
                    ms = cur.fetchone(); ms_deger = ms[0] if ms and ms[0] else 0
                    c.rect(x_start + 120 + (g-1)*hucre_w, y_konum, hucre_w, hucre_h)
                    if dur:
                        d_metin = "X" if dur[0] == "GELDİ" else "İ" if dur[0] in ["İZİNLİ", "RAPORLU"] else "1/2" if dur[0] == "YARIM GÜN" else "-"
                        c.setFont(ANAFONT_BOLD, 9); c.drawCentredString(x_start + 120 + (g-1)*hucre_w + hucre_w/2, y_konum + 18, d_metin)
                    if ms_deger > 0:
                        c.setFont(ANAFONT, 7); c.drawCentredString(x_start + 120 + (g-1)*hucre_w + hucre_w/2, y_konum + 5, str(ms_deger)); aylik_mesai += ms_deger
                c.rect(x_start + 120 + gun_sayisi*hucre_w, y_konum, 45, hucre_h)
                c.setFont(ANAFONT_BOLD, 7); c.drawString(x_start + 120 + gun_sayisi*hucre_w + 3, y_konum + 18, f"G:{v[3]}"); c.drawString(x_start + 120 + gun_sayisi*hucre_w + 3, y_konum + 5, f"M:{aylik_mesai}")
                y_konum -= hucre_h
                if y_konum < 100: c.showPage(); c.setPageSize(landscape(A3)); y_konum = yukseklik - 100
            c.save(); conn.close(); os.startfile(dosya_adi)
        except Exception as e: messagebox.showerror("HATA", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = AnaProgram(root)
    root.mainloop()