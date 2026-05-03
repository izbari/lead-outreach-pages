#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

NORMALIZED_COLUMNS = [
    "lead_id",
    "business_name",
    "category",
    "address",
    "district",
    "city",
    "phone",
    "email",
    "instagram",
    "website",
    "maps_url",
    "rating",
    "review_count",
    "website_status",
    "target",
    "approved",
    "landing_slug",
    "landing_url",
    "email_subject",
    "email_body_path",
    "send_status",
    "notes",
]

EMAIL_QUEUE_COLUMNS = [
    "lead_id",
    "business_name",
    "email",
    "phone",
    "instagram",
    "landing_url",
    "approved",
    "email_subject",
    "email_body_path",
    "send_status",
    "notes",
]

FIELD_ALIASES = {
    "lead_id": ["lead_id", "id", "osm_id", "kgmid", "cid", "place_id", "data_id"],
    "business_name": ["business_name", "name", "title", "isletme", "isletme_adi", "işletme", "işletme adı", "firma", "place_name", "displayName", "display_name"],
    "category": ["category", "kategori", "type", "types", "sector", "sektor", "sektör", "main_category", "main category", "primaryTypeDisplayName", "primary_type_display_name", "categories"],
    "address": ["address", "adres", "formatted_address", "formattedAddress", "vicinity", "detailed_address", "detailed address"],
    "district": ["district", "ilce", "ilçe", "town"],
    "city": ["city", "il", "province"],
    "phone": ["phone", "telefon", "phone_number", "formatted_phone_number", "nationalPhoneNumber", "national_phone_number", "international_phone_number", "internationalPhoneNumber", "phone_international"],
    "email": ["email", "emails", "mail", "e-mail", "eposta", "e_posta", "recommended_email", "recommended email", "best_email", "best email", "email_1"],
    "instagram": ["instagram", "ig", "instagram_url", "instagram_handle"],
    "website": ["website", "web", "site", "website_uri", "websiteUri", "websiteuri", "websiteUrl", "url"],
    "maps_url": ["maps_url", "google_maps_url", "googleMapsUri", "google_maps_uri", "google_maps", "maps", "place_url", "google_url", "gmap", "link"],
    "rating": ["rating", "puan", "stars"],
    "review_count": ["review_count", "reviews", "yorum", "yorum_sayisi", "user_ratings_total", "userRatingCount", "user_rating_count"],
    "approved": ["approved", "approve", "onay", "onayli", "send_approved"],
    "notes": ["notes", "note", "not", "durum"],
}

DEFAULT_EXCLUDED_CHAIN_NAMES = [
    "Starbucks",
    "Mado",
    "Caffe Nero",
    "Caffè Nero",
    "Kahve Dunyasi",
    "Kahve Dünyası",
    "Gloria Jean",
    "Espressolab",
    "Caribou",
    "Robert's Coffee",
    "Pelit",
    "Midpoint",
    "BigChefs",
    "Burger King",
    "McDonald's",
    "McDonalds",
    "KFC",
    "Popeyes",
    "Domino's",
    "Pizza Hut",
    "Baydoner",
    "Baydöner",
    "Simit Sarayi",
    "Simit Sarayı",
    "Shakespeare",
    "David People",
    "Extrablatt",
    "Big Yellow Taxi",
    "Tavuk Dunyasi",
    "Tavuk Dünyası",
    "Faruk Gulluoglu",
    "Faruk Güllüoğlu",
    "Komagene",
    "Ozsut",
    "Özsüt",
    "Yemen Kahvesi",
    "Osmanli Kahvecisi",
    "Osmanlı Kahvecisi",
    "Alacati Muhallebicisi",
    "Alaçatı Muhallebicisi",
    "Coffee Lab",
    "Mackbear",
    "Arabica",
    "Schiller",
    "Welldone",
]

DEFAULT_CONFIG = {
    "scraper_command": "",
    "raw_input_path": "data/sample_leads.csv",
    "normalized_output_path": "output/leads.csv",
    "email_queue_path": "output/email_queue.csv",
    "site_output_dir": "dist",
    "landing_base_url": "",
    "google_places": {
        "enabled": False,
        "output_path": "data/raw/google_places.csv",
        "queries": [],
        "language_code": "tr",
        "region_code": "TR",
        "max_results_per_query": 40,
    },
    "osm_overpass": {
        "enabled": False,
        "output_path": "data/raw/osm_overpass.csv",
        "bbox": {
            "south": 40.963,
            "west": 29.005,
            "north": 41.018,
            "east": 29.115,
        },
        "area_label": "Kadikoy",
        "area_city": "İstanbul",
        "categories": {
            "kafe": [["amenity", "cafe"]],
            "kuafor": [["shop", "hairdresser"]],
            "dis_klinigi": [["amenity", "dentist"], ["healthcare", "dentist"]],
        },
    },
    "campaign": {
        "sender_email": "",
        "sender_name": "Zafer",
        "sender_signature": "Zafer Baris",
        "service_name": "mini web sitesi",
        "cta_label": "Randevu / teklif al",
        "reply_line": "Uygunsa 10 dakikada üzerinden geçip işletmenize göre düzenleyebilirim.",
    },
    "filters": {
        "target_only": True,
        "min_rating": 0,
        "min_review_count": 0,
        "exclude_chain_names": DEFAULT_EXCLUDED_CHAIN_NAMES,
    },
}

GOOGLE_PLACES_COLUMNS = [
    "id",
    "displayName",
    "formattedAddress",
    "primaryTypeDisplayName",
    "types",
    "nationalPhoneNumber",
    "internationalPhoneNumber",
    "websiteUri",
    "googleMapsUri",
    "rating",
    "userRatingCount",
    "businessStatus",
]

OSM_COLUMNS = [
    "osm_id",
    "business_name",
    "category",
    "address",
    "district",
    "city",
    "phone",
    "email",
    "instagram",
    "website",
    "maps_url",
    "source_category",
    "source_tags",
]

CATEGORY_ASSETS = [
    {
        "keywords": ["kafe", "cafe", "kahve", "restaurant", "restoran", "lokanta", "pastane"],
        "hero_image": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=1800&q=82",
        "accent_color": "#0f766e",
        "accent_dark": "#115e59",
        "accent_soft": "#ecfdf5",
    },
    {
        "keywords": ["kuafor", "kuaför", "hair", "salon", "berber", "guzellik", "güzellik"],
        "hero_image": "https://images.unsplash.com/photo-1560066984-138dadb4c035?auto=format&fit=crop&w=1800&q=82",
        "accent_color": "#9f1239",
        "accent_dark": "#881337",
        "accent_soft": "#fff1f2",
    },
    {
        "keywords": ["dis", "diş", "dent", "klinik", "clinic", "saglik", "sağlık"],
        "hero_image": "https://images.unsplash.com/photo-1606811971618-4486d14f3f99?auto=format&fit=crop&w=1800&q=82",
        "accent_color": "#2563eb",
        "accent_dark": "#1d4ed8",
        "accent_soft": "#eff6ff",
    },
]

DEFAULT_ASSET = {
    "hero_image": "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1800&q=82",
    "accent_color": "#334155",
    "accent_dark": "#1f2937",
    "accent_soft": "#f1f5f9",
}


def canonical_key(value: str) -> str:
    value = value.strip().lower()
    table = str.maketrans({
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c",
        "İ": "i",
        "Ğ": "g",
        "Ü": "u",
        "Ş": "s",
        "Ö": "o",
        "Ç": "c",
    })
    value = value.translate(table)
    return re.sub(r"[^a-z0-9]+", "", value)


def transliterate(value: str) -> str:
    table = str.maketrans({
        "ı": "i",
        "ğ": "g",
        "ü": "u",
        "ş": "s",
        "ö": "o",
        "ç": "c",
        "İ": "i",
        "Ğ": "g",
        "Ü": "u",
        "Ş": "s",
        "Ö": "o",
        "Ç": "c",
    })
    return value.strip().lower().translate(table)


ALIAS_LOOKUP = {
    canonical_key(alias): field
    for field, aliases in FIELD_ALIASES.items()
    for alias in aliases
}


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    return candidate


def load_config(path: str | None) -> dict[str, Any]:
    config = DEFAULT_CONFIG
    if path:
        config_path = resolve_path(path)
        with config_path.open("r", encoding="utf-8") as handle:
            config = deep_merge(config, json.load(handle))
    env_base_url = os.getenv("LANDING_BASE_URL", "").strip()
    if env_base_url:
        config["landing_base_url"] = env_base_url
    return config


def load_dotenv(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def read_json(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return [dict(item) for item in payload]
    if isinstance(payload, dict):
        for key in ("results", "leads", "places", "data"):
            if isinstance(payload.get(key), list):
                return [dict(item) for item in payload[key]]
    raise ValueError(f"JSON input must be a list or contain results/leads/places/data: {path}")


def read_input(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return read_csv(path)
    if suffix == ".json":
        return read_json(path)
    raise ValueError(f"Unsupported input format: {path.suffix}. Use CSV or JSON.")


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
    ensure_parent(path)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def normalize_row_keys(row: dict[str, Any]) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for key, value in row.items():
        field = ALIAS_LOOKUP.get(canonical_key(str(key)))
        if not field:
            continue
        text = "" if value is None else str(value).strip()
        if text and field not in normalized:
            normalized[field] = text
    return normalized


def parse_bool(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return text in {"1", "true", "yes", "y", "evet", "onay", "approved", "send"}


def parse_number(value: Any) -> float:
    text = str(value or "").strip().replace(",", ".")
    if not text:
        return 0.0
    match = re.search(r"-?\d+(\.\d+)?", text)
    return float(match.group(0)) if match else 0.0


def clean_phone(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def phone_href(phone: str) -> str:
    digits = re.sub(r"\D+", "", phone)
    if not digits:
        return "#iletisim"
    if digits.startswith("0"):
        digits = "90" + digits[1:]
    return f"tel:+{digits}"


def looks_like_instagram(value: str) -> bool:
    text = value.strip().lower()
    return bool(text) and (
        "instagram.com" in text
        or text.startswith("@")
        or re.fullmatch(r"[a-z0-9._]{2,30}", text) is not None and "." not in text
    )


def normalize_instagram(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if "instagram.com" in text.lower():
        text = text.rstrip("/")
        handle = text.split("/")[-1]
        return f"@{handle}" if handle else text
    if not text.startswith("@"):
        return f"@{text}"
    return text


def instagram_url(value: str) -> str:
    handle = normalize_instagram(value)
    if not handle:
        return "#iletisim"
    return f"https://instagram.com/{handle.lstrip('@')}"


def normalize_website(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if looks_like_instagram(text):
        return ""
    if text.startswith(("http://", "https://")):
        return text
    if "." in text:
        return f"https://{text}"
    return text


def website_status(website: str, instagram: str) -> str:
    if website:
        return "has_website"
    if instagram:
        return "instagram_only"
    return "no_website"


def slugify(value: str) -> str:
    text = transliterate(value)
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:64] or "lead"


def stable_id(*parts: str) -> str:
    raw = "|".join(part.strip().lower() for part in parts if part)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12]


def build_landing_url(base_url: str, slug: str) -> str:
    if not base_url:
        return f"/demo/{slug}/"
    return f"{base_url.rstrip('/')}/demo/{slug}/"


def is_excluded_chain(name: str, config: dict[str, Any]) -> bool:
    filters = config.get("filters", {})
    excluded = filters.get("exclude_chain_names", DEFAULT_EXCLUDED_CHAIN_NAMES)
    normalized_name = canonical_key(name)
    return any(canonical_key(str(pattern)) in normalized_name for pattern in excluded if str(pattern).strip())


def normalize_rows(raw_rows: list[dict[str, Any]], config: dict[str, Any]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    seen_slugs: dict[str, int] = {}
    base_url = str(config.get("landing_base_url", "")).strip()

    for raw in raw_rows:
        source = normalize_row_keys(raw)
        name = source.get("business_name", "").strip()
        if not name:
            continue
        if is_excluded_chain(name, config):
            continue

        raw_website = source.get("website", "")
        raw_instagram = source.get("instagram", "")
        if raw_website and looks_like_instagram(raw_website) and not raw_instagram:
            raw_instagram = raw_website
            raw_website = ""

        instagram = normalize_instagram(raw_instagram)
        website = normalize_website(raw_website)
        category = source.get("category", "").strip() or "İşletme"
        address = source.get("address", "").strip()
        district = source.get("district", "").strip()
        city = source.get("city", "").strip() or "İstanbul"
        phone = clean_phone(source.get("phone", ""))
        email = source.get("email", "").strip()
        maps_url = source.get("maps_url", "").strip() or "#"
        rating = source.get("rating", "").strip()
        review_count = source.get("review_count", "").strip()
        status = website_status(website, instagram)
        target = status in {"no_website", "instagram_only"}
        base_slug = slugify(name)
        count = seen_slugs.get(base_slug, 0)
        seen_slugs[base_slug] = count + 1
        slug = base_slug if count == 0 else f"{base_slug}-{count + 1}"
        landing_url = build_landing_url(base_url, slug)

        row = {
            "lead_id": source.get("lead_id", "").strip() or stable_id(name, address, phone),
            "business_name": name,
            "category": category,
            "address": address,
            "district": district,
            "city": city,
            "phone": phone,
            "email": email,
            "instagram": instagram,
            "website": website,
            "maps_url": maps_url,
            "rating": rating,
            "review_count": review_count,
            "website_status": status,
            "target": "true" if target else "false",
            "approved": "true" if parse_bool(source.get("approved", "")) else "false",
            "landing_slug": slug,
            "landing_url": landing_url,
            "email_subject": "",
            "email_body_path": "",
            "send_status": "",
            "notes": source.get("notes", ""),
        }
        rows.append(row)
    return rows


def passes_filters(row: dict[str, str], config: dict[str, Any]) -> bool:
    filters = config.get("filters", {})
    if filters.get("target_only", True) and row.get("target") != "true":
        return False
    if parse_number(row.get("rating")) < float(filters.get("min_rating", 0) or 0):
        return False
    if parse_number(row.get("review_count")) < float(filters.get("min_review_count", 0) or 0):
        return False
    return True


def choose_asset(category: str) -> dict[str, str]:
    text = canonical_key(category)
    for asset in CATEGORY_ASSETS:
        if any(canonical_key(keyword) in text for keyword in asset["keywords"]):
            return {key: str(value) for key, value in asset.items() if key != "keywords"}
    return DEFAULT_ASSET


def render_template(path: Path, context: dict[str, str]) -> str:
    template = path.read_text(encoding="utf-8")
    def replace(match: re.Match[str]) -> str:
        return context.get(match.group(1), "")
    return re.sub(r"\{\{([a-zA-Z0-9_]+)\}\}", replace, template)


def html_context(row: dict[str, str], config: dict[str, Any]) -> dict[str, str]:
    campaign = config.get("campaign", {})
    asset = choose_asset(row.get("category", ""))
    name = row.get("business_name", "")
    category = row.get("category", "İşletme")
    address = row.get("address", "") or f"{row.get('district', '')}, {row.get('city', '')}".strip(", ")
    phone = row.get("phone", "") or "Telefon bilgisi eklenecek"
    instagram = row.get("instagram", "") or "Instagram bilgisi eklenecek"

    context = {
        "business_name": html.escape(name),
        "category": html.escape(category),
        "address": html.escape(address),
        "district": html.escape(row.get("district", "") or "Konum"),
        "city": html.escape(row.get("city", "") or "İstanbul"),
        "phone": html.escape(phone),
        "instagram": html.escape(instagram),
        "maps_url": html.escape(row.get("maps_url", "#") or "#"),
        "instagram_url": html.escape(instagram_url(row.get("instagram", ""))),
        "phone_href": html.escape(phone_href(row.get("phone", ""))),
        "cta_label": html.escape(str(campaign.get("cta_label", "İletişime geç"))),
        "hero_text": html.escape(f"{category} için hızlı ulaşılabilir, mobil uyumlu ve sade bir web deneyimi."),
        "intro_text": html.escape(f"{name}, çevrede arama yapan müşterilerin işletmeye daha hızlı ulaşmasını sağlayan net ve güven veren bir sayfayla öne çıkabilir."),
        "contact_text": html.escape("Telefon, harita ve sosyal kanal bağlantıları tek yerde toplandığı için müşteriler beklemeden aksiyon alabilir."),
        **asset,
    }
    return context


def generate_sites(rows: list[dict[str, str]], dist_dir: Path, config: dict[str, Any]) -> int:
    dist_dir.mkdir(parents=True, exist_ok=True)
    demo_dir = dist_dir / "demo"
    if demo_dir.exists():
        shutil.rmtree(demo_dir)
    for artifact in ("index.html", "robots.txt", ".nojekyll"):
        artifact_path = dist_dir / artifact
        if artifact_path.exists():
            artifact_path.unlink()
    template_dir = ROOT / "templates"
    landing_template = template_dir / "landing.html"
    index_template = template_dir / "index.html"
    rendered = 0
    index_rows = []

    for row in rows:
        if row.get("target") != "true":
            continue
        page_dir = dist_dir / "demo" / row["landing_slug"]
        page_dir.mkdir(parents=True, exist_ok=True)
        page_html = render_template(landing_template, html_context(row, config))
        (page_dir / "index.html").write_text(page_html, encoding="utf-8")
        rendered += 1
        index_rows.append(
            "<tr>"
            f"<td>{html.escape(row.get('business_name', ''))}</td>"
            f"<td>{html.escape(row.get('category', ''))}</td>"
            f"<td>{html.escape(row.get('website_status', ''))}</td>"
            f"<td><a href=\"demo/{html.escape(row['landing_slug'])}/\">Aç</a></td>"
            "</tr>"
        )

    index_html = render_template(index_template, {"rows": "\n".join(index_rows)})
    (dist_dir / "index.html").write_text(index_html, encoding="utf-8")
    (dist_dir / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    (dist_dir / ".nojekyll").write_text("", encoding="utf-8")
    return rendered


def compose_email(row: dict[str, str], config: dict[str, Any]) -> tuple[str, str]:
    campaign = config.get("campaign", {})
    sender_name = campaign.get("sender_name", "Zafer")
    signature = campaign.get("sender_signature", sender_name)
    service_name = campaign.get("service_name", "mini web sitesi")
    reply_line = campaign.get("reply_line", "Uygunsa kısa bir görüşmeyle düzenleyebilirim.")
    subject = f"{row['business_name']} için kısa bir web sitesi örneği hazırladım"
    landing_url = row.get("landing_url") or "Demo linki deploy sonrası eklenecek."
    body = f"""Merhaba,

{row['business_name']} için küçük bir {service_name} örneği hazırladım:
{landing_url}

Google'da arayan müşterilerin telefon, harita ve sosyal kanallara daha hızlı ulaşması için tek sayfalık sade bir yapı düşündüm.

{reply_line}

İyi günler,
{signature}
"""
    return subject, body


def compose_email_queue(rows: list[dict[str, str]], queue_path: Path, config: dict[str, Any]) -> int:
    email_dir = queue_path.parent / "emails"
    email_dir.mkdir(parents=True, exist_ok=True)
    queue_rows: list[dict[str, str]] = []
    count = 0

    for row in rows:
        if not passes_filters(row, config):
            continue
        subject, body = compose_email(row, config)
        body_path = email_dir / f"{row['landing_slug']}.txt"
        body_path.write_text(body, encoding="utf-8")
        updated = dict(row)
        updated["email_subject"] = subject
        updated["email_body_path"] = str(body_path.relative_to(ROOT))
        updated["send_status"] = updated.get("send_status") or ("queued" if updated.get("email") else "needs_email")
        queue_rows.append({column: updated.get(column, "") for column in EMAIL_QUEUE_COLUMNS})
        row.update({
            "email_subject": subject,
            "email_body_path": str(body_path.relative_to(ROOT)),
            "send_status": updated["send_status"],
        })
        count += 1

    write_csv(queue_path, queue_rows, EMAIL_QUEUE_COLUMNS)
    return count


def run_scraper(config: dict[str, Any]) -> None:
    osm_overpass = config.get("osm_overpass", {})
    if osm_overpass.get("enabled"):
        scrape_osm_overpass(config)
        return
    google_places = config.get("google_places", {})
    if google_places.get("enabled"):
        scrape_google_places(config)
        return
    command = str(config.get("scraper_command", "")).strip()
    if not command:
        print("No scraper_command configured. Skipping scraper run.")
        return
    print(f"Running scraper: {command}")
    subprocess.run(command, cwd=ROOT, shell=True, check=True)


def overpass_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def osm_category_from_tags(tags: dict[str, Any], fallback: str) -> str:
    for key in ("amenity", "shop", "healthcare", "craft", "tourism"):
        if tags.get(key):
            return str(tags[key]).replace("_", " ").title()
    return fallback.replace("_", " ").title()


def osm_first_tag(tags: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = str(tags.get(key) or "").strip()
        if value:
            return value
    return ""


def osm_address(tags: dict[str, Any]) -> str:
    parts = [
        tags.get("addr:street"),
        tags.get("addr:housenumber"),
        tags.get("addr:neighbourhood") or tags.get("addr:suburb"),
        tags.get("addr:district"),
        tags.get("addr:city"),
    ]
    return " ".join(str(part).strip() for part in parts if str(part or "").strip())


def osm_maps_url(element: dict[str, Any]) -> str:
    element_type = element.get("type", "node")
    osm_id = element.get("id", "")
    lat = element.get("lat") or element.get("center", {}).get("lat")
    lon = element.get("lon") or element.get("center", {}).get("lon")
    if lat and lon:
        return f"https://www.openstreetmap.org/{element_type}/{osm_id}#map=19/{lat}/{lon}"
    return f"https://www.openstreetmap.org/{element_type}/{osm_id}"


def flatten_osm_element(element: dict[str, Any], source_category: str, default_city: str) -> dict[str, str]:
    tags = element.get("tags") or {}
    return {
        "osm_id": f"{element.get('type', 'node')}/{element.get('id')}",
        "business_name": osm_first_tag(tags, ["name", "brand", "operator"]),
        "category": osm_category_from_tags(tags, source_category),
        "address": osm_address(tags),
        "district": osm_first_tag(tags, ["addr:district", "addr:suburb", "addr:neighbourhood"]),
        "city": osm_first_tag(tags, ["addr:city"]) or default_city,
        "phone": osm_first_tag(tags, ["phone", "contact:phone", "mobile", "contact:mobile"]),
        "email": osm_first_tag(tags, ["email", "contact:email"]),
        "instagram": osm_first_tag(tags, ["contact:instagram", "instagram"]),
        "website": osm_first_tag(tags, ["website", "contact:website", "url", "contact:url"]),
        "maps_url": osm_maps_url(element),
        "source_category": source_category,
        "source_tags": ";".join(
            f"{key}={value}"
            for key, value in sorted(tags.items())
            if key in {"amenity", "shop", "healthcare", "craft", "tourism"}
        ),
    }


def overpass_request(query: str) -> dict[str, Any]:
    endpoint = "https://overpass-api.de/api/interpreter"
    request = urllib.request.Request(
        endpoint,
        data=query.encode("utf-8"),
        headers={
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "User-Agent": "lead-outreach-pipeline/0.1 (coding.izbaris@gmail.com)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Overpass API error {exc.code}: {detail}") from exc


def scrape_osm_overpass(config: dict[str, Any]) -> None:
    settings = config.get("osm_overpass", {})
    output_path = resolve_path(settings.get("output_path") or config.get("raw_input_path") or "data/raw/osm_overpass.csv")
    bbox = settings.get("bbox") or {}
    if not all(key in bbox for key in ("south", "west", "north", "east")):
        raise RuntimeError("osm_overpass.bbox must include south, west, north, and east.")

    south = float(bbox["south"])
    west = float(bbox["west"])
    north = float(bbox["north"])
    east = float(bbox["east"])
    categories = settings.get("categories") or {}
    default_city = str(settings.get("area_city") or "İstanbul")
    if not categories:
        raise RuntimeError("osm_overpass.categories is empty.")

    rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for category, filters in categories.items():
        clauses = []
        for item in filters:
            if not isinstance(item, list) or len(item) != 2:
                raise RuntimeError(f"Invalid OSM filter for {category}: {item}")
            key, value = str(item[0]), str(item[1])
            clauses.extend(
                [
                    f'node["{overpass_escape(key)}"="{overpass_escape(value)}"]({south},{west},{north},{east});',
                    f'way["{overpass_escape(key)}"="{overpass_escape(value)}"]({south},{west},{north},{east});',
                    f'relation["{overpass_escape(key)}"="{overpass_escape(value)}"]({south},{west},{north},{east});',
                ]
            )
        query = "[out:json][timeout:45];\n(\n" + "\n".join(clauses) + "\n);\nout center tags;"
        result = overpass_request(query)
        for element in result.get("elements", []):
            element_id = f"{element.get('type')}/{element.get('id')}"
            if element_id in seen_ids:
                continue
            row = flatten_osm_element(element, str(category), default_city)
            if not row.get("business_name"):
                continue
            seen_ids.add(element_id)
            rows.append(row)
        time.sleep(1)

    write_csv(output_path, rows, OSM_COLUMNS)
    print(f"Scraped {len(rows)} OSM rows -> {output_path}")


def extract_localized_text(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("text") or value.get("displayName") or "").strip()
    return str(value or "").strip()


def flatten_google_place(place: dict[str, Any]) -> dict[str, str]:
    display_name = extract_localized_text(place.get("displayName"))
    primary_type = extract_localized_text(place.get("primaryTypeDisplayName"))
    return {
        "id": str(place.get("id") or place.get("name") or "").strip(),
        "displayName": display_name,
        "formattedAddress": str(place.get("formattedAddress") or "").strip(),
        "primaryTypeDisplayName": primary_type,
        "types": ", ".join(str(item) for item in place.get("types", []) if item),
        "nationalPhoneNumber": str(place.get("nationalPhoneNumber") or "").strip(),
        "internationalPhoneNumber": str(place.get("internationalPhoneNumber") or "").strip(),
        "websiteUri": str(place.get("websiteUri") or "").strip(),
        "googleMapsUri": str(place.get("googleMapsUri") or "").strip(),
        "rating": str(place.get("rating") or "").strip(),
        "userRatingCount": str(place.get("userRatingCount") or "").strip(),
        "businessStatus": str(place.get("businessStatus") or "").strip(),
    }


def google_places_request(payload: dict[str, Any], api_key: str) -> dict[str, Any]:
    endpoint = "https://places.googleapis.com/v1/places:searchText"
    body = json.dumps(payload).encode("utf-8")
    field_mask = ",".join(
        [
            "places.id",
            "places.displayName",
            "places.formattedAddress",
            "places.primaryTypeDisplayName",
            "places.types",
            "places.nationalPhoneNumber",
            "places.internationalPhoneNumber",
            "places.websiteUri",
            "places.googleMapsUri",
            "places.rating",
            "places.userRatingCount",
            "places.businessStatus",
            "nextPageToken",
        ]
    )
    request = urllib.request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": field_mask,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Google Places API error {exc.code}: {detail}") from exc


def scrape_google_places(config: dict[str, Any]) -> None:
    load_dotenv()
    settings = config.get("google_places", {})
    api_key = os.getenv("GOOGLE_PLACES_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GOOGLE_PLACES_API_KEY is missing. Add it to .env before running automation.")

    queries = [str(query).strip() for query in settings.get("queries", []) if str(query).strip()]
    if not queries:
        raise RuntimeError("google_places.queries is empty.")

    output_path = resolve_path(settings.get("output_path") or config.get("raw_input_path") or "data/raw/google_places.csv")
    language_code = str(settings.get("language_code") or "tr")
    region_code = str(settings.get("region_code") or "TR")
    max_results = max(1, int(settings.get("max_results_per_query") or 40))
    page_size = min(20, max_results)

    rows: list[dict[str, str]] = []
    seen_ids: set[str] = set()

    for query in queries:
        fetched = 0
        page_token = ""
        while fetched < max_results:
            payload: dict[str, Any] = {
                "textQuery": query,
                "languageCode": language_code,
                "regionCode": region_code,
                "pageSize": min(page_size, max_results - fetched),
            }
            if page_token:
                payload["pageToken"] = page_token

            result = google_places_request(payload, api_key)
            places = result.get("places", [])
            if not places:
                break

            for place in places:
                row = flatten_google_place(place)
                place_id = row.get("id") or stable_id(row.get("displayName", ""), row.get("formattedAddress", ""))
                if place_id in seen_ids:
                    continue
                seen_ids.add(place_id)
                row["sourceQuery"] = query
                rows.append(row)
                fetched += 1
                if fetched >= max_results:
                    break

            page_token = str(result.get("nextPageToken") or "")
            if not page_token:
                break
            time.sleep(2)

    ensure_parent(output_path)
    columns = GOOGLE_PLACES_COLUMNS + ["sourceQuery"]
    write_csv(output_path, rows, columns)
    print(f"Scraped {len(rows)} Google Places rows -> {output_path}")


def deploy_netlify(dist_dir: Path, prod: bool) -> None:
    if not dist_dir.exists():
        raise FileNotFoundError(f"Dist directory not found: {dist_dir}")
    executable = shutil.which("netlify")
    command: list[str]
    if executable:
        command = [executable, "deploy", "--dir", str(dist_dir)]
    else:
        command = ["npx", "--yes", "netlify-cli", "deploy", "--dir", str(dist_dir)]
    if prod:
        command.append("--prod")
    site_id = os.getenv("NETLIFY_SITE_ID", "").strip()
    if site_id:
        command.extend(["--site", site_id])
    if os.getenv("NETLIFY_AUTH_TOKEN", "").strip():
        command.extend(["--auth", os.getenv("NETLIFY_AUTH_TOKEN", "").strip()])
    print(" ".join(command))
    subprocess.run(command, cwd=ROOT, check=True)


def command_normalize(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    input_path = resolve_path(args.input or config["raw_input_path"])
    output_path = resolve_path(args.output or config["normalized_output_path"])
    raw_rows = read_input(input_path)
    rows = normalize_rows(raw_rows, config)
    write_csv(output_path, rows, NORMALIZED_COLUMNS)
    print(f"Normalized {len(rows)} leads -> {output_path}")


def command_generate_sites(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    if args.base_url:
        config["landing_base_url"] = args.base_url
    input_path = resolve_path(args.input or config["normalized_output_path"])
    dist_dir = resolve_path(args.dist or config["site_output_dir"])
    rows = read_csv(input_path)
    if config.get("landing_base_url"):
        for row in rows:
            row["landing_url"] = build_landing_url(config["landing_base_url"], row["landing_slug"])
        write_csv(input_path, rows, NORMALIZED_COLUMNS)
    count = generate_sites(rows, dist_dir, config)
    print(f"Generated {count} demo pages -> {dist_dir}")


def command_compose_emails(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    input_path = resolve_path(args.input or config["normalized_output_path"])
    queue_path = resolve_path(args.queue or config["email_queue_path"])
    rows = read_csv(input_path)
    count = compose_email_queue(rows, queue_path, config)
    write_csv(input_path, rows, NORMALIZED_COLUMNS)
    print(f"Prepared {count} outreach rows -> {queue_path}")


def command_all(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    if args.run_scraper:
        run_scraper(config)
    input_path = resolve_path(args.input or config["raw_input_path"])
    output_path = resolve_path(args.output or config["normalized_output_path"])
    queue_path = resolve_path(args.queue or config["email_queue_path"])
    dist_dir = resolve_path(args.dist or config["site_output_dir"])
    if args.base_url:
        config["landing_base_url"] = args.base_url
    raw_rows = read_input(input_path)
    rows = normalize_rows(raw_rows, config)
    write_csv(output_path, rows, NORMALIZED_COLUMNS)
    pages = generate_sites(rows, dist_dir, config)
    queued = compose_email_queue(rows, queue_path, config)
    write_csv(output_path, rows, NORMALIZED_COLUMNS)
    print(f"Normalized {len(rows)} leads -> {output_path}")
    print(f"Generated {pages} demo pages -> {dist_dir}")
    print(f"Prepared {queued} outreach rows -> {queue_path}")


def command_deploy_netlify(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    dist_dir = resolve_path(args.dist or config["site_output_dir"])
    deploy_netlify(dist_dir, args.prod)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Lead generation pipeline for local business website outreach.")
    parser.add_argument("--config", default="config.example.json", help="Path to config JSON.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    normalize = subparsers.add_parser("normalize", help="Normalize scraper CSV/JSON into output/leads.csv.")
    normalize.add_argument("--config", default=argparse.SUPPRESS)
    normalize.add_argument("--input")
    normalize.add_argument("--output")
    normalize.set_defaults(func=command_normalize)

    sites = subparsers.add_parser("generate-sites", help="Generate static landing pages.")
    sites.add_argument("--config", default=argparse.SUPPRESS)
    sites.add_argument("--input")
    sites.add_argument("--dist")
    sites.add_argument("--base-url")
    sites.set_defaults(func=command_generate_sites)

    emails = subparsers.add_parser("compose-emails", help="Create email queue and body files.")
    emails.add_argument("--config", default=argparse.SUPPRESS)
    emails.add_argument("--input")
    emails.add_argument("--queue")
    emails.set_defaults(func=command_compose_emails)

    all_cmd = subparsers.add_parser("all", help="Run normalize, site generation, and email queue.")
    all_cmd.add_argument("--config", default=argparse.SUPPRESS)
    all_cmd.add_argument("--run-scraper", action="store_true")
    all_cmd.add_argument("--input")
    all_cmd.add_argument("--output")
    all_cmd.add_argument("--queue")
    all_cmd.add_argument("--dist")
    all_cmd.add_argument("--base-url")
    all_cmd.set_defaults(func=command_all)

    deploy = subparsers.add_parser("deploy-netlify", help="Deploy dist to Netlify via Netlify CLI.")
    deploy.add_argument("--config", default=argparse.SUPPRESS)
    deploy.add_argument("--dist")
    deploy.add_argument("--prod", action="store_true")
    deploy.set_defaults(func=command_deploy_netlify)

    scrape = subparsers.add_parser("scrape-google-places", help="Fetch Google Places API data into raw CSV.")
    scrape.add_argument("--config", default=argparse.SUPPRESS)
    scrape.set_defaults(func=command_scrape_google_places)

    scrape_osm = subparsers.add_parser("scrape-osm", help="Fetch free OpenStreetMap/Overpass data into raw CSV.")
    scrape_osm.add_argument("--config", default=argparse.SUPPRESS)
    scrape_osm.set_defaults(func=command_scrape_osm)
    return parser


def command_scrape_google_places(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    scrape_google_places(config)


def command_scrape_osm(args: argparse.Namespace) -> None:
    config = load_config(args.config)
    scrape_osm_overpass(config)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        args.func(args)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
