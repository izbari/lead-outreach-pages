# Omkar Google Maps Scraper İncelemesi

Repo: https://github.com/omkarcloud/google-maps-scraper

İncelenen commit:

```text
9d2190e3363d1b6425bf1f94cd212e86d33d60c5
```

## Kısa Sonuç

Bu repo şu an doğrudan clone edilip local Python scraper olarak çalıştırılacak bir kod deposu değil. Depoda çalıştırılabilir scraper kaynak kodu yok; README, alan listesi, ekran görüntüleri ve indirilebilir desktop app/API yönlendirmeleri var.

Bu yüzden bizim pipeline'a `scraper_command` olarak doğrudan bağlanamaz.

## Kullanılabilir Bağlantı Şekli

En pratik kullanım:

1. Omkar desktop app veya API ile Google Maps datası alınır.
2. Sonuç CSV/JSON/Excel olarak export edilir.
3. Export dosyası bu repo altında `data/raw/omkar_export.csv` gibi bir yola koyulur.
4. Pipeline normalize eder:

```bash
python3 scripts/leadgen.py all --config config.json --input data/raw/omkar_export.csv
```

## Desteklenen Alanlar

Omkar dokümanında görünen alanlardan bizim pipeline için önemli olanlar:

- `KGMID`, `CID`, `PLACE_ID`, `DATA_ID`
- `NAME`
- `MAIN_CATEGORY`, `CATEGORIES`
- `WEBSITE`
- `PHONE`, `PHONE_INTERNATIONAL`
- `ADDRESS`, `DETAILED_ADDRESS`
- `LINK`
- `RATING`, `REVIEWS`
- `INSTAGRAM`
- olursa `EMAIL`, `EMAILS`, `RECOMMENDED_EMAIL`

Normalizer bu alanları okuyacak şekilde genişletildi.

## Operasyon Notları

- README'ye göre free plan aylık 200 search veriyor.
- Desktop app export tarafında CSV, JSON ve Excel desteklediğini söylüyor.
- Programatik kullanım için ayrı Google Maps Extractor API yönlendirmesi var.
- Enrichment/email tarafı ayrı Business Enrichment API'ye taşınmış.

## Bizim Karar

MVP için Omkar export'u veri kaynağı olarak kullanabiliriz. Tam otomatik, baştan sona local scrape istiyorsak bu repo doğru seçenek değil; Omkar API veya resmi Google Places API gerekir.
