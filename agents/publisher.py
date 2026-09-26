"""Multi-Platform Publisher & First-Comment Engagement Engine.

Publishes 5-slide PDF carousels to LinkedIn, Meta Facebook Page, and Instagram Container API.
Dispatches an insightful First Comment containing GitHub/doc links 120 seconds post-publish.
Includes zero-config Sandbox / Mock mode when API credentials are unset.
"""

import os
import sys
import time
import threading
import re
import json
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
        """Publishes multi-photo carousel album to Meta Facebook Page."""
        if self.mock_mode or not self.meta_token:
            mock_id = f"meta_page_mock_{int(time.time())}"
            print(f"[Publisher][Facebook][Mock] Page post published successfully: {mock_id}")
            return mock_id

        # Real Meta Graph API implementation
        try:
            target_page_id = self.meta_page_id or "105656909238175"
            page_token = self.meta_token

            # Strict Enforcement: ONLY post to Advance Digital Marketing Course (105656909238175)
            try:
                # 1. First, query target page directly to verify access token and page name
                page_query = requests.get(
                    f"https://graph.facebook.com/v19.0/{target_page_id}?fields=access_token,name,id&access_token={self.meta_token}",
                    timeout=8,
                ).json()
                if "access_token" in page_query:
                    page_token = page_query["access_token"]
                    self._active_page_token = page_token
                    print(f"[Publisher][Facebook] Verified Page Access Token for '{page_query.get('name')}' ({target_page_id})")
                elif "name" in page_query and page_query.get("id") == str(target_page_id):
                    # self.meta_token is already a valid Page Access Token for Advance Digital Marketing Course
                    self._active_page_token = page_token
                    print(f"[Publisher][Facebook] Authenticated with Page Access Token for '{page_query.get('name')}' ({target_page_id})")
                else:
                    # 2. Try matching from /me/accounts, with STRICT match on target_page_id
                    acc_res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?access_token={self.meta_token}", timeout=8).json()
                    pages = acc_res.get("data", [])
                    matched = None
                    for p in pages:
                        if str(p.get("id")) == str(target_page_id) or "advance digital marketing" in str(p.get("name", "")).lower():
                            matched = p
                            break
                    if matched:
                        target_page_id = matched["id"]
                        page_token = matched["access_token"]
                        self._active_page_token = page_token
                        print(f"[Publisher][Facebook] Resolved Page Access Token from accounts for '{matched.get('name')}' ({target_page_id})")
                    else:
                        print(f"[Publisher][Facebook] Using configured Page Access Token for {target_page_id}")
            except Exception as e:
                print(f"[Publisher][Facebook] Account resolution notice: {e}")

            # Safety Guardrail: NEVER allow posting to any other Facebook page
            if str(target_page_id) != "105656909238175":
                raise ValueError(
                    f"SECURITY GUARDRAIL TRIGGERED: Refusing to publish to page {target_page_id}. "
                    f"System is strictly locked ONLY to 'Advance Digital Marketing Course' (105656909238175)."
                )

            if not target_page_id:
                print("[Publisher][Facebook] Warning: No valid page ID found.")
                return f"meta_no_page_{int(time.time())}"

            # Step 1: Upload each slide as an unpublished photo to the Facebook Page
            photo_ids = []
            if png_paths:
                print(f"[Publisher][Facebook] Uploading {len(png_paths)} slide photos for carousel album...")
                for idx, png_file in enumerate(png_paths):
                    if os.path.exists(png_file):
                        try:
                            with open(png_file, "rb") as pf:
                                photo_res = requests.post(
                                    f"https://graph.facebook.com/v19.0/{target_page_id}/photos",
                                    data={"published": "false", "access_token": page_token},
                                    files={"source": pf},
                                    timeout=20,
                                ).json()
                            if "id" in photo_res:
                                photo_ids.append(photo_res["id"])
                                print(f"[Publisher][Facebook] Uploaded slide {idx+1} photo ID: {photo_res['id']}")
                            else:
                                print(f"[Publisher][Facebook] Notice on slide {idx+1} upload: {photo_res}")
                        except Exception as e:
                            print(f"[Publisher][Facebook] Photo upload error on slide {idx+1}: {e}")

            # Step 2: Publish feed post attaching all uploaded photos (Multi-Photo Carousel)
            import json
            url = f"https://graph.facebook.com/v19.0/{target_page_id}/feed"
            full_text = f"{carousel.post_caption}\n\n{' '.join(carousel.hashtags)}"
            payload = {"message": full_text, "access_token": page_token}

            if photo_ids:
                for i, pid in enumerate(photo_ids):
                    payload[f"attached_media[{i}]"] = json.dumps({"media_fbid": str(pid)})

            res = requests.post(url, data=payload, timeout=15)
            res_data = res.json()
            if "id" in res_data:
                print(f"[Publisher][Facebook] Live Carousel Post published successfully! Post ID: {res_data['id']} (Attached {len(photo_ids)} photos)")
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
        ig_token = getattr(self, "_active_page_token", None) or self.meta_token

        if self.mock_mode or not ig_token or not ig_id:
            if not ig_id and not self.mock_mode:
                print(f"[Publisher][Instagram] All {len(png_paths)} slides generated and archived in output/ directory.")
                print("[Publisher][Instagram] (Live direct Instagram posting will auto-trigger once Instagram account is connected).")
            ready_id = f"ig_slides_ready_{int(time.time())}"
            print(f"[Publisher][Instagram] Instagram Carousel Package Ready: {ready_id}")
            return ready_id

        try:
            print(f"[Publisher][Instagram] Preparing multi-slide Instagram carousel for account {ig_id}...")
            item_container_ids = []

            # Step 1: Upload each slide as an Instagram Carousel Item
            for i, png in enumerate(png_paths):
                public_url = self._upload_image_to_public_url(png)
                if not public_url:
                    print(f"[Publisher][Instagram] Warning: Could not obtain public URL for slide {i+1}. Skipping live IG.")
                    return f"ig_fallback_{int(time.time())}"

                item_url = f"https://graph.facebook.com/v19.0/{ig_id}/media"
                payload = {
                    "image_url": public_url,
                    "is_carousel_item": "true",
                    "access_token": ig_token,
                }
                r = requests.post(item_url, data=payload, timeout=20)
                res_data = r.json()
                if "id" in res_data:
                    item_container_ids.append(res_data["id"])
                    print(f"[Publisher][Instagram] Uploaded slide {i+1} container ID: {res_data['id']}")
                else:
                    err_info = res_data.get("error", {})
                    err_msg = err_info.get("message", str(res_data))
                    print(f"[Publisher][Instagram] Error uploading slide {i+1} container: {err_msg}")
                    if err_info.get("code") == 190:
                        print("[Publisher][Instagram] Meta access token has expired (OAuth 190). Please refresh token via /settoken.")
                        return f"ig_token_expired_{int(time.time())}"

            if len(item_container_ids) < 2:
                print("[Publisher][Instagram] Less than 2 slide containers available. Aborting carousel publishing.")
                return f"ig_partial_{int(time.time())}"

            # Step 2: Create Parent Carousel Container
            carousel_url = f"https://graph.facebook.com/v19.0/{ig_id}/media"
            full_caption = f"{carousel.post_caption}\n\n{' '.join(carousel.hashtags)}"
            carousel_payload = {
                "media_type": "CAROUSEL",
                "children": ",".join(item_container_ids),
                "caption": full_caption,
                "access_token": ig_token,
            }
            c_res = requests.post(carousel_url, data=carousel_payload, timeout=25)
            c_data = c_res.json()
            creation_id = c_data.get("id")

            if not creation_id:
                print(f"[Publisher][Instagram] Error creating parent carousel container: {c_data}")
                return f"ig_container_err_{int(time.time())}"

            print(f"[Publisher][Instagram] Parent carousel container created (ID: {creation_id}). Polling processing status...")

            # Step 3: Wait & Poll for container readiness (Meta asynchronous processing)
            is_ready = False
            for attempt in range(12):  # up to 24 seconds
                time.sleep(2)
                try:
                    status_res = requests.get(
                        f"https://graph.facebook.com/v19.0/{creation_id}?fields=status_code&access_token={ig_token}",
                        timeout=10,
                    ).json()
                    status_code = status_res.get("status_code")
                    if status_code == "FINISHED":
                        is_ready = True
                        break
                    elif status_code == "ERROR":
                        print(f"[Publisher][Instagram] Container media processing failed: {status_res}")
                        return f"ig_processing_error_{int(time.time())}"
                except Exception as ex:
                    print(f"[Publisher][Instagram] Polling attempt notice: {ex}")

            # Step 4: Publish Carousel Container
            pub_url = f"https://graph.facebook.com/v19.0/{ig_id}/media_publish"
            pub_payload = {
                "creation_id": creation_id,
                "access_token": ig_token,
            }
            pub_res = requests.post(pub_url, data=pub_payload, timeout=25)
            pub_data = pub_res.json()
            published_media_id = pub_data.get("id", creation_id)
            print(f"[Publisher][Instagram] Live Carousel Published Successfully! Media ID: {published_media_id}")

            # Step 5: Fetch Live Instagram Post Permalink
            try:
                link_res = requests.get(
                    f"https://graph.facebook.com/v19.0/{published_media_id}?fields=permalink&access_token={ig_token}",
                    timeout=10,
                ).json()
                permalink = link_res.get("permalink")
                if permalink:
                    self.latest_ig_permalink = permalink
                    print(f"[Publisher][Instagram] Live Instagram Post Link: {permalink}")
            except Exception as e:
                print(f"[Publisher][Instagram] Notice retrieving permalink: {e}")

            return str(published_media_id)

        except Exception as e:
            print(f"[Publisher][Instagram] Exception: {e}")
            return f"ig_error_{int(time.time())}"

    def _delayed_first_comment_worker(
        self, comment_text: str, li_urn: Optional[str], meta_id: Optional[str], delay: int, ig_id: Optional[str] = None
    ):
        """Worker that sleeps for delay seconds and injects the first comment across platforms."""
        if delay > 0:
            time.sleep(delay)

        print("[FirstCommentEngine] 120s delay elapsed. Dispatching automated first comments across all platforms...")

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

        # 2. Post first comment on Facebook Page Post
        is_real_fb = (
            not self.mock_mode
            and self.meta_token
            and meta_id
            and not any(k in str(meta_id) for k in ["mock", "error", "no_page", "fail"])
        )
        if is_real_fb:
            try:
                fb_token = getattr(self, "_active_page_token", None) or self.meta_token
                fb_comment_url = f"https://graph.facebook.com/v19.0/{meta_id}/comments"
                r = requests.post(
                    fb_comment_url,
                    data={"message": comment_text, "access_token": fb_token},
                    timeout=15,
                )
                r_json = r.json()
                if "id" in r_json:
                    print(f"[FirstCommentEngine] Facebook first comment dispatched live! Comment ID: {r_json['id']}")
                else:
                    print(f"[FirstCommentEngine] Facebook comment response: {r_json}")
            except Exception as e:
                print(f"[FirstCommentEngine] Failed to post Facebook comment: {e}")
        else:
            print(f"[FirstCommentEngine][Sandbox] Facebook first comment dropped:\n{comment_text}")

        # 3. Post first comment on Instagram Carousel Post
        is_real_ig = (
            not self.mock_mode
            and self.meta_token
            and ig_id
            and not any(k in str(ig_id) for k in ["mock", "error", "ready", "fallback", "err", "fail", "partial", "token_expired"])
        )
        if is_real_ig:
            try:
                ig_token = getattr(self, "_active_page_token", None) or self.meta_token
                ig_comment_url = f"https://graph.facebook.com/v19.0/{ig_id}/comments"
                r = requests.post(
                    ig_comment_url,
                    data={"message": comment_text, "access_token": ig_token},
                    timeout=15,
                )
                r_json = r.json()
                if "id" in r_json:
                    print(f"[FirstCommentEngine] Instagram first comment dispatched live! Comment ID: {r_json['id']}")
                else:
                    print(f"[FirstCommentEngine] Instagram comment response: {r_json}")
            except Exception as e:
                print(f"[FirstCommentEngine] Failed to post Instagram comment: {e}")
        else:
            print(f"[FirstCommentEngine][Sandbox] Instagram first comment dropped:\n{comment_text}")


def save_meta_app_credentials(app_id: str, app_secret: str, env_file_path: str = ".env") -> bool:
    """Saves Meta App ID and App Secret to .env and updates current environment."""
    app_id = app_id.strip()
    app_secret = app_secret.strip()
    if not app_id or not app_secret:
        return False

    if os.path.exists(env_file_path):
        with open(env_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        def update_or_append(text: str, key: str, val: str) -> str:
            pattern = rf"^{key}=.*$"
            if re.search(pattern, text, flags=re.MULTILINE):
                return re.sub(pattern, f"{key}={val}", text, flags=re.MULTILINE)
            else:
                return text.strip() + f"\n{key}={val}\n"

        content = update_or_append(content, "META_APP_ID", app_id)
        content = update_or_append(content, "META_APP_SECRET", app_secret)

        with open(env_file_path, "w", encoding="utf-8") as f:
            f.write(content)

    os.environ["META_APP_ID"] = app_id
    os.environ["META_APP_SECRET"] = app_secret
    return True


def get_meta_token_info(token: Optional[str] = None) -> Dict[str, Any]:
    """
    Inspects Meta token validity, expiration time, scope permissions,
    and associated Facebook Page and Instagram Account.
    """
    active_token = (token or os.getenv("META_PAGE_ACCESS_TOKEN", "")).strip().strip("<>\"' \t\r\n")
    if not active_token:
        return {
            "configured": False,
            "valid": False,
            "error": "No token configured.",
            "never_expires": False,
            "days_remaining": None,
            "page_id": "105656909238175",
            "page_name": "Advance Digital Marketing Course",
            "instagram_id": os.getenv("INSTAGRAM_ACCOUNT_ID", "17841405072430897"),
            "instagram_username": None,
        }

    info = {
        "configured": True,
        "valid": False,
        "error": None,
        "name": None,
        "id": None,
        "type": None,
        "never_expires": False,
        "days_remaining": None,
        "expires_at": None,
        "page_id": "105656909238175",
        "page_name": "Advance Digital Marketing Course",
        "instagram_id": os.getenv("INSTAGRAM_ACCOUNT_ID", "17841405072430897"),
        "instagram_username": None,
        "scopes": [],
    }

    try:
        # 1. Query /me
        me_res = requests.get(
            f"https://graph.facebook.com/v19.0/me?fields=id,name&access_token={active_token}",
            timeout=8
        ).json()

        if "error" in me_res:
            err_msg = me_res["error"].get("message", "Invalid Meta token")
            info["error"] = err_msg
            info["valid"] = False
            return info

        info["valid"] = True
        info["name"] = me_res.get("name")
        info["id"] = me_res.get("id")

        # 2. Query debug_token
        try:
            dbg_res = requests.get(
                f"https://graph.facebook.com/v19.0/debug_token?input_token={active_token}&access_token={active_token}",
                timeout=8
            ).json()
            data = dbg_res.get("data", {})
            if data:
                info["type"] = data.get("type")
                info["scopes"] = data.get("scopes", [])
                exp = data.get("expires_at", 0)
                info["expires_at"] = exp
                if exp == 0:
                    info["never_expires"] = True
                    info["days_remaining"] = None
                    info["time_remaining_str"] = "আজীবন (Never Expires)"
                elif exp > 0:
                    rem = exp - time.time()
                    if rem > 86400:
                        days = round(rem / 86400, 1)
                        info["days_remaining"] = days
                        info["time_remaining_str"] = f"{days} দিন"
                    elif rem > 0:
                        info["days_remaining"] = round(rem / 86400, 2)
                        hours = int(rem // 3600)
                        mins = int((rem % 3600) // 60)
                        if hours > 0:
                            info["time_remaining_str"] = f"{hours} ঘণ্টা {mins} মিনিট"
                        else:
                            info["time_remaining_str"] = f"{mins} মিনিট"
                    else:
                        info["days_remaining"] = 0
                        info["time_remaining_str"] = "মেয়াদ শেষ (Expired)"
                    info["never_expires"] = False
        except Exception:
            pass

        # 3. Target Page check
        try:
            target_res = requests.get(
                f"https://graph.facebook.com/v19.0/105656909238175?fields=id,name,instagram_business_account&access_token={active_token}",
                timeout=8
            ).json()
            if "name" in target_res:
                info["page_name"] = target_res.get("name")
                ig = target_res.get("instagram_business_account", {})
                if ig.get("id"):
                    info["instagram_id"] = ig["id"]
        except Exception:
            pass

        # 4. Instagram check
        if info["instagram_id"]:
            try:
                ig_info = requests.get(
                    f"https://graph.facebook.com/v19.0/{info['instagram_id']}?fields=username,name&access_token={active_token}",
                    timeout=8
                ).json()
                if "username" in ig_info:
                    info["instagram_username"] = ig_info.get("username")
            except Exception:
                pass

        return info
    except Exception as e:
        info["valid"] = False
        info["error"] = str(e)
        return info


def exchange_and_generate_permanent_token(
    token: str,
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None
) -> Dict[str, Any]:
    """
    Exchanges a short-lived token for a 60-day Long-Lived User Token,
    then requests the Page Access Token for Page 105656909238175.
    Meta's API guarantees that a Page Token derived from a Long-Lived User Token
    is NEVER-EXPIRING (Permanent / Lifetime).
    """
    token = token.strip().strip("<>\"' \t\r\n")
    resolved_app_id = (app_id or os.getenv("META_APP_ID", "")).strip()
    resolved_app_secret = (app_secret or os.getenv("META_APP_SECRET", "")).strip()

    if not resolved_app_id or not resolved_app_secret:
        return {
            "success": False,
            "error": "Missing Meta App ID or App Secret. Configure META_APP_ID and META_APP_SECRET or provide them via Telegram /setappcreds."
        }

    try:
        # Step A: Exchange short-lived token for 60-day Long-Lived Token
        exchange_url = "https://graph.facebook.com/v19.0/oauth/access_token"
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": resolved_app_id,
            "client_secret": resolved_app_secret,
            "fb_exchange_token": token
        }
        res = requests.get(exchange_url, params=params, timeout=12).json()
        if "error" in res:
            return {
                "success": False,
                "error": f"OAuth Exchange Error: {res['error'].get('message', 'Failed to exchange token')}"
            }

        long_lived_token = res.get("access_token")
        if not long_lived_token:
            return {"success": False, "error": "No access_token returned from Meta exchange endpoint."}

        # Step B: Get Permanent Page Access Token for target Page (105656909238175)
        target_page_id = "105656909238175"
        page_url = f"https://graph.facebook.com/v19.0/{target_page_id}?fields=access_token,name,id,instagram_business_account&access_token={long_lived_token}"
        p_res = requests.get(page_url, timeout=12).json()

        permanent_page_token = None
        if "access_token" in p_res:
            permanent_page_token = p_res["access_token"]
        else:
            # Fallback to /me/accounts
            acc_res = requests.get(f"https://graph.facebook.com/v19.0/me/accounts?access_token={long_lived_token}", timeout=12).json()
            for p in acc_res.get("data", []):
                if str(p.get("id")) == target_page_id or "advance digital marketing" in str(p.get("name", "")).lower():
                    permanent_page_token = p.get("access_token")
                    break

        if not permanent_page_token:
            return {
                "success": False,
                "error": f"Could not obtain Page Access Token for '{target_page_id}'. Ensure your user profile is an Admin of 'Advance Digital Marketing Course'."
            }

        return {
            "success": True,
            "permanent_page_token": permanent_page_token,
            "long_lived_user_token": long_lived_token,
            "page_id": target_page_id,
            "page_name": p_res.get("name", "Advance Digital Marketing Course")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def verify_and_update_meta_token(
    new_token: str,
    env_file_path: str = ".env",
    app_id: Optional[str] = None,
    app_secret: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Verifies a user, page, or system user token with Meta Graph API,
    optionally auto-exchanges it for a Permanent Never-Expiring Page Token if App credentials exist,
    resolves the Facebook Page and linked Instagram Business Account,
    and updates .env and current runtime environment.
    """
    token = new_token.strip().strip("<>\"' \t\r\n")
    result = {
        "success": False,
        "error": None,
        "user_name": None,
        "page_id": None,
        "page_name": None,
        "page_token": None,
        "instagram_id": None,
        "instagram_username": None,
        "never_expires": False,
        "expires_at": None,
        "days_remaining": None,
    }

    if not token:
        result["error"] = "Empty token provided."
        return result

    try:
        # Check if we should and can auto-exchange for a Permanent Page Token
        resolved_app_id = (app_id or os.getenv("META_APP_ID", "")).strip()
        resolved_app_secret = (app_secret or os.getenv("META_APP_SECRET", "")).strip()
        if resolved_app_id and resolved_app_secret:
            print("[TokenUpdater] Meta App credentials detected. Attempting permanent token exchange...")
            perm_res = exchange_and_generate_permanent_token(token, resolved_app_id, resolved_app_secret)
            if perm_res.get("success") and perm_res.get("permanent_page_token"):
                token = perm_res["permanent_page_token"]
                result["never_expires"] = True
                print("[TokenUpdater] Successfully exchanged token for Permanent Never-Expiring Page Token!")

        # Step 1: Query /me to test validity and user identity
        me_res = requests.get(
            f"https://graph.facebook.com/v19.0/me?fields=id,name&access_token={token}",
            timeout=10,
        ).json()

        if "error" in me_res:
            result["error"] = me_res["error"].get("message", "Invalid Meta token.")
            return result

        result["user_name"] = me_res.get("name")
        user_or_entity_id = me_res.get("id")

        # Step 2: STRICT Target Page Enforcement - ONLY "Advance Digital Marketing Course" (105656909238175)
        target_page_id = "105656909238175"
        chosen_page = None

        # Try querying target page directly first
        try:
            target_query = requests.get(
                f"https://graph.facebook.com/v19.0/{target_page_id}?fields=access_token,name,id,instagram_business_account&access_token={token}",
                timeout=10,
            ).json()
            if "name" in target_query and target_query.get("id") == target_page_id:
                chosen_page = {
                    "id": target_page_id,
                    "name": target_query.get("name", "Advance Digital Marketing Course"),
                    "access_token": target_query.get("access_token", token),
                    "instagram_business_account": target_query.get("instagram_business_account", {})
                }
        except Exception as e:
            print(f"[TokenUpdater] Direct target page query notice: {e}")

        # If not resolved directly, try checking /me/accounts with STRICT matching
        if not chosen_page:
            acc_res = requests.get(
                f"https://graph.facebook.com/v19.0/me/accounts?access_token={token}",
                timeout=10,
            ).json()
            pages = acc_res.get("data", [])
            for p in pages:
                if str(p.get("id")) == str(target_page_id) or "advance digital marketing" in str(p.get("name", "")).lower():
                    chosen_page = p
                    break

        # CRITICAL SAFETY: NEVER fall back to pages[0] or any other page
        if not chosen_page:
            result["error"] = (
                f"Authentication Error: Provided token does not have access to 'Advance Digital Marketing Course' (Page ID: {target_page_id}). "
                "For brand security, this system strictly refuses to bind to or publish on any other page."
            )
            return result

        result["page_id"] = chosen_page.get("id", target_page_id)
        result["page_name"] = chosen_page.get("name", "Advance Digital Marketing Course")
        result["page_token"] = chosen_page.get("access_token", token)

        active_page_token = result["page_token"] or token
        active_page_id = result["page_id"]

        # Step 3: Query Instagram Business Account connected to this page
        if active_page_id:
            try:
                ig_res = requests.get(
                    f"https://graph.facebook.com/v19.0/{active_page_id}?fields=instagram_business_account,connected_instagram_account&access_token={active_page_token}",
                    timeout=10,
                ).json()

                ig_biz = ig_res.get("instagram_business_account", {})
                conn_ig = ig_res.get("connected_instagram_account", {})
                detected_ig = ig_biz.get("id") or conn_ig.get("id")
                if detected_ig:
                    result["instagram_id"] = detected_ig
                    try:
                        ig_info = requests.get(
                            f"https://graph.facebook.com/v19.0/{detected_ig}?fields=username,name&access_token={active_page_token}",
                            timeout=8,
                        ).json()
                        result["instagram_username"] = ig_info.get("username")
                    except Exception:
                        pass
                else:
                    result["instagram_id"] = os.getenv("INSTAGRAM_ACCOUNT_ID", "17841405072430897")
            except Exception as e:
                print(f"[TokenUpdater] IG resolution notice: {e}")
                result["instagram_id"] = os.getenv("INSTAGRAM_ACCOUNT_ID", "17841405072430897")

        # Step 4: Check Token Expiry & Lifetime via debug_token
        try:
            dbg = requests.get(
                f"https://graph.facebook.com/v19.0/debug_token?input_token={active_page_token}&access_token={active_page_token}",
                timeout=8,
            ).json()
            d_data = dbg.get("data", {})
            exp = d_data.get("expires_at", 0)
            result["expires_at"] = exp
            if exp == 0:
                result["never_expires"] = True
                result["days_remaining"] = None
                result["time_remaining_str"] = "আজীবন (Never Expires)"
            elif exp > 0:
                result["never_expires"] = False
                rem = exp - time.time()
                if rem > 86400:
                    days = round(rem / 86400, 1)
                    result["days_remaining"] = days
                    result["time_remaining_str"] = f"{days} দিন"
                elif rem > 0:
                    result["days_remaining"] = round(rem / 86400, 2)
                    hours = int(rem // 3600)
                    mins = int((rem % 3600) // 60)
                    if hours > 0:
                        result["time_remaining_str"] = f"{hours} ঘণ্টা {mins} মিনিট"
                    else:
                        result["time_remaining_str"] = f"{mins} মিনিট"
                else:
                    result["days_remaining"] = 0
                    result["time_remaining_str"] = "মেয়াদ শেষ (Expired)"
        except Exception:
            pass

        # Step 5: Persist to .env file
        if os.path.exists(env_file_path):
            with open(env_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            def update_or_append_env(text: str, key: str, val: str) -> str:
                pattern = rf"^{key}=.*$"
                if re.search(pattern, text, flags=re.MULTILINE):
                    return re.sub(pattern, f"{key}={val}", text, flags=re.MULTILINE)
                else:
                    return text.strip() + f"\n{key}={val}\n"

            if result["page_token"]:
                content = update_or_append_env(content, "META_PAGE_ACCESS_TOKEN", result["page_token"])
            if result["page_id"]:
                content = update_or_append_env(content, "META_PAGE_ID", str(result["page_id"]))
            if result["instagram_id"]:
                content = update_or_append_env(content, "INSTAGRAM_ACCOUNT_ID", str(result["instagram_id"]))

            with open(env_file_path, "w", encoding="utf-8") as f:
                f.write(content)

        # Step 6: Update active runtime environment variables
        if result["page_token"]:
            os.environ["META_PAGE_ACCESS_TOKEN"] = result["page_token"]
        if result["page_id"]:
            os.environ["META_PAGE_ID"] = str(result["page_id"])
        if result["instagram_id"]:
            os.environ["INSTAGRAM_ACCOUNT_ID"] = str(result["instagram_id"])

        result["success"] = True
        return result

    except Exception as e:
        result["error"] = str(e)
        return result
