<div align="center">

# 🌌 SkyLyne Multi-Server VPN Manager

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python)
![Aiogram](https://img.shields.io/badge/Aiogram-v3.x-blueviolet?style=for-the-badge&logo=telegram)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Telegram üzerinden sınırsız sayıda VPS sunucusunu yönetin, OpenVPN kurun, kullanıcı satın ve otomatik takip edin.**

<p align="center">
  <a href="https://t.me/storm_inc">👨‍💻 Geliştirici İletişim</a> •
  <a href="https://t.me/DevolpersLab">📢 Kanal</a>
</p>

</div>

---

## 🚀 Özellikler

Bu bot, basit bir VPN yöneticisi değil, tam kapsamlı bir **SaaS (Yazılım Hizmeti)** panelidir.

* **☁️ Çoklu Sunucu (Multi-VPS):** Tek bot üzerinden sınırsız sayıda sunucuyu yönetin.
* **⚡ Otomatik Kurulum:** Tek tıkla boş bir VPS'e OpenVPN ve Gerekli Ajanları kurar.
* **👤 Kullanıcı Yönetimi:**
    * Kullanıcı oluşturma (.ovpn dosyasını otomatik gönderir).
    * **Trafik Limiti** belirleme (Örn: 10GB).
    * **Süre Limiti** belirleme (Örn: 30 Gün).
* **🛡️ Otomatik Koruma:** Süresi biten kullanıcıları sistemden **otomatik siler** (Auto-Revoke).
* **👀 Canlı İzleme:** Sunucuda o an kimlerin bağlı olduğunu (Online Users) gösterir.
* **📱 Modern Arayüz:** Klavye butonları ve şık HTML tasarımlı mesajlar.
* **💾 Veritabanı:** SQLite ile güvenli veri saklama.

---

## 🛠️ Kurulum Gereksinimleri

Botu kendi bilgisayarınızda veya bir sunucuda çalıştırmak için şunlara ihtiyacınız var:

* **Python 3.10** veya üzeri.
* **Yönetilecek VPS'ler:** Ubuntu 20.04/22.04 veya Debian 10/11 işletim sistemi.

---

## 📥 Adım Adım Kurulum

### 1. Projeyi İndirin
Terminali açın ve projeyi bilgisayarınıza çekin:
```bash
git clone [https://github.com/KULLANICI_ADIN/SkyLyne-VPN-Bot.git](https://github.com/KULLANICI_ADIN/SkyLyne-VPN-Bot.git)
cd SkyLyne-VPN-Bot
