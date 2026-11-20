# Son günlerin ortak iyileştirmeleri (13–16 Kas): her kanal oturumu okusun

Önce `C:\Users\meteh\Kanallar\SISTEM.md`'yi baştan yeniden oku. Oturum açıldığında yüklenen sürüm eskidir; dosya 16 Kas 12:40'ta güncellendi.

## Hız ve token
- **Bekleme:** Uzun işte tek arka plan bekçisi `bekci.py` kullan. Adım adım uyandıran Monitor ya da izleyici ajan kullanma; ana token okumasının ~%60'ı bu uyanmalardı (`beyin/ders/token-denetimi-1110`).
- **Çalıştır-izle-onar döngüsü:** Ana oturumda değil, `operator` alt ajanında koşar. Ana bağlama sonuç girsin, döküm değil.
- **Bekçi bash ile çağrılmaz:** WSL'e gidip çöker. Komutu python betiğine sar (`bekci-bash-c-wsl-1113`).

## Eş zamanlı görev ve doğru ajan
- **Sıra:** mekanik iş önce `gpt_isci.py tek|toplu` ile GPT işçisine gider. Birden çok bağımsız iş tek `gorevler.json` dosyasına yazılır, 8 paralel koşar. GPT limitteyse Flash, o da doluysa `CLAUDE_GEREK` döner.
- **CLAUDE_GEREK dönünce:**
  - **Haiku low:** tarama, sayma, log analizi, adımları yazılmış ölçüm. Görevi kontrol listesi gibi yaz: her varyant, gerçek girdi yolu, başarı şartı.
  - **Sonnet low:** varyant seçimi ya da hedef yorumu gereken iş (`haiku-isci-denemesi-1116`).
- **İşçinin PASS'i beyandır:** `kanit/` ham dosyasıyla sayıyı kontrol etmeden kabul etme.

## LLM: gemweb
- Flash yerine yerel Gemini web: `:8790`, `gemini-4-hydrogen` + low. Kullanım `Kanallar/gemweb_kullanim.md`.
- 16 Kas kanal sonuçları: `beyin/ders/gemweb-*-1116`.
- **Çerez yenilemesi** (`gemweb-cerez-donusu-1116`): Firefox çerezi yenileyince hesaplar topluca düşüyordu. Sunucuya düzeltme 13:1x'te girdi.
- **Görsel reddi:** Model bazı görsellerde HTTP 200 ile "Sorry I can't help with that image" dönebiliyor. Bunu ret say, grubu sayfa sayfa böl (`gemweb-asker-1116`).

## RAM (16 GB makine)
- **Ölçüm:** `beyin/ders/ram-denetim-1115`. Paralel film sayısını RAM belirler. RAM düşüşünün sebebi eşzamanlı ffmpeg kesimi ve chrome render.
- **SigLIP:** Bellek kırpma (`_trim_working_set`) bozuktu, ctypes handle'ı 32-bit kalıyordu. Düzeltildi; prod'da SigLIP idle (9769e83, `emptyworkingset-ctypes-1115`).
- **Testbench'te ölçülen, prod'a henüz girmemiş öneriler** (`testbench/ram_1115`, R7–R13): ffmpeg ayarları, kart render'ı için tek kalıcı tarayıcı, öğrenen MemoryGate. Prod'a geçmeleri kullanıcı onayı ve A/B gerektirir. Kendi başına prod'a alma.

## Kural
Bu dosyadaki değişikliklerin kanalına dokunan kısmını kendi `CLAUDE.md`'ne ya da işine uygula. Prod kodu değiştirme. Okuyunca ana oturuma tek satır "okudum + kanalıma etkisi şu" yaz.
