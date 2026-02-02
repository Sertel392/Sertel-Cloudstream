from cloudscraper import CloudScraper
import os, re

class CloudstreamMainUrlUpdater:
    def __init__(self, base_dir="."):
        self.base_dir = base_dir
        self.session = CloudScraper()

    # Repo içindeki eklenti klasörlerini bul
    @property
    def eklentiler(self):
        return [
            d for d in os.listdir(self.base_dir)
            if os.path.isdir(d)
            and not d.startswith(".")
            and os.path.exists(os.path.join(d, "build.gradle.kts"))
        ]

    # Klasör içinde tüm .kt dosyalarını bul
    def kt_dosyalarini_bul(self, klasor):
        kt_list = []
        for root, _, files in os.walk(klasor):
            for f in files:
                if f.endswith(".kt"):
                    kt_list.append(os.path.join(root, f))
        return kt_list

    # mainUrl değerini çek
    def mainurl_bul(self, kt_path):
        with open(kt_path, "r", encoding="utf-8") as f:
            icerik = f.read()
        eslesme = re.search(r'override\s+var\s+mainUrl\s*=\s*"([^"]+)"', icerik)
        return eslesme.group(1) if eslesme else None

    # mainUrl değiştir
    def mainurl_degistir(self, kt_path, eski, yeni):
        with open(kt_path, "r+", encoding="utf-8") as f:
            icerik = f.read()
            f.seek(0)
            f.write(icerik.replace(eski, yeni))
            f.truncate()

    # Versiyon artır
    def versiyon_artir(self, gradle_path):
        with open(gradle_path, "r+", encoding="utf-8") as f:
            icerik = f.read()
            eslesme = re.search(r'version\s*=\s*(\d+)', icerik)
            if not eslesme:
                return False

            eski = int(eslesme.group(1))
            yeni = eski + 1
            yeni_icerik = icerik.replace(f"version = {eski}", f"version = {yeni}")

            f.seek(0)
            f.write(yeni_icerik)
            f.truncate()
            return yeni

    # URL'nin yönlendirilmiş halini bul
    def final_url_bul(self, url):
        try:
            r = self.session.get(url, timeout=10, allow_redirects=True)
            final = r.url
            return final[:-1] if final.endswith("/") else final
        except:
            return None

    # Ana güncelleme işlemi
    def guncelle(self):
        print("\n🔍 Cloudstream MainUrl Güncelleyici Başladı\n")

        for eklenti in self.eklentiler:
            print(f"📦 Eklenti: {eklenti}")
            kt_dosyalar = self.kt_dosyalarini_bul(eklenti)

            degisti = False

            for kt in kt_dosyalar:
                mainurl = self.mainurl_bul(kt)
                if not mainurl:
                    continue

                print(f"   ├─ Kontrol: {mainurl}")
                yeni_url = self.final_url_bul(mainurl)

                if not yeni_url:
                    print("   │  ❌ Ulaşılamadı")
                    continue

                if mainurl == yeni_url:
                    print("   │  ✔ Güncel")
                    continue

                print(f"   │  🔄 Güncellendi → {yeni_url}")
                self.mainurl_degistir(kt, mainurl, yeni_url)
                degisti = True

            # Eğer değişiklik olduysa versiyon artır
            if degisti:
                yeni_ver = self.versiyon_artir(os.path.join(eklenti, "build.gradle.kts"))
                if yeni_ver:
                    print(f"   └─ 🚀 Versiyon artırıldı → {yeni_ver}")
            else:
                print("   └─ ✨ Değişiklik yok")

        print("\n✅ İşlem tamamlandı.\n")


if __name__ == "__main__":
    updater = CloudstreamMainUrlUpdater()
    updater.guncelle()
