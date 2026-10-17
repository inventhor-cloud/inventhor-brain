import unittest
from dataclasses import replace

from repair.research_media import (
    MediaCandidate, ResearchRequest, prepare_media_cards, plan_research,
)


class CrossPlatformResearchPlannerTests(unittest.TestCase):
    def request(self, **changes):
        params = dict(
            request_id="repair-case-1", purpose="REPAIR",
            query="Bosch dishwasher E15 official repair manual",
            authorized=True, internet_consent=True,
        )
        params.update(changes)
        return ResearchRequest(**params)

    def test_cross_platform_research_plan_includes_requested_engines(self):
        r = plan_research(self.request())
        self.assertEqual(r.state, "SOURCE_PLAN_ONLY")
        self.assertEqual(r.planned_providers,
                         ("YOUTUBE", "GOOGLE", "YANDEX", "OEM"))
        self.assertTrue(any(p == "YANDEX" for p, _ in r.adapter_hints))
        self.assertFalse(r.network_performed)
        self.assertFalse(r.video_or_image_rendered)
        self.assertTrue(r.source_only)

    def test_other_sources_can_be_added_without_duplicate_brain(self):
        r = plan_research(self.request(
            providers=("GENERAL_WEB", "TECHNICAL_FORUM", "OTHER_VERIFIED"),
            purpose="EDUCATION"))
        self.assertEqual(len(r.planned_providers), 3)

    def test_missing_consent_blocks_outbound_research(self):
        self.assertEqual(plan_research(self.request(
            internet_consent=False)).reason, "EXTERNAL_SEARCH_CONSENT_REQUIRED")
        self.assertEqual(plan_research(self.request(
            authorized=False)).reason, "MAIN_AUTH_REQUIRED")

    def test_serial_numbers_vin_and_private_identifiers_are_not_forwarded(self):
        r = plan_research(self.request(contains_personal_device_data=True))
        self.assertEqual(r.state, "BLOCKED")
        self.assertIsNone(r.query)

    def test_invalid_duplicate_unknown_provider_is_not_dispatched(self):
        for providers in (("YOUTUBE", "YOUTUBE"), ("SOME_SCRAPER",), ()):
            with self.subTest(providers=providers):
                self.assertEqual(plan_research(
                    self.request(providers=providers)).reason,
                    "INVALID_PROVIDER_LIST")

    def test_bad_query_or_unsafe_control_character_rejected(self):
        for query in ("", "a", "x\nhidden instructions", "x" * 251):
            with self.subTest(query=query[:12]):
                self.assertEqual(plan_research(
                    self.request(query=query)).state, "BLOCKED")


class MediaPresentationContractTests(unittest.TestCase):
    def item(self, **changes):
        data = dict(
            item_id="item-101", provider="YOUTUBE", media_type="VIDEO",
            title="Example repair tutorial",
            source_url="https://www.youtube.com/watch?v=abcdefghijk",
            source_tier="UNVERIFIED_TUTORIAL",
            host_source_verified=False, device_revision_matched=False,
            embeddable_verified=True, display_allowed=True,
        )
        data.update(changes)
        return MediaCandidate(**data)

    def test_official_embed_only_when_embedding_verified(self):
        c = prepare_media_cards((self.item(),)).cards[0]
        self.assertEqual(c.presentation, "OFFICIAL_EMBED_OPTION")
        self.assertEqual(c.preview_url, "https://www.youtube.com/embed/abcdefghijk")
        self.assertFalse(c.factually_authoritative)
        self.assertTrue(c.user_must_open_or_start_player)
        self.assertFalse(c.may_download_media)
        self.assertFalse(c.may_change_repair_plan)

    def test_unembeddable_video_is_valid_clickable_source(self):
        c = prepare_media_cards((self.item(embeddable_verified=False),)).cards[0]
        self.assertEqual(c.presentation, "SOURCE_LINK")
        self.assertIsNone(c.preview_url)

    def test_youtu_be_short_video_link_supported_only_exact_id(self):
        c = prepare_media_cards((self.item(
            source_url="https://youtu.be/abcdefghijk"),)).cards[0]
        self.assertEqual(c.preview_url, "https://www.youtube.com/embed/abcdefghijk")

    def test_a_page_with_youtube_words_does_not_get_embed(self):
        results = prepare_media_cards((self.item(
            source_url="https://youtube.com.attacker.example/watch?v=abcdefghijk"),))
        self.assertEqual(results.cards, ())
        self.assertEqual(results.rejected_count, 1)

    def test_malformed_youtube_ids_never_embedded(self):
        for url in (
            "https://www.youtube.com/watch?v=too_short",
            "https://youtu.be/abcdefghijk/malicious",
            "https://www.youtube.com/watch?v=abcdefghijk&v=01234567890",
        ):
            with self.subTest(url=url):
                self.assertEqual(
                    prepare_media_cards((self.item(source_url=url),)).cards, ())

    def test_images_and_documents_use_separate_safe_viewers(self):
        photo = self.item(item_id="img", provider="GOOGLE", media_type="IMAGE",
                          source_url="https://example.org/repair/image.png",
                          title="Module photo",
                          external_thumbnail_url="https://example.org/thumb.png")
        pdf = self.item(item_id="manual", provider="OEM", media_type="DOCUMENT",
                        source_url="https://manuals.example.org/doc.pdf",
                        title="Service manual", host_source_verified=True,
                        device_revision_matched=True,
                        source_tier="MATCHED_OEM_MANUAL")
        results = prepare_media_cards((photo, pdf))
        self.assertEqual(results.cards[0].presentation,
                         "HOST_SANDBOXED_IMAGE_PREVIEW")
        self.assertEqual(results.cards[0].thumbnail_url,
                         "https://example.org/thumb.png")
        self.assertEqual(results.cards[1].presentation,
                         "DOCUMENT_PREVIEW_OR_SOURCE_LINK")
        self.assertTrue(results.cards[1].factually_authoritative)
        self.assertFalse(results.media_rendered)

    def test_tutorial_never_promoted_to_factory_manual(self):
        c = prepare_media_cards((self.item(
            host_source_verified=True, device_revision_matched=True),)).cards[0]
        self.assertFalse(c.factually_authoritative)

    def test_factory_manual_cannot_be_promoted_without_exact_revision(self):
        c = prepare_media_cards((self.item(
            provider="OEM", media_type="DOCUMENT",
            source_url="https://manuals.example.org/a.pdf",
            source_tier="MATCHED_OEM_MANUAL",
            host_source_verified=True, device_revision_matched=False),)).cards[0]
        self.assertFalse(c.factually_authoritative)

    def test_duplicate_provider_hits_are_merged_by_source(self):
        first = self.item(item_id="item-1", provider="YOUTUBE")
        second = self.item(item_id="item-2", provider="YOUTUBE")
        results = prepare_media_cards((first, second))
        self.assertEqual(len(results.cards), 1)
        self.assertEqual(results.rejected_count, 1)

    def test_unapproved_preview_not_shown(self):
        results = prepare_media_cards((self.item(display_allowed=False),))
        self.assertEqual(results.cards, ())
        self.assertEqual(results.rejected_count, 1)

    def test_local_private_non_https_scheme_and_userinfo_rejected(self):
        for url in (
            "http://example.org/m.jpg", "file:///etc/passwd",
            "https://localhost/private", "https://127.0.0.1/private",
            "https://192.168.1.2/router", "https://user:secret@example.org/p",
            "https://example.org\\@attacker.org/x",
            "javascript:alert(1)", "https://host.local/abc",
        ):
            with self.subTest(url=url):
                results = prepare_media_cards((self.item(
                    provider="GENERAL_WEB", media_type="IMAGE",
                    source_url=url),))
                self.assertEqual(results.cards, ())

    def test_https_nonstandard_port_rejected(self):
        r = prepare_media_cards((self.item(
            provider="GENERAL_WEB", media_type="IMAGE",
            source_url="https://example.org:8080/path"),))
        self.assertEqual(r.cards, ())

    def test_thumbnail_url_is_validated_not_assumed_safe(self):
        c = prepare_media_cards((self.item(
            external_thumbnail_url="http://localhost/private.png"),)).cards[0]
        self.assertIsNone(c.thumbnail_url)

    def test_source_cards_are_not_actual_browser_or_media_execution(self):
        collection = prepare_media_cards((self.item(),))
        self.assertFalse(collection.network_performed)
        self.assertFalse(collection.media_rendered)
        self.assertTrue(collection.source_only)

    def test_bad_batch_or_bad_record_does_not_crash(self):
        self.assertEqual(prepare_media_cards("not a collection").state,
                         "INVALID_BATCH")
        self.assertEqual(prepare_media_cards((object(),)).rejected_count, 1)

    def test_existing_unsafe_metadata_not_promoted(self):
        r = prepare_media_cards((self.item(
            title="Unsafe\nname"),))
        self.assertEqual(r.cards, ())
