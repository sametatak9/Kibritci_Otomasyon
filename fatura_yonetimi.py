import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import datetime
import os
import shutil
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- MODERN TASARIM PALETİ ---
RENK_BG = "#F1F5F9"           # Açık, ferah arka plan
RENK_SIDEBAR = "#FFFFFF"      # Beyaz temiz paneller
RENK_PRIMARY = "#2563EB"      # Modern Kurumsal Mavi
RENK_SUCCESS = "#059669"      # Zümrüt Yeşili (Onay)
RENK_DANGER = "#DC2626"       # Canlı Kırmızı (Sil)
RENK_TEXT = "#1E293B"         # Koyu Lacivert/Gri Metin
RENK_ACCENT = "#6366F1"       # İndigo (Vurgu)

class FaturaSistemi:
    def __init__(self, root):
        self.root = root
        self.root.title("KİBRİTÇİ İNŞAAT | DENETİM VE ARŞİV SİSTEMİ V6.0")
        self.root.geometry("1500x950")
        self.root.configure(bg=RENK_BG)
        
        # Klasör Hazırlığı
        self.arsiv_klasoru = "FATURA_ARSIVI"
        self.rapor_klasoru = "DENETIM_RAPORLARI"
        for klasor in [self.arsiv_klasoru, self.rapor_klasoru]:
            if not os.path.exists(klasor): os.makedirs(klasor)
        
        self.gecici_kalemler = [] 
        self.veritabani_hazirla()
        self.stil_olustur()
        
        # Ana Konteyner
        self.main_container = tk.Frame(self.root, bg=RENK_BG)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Tab Yapısı (Modern Stil)
        self.tabs = ttk.Notebook(self.main_container)
        self.tab_arsiv = tk.Frame(self.tabs, bg=RENK_BG)
        self.tab_denetim = tk.Frame(self.tabs, bg=RENK_BG)
        self.tabs.add(self.tab_arsiv, text="  📥 EVRAK KAYIT VE ARŞİV  ")
        self.tabs.add(self.tab_denetim, text="  ⚖️ DENETİM VE ONAY MERKEZİ  ")
        self.tabs.pack(fill="both", expand=True)
        
        self.setup_arsiv_ui()
        self.setup_denetim_ui()
        self.denetim_listele()

    def stil_olustur(self):
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TNotebook", background=RENK_BG, borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 11, "bold"), padding=[20, 10], background="#E2E8F0")
        style.map("TNotebook.Tab", background=[("selected", RENK_PRIMARY)], foreground=[("selected", "white")])
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=30, background="white", fieldbackground="white")
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"), background="#F8FAFC")

    def veritabani_hazirla(self):
        conn = sqlite3.connect("fatura_arsiv.db")
        conn.execute('''CREATE TABLE IF NOT EXISTS evraklar 
            (id INTEGER PRIMARY KEY AUTOINCREMENT, firma TEXT, evrak_no TEXT, evrak_cinsi TEXT, 
             tarih TEXT, birim TEXT, miktar REAL, urun_adi TEXT, dosya_adi TEXT, durum INTEGER DEFAULT 0)''')
        conn.commit()
        conn.close()

    def setup_arsiv_ui(self):
        # Sol Taraf: Kayıt Formu
        left_side = tk.Frame(self.tab_arsiv, bg=RENK_BG, width=450)
        left_side.pack(side="left", fill="y", padx=(0, 20), pady=10)
        
        form_card = tk.LabelFrame(left_side, text=" Yeni Evrak Girişi ", font=("Segoe UI", 11, "bold"), bg="white", fg=RENK_TEXT, padx=20, pady=20)
        form_card.pack(fill="x")

        fields = [("Firma Adı", "ent_firma"), ("Evrak Numarası", "ent_no")]
        for label, attr in fields:
            tk.Label(form_card, text=label, bg="white", font=("Segoe UI", 9)).pack(anchor="w", pady=(10, 0))
            entry = tk.Entry(form_card, font=("Segoe UI", 11), bg="#F8FAFC", bd=1, relief="solid")
            entry.pack(fill="x", pady=5)
            setattr(self, attr, entry)

        tk.Label(form_card, text="Evrak Türü", bg="white", font=("Segoe UI", 9)).pack(anchor="w")
        self.cmb_cins = ttk.Combobox(form_card, values=["İRSALİYE", "FATURA", "FİŞ", "MAKBUZ"], font=("Segoe UI", 10))
        self.cmb_cins.pack(fill="x", pady=5); self.cmb_cins.set("İRSALİYE")

        detail_card = tk.LabelFrame(left_side, text=" Kalem Detayları ", font=("Segoe UI", 11, "bold"), bg="white", fg=RENK_TEXT, padx=20, pady=20)
        detail_card.pack(fill="x", pady=20)

        self.ent_urun = tk.Entry(detail_card, font=("Segoe UI", 10), bg="#F8FAFC", bd=1); self.ent_urun.pack(fill="x", pady=2)
        tk.Label(detail_card, text="Ürün Adı / Miktar / Birim", bg="white", font=("Segoe UI", 8, "italic")).pack(anchor="w")
        
        mid_row = tk.Frame(detail_card, bg="white")
        mid_row.pack(fill="x")
        self.ent_miktar = tk.Entry(mid_row, font=("Segoe UI", 10), bg="#F8FAFC", bd=1, width=15); self.ent_miktar.pack(side="left", pady=5)
        self.cmb_birim = ttk.Combobox(mid_row, values=["ADET", "TON", "m2", "m3", "SEFER", "KG"], width=15); self.cmb_birim.pack(side="right", pady=5); self.cmb_birim.set("ADET")

        tk.Button(detail_card, text="+ KALEMİ LİSTEYE EKLE", bg=RENK_ACCENT, fg="white", font=("Segoe UI", 9, "bold"), command=self.kalem_ekle, cursor="hand2").pack(fill="x", pady=10)
        
        self.file_var = tk.StringVar(value="Henüz dosya seçilmedi...")
        tk.Label(left_side, textvariable=self.file_var, bg=RENK_BG, font=("Segoe UI", 8), fg="gray").pack()
        tk.Button(left_side, text="📂 PDF / GÖRSEL SEÇ", bg="#64748B", fg="white", font=("Segoe UI", 10, "bold"), command=self.dosya_sec, cursor="hand2").pack(fill="x", pady=5)
        tk.Button(left_side, text="✅ KAYDI TAMAMLA VE ARŞİVLE", bg=RENK_SUCCESS, fg="white", font=("Segoe UI", 12, "bold"), height=2, command=self.toplu_kaydet, cursor="hand2").pack(fill="x", pady=10)

        # Sağ Taraf: Liste ve Araçlar
        right_side = tk.Frame(self.tab_arsiv, bg=RENK_BG)
        right_side.pack(side="right", fill="both", expand=True)

        tool_bar = tk.Frame(right_side, bg=RENK_BG)
        tool_bar.pack(fill="x", pady=(0, 15))
        
        self.ent_search = tk.Entry(tool_bar, font=("Segoe UI", 11), bg="white", width=30); self.ent_search.pack(side="left", padx=5)
        self.ent_search.insert(0, "Arama yapın...")
        self.ent_search.bind("<KeyRelease>", lambda e: self.liste_guncelle())

        btn_style = {"font": ("Segoe UI", 9, "bold"), "fg": "white", "padx": 15, "cursor": "hand2"}
        tk.Button(tool_bar, text="👁️ PDF GÖRÜNTÜLE", bg="#F59E0B", **btn_style, command=self.pdf_ac).pack(side="left", padx=5)
        tk.Button(tool_bar, text="📄 GENEL RAPOR AL", bg="#8B5CF6", **btn_style, command=self.detayli_rapor_hazirla).pack(side="left", padx=5)
        tk.Button(tool_bar, text="🗑️ SEÇİLİ KAYDI SİL", bg=RENK_DANGER, **btn_style, command=self.kayit_sil).pack(side="right", padx=5)

        self.tree = ttk.Treeview(right_side, columns=("ID", "FİRMA", "NO", "CİNS", "ÜRÜN", "MİKTAR", "DURUM"), show="headings")
        for c in ("ID", "FİRMA", "NO", "CİNS", "ÜRÜN", "MİKTAR", "DURUM"): 
            self.tree.heading(c, text=c)
            self.tree.column(c, anchor="center")
        self.tree.pack(fill="both", expand=True)
        self.liste_guncelle()

    def setup_denetim_ui(self):
        main_d = tk.Frame(self.tab_denetim, bg=RENK_BG)
        main_d.pack(fill="both", expand=True, padx=20, pady=20)

        # Üst Arama Alanı
        search_panel = tk.Frame(main_d, bg="white", padx=20, pady=15, highlightbackground="#E2E8F0", highlightthickness=1)
        search_panel.pack(fill="x")
        tk.Label(search_panel, text="Eşleştirme İçin Filtrele:", bg="white", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.ent_denetim_ara = tk.Entry(search_panel, font=("Segoe UI", 11), width=40); self.ent_denetim_ara.pack(side="left", padx=20)
        tk.Button(search_panel, text="🔄 LİSTEYİ TAZELE", bg=RENK_PRIMARY, fg="white", font=("Segoe UI", 9, "bold"), command=self.denetim_listele).pack(side="left")

        # Tablolar
        tables_row = tk.Frame(main_d, bg=RENK_BG)
        tables_row.pack(fill="both", expand=True, pady=20)

        # Sol: İrsaliyeler
        self.f_irs = tk.LabelFrame(tables_row, text=" BEKLEYEN İRSALİYELER VE FİŞLER ", font=("Segoe UI", 10, "bold"), bg="white", padx=10, pady=10)
        self.f_irs.pack(side="left", fill="both", expand=True, padx=(0, 10))
        self.tree_irs = ttk.Treeview(self.f_irs, columns=("ID", "FİRMA", "NO", "ÜRÜN", "MİKTAR"), show="headings")
        for c in ("ID", "FİRMA", "NO", "ÜRÜN", "MİKTAR"): self.tree_irs.heading(c, text=c); self.tree_irs.column(c, width=80)
        self.tree_irs.pack(fill="both", expand=True)

        # Sağ: Faturalar
        self.f_fat = tk.LabelFrame(tables_row, text=" BEKLEYEN FATURALAR ", font=("Segoe UI", 10, "bold"), bg="white", padx=10, pady=10)
        self.f_fat.pack(side="right", fill="both", expand=True, padx=(10, 0))
        self.tree_fat = ttk.Treeview(self.f_fat, columns=("ID", "FİRMA", "NO", "ÜRÜN", "MİKTAR"), show="headings")
        for c in ("ID", "FİRMA", "NO", "ÜRÜN", "MİKTAR"): self.tree_fat.heading(c, text=c); self.tree_fat.column(c, width=80)
        self.tree_fat.pack(fill="both", expand=True)

        # Onay Butonu
        onay_card = tk.Frame(main_d, bg=RENK_PRIMARY, pady=15)
        onay_card.pack(fill="x")
        self.lbl_denetim_sonuc = tk.Label(onay_card, text="LÜTFEN SOLDAKİ İRSALİYELERİ VE SAĞDAKİ FATURAYI SEÇİNİZ", bg=RENK_PRIMARY, fg="white", font=("Segoe UI", 11, "bold"))
        self.lbl_denetim_sonuc.pack()
        tk.Button(onay_card, text="⚖️ DENETİMİ BAŞLAT VE ONAY RAPORU OLUŞTUR", bg="white", fg=RENK_PRIMARY, font=("Segoe UI", 12, "bold"), command=self.karsilastir_ve_raporla, cursor="hand2").pack(pady=10)

    # --- ARKA PLAN İŞLEMLERİ VE TÜRKÇE PDF DESTEĞİ ---

    def pdf_ac(self):
        secili = self.tree.selection()
        if not secili: return
        evrak_id = self.tree.item(secili[0])['values'][0]
        conn = sqlite3.connect("fatura_arsiv.db")
        res = conn.execute("SELECT dosya_adi FROM evraklar WHERE id=?", (evrak_id,)).fetchone()
        conn.close()
        if res and res[0] != "Dosya Seçilmedi":
            yol = os.path.join(self.arsiv_klasoru, res[0])
            if os.path.exists(yol): os.startfile(yol)
            else: messagebox.showerror("Hata", "Dosya bulunamadı!")

    def kayit_sil(self):
        secili = self.tree.selection()
        if not secili: return
        if messagebox.askyesno("Onay", "Bu işlem geri alınamaz. Silinsin mi?"):
            evrak_id = self.tree.item(secili[0])['values'][0]
            conn = sqlite3.connect("fatura_arsiv.db")
            conn.execute("DELETE FROM evraklar WHERE id=?", (evrak_id,))
            conn.commit(); conn.close(); self.liste_guncelle(); self.denetim_listele()

    def denetim_listele(self):
        for t in [self.tree_irs, self.tree_fat]:
            for i in t.get_children(): t.delete(i)
        search = f"%{self.ent_denetim_ara.get().upper()}%"
        conn = sqlite3.connect("fatura_arsiv.db")
        cursor_irs = conn.execute("SELECT id, firma, evrak_no, urun_adi, miktar FROM evraklar WHERE evrak_cinsi IN ('İRSALİYE','FİŞ','MAKBUZ') AND durum=0 AND (firma LIKE ? OR evrak_no LIKE ?)", (search, search))
        for r in cursor_irs: self.tree_irs.insert("", "end", values=r)
        cursor_fat = conn.execute("SELECT id, firma, evrak_no, urun_adi, miktar FROM evraklar WHERE evrak_cinsi='FATURA' AND durum=0 AND (firma LIKE ? OR evrak_no LIKE ?)", (search, search))
        for r in cursor_fat: self.tree_fat.insert("", "end", values=r)
        conn.close()

    def karsilastir_ve_raporla(self):
        irs_sec = self.tree_irs.selection(); fat_sec = self.tree_fat.selection()
        if not irs_sec or not fat_sec: return
        irs_data = [self.tree_irs.item(s)['values'] for s in irs_sec]
        fat_data = self.tree_fat.item(fat_sec[0])['values']
        toplam_irs = sum([float(i[4]) for i in irs_data]); fatura_mik = float(fat_data[4])
        
        if abs(toplam_irs - fatura_mik) < 0.01:
            if messagebox.askyesno("Onay", "Evraklar uyumlu. Onay raporu oluşturulsun mu?"):
                rapor_yolu = self.pdf_onay_raporu(fat_data[1], irs_data, fat_data, toplam_irs)
                ids = [i[0] for i in irs_data] + [fat_data[0]]
                conn = sqlite3.connect("fatura_arsiv.db")
                for i in ids: conn.execute("UPDATE evraklar SET durum=1 WHERE id=?", (i,))
                conn.commit(); conn.close(); self.denetim_listele(); self.liste_guncelle(); os.startfile(rapor_yolu)
        else:
            self.lbl_denetim_sonuc.config(text=f"MİKTAR UYUMSUZ! İrsaliye: {toplam_irs} | Fatura: {fatura_mik}", fg="red")

    def pdf_onay_raporu(self, firma, irs_listesi, fat_bilgi, miktar):
        # Türkçe karakterler için ReportLab Standart Font Kullanımı
        yol = os.path.join(self.rapor_klasoru, f"ONAY_{firma}_{datetime.datetime.now().strftime('%H%M%S')}.pdf")
        doc = SimpleDocTemplate(yol, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Türkçe Karakter Uyumlu Stil Ayarı
        tr_style = ParagraphStyle('TRStyle', parent=styles['Normal'], fontName='Helvetica', fontSize=10, encoding='utf-8')
        title_style = ParagraphStyle('TRTitle', parent=styles['Title'], fontName='Helvetica-Bold', fontSize=18)

        elements.append(Paragraph("ZER LOJISTIK DENETIM ONAYI", title_style))
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"<b>FIRMA:</b> {firma}", tr_style))
        elements.append(Paragraph(f"<b>TARIH:</b> {datetime.datetime.now().strftime('%d.%m.%Y')}", tr_style))
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("<font color='green'>DURUM: DENETIMDEN GECTI - ODEME HAZIR</font>", tr_style))
        elements.append(Spacer(1, 20))

        data = [["ID", "FIRMA", "NO", "URUN", "MIKTAR"]] + irs_listesi
        t = Table(data, colWidths=[40, 100, 100, 180, 70])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.5,colors.black),('FONTNAME',(0,0),(-1,-1),'Helvetica')]))
        elements.append(t)
        
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"<b>FATURA NO:</b> {fat_bilgi[2]}  |  <b>TOPLAM MIKTAR:</b> {miktar}", tr_style))
        
        doc.build(elements)
        return yol

    def detayli_rapor_hazirla(self):
        yol = os.path.join(self.rapor_klasoru, "GENEL_ARSIV_DOKUMU.pdf")
        doc = SimpleDocTemplate(yol, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        elements.append(Paragraph("GENEL ARSIV KAYITLARI", styles['Title']))
        
        data = [["ID", "FIRMA", "NO", "CINS", "URUN", "MIKTAR"]]
        conn = sqlite3.connect("fatura_arsiv.db")
        cursor = conn.execute("SELECT id, firma, evrak_no, evrak_cinsi, urun_adi, miktar FROM evraklar")
        for r in cursor: data.append(r)
        conn.close()
        
        t = Table(data, colWidths=[30, 80, 80, 70, 180, 60])
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightblue),('GRID',(0,0),(-1,-1),0.5,colors.black)]))
        elements.append(t)
        doc.build(elements)
        os.startfile(yol)

    def kalem_ekle(self):
        u, m, b = self.ent_urun.get(), self.ent_miktar.get(), self.cmb_birim.get()
        if u and m: self.gecici_kalemler.append((u.upper(), m, b)); self.ent_urun.delete(0, tk.END); self.ent_miktar.delete(0, tk.END)

    def dosya_sec(self):
        d = filedialog.askopenfilename()
        if d: self.file_var.set(os.path.basename(d)); self.temp_file_path = d

    def toplu_kaydet(self):
        firma, no, cins = self.ent_firma.get().upper(), self.ent_no.get().upper(), self.cmb_cins.get()
        if not self.gecici_kalemler: return
        tarih = datetime.datetime.now().strftime("%d.%m.%Y")
        dosya_adi = f"{no}_{os.path.basename(self.file_var.get())}" if self.file_var.get() != "Henüz dosya seçilmedi..." else "Dosya Seçilmedi"
        if hasattr(self, 'temp_file_path'): shutil.copy2(self.temp_file_path, os.path.join(self.arsiv_klasoru, dosya_adi))
        conn = sqlite3.connect("fatura_arsiv.db")
        for u, m, b in self.gecici_kalemler:
            conn.execute("INSERT INTO evraklar (firma, evrak_no, evrak_cinsi, tarih, birim, miktar, urun_adi, dosya_adi, durum) VALUES (?,?,?,?,?,?,?,?,0)",(firma, no, cins, tarih, b, float(m), u, dosya_adi))
        conn.commit(); conn.close(); self.gecici_kalemler = []; self.liste_guncelle(); self.denetim_listele(); self.file_var.set("Kayıt Başarılı!")

    def liste_guncelle(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        search = f"%{self.ent_search.get().upper()}%" if self.ent_search.get() != "Arama yapın..." else "%"
        conn = sqlite3.connect("fatura_arsiv.db")
        cursor = conn.execute("SELECT id, firma, evrak_no, evrak_cinsi, urun_adi, miktar, durum FROM evraklar WHERE firma LIKE ? OR evrak_no LIKE ? ORDER BY id DESC", (search, search))
        for r in cursor:
            d_metin = "BEKLEMEDE" if r[6] == 0 else "ONAYLANDI ✅"
            self.tree.insert("", "end", values=(r[0], r[1], r[2], r[3], r[4], r[5], d_metin))
        conn.close()

if __name__ == "__main__":
    root = tk.Tk(); app = FaturaSistemi(root); root.mainloop()