
import tkinter as tk
from tkinter import messagebox
import subprocess
import sys
import os

class AnaSistem:
    def __init__(self, pencere):
        self.pencere = pencere
        self.pencere.title("Kibritçi İnşaat - Yönetim Paneli")
        self.pencere.geometry("450x600")
        self.pencere.configure(bg="#2c2c2c") # Mat koyu gri arka plan

        # Giriş Bilgileri
        self.username = "admin"
        self.password = "12345"

        self.giris_ekrani()

    def ekranı_temizle(self):
        for widget in self.pencere.winfo_children():
            widget.destroy()

    def giris_ekrani(self):
        self.ekranı_temizle()
        
        # Logo veya Başlık Alanı
        tk.Label(self.pencere, text="KİBRİTÇİ İNŞAAT", font=("Arial", 18, "bold"), 
                 bg="#2c2c2c", fg="#ffffff").pack(pady=(60, 40))

        # Giriş Kutuları
        tk.Label(self.pencere, text="Kullanıcı Adı:", bg="#2c2c2c", fg="#bbb").pack()
        self.ent_user = tk.Entry(self.pencere, font=("Arial", 12), width=25, bg="#3d3d3d", fg="white", insertbackground="white", relief="flat")
        self.ent_user.pack(pady=10)

        tk.Label(self.pencere, text="Şifre:", bg="#2c2c2c", fg="#bbb").pack()
        self.ent_pass = tk.Entry(self.pencere, font=("Arial", 12), width=25, bg="#3d3d3d", fg="white", insertbackground="white", relief="flat", show="*")
        self.ent_pass.pack(pady=10)

        # Giriş Butonu
        tk.Button(self.pencere, text="SİSTEME GİRİŞ", command=self.kontrol, 
                  bg="#4a4a4a", fg="white", font=("Arial", 10, "bold"), 
                  width=20, height=2, cursor="hand2", relief="flat").pack(pady=30)

    def kontrol(self):
        if self.ent_user.get() == self.username and self.ent_pass.get() == self.password:
            self.ana_menu()
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre yanlış!")

    def ana_menu(self):
        self.ekranı_temizle()
        
        tk.Label(self.pencere, text="ANA YÖNETİM PANELİ", font=("Arial", 14, "bold"), 
                 bg="#2c2c2c", fg="#ffffff").pack(pady=40)

            # Klasöründeki isimlere göre (Büyük/küçük harf duyarlıdır!)
        butonlar = [
            ("PERSONEL YÖNETİMİ GİT", "personel_yonetimi.py"), # Uzantı yoksa .py kısmını silin
            ("FATURA YÖNETİMİ GİT", "fatura_yonetimi.py"),
            ("İDARİ İŞLER YÖNETİMİ GİT", "idari_isler.py")
                   ]

        for metin, dosya in butonlar:
            tk.Button(
                self.pencere, 
                text=metin, 
                command=lambda d=dosya: self.dosya_calistir(d),
                bg="#3d3d3d", 
                fg="#e0e0e0", 
                font=("Arial", 10, "bold"),
                width=35,
                height=2,
                cursor="hand2",
                activebackground="#4a4a4a",
                relief="flat"
            ).pack(pady=10)

        tk.Button(self.pencere, text="ÇIKIŞ YAP", command=self.pencere.quit, 
                  bg="#7b1f1f", fg="white", relief="flat").pack(side="bottom", pady=30)

    def dosya_calistir(self, dosya_adi):
        import sys
        import os
        import subprocess

        # 1. Programın çalıştığı klasörü bul
        if getattr(sys, 'frozen', False):
            mevcut_dizin = os.path.dirname(sys.executable)
            # EXE olarak çalışırken Python yolunu belirle
            python_yolu = os.path.join(os.path.dirname(sys.executable), "_internal", "python.exe")
            # Eğer yukarıdaki özel yol yoksa sistemin varsayılan python'ını dene
            if not os.path.exists(python_yolu):
                python_yolu = "python"
        else:
            mevcut_dizin = os.path.dirname(os.path.abspath(__file__))
            python_yolu = sys.executable

        yol = os.path.join(mevcut_dizin, dosya_adi)

        if os.path.exists(yol):
            try:
                # Dosyayı arka planda, pencere çakışması olmadan başlat
                subprocess.Popen([python_yolu, yol], creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
            except Exception as e:
                # Eğer yukarıdaki yöntem başarısız olursa doğrudan işletim sistemiyle açmayı dene
                os.startfile(yol)
        else:
            messagebox.showwarning("Dosya Eksik", f"Konumda dosya yok: {yol}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnaSistem(root)
    root.mainloop()