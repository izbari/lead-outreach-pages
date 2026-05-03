# GitHub Pages Deploy

Bu proje Antalya landing sayfalarını GitHub Pages'e ücretsiz deploy edecek şekilde hazırlandı.

## Ne Çalışır?

Workflow:

```text
.github/workflows/pages.yml
```

GitHub'a push edilince veya manuel `workflow_dispatch` ile:

1. `config.antalya.json` kullanır.
2. OpenStreetMap/Overpass üzerinden Antalya merkez datasını çeker.
3. Zincir marka filtresini uygular.
4. `dist-antalya/` üretir.
5. `dist-antalya/` klasörünü GitHub Pages'e deploy eder.

## Gerekli GitHub Ayarı

Repo GitHub'a push edildikten sonra:

1. GitHub repo sayfasını aç.
2. `Settings` -> `Pages`
3. `Build and deployment` altında `Source` değerini `GitHub Actions` yap.
4. `Actions` sekmesinden `Deploy Antalya Leads Pages` workflow'unu çalıştır.

## Beklenen URL

Repo adı örneğin `lead-outreach-pages` olursa:

```text
https://izbari.github.io/lead-outreach-pages/
```

Landing örnekleri:

```text
https://izbari.github.io/lead-outreach-pages/demo/butterfly-time/
```

Bu URL belli olduktan sonra local `config.antalya.json` içindeki `landing_base_url` alanı aynı URL ile güncellenmelidir.
