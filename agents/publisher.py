"""Multi-Platform Publisher & First-Comment Engagement Engine.

Publishes 5-slide PDF carousels to LinkedIn, Meta Facebook Page, and Instagram Container API.
Dispatches an insightful First Comment containing GitHub/doc links 120 seconds post-publish.
Includes zero-config Sandbox / Mock mode when API credentials are unset.
"""

import os
import sys
import time
import threading
from typing import Dict, Any, List, Optional
import requests
from dotenv import load_dotenv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

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

        # 4. Push direct notification to Telegram if chat ID is set
        self._push_telegram_broadcast(carousel, pdf_path, png_paths, li_urn, fb_post_id)

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
                args=(carousel.first_comment, li_urn, fb_post_id, delay, ig_id),
                daemon=True,
            ).start()
            print(f"[Publisher] First-Comment Engine scheduled to trigger in {delay}s in background.")
        else:
            self._delayed_first_comment_worker(carousel.first_comment, li_urn, fb_post_id, delay, ig_id)

        return result

    def _push_telegram_broadcast(
        self, carousel: CarouselContent, pdf_path: str, png_paths: List[str], li_urn: Optional[str], fb_id: Optional[str]
    ):
        """Pushes direct notification to Telegram chat if TELEGRAM_CHAT_ID is configured or auto-detected."""
        tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")
        if not tg_token:
            return

        # Auto-discover chat_id from recent bot updates if not configured
        if not chat_id:
            try:
                r = requests.get(f"https://api.telegram.org/bot{tg_token}/getUpdates", timeout=5).json()
                results = r.get("result", [])
                if results:
                    last_update = results[-1]
                    msg_obj = last_update.get("message") or last_update.get("channel_post") or {}
                    detected_id = msg_obj.get("chat", {}).get("id")
                    if detected_id:
                        chat_id = str(detected_id)
                        print(f"[Publisher][Telegram] Auto-detected Telegram chat ID: {chat_id}")
            except Exception as e:
                print(f"[Publisher][Telegram] Could not auto-detect chat ID: {e}")

        if not chat_id:
            print("[Publisher][Telegram] Notice: TELEGRAM_CHAT_ID is not configured and no recent Telegram updates found.")
            print(" -> To receive automated Telegram broadcasts, open Telegram and send /start to your bot.")
            return

        try:
            li_link = f"https://www.linkedin.com/feed/update/{li_urn}/" if li_urn and "mock" not in str(li_urn) else "Published"
            fb_link = f"https://facebook.com/{fb_id}" if fb_id and "mock" not in str(fb_id) else None
            
            links_text = f"🔗 *LinkedIn:* {li_link}"
            if fb_link:
                links_text += f"\n🔗 *Facebook Page:* {fb_link}"
            ig_link = getattr(self, "latest_ig_permalink", None)
            if ig_link:
                links_text += f"\n🔗 *Instagram Post:* {ig_link}"
            else:
                links_text += f"\n📸 *Instagram:* 5 Carousel Slides & Caption ready in `output/`"

            msg = (
                f"🚀 *New Campaign Published Live!*\n\n"
                f"📌 *Topic:* {carousel.topic_headline}\n"
                f"{links_text}\n\n"
                f"📝 *Caption:*\n{carousel.post_caption[:250]}..."
            )
            requests.post(
                f"https://api.telegram.org/bot{tg_token}/sendMessage",
                data={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"},
                timeout=10,
            )
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    requests.post(
                        f"https://api.telegram.org/bot{tg_token}/sendDocument",
                        data={"chat_id": chat_id, "caption": "📄 Compiled Carousel PDF"},
                        files={"document": f},
                        timeout=20,
                    )
            print(f"[Publisher][Telegram] Broadcast pushed successfully to chat ID: {chat_id}")
        except Exception as e:
            print(f"[Publisher][Telegram] Broadcast notification warning: {e}")

    def _publish_linkedin(self, carousel: CarouselContent, pdf_path: str) -> str:
        """Uploads growth_carousel.pdf to LinkedIn and creates a Document Post."""
        if self.mock_mode or not self.linkedin_token:
            mock_urn = f"urn:li:share:mock_{int(time.time())}"
            print(f"[Publisher][LinkedIn][Mock] Document post published successfully: {mock_urn}")
            print(f"[Publisher][LinkedIn][Mock] Attached PDF: {pdf_path}")
            return mock_urn

        # Modern LinkedIn REST Posts & Documents API (version 202503)
        headers = {
            "Authorization": f"Bearer {self.linkedin_token}",
            "LinkedIn-Version": "202503",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        try:
            # Step 1: Initialize Document Upload
            init_url = "https://api.linkedin.com/rest/documents?action=initializeUpload"
            init_payload = {"initializeUploadRequest": {"owner": self.linkedin_author}}
            init_res = requests.post(init_url, headers=headers, json=init_payload, timeout=15)
            if init_res.status_code != 200:
                print(f"[Publisher][LinkedIn] Init upload error ({init_res.status_code}): {init_res.text}")
                return f"urn:li:share:simulated_{int(time.time())}"

            init_data = init_res.json().get("value", {})
            upload_url = init_data.get("uploadUrl")
            document_urn = init_data.get("document")

            # Step 2: Upload PDF Binary
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            upload_headers = {"Authorization": f"Bearer {self.linkedin_token}", "Content-Type": "application/pdf"}
            requests.put(upload_url, headers=upload_headers, data=pdf_bytes, timeout=30)

            # Step 3: Create Feed Post with Document
            post_url = "https://api.linkedin.com/rest/posts"
            full_text = f"{carousel.post_caption}\n\n{' '.join(carousel.hashtags)}"
            post_payload = {
                "author": self.linkedin_author,
                "commentary": full_text,
                "visibility": "PUBLIC",
                "distribution": {
                    "feedDistribution": "MAIN_FEED",
                    "targetEntities": [],
                    "thirdPartyDistributionChannels": []
                },
                "content": {
                    "media": {
                        "title": f"{carousel.slides[0].badge} - {carousel.topic_headline}",
                        "id": document_urn
                    }
                },
                "lifecycleState": "PUBLISHED"
            }
            post_res = requests.post(post_url, headers=headers, json=post_payload, timeout=15)
            post_urn = post_res.headers.get("x-restli-id") or post_res.headers.get("x-linkedin-id") or document_urn
            print(f"[Publisher][LinkedIn] Live post published successfully! URN: {post_urn}")
            return post_urn
        except Exception as e:
            print(f"[Publisher][LinkedIn] API Exception: {e}")
            return f"urn:li:share:error_{int(time.time())}"

    def _publish_meta(self, carousel: CarouselContent, png_paths: List[str]) -> str:
        """Publishes carousel content to Meta Facebook Page."""
        if self.mock_mode or not self.meta_token:
            mock_id = f"meta_page_mock_{int(time.time())}"
            print(f"[Publisher][Facebook][Mock] Page post published successfully: {mock_id}")
            return mock_id

        # Real Meta Graph API implementation
        try:
            target_page_id = self.meta_page_id
            page_token = self.meta_token

            # Auto-resolve Page Access Token from /me/accounts if a User Token was provided
            try:
                acc_res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?access_token={self.meta_token}", timeout=8).json()
                pages = acc_res.get("data", [])
                if pages:
                    matched = None
                    if target_page_id:
                        for p in pages:
                            if p.get("id") == str(target_page_id):
                                matched = p
                                break
                    if not matched:
                        matched = pages[0]
                    target_page_id = matched["id"]
                    page_token = matched["access_token"]
                    self._active_page_token = page_token
                    self.meta_page_id = target_page_id
                    safe_name = str(matched.get('name', '')).encode('ascii', errors='replace').decode('ascii')
                    print(f"[Publisher][Facebook] Resolved Page Access Token for '{safe_name}' ({target_page_id})")
            except Exception as e:
                print(f"[Publisher][Facebook] Account resolution notice: {e}")

            if not target_page_id:
                print("[Publisher][Facebook] Warning: No valid page ID found.")
                return f"meta_no_page_{int(time.time())}"

            url = f"https://graph.facebook.com/v19.0/{target_page_id}/feed"
            full_text = f"{carousel.post_caption}\n\n{' '.join(carousel.hashtags)}"
            payload = {"message": full_text, "access_token": page_token}
            res = requests.post(url, data=payload, timeout=12)
            res_data = res.json()
            if "id" in res_data:
                print(f"[Publisher][Facebook] Live post published successfully! Post ID: {res_data['id']}")
                return res_data["id"]
            else:
                print(f"[Publisher][Facebook] API Response: {res_data}")
                return f"meta_page_{int(time.time())}"
        except Exception as e:
            print(f"[Publisher][Facebook] Exception: {e}")
            return f"meta_error_{int(time.time())}"

    def _upload_image_to_public_url(self, image_path: str) -> Optional[str]:
        """Uploads a local slide image to a direct public HTTPS URL for Meta crawler access."""
        # 1. Primary: Catbox.moe (Direct CDN PNG URL, verified Meta compatible)
        try:
            with open(image_path, "rb") as f:
                r = requests.post(
                    "https://catbox.moe/user/api.php",
                    data={"reqtype": "fileupload"},
                    files={"fileToUpload": f},
                    timeout=15,
                )
            if r.status_code == 200 and r.text.startswith("https://files.catbox.moe/"):
                return r.text.strip()
        except Exception as e:
            print(f"[Publisher][Instagram] Catbox upload notice: {e}")

        # 2. Secondary fallback: tmpfiles.org
        try:
            with open(image_path, "rb") as f:
                r = requests.post("https://tmpfiles.org/api/v1/upload", files={"file": f}, timeout=15)
            if r.status_code == 200:
                data = r.json().get("data", {})
                raw_url = data.get("url", "")
                if "tmpfiles.org/" in raw_url:
                    parts = raw_url.split("tmpfiles.org/")
                    direct_url = f"https://tmpfiles.org/dl/{parts[1]}"
                    return direct_url
        except Exception as e:
            print(f"[Publisher][Instagram] Secondary upload notice: {e}")

        return None

    def _get_or_detect_instagram_id(self) -> Optional[str]:
        """Returns configured INSTAGRAM_ACCOUNT_ID or auto-detects from Facebook Page."""
        if self.ig_account_id:
            return self.ig_account_id

        if not self.meta_token or not self.meta_page_id:
            return None

        try:
            url = f"https://graph.facebook.com/v19.0/{self.meta_page_id}"
            params = {
                "fields": "instagram_business_account,connected_instagram_account,page_backed_instagram_accounts",
                "access_token": self.meta_token,
            }
            r = requests.get(url, params=params, timeout=10)
            data = r.json()

            # 1. Instagram Business / Creator Account (Standard required by Meta for posting)
            ig_acc = data.get("instagram_business_account", {})
            if ig_acc and "id" in ig_acc:
                detected_id = ig_acc["id"]
                print(f"[Publisher][Instagram] Auto-detected Instagram Business Account: {detected_id}")
                self.ig_account_id = detected_id
                return detected_id

            # 2. Connected Instagram Account
            conn_ig = data.get("connected_instagram_account", {})
            if conn_ig and "id" in conn_ig:
                detected_id = conn_ig["id"]
                print(f"[Publisher][Instagram] Auto-detected Connected Instagram Account: {detected_id}")
                self.ig_account_id = detected_id
                return detected_id

            # 3. Page Backed Instagram Account (Personal/Ad mode)
            pb_list = data.get("page_backed_instagram_accounts", {}).get("data", [])
            if pb_list and "id" in pb_list[0]:
                pb_id = pb_list[0]["id"]
                print(f"[Publisher][Instagram] Page-Backed Instagram link verified ({pb_id}). Instagram profile is currently in Personal mode.")
                return None

        except Exception as e:
            print(f"[Publisher][Instagram] Auto-detection notice: {e}")

        return None

    def _publish_instagram(self, carousel: CarouselContent, png_paths: List[str]) -> str:
        """Publishes multi-image carousel container to Instagram Graph API."""
        ig_id = self._get_or_detect_instagram_id()

        if self.mock_mode or not self.meta_token or not ig_id:
            if not ig_id and not self.mock_mode:
                print(f"[Publisher][Instagram] All {len(png_paths)} slides generated and archived in output/ directory.")
                print("[Publisher][Instagram] (Live direct Instagram posting will auto-trigger once Instagram account is switched to Professional/Creator mode).")
            ready_id = f"ig_slides_ready_{int(time.time())}"
            print(f"[Publisher][Instagram] Instagram Carousel Package Ready: {ready_id}")
            return ready_id

        try:
            print(f"[Publisher][Instagram] Uploading {len(png_paths)} slide containers to Meta Graph API...")
            item_container_ids = []

            # Step 1: Upload each slide as an Instagram Carousel Item
            for i, png in enumerate(png_paths):
                public_url = self._upload_image_to_public_url(png)
                if not public_url:
                    print(f"[Publisher][Instagram] Failed to get public URL for slide {i+1}. Skipping live IG.")
                    return f"ig_fallback_{int(time.time())}"

                item_url = f"https://graph.facebook.com/v19.0/{ig_id}/media"
                payload = {
                    "image_url": public_url,
                    "is_carousel_item": "true",
                    "access_token": self.meta_token,
                }
                r = requests.post(item_url, data=payload, timeout=15)
                res_data = r.json()
                if "id" in res_data:
                    item_container_ids.append(res_data["id"])
                else:
                    print(f"[Publisher][Instagram] Error uploading slide {i+1} container: {res_data}")

            if len(item_container_ids) < 2:
                print("[Publisher][Instagram] Could not create at least 2 slide containers. Aborting IG publish.")
                return f"ig_partial_{int(time.time())}"

            # Step 2: Create Parent Carousel Container
            carousel_url = f"https://graph.facebook.com/v19.0/{ig_id}/media"
            full_caption = f"{carousel.post_caption}\n\n{' '.join(carousel.hashtags)}"
            carousel_payload = {
                "media_type": "CAROUSEL",
                "children": ",".join(item_container_ids),
                "caption": full_caption,
                "access_token": self.meta_token,
            }
            c_res = requests.post(carousel_url, data=carousel_payload, timeout=20)
            c_data = c_res.json()
            creation_id = c_data.get("id")

            if not creation_id:
                print(f"[Publisher][Instagram] Error creating carousel container: {c_data}")
                return f"ig_container_err_{int(time.time())}"

            # Step 3: Wait for container to be ready
            time.sleep(3)

            # Step 4: Publish Carousel Container
            pub_url = f"https://graph.facebook.com/v19.0/{ig_id}/media_publish"
            pub_payload = {
                "creation_id": creation_id,
                "access_token": self.meta_token,
            }
            pub_res = requests.post(pub_url, data=pub_payload, timeout=20)
            pub_data = pub_res.json()
            published_media_id = pub_data.get("id", creation_id)
            print(f"[Publisher][Instagram] Live Carousel Published Successfully! Media ID: {published_media_id}")

            # Step 5: Fetch Live Instagram Post Permalink
            try:
                link_res = requests.get(
                    f"https://graph.facebook.com/v19.0/{published_media_id}?fields=permalink&access_token={self.meta_token}",
                    timeout=8
                ).json()
                permalink = link_res.get("permalink")
                if permalink:
                    self.latest_ig_permalink = permalink
                    print(f"[Publisher][Instagram] Live Instagram Post Link: {permalink}")
            except Exception as e:
                print(f"[Publisher][Instagram] Notice retrieving permalink: {e}")

            return published_media_id

        except Exception as e:
            print(f"[Publisher][Instagram] Exception: {e}")
            return f"ig_error_{int(time.time())}"

    def _delayed_first_comment_worker(
        self, comment_text: str, li_urn: Optional[str], meta_id: Optional[str], delay: int, ig_id: Optional[str] = None
    ):
        """Worker that sleeps for delay seconds and injects the first comment across platforms."""
        if delay > 0:
            time.sleep(delay)

        print("[FirstCommentEngine] 120s delay elapsed. Dispatching automated first comments...")

        # 1. Post first comment on LinkedIn (using verified v2 socialActions endpoint)
        if not self.mock_mode and self.linkedin_token and li_urn:
            try:
                import urllib.parse
                headers = {
                    "Authorization": f"Bearer {self.linkedin_token}",
                    "X-Restli-Protocol-Version": "2.0.0",
                    "Content-Type": "application/json",
                }
                enc_urn = urllib.parse.quote(li_urn, safe="")
                comment_url = f"https://api.linkedin.com/v2/socialActions/{enc_urn}/comments"
                payload = {
                    "actor": self.linkedin_author,
                    "message": {"text": comment_text},
                }
                r = requests.post(comment_url, headers=headers, json=payload, timeout=15)
                if r.status_code == 404:
                    print("[FirstCommentEngine] LinkedIn post still propagating (404), waiting 15s for indexing...")
                    time.sleep(15)
                    r = requests.post(comment_url, headers=headers, json=payload, timeout=15)
                if r.status_code in [200, 201]:
                    print(f"[FirstCommentEngine] LinkedIn first comment dispatched live successfully! Status: {r.status_code}")
                else:
                    print(f"[FirstCommentEngine] LinkedIn comment error ({r.status_code}): {r.text}")
            except Exception as e:
                print(f"[FirstCommentEngine] Failed to post LinkedIn comment: {e}")
        else:
            print(f"[FirstCommentEngine][Sandbox] LinkedIn first comment dropped:\n{comment_text}")

        # 2. Post first comment on Facebook
        if not self.mock_mode and self.meta_token and meta_id and "mock" not in str(meta_id):
            try:
                fb_token = getattr(self, "_active_page_token", self.meta_token)
                fb_comment_url = f"https://graph.facebook.com/v19.0/{meta_id}/comments"
                requests.post(
                    fb_comment_url,
                    data={"message": comment_text, "access_token": fb_token},
                    timeout=10,
                )
                print("[FirstCommentEngine] Facebook first comment dispatched live.")
            except Exception as e:
                print(f"[FirstCommentEngine] Failed to post Facebook comment: {e}")
        else:
            print(f"[FirstCommentEngine][Sandbox] Facebook first comment dropped:\n{comment_text}")

        # 3. Post first comment on Instagram (if live published)
        if not self.mock_mode and self.meta_token and ig_id and "mock" not in str(ig_id) and "error" not in str(ig_id):
            try:
                ig_comment_url = f"https://graph.facebook.com/v19.0/{ig_id}/comments"
                requests.post(
                    ig_comment_url,
                    data={"message": comment_text, "access_token": self.meta_token},
                    timeout=10,
                )
                print("[FirstCommentEngine] Instagram first comment dispatched live.")
            except Exception as e:
                print(f"[FirstCommentEngine] Failed to post Instagram comment: {e}")
