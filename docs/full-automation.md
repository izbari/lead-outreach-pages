# Full Automation Plan

Hedef: Kullanıcı sadece Gmail Drafts içinde mesajları inceleyip gönderime karar verir. Veri çekme, landing üretme, Sheet güncelleme ve draft hazırlama otomasyon tarafından yapılır.

## Programatik Veri Kaynağı

Desktop export kullanılmayacak. Ücretsiz tam otomasyon için varsayılan kaynak:

- OpenStreetMap / Overpass API

Bu kaynak API key istemez ve `config.json` içinde `osm_overpass.enabled=true` olarak ayarlanmıştır.

Google Places API daha kaliteli veri verir ama ücretsiz kalma şartı için devre dışıdır.

Overpass public endpoint bağışlanan sunucular üzerinde çalışır; bu yüzden iş düşük frekansta ve küçük bölge bazlı koşturulmalıdır. Başlangıç için Kadıköy bbox + 3 kategori yeterlidir.

## Email Gerçeği

Google Places API email adresi vermez. Bu yüzden Gmail draft oluşması için şu iki durumdan biri gerekir:

- Lead datasında `email` alanı vardır.
- Ayrı bir enrichment servisi email üretir.

Email yoksa satır `needs_email` olur; sistem Gmail draft yaratmaz. Bu kasıtlıdır, çünkü yanlış veya tahmini adrese mail atmak hesabı riske sokar.

Enrichment için uygun kaynaklar:

- Omkar Business Enrichment API
- Apollo/Hunter/Clearbit benzeri servisler
- Website olan işletmelerde contact-page email scraper

Web sitesi olmayan işletmelerde email bulma oranı düşük olabilir; bu lead'ler genelde telefon/Instagram outreach kuyruğuna düşer.

## Deploy

Landing sayfalarının müşteriye gönderilebilir public link alması için bir statik deploy gerekir.

Netlify için gerekli secret'lar:

```bash
NETLIFY_AUTH_TOKEN=...
NETLIFY_SITE_ID=...
LANDING_BASE_URL=https://siteadi.netlify.app
```

Bu değerler yoksa site local `dist/` altında üretilir ama mail içinde public link olmaz.

## Scheduled Job Davranışı

Her çalışmada:

1. `config.json` okunur.
2. OpenStreetMap/Overpass ile bbox içindeki kategoriler taranır.
3. `data/raw/osm_overpass.csv` üretilir.
4. `output/leads.csv` normalize edilir.
5. `dist/` altında demo landing page'ler üretilir.
6. Netlify secrets varsa deploy edilir.
7. `output/email_queue.csv` hazırlanır.
8. Google Drive MCP ile Sheet güncellenir veya yeni rapor Sheet'i oluşturulur.
9. Gmail MCP ile sadece `email` dolu lead'ler için draft oluşturulur.
10. Draft oluşturulan satırlar `drafted`, email olmayanlar `needs_email` olarak takip edilir.

## Önerilen Sıklık

Başlangıç:

- Haftada 1 çalışma
- İlk 2 hafta günlük 20-40 draft üst sınırı

Sonra:

- 3 günde 1 çalışma
- Yanıt/spam/bounce durumu iyiyse hacim artırma

Kişisel Gmail ve ücretsiz public data endpoint ile agresif gönderim/tarama yapılmamalı.

## Ücretsiz Mod Komutu

```bash
python3 scripts/leadgen.py scrape-osm --config config.json
python3 scripts/leadgen.py all --config config.json
```

Tek komutta yeniden scrape ederek çalıştırmak için:

```bash
python3 scripts/leadgen.py all --config config.json --run-scraper
```
