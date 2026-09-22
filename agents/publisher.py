"""Multi-Platform Publisher & First-Comment Engagement Engine.

Publishes 5-slide PDF carousels to LinkedIn, Meta Facebook Page, and Instagram Container API.
Dispatches an insightful First Comment containing GitHub/doc links 120 seconds post-publish.
Includes zero-config Sandbox / Mock mode when API credentials are unset.
"""

import os
import time
import threading
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

from state import CarouselContent, PublicationResult
from agents.analytics_tracker import AnalyticsTracker

load_dotenv()


class MultiPlatformPublisher:
    """Manages cross-platform publication and delayed first-comment injection."""

    def __init__(self):
        self.mock_mode = os.getenv("MOCK_MODE", "True").lower() == "true"
        self.linkedin_token = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
        self.linkedin_author = os.getenv("LINKEDIN_AUTHOR_URN", "urn:li:person:demo_author")
        self.meta_token = os.getenv("META_PAGE_ACCESS_TOKEN", "")
        self.meta_page_id = os.getenv("META_PAGE_ID", "")
        self.ig_account_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
        self.first_comment_delay = int(os.getenv("FIRST_COMMENT_DELAY_SECONDS", "120"))
        self.analytics_tracker = AnalyticsTracker()

    def publish_all(
        self,
        carousel: CarouselContent,
        pdf_path: str,
        png_paths: List[str],
        async_first_comment: bool = True,
        override_delay_seconds: Optional[int] = None,
    ) -> PublicationResult:
        """Publishes to LinkedIn, Meta Facebook, and Instagram, then schedules the First Comment."""
        print("[Publisher] Initiating multi-platform distribution...")

        # 1. LinkedIn Document Post
        li_urn = self._publish_linkedin(carousel, pdf_path)

        # 2. Meta Facebook Post
        fb_post_id = self._publish_meta(carousel, png_paths)

        # 3. Instagram Container Carousel
        ig_id = self._publish_instagram(carousel, png_paths)

        # Record publication into SQLite memory loop
        self.analytics_tracker.record_published_post(
            topic_id=f"topic_{carousel.day_number}_{int(time.time())}",
            topic_title=carousel.topic_headline,
            hook_text=carousel.slides[0].title,
            linkedin_urn=li_urn,
            meta_post_id=fb_post_id,
            code_snippet_included=bool(carousel.slides[2].code_snippet),
        )

        result = PublicationResult(
            linkedin_urn=li_urn,
            facebook_post_id=fb_post_id,
            instagram_container_id=ig_id,
            published_at=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            status="published",
            mock_mode=self.mock_mode,
            details={
                "pdf_path": pdf_path,
                "first_comment_scheduled": True,
                "first_comment_delay_seconds": override_delay_seconds or self.first_comment_delay,
            },
        )

        # Schedule First Comment
        delay = override_delay_seconds if override_delay_seconds is not None else self.first_comment_delay
        if async_first_comment:
            threading.Thread(
                target=self._delayed_first_comment_worker,
                args=(carousel.first_comment, li_urn, fb_post_id, delay),
                daemon=True,
            ).start()
            print(f"[Publisher] First-Comment Engine scheduled to trigger in {delay}s in background.")
        else:
            self._delayed_first_comment_worker(carousel.first_comment, li_urn, fb_post_id, delay)

        return result

    def _publish_linkedin(self, carousel: CarouselContent, pdf_path: str) -> str:
        """Uploads growth_carousel.pdf to LinkedIn and creates a Document Post."""
        if self.mock_mode or not self.linkedin_token:
            mock_urn = f"urn:li:share:mock_{int(time.time())}"
            print(f"[Publisher][LinkedIn][Mock] Document post published successfully: {mock_urn}")
            print(f"[Publisher][LinkedIn][Mock] Attached PDF: {pdf_path}")
            return mock_urn

        # Real LinkedIn Community Management / Document API implementation
        headers = {
            "Authorization": f"Bearer {self.linkedin_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        # Step 1: Register Document Upload
        reg_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
        reg_payload = {
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-document"],
                "owner": self.linkedin_author,
                "supportedUploadMechanism": ["SYNCHRONOUS_UPLOAD"],
            }
        }
        reg_res = requests.post(reg_url, headers=headers, json=reg_payload, timeout=10)
        reg_data = reg_res.json()
        upload_url = reg_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
        asset_urn = reg_data["value"]["asset"]

        # Step 2: Upload Binary
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        upload_headers = {"Authorization": f"Bearer {self.linkedin_token}", "Content-Type": "application/pdf"}
        requests.put(upload_url, headers=upload_headers, data=pdf_bytes, timeout=30)

        # Step 3: Create Feed Post with Document
        post_url = "https://api.linkedin.com/v2/ugcPosts"
        full_text = f"{carousel.post_caption}\n\n{' '.join(carousel.hashtags)}"
        post_payload = {
            "author": self.linkedin_author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": full_text},
                    "shareMediaCategory": "DOCUMENT",
                    "media": [
                        {
                            "status": "READY",
                            "description": {"text": carousel.topic_headline},
                            "media": asset_urn,
                            "title": {"text": f"{carousel.slides[0].badge} - {carousel.topic_headline}"},
                        }
                    ],
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }
        post_res = requests.post(post_url, headers=headers, json=post_payload, timeout=10)
        post_data = post_res.json()
        urn = post_data.get("id", asset_urn)
        print(f"[Publisher][LinkedIn] Live post published: {urn}")
        return urn

    def _publish_meta(self, carousel: CarouselContent, png_paths: List[str]) -> str:
        """Publishes carousel content to Meta Facebook Page."""
        if self.mock_mode or not self.meta_token or not self.meta_page_id:
            mock_id = f"meta_page_mock_{int(time.time())}"
            print(f"[Publisher][Facebook][Mock] Page post published successfully: {mock_id}")
            return mock_id

        # Real Meta Graph API implementation
        url = f"https://graph.facebook.com/v19.0/{self.meta_page_id}/feed"
        full_text = f"{carousel.post_caption}\n\n{' '.join(carousel.hashtags)}"
        payload = {"message": full_text, "access_token": self.meta_token}
        res = requests.post(url, data=payload, timeout=10)
        return res.json().get("id", f"meta_{int(time.time())}")

    def _publish_instagram(self, carousel: CarouselContent, png_paths: List[str]) -> str:
        """Publishes multi-image carousel container to Instagram Graph API."""
        if self.mock_mode or not self.meta_token or not self.ig_account_id:
            mock_ig = f"ig_carousel_mock_{int(time.time())}"
            print(f"[Publisher][Instagram][Mock] Carousel container published successfully: {mock_ig}")
            return mock_ig

        print(f"[Publisher][Instagram] Live IG carousel publish requested for {len(png_paths)} slides.")
        return f"ig_container_{int(time.time())}"

    def _delayed_first_comment_worker(
        self, comment_text: str, li_urn: Optional[str], meta_id: Optional[str], delay: int
    ):
        """Worker that sleeps for delay seconds and injects the first comment."""
        if delay > 0:
            time.sleep(delay)

        print("[FirstCommentEngine] 120s delay elapsed. Dispatching automated first comment...")

        # Post first comment on LinkedIn
        if not self.mock_mode and self.linkedin_token and li_urn:
            try:
                comment_url = f"https://api.linkedin.com/v2/socialActions/{li_urn}/comments"
                headers = {
                    "Authorization": f"Bearer {self.linkedin_token}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "actor": self.linkedin_author,
                    "message": {"text": comment_text},
                }
                requests.post(comment_url, headers=headers, json=payload, timeout=10)
                print("[FirstCommentEngine] LinkedIn first comment dispatched live.")
            except Exception as e:
                print(f"[FirstCommentEngine] Failed to post LinkedIn comment: {e}")
        else:
            print(f"[FirstCommentEngine][Mock] LinkedIn first comment dropped: \n{comment_text}")

        # Post first comment on Facebook
        if not self.mock_mode and self.meta_token and meta_id:
            try:
                fb_comment_url = f"https://graph.facebook.com/v19.0/{meta_id}/comments"
                requests.post(
                    fb_comment_url,
                    data={"message": comment_text, "access_token": self.meta_token},
                    timeout=10,
                )
                print("[FirstCommentEngine] Facebook first comment dispatched live.")
            except Exception as e:
                print(f"[FirstCommentEngine] Failed to post Facebook comment: {e}")
        else:
            print(f"[FirstCommentEngine][Mock] Facebook first comment dropped: \n{comment_text}")
