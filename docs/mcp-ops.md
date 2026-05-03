# MCP Operasyon Notları

Bu repo local pipeline üretir; Google Sheets ve Gmail aksiyonlarını Codex MCP araçları çalıştırır.

## Sheet

1. Pipeline çalışır:
   ```bash
   python3 scripts/leadgen.py all --config config.json
   ```
2. `output/leads.csv` Google Drive MCP ile native Google Sheets olarak import edilir.
3. Sheet'te `approved` kolonu sadece gönderime uygun lead'lerde `true` yapılır.
4. `send_status` takip değerleri:
   - `queued`: email var, draft üretilebilir.
   - `needs_email`: email yok, telefon/Instagram kanalı gerekir.
   - `drafted`: Gmail draft oluşturuldu.
   - `sent`: draft gönderildi.
   - `skipped`: manuel olarak pas geçildi.

## Gmail

Gmail MCP için güvenli kural:

0. Gmail connector gönderen hesap olarak `coding.izbaris@gmail.com` hesabına bağlı olmalı. MCP draft/send işlemlerinde `From` hesabını koddan seçmez; bağlı Gmail hesabı neyse onu kullanır.
1. Sadece `approved=true`, `email` dolu ve `send_status=queued` satırlar işlenir.
2. Önce Gmail draft oluşturulur.
3. Gönderim, kullanıcı onayı veya ayrıca belirlenen otomasyon kuralı ile yapılır.
4. Draft oluşturulduktan sonra Sheet'te ilgili satır `drafted` yapılır.

Bu yaklaşım otomasyonu durdurmaz; sadece hatalı kişiye, hatalı içerikle veya yüksek hacimde mail gönderme riskini azaltır.

Kişisel Gmail ile ilk hacim önerisi: günde 20-40 kişiselleştirilmiş mail. Yanıt oranı, bounce ve spam sinyali görülmeden hacim artırılmamalı.

## Deploy

Statik sayfalar `dist/` altına basılır.

```bash
python3 scripts/leadgen.py deploy-netlify --prod
```

Gerekli ortam değişkenleri:

```bash
NETLIFY_AUTH_TOKEN=...
NETLIFY_SITE_ID=...
LANDING_BASE_URL=https://siteadi.netlify.app
```

Deploy URL belli olduktan sonra pipeline tekrar base URL ile çalıştırılır:

```bash
LANDING_BASE_URL=https://siteadi.netlify.app python3 scripts/leadgen.py all --config config.json
```
