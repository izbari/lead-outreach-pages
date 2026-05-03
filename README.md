# Local Business Lead Pipeline

Yerel işletmeleri tarayıp web sitesi olmayanları hedefleyen basit otomasyon iskeleti.

## Ne Yapar

- Scraper CSV/JSON çıktısını normalize eder.
- Web sitesi olmayan veya sadece Instagram'ı olan işletmeleri hedefler.
- Her hedef için statik demo landing page üretir.
- Google Sheets'e import edilecek `output/leads.csv` dosyasını çıkarır.
- Gmail draft otomasyonu için `output/email_queue.csv` ve mail gövdeleri üretir.
- Netlify/Vercel benzeri statik deploy'a uygun `dist/` klasörü hazırlar.

## Hızlı Başlangıç

```bash
cp config.example.json config.json
python3 scripts/leadgen.py all --config config.json
```

Ücretsiz tam otomasyon modu OpenStreetMap/Overpass kullanır:

```bash
python3 scripts/leadgen.py all --config config.json --run-scraper
```

Çıktılar:

```text
output/leads.csv
output/email_queue.csv
output/emails/*.txt
dist/index.html
dist/demo/*/index.html
```

## Scraper Bağlama

`config.json` içinde scraper komutunu ve ham veri yolunu ayarla:

```json
{
  "scraper_command": "python3 /path/to/scraper.py --query 'Kadikoy kafe' --out data/raw/leads.csv",
  "raw_input_path": "data/raw/leads.csv"
}
```

Sonra:

```bash
python3 scripts/leadgen.py all --config config.json --run-scraper
```

Desteklenen input formatları: `.csv`, `.json`.

Omkar Google Maps Scraper export'u için:

```bash
python3 scripts/leadgen.py all --config config.json --input data/raw/omkar_export.csv
```

İnceleme notları: [docs/scraper-omkar.md](docs/scraper-omkar.md)

## Beklenen Kolonlar

Scraper çıktısı birebir aynı kolon adlarını kullanmak zorunda değil. Şu alanlar alias'larla yakalanır:

```text
business_name, category, address, district, city, phone, email,
instagram, website, maps_url, rating, review_count, approved, notes
```

## Landing URL

Deploy URL belli olduğunda:

```bash
LANDING_BASE_URL=https://siteadi.netlify.app python3 scripts/leadgen.py all --config config.json
```

Bu, mail gövdelerine gerçek demo linklerini yazar.

## Netlify

```bash
cp .env.example .env
python3 scripts/leadgen.py deploy-netlify --prod
```

`NETLIFY_AUTH_TOKEN` ve `NETLIFY_SITE_ID` doluysa komut non-interactive çalışır.

## MCP Akışı

Detay: [docs/mcp-ops.md](docs/mcp-ops.md)
Full automation planı: [docs/full-automation.md](docs/full-automation.md)
GitHub Pages deploy notları: [docs/pages.md](docs/pages.md)

Kısa versiyon:

1. `output/leads.csv` Google Drive MCP ile native Google Sheets'e import edilir.
2. Gmail connector `coding.izbaris@gmail.com` hesabına bağlı olmalıdır.
3. Sheet'te `approved=true` yapılan ve email'i olan satırlar Gmail draft'a çevrilir.
4. Draftlar incelendikten sonra gönderilir veya otomasyonla gönderim açılır.

## Test

```bash
python3 -m unittest discover -s tests
```
