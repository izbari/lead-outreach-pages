from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("leadgen", ROOT / "scripts" / "leadgen.py")
leadgen = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(leadgen)


class LeadgenTests(unittest.TestCase):
    def test_slugify_handles_turkish_and_spaces(self) -> None:
        self.assertEqual(leadgen.slugify("Naive Floral Café"), "naive-floral-caf")
        self.assertEqual(leadgen.slugify("Atikhair Kuaför"), "atikhair-kuafor")

    def test_normalize_marks_instagram_only_as_target(self) -> None:
        rows = leadgen.normalize_rows(
            [
                {
                    "name": "Polika Kafe",
                    "category": "Kafe",
                    "phone": "0216 405 27 48",
                    "website": "@polikakafe",
                    "rating": "4.6",
                    "reviews": "128",
                }
            ],
            leadgen.DEFAULT_CONFIG,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["instagram"], "@polikakafe")
        self.assertEqual(rows[0]["website"], "")
        self.assertEqual(rows[0]["website_status"], "instagram_only")
        self.assertEqual(rows[0]["target"], "true")

    def test_normalize_accepts_omkar_export_fields(self) -> None:
        rows = leadgen.normalize_rows(
            [
                {
                    "KGMID": "/g/11sample",
                    "NAME": "Moda Test",
                    "MAIN_CATEGORY": "Kafe",
                    "ADDRESS": "Kadikoy Istanbul",
                    "PHONE_INTERNATIONAL": "+90 216 000 00 00",
                    "LINK": "https://maps.google.com/?cid=sample",
                    "REVIEWS": "120",
                    "INSTAGRAM": "@modatest",
                }
            ],
            leadgen.DEFAULT_CONFIG,
        )

        self.assertEqual(rows[0]["lead_id"], "/g/11sample")
        self.assertEqual(rows[0]["business_name"], "Moda Test")
        self.assertEqual(rows[0]["category"], "Kafe")
        self.assertEqual(rows[0]["maps_url"], "https://maps.google.com/?cid=sample")
        self.assertEqual(rows[0]["review_count"], "120")
        self.assertEqual(rows[0]["target"], "true")

    def test_normalize_accepts_google_places_fields(self) -> None:
        rows = leadgen.normalize_rows(
            [
                {
                    "id": "places/sample",
                    "displayName": "Moda Test",
                    "formattedAddress": "Kadikoy Istanbul",
                    "primaryTypeDisplayName": "Kafe",
                    "nationalPhoneNumber": "0216 000 00 00",
                    "googleMapsUri": "https://maps.google.com/?cid=sample",
                    "userRatingCount": "88",
                }
            ],
            leadgen.DEFAULT_CONFIG,
        )

        self.assertEqual(rows[0]["lead_id"], "places/sample")
        self.assertEqual(rows[0]["business_name"], "Moda Test")
        self.assertEqual(rows[0]["category"], "Kafe")
        self.assertEqual(rows[0]["maps_url"], "https://maps.google.com/?cid=sample")
        self.assertEqual(rows[0]["review_count"], "88")
        self.assertEqual(rows[0]["website_status"], "no_website")

    def test_normalize_accepts_osm_fields(self) -> None:
        rows = leadgen.normalize_rows(
            [
                {
                    "osm_id": "node/123",
                    "business_name": "Moda Test",
                    "category": "Cafe",
                    "maps_url": "https://www.openstreetmap.org/node/123",
                    "website": "",
                }
            ],
            leadgen.DEFAULT_CONFIG,
        )

        self.assertEqual(rows[0]["lead_id"], "node/123")
        self.assertEqual(rows[0]["business_name"], "Moda Test")
        self.assertEqual(rows[0]["target"], "true")

    def test_normalize_excludes_chain_names(self) -> None:
        rows = leadgen.normalize_rows(
            [
                {"osm_id": "node/1", "business_name": "Starbucks Lara", "category": "Cafe"},
                {"osm_id": "node/2", "business_name": "Simit Sarayı Antalya", "category": "Cafe"},
                {"osm_id": "node/3", "business_name": "Mahalle Kahvesi", "category": "Cafe"},
            ],
            leadgen.DEFAULT_CONFIG,
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["business_name"], "Mahalle Kahvesi")

    def test_generate_site_writes_demo_page(self) -> None:
        rows = leadgen.normalize_rows(
            [{"business_name": "Moda Test", "category": "Kafe", "instagram": "@modatest"}],
            leadgen.DEFAULT_CONFIG,
        )
        with tempfile.TemporaryDirectory() as tmp:
            count = leadgen.generate_sites(rows, Path(tmp), leadgen.DEFAULT_CONFIG)
            self.assertEqual(count, 1)
            self.assertTrue((Path(tmp) / "demo" / "moda-test" / "index.html").exists())
            self.assertTrue((Path(tmp) / "robots.txt").exists())


if __name__ == "__main__":
    unittest.main()
