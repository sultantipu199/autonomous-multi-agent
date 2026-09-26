"""Advanced Carousel & Visual Rendering Engine.

Renders 5-slide high-retention technical carousels (1080x1080 aesthetic dark-theme #0D1117)
using Pillow, featuring clean, large, mobile-optimized typography, syntax-highlighted code terminals,
ROI metric cards, and compiles them into LinkedIn-ready PDF documents via PyMuPDF (fitz).
"""

import os
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont, ImageOps

try:
    import fitz  # PyMuPDF
    HAVE_PYMUPDF = True
except Exception:
    HAVE_PYMUPDF = False

from state import CarouselContent, Slide


class CarouselEngine:
    """Renders 1080x1080 aesthetic dark-theme slides and compiles PDF carousels."""

    # Aesthetic Color Palette (GitHub Dark / Linear theme)
    BG_COLOR = (13, 17, 23)             # #0D1117
    CARD_BG = (22, 27, 34)              # #161B22
    CARD_BORDER = (48, 54, 61)          # #30363D
    CODE_BG = (9, 13, 18)               # #090D12
    TEXT_PRIMARY = (240, 246, 252)      # #F0F6FC
    TEXT_MUTED = (139, 148, 158)        # #8B949E
    TEXT_SUBTLE = (203, 213, 225)       # #CBD5E1
    ACCENT_BLUE = (88, 166, 255)        # #58A6FF
    ACCENT_BLUE_BORDER = (56, 139, 253) # #388BFD
    ACCENT_GREEN = (46, 160, 67)        # #2EA043
    ACCENT_GREEN_BRIGHT = (63, 185, 80) # #3FB950
    ACCENT_ORANGE = (240, 136, 62)      # #F0883E
    ACCENT_PURPLE = (210, 168, 255)     # #D2A8FF
    ACCENT_CYAN = (121, 192, 255)       # #79C0FF
    BADGE_BG = (33, 38, 45)             # #21262D
    LINE_COLOR = (33, 38, 45)           # Separator lines

    WIDTH = 1080
    HEIGHT = 1080

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.fonts = self._load_fonts()

    def _load_fonts(self) -> dict:
        """Loads crisp system or bundled fonts with multi-platform fallbacks."""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        candidate_dirs = [
            os.path.join(base_dir, "..", "assets", "fonts"),
            os.path.join(os.getcwd(), "assets", "fonts"),
            "assets/fonts",
            os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts"),
            "C:/Windows/Fonts",
            "/usr/share/fonts/truetype/dejavu",
            "/usr/share/fonts/truetype/freefont",
            "/usr/share/fonts/truetype/liberation",
            "/usr/share/fonts",
            "/Library/Fonts",
            "/System/Library/Fonts",
        ]

        def try_font(names: List[str], size: int) -> ImageFont.FreeTypeFont:
            for d in candidate_dirs:
                if not os.path.exists(d):
                    continue
                for name in names:
                    path = os.path.join(d, name)
                    if os.path.exists(path):
                        try:
                            return ImageFont.truetype(path, size)
                        except Exception:
                            pass
            try:
                return ImageFont.load_default(size=size)
            except Exception:
                return ImageFont.load_default()

        bold_candidates = ["segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf", "FreeSansBold.ttf", "LiberationSans-Bold.ttf"]
        reg_candidates = ["segoeui.ttf", "arial.ttf", "DejaVuSans.ttf", "FreeSans.ttf", "LiberationSans-Regular.ttf"]
        mono_candidates = ["consola.ttf", "consolab.ttf", "DejaVuSansMono.ttf", "FreeMono.ttf", "cour.ttf"]

        fonts = {
            "title_hero": try_font(bold_candidates, 62),
            "title_large": try_font(bold_candidates, 50),
            "subtitle": try_font(reg_candidates, 30),
            "card_header": try_font(bold_candidates, 22),
            "body_bold": try_font(bold_candidates, 30),
            "body": try_font(reg_candidates, 29),
            "body_small": try_font(reg_candidates, 26),
            "badge": try_font(bold_candidates, 22),
            "code": try_font(mono_candidates, 24),
            "metric_val": try_font(bold_candidates, 68),
            "metric_val_small": try_font(bold_candidates, 54),
            "metric_lbl": try_font(bold_candidates, 26),
            "small": try_font(reg_candidates, 22),
            "auth_name": try_font(bold_candidates, 44),
            "auth_role": try_font(bold_candidates, 28),
            "auth_sub": try_font(reg_candidates, 24),
            "cta": try_font(bold_candidates, 24),
        }
        return fonts

    def _get_avatar(self, size: int = 60) -> Optional[Image.Image]:
        """Loads and crops Tipu Sultan's real authentic photo into a crisp circular avatar."""
        asset_paths = [
            os.path.join("assets", "tipu_sultan.png"),
            os.path.join(os.path.dirname(__file__), "..", "assets", "tipu_sultan.png"),
            "assets/test_headshot.png",
            "assets/tipu_sultan.png"
        ]
        chosen = None
        for p in asset_paths:
            if os.path.exists(p):
                chosen = p
                break
        if not chosen:
            return None

        try:
            im = Image.open(chosen).convert("RGBA")
            if im.size == (206, 206):
                im = im.crop((35, 25, 165, 155))

            im = ImageOps.fit(im, (size, size), Image.Resampling.LANCZOS)

            # Antialiased circular mask via 4x supersampling
            scale = 4
            mask = Image.new("L", (size * scale, size * scale), 0)
            mdraw = ImageDraw.Draw(mask)
            mdraw.ellipse([0, 0, size * scale, size * scale], fill=255)
            mask = mask.resize((size, size), Image.Resampling.LANCZOS)

            avatar = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            avatar.paste(im, (0, 0), mask=mask)

            # Glowing accent blue border
            border = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            bdraw = ImageDraw.Draw(border)
            bdraw.ellipse([1, 1, size - 2, size - 2], outline=self.ACCENT_BLUE, width=2)

            return Image.alpha_composite(avatar, border)
        except Exception:
            return None

    def _draw_checkmark(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int = 12):
        """Draws a crisp antialiased green checkmark circle."""
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=self.ACCENT_GREEN_BRIGHT)
        pts = [
            (cx - int(r * 0.45), cy),
            (cx - int(r * 0.1), cy + int(r * 0.4)),
            (cx + int(r * 0.5), cy - int(r * 0.35))
        ]
        draw.line([pts[0], pts[1]], fill=self.BG_COLOR, width=3)
        draw.line([pts[1], pts[2]], fill=self.BG_COLOR, width=3)

    def _draw_header(self, draw: ImageDraw.ImageDraw, slide: Slide, current: int, total: int = 5, canvas: Optional[Image.Image] = None):
        """Draws top brand badge, author avatar, and pagination tracker."""
        x0 = 70
        if canvas is not None:
            avatar = self._get_avatar(60)
            if avatar:
                canvas.paste(avatar, (70, 54), mask=avatar)
                x0 = 146

        # Top Brand Badge (Cleaned string without corrupted characters)
        raw_badge = (slide.badge or "TIPU SULTAN | AI & DATA GROWTH ARCHITECT").replace("\ufffd", " | ").replace("•", " | ").replace("  |  ", " | ")
        badge_text = raw_badge.upper()
        badge_bbox = self.fonts["badge"].getbbox(badge_text)
        badge_w = badge_bbox[2] - badge_bbox[0] + 32
        badge_h = badge_bbox[3] - badge_bbox[1] + 18

        y0 = 62
        draw.rounded_rectangle(
            [x0, y0, x0 + badge_w, y0 + badge_h],
            radius=8,
            fill=self.BADGE_BG,
            outline=self.ACCENT_BLUE,
            width=1,
        )
        draw.text(
            (x0 + 16, y0 + 8),
            badge_text,
            font=self.fonts["badge"],
            fill=self.ACCENT_BLUE,
        )

        # Pagination: 01 / 05
        page_str = f"0{current} / 0{total}"
        draw.text(
            (self.WIDTH - 170, 70),
            page_str,
            font=self.fonts["badge"],
            fill=self.TEXT_MUTED,
        )

        # Divider line
        draw.line([(70, 130), (self.WIDTH - 70, 130)], fill=self.CARD_BORDER, width=1)

    def _draw_footer(self, draw: ImageDraw.ImageDraw, slide: Slide):
        """Draws bottom branding and swipe indicator with Tipu Sultan's verified authority."""
        y = self.HEIGHT - 80
        draw.line([(70, y), (self.WIDTH - 70, y)], fill=self.CARD_BORDER, width=1)

        draw.text(
            (70, y + 22),
            "TIPU SULTAN  •  AI & DATA GROWTH ARCHITECT",
            font=self.fonts["small"],
            fill=self.TEXT_MUTED,
        )

        cta_right = "Save & Follow →" if slide.slide_number == 5 else "Swipe next →"
        cta_bbox = self.fonts["cta"].getbbox(cta_right)
        cta_w = cta_bbox[2] - cta_bbox[0]
        draw.text(
            (self.WIDTH - 70 - cta_w, y + 20),
            cta_right,
            font=self.fonts["cta"],
            fill=self.ACCENT_BLUE,
        )

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
        """Utility to wrap lines cleanly within given pixel width."""
        words = text.split(" ")
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = font.getbbox(test_line)
            w = bbox[2] - bbox[0]
            if w <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))
        return lines

    def render_slide_1_hook(self, slide: Slide) -> Image.Image:
        """Slide 1: High-contrast Hook + Topic Category Pill + Structured Problem/Solution Cards."""
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        self._draw_header(draw, slide, 1, canvas=img)

        # Topic Category Pill
        sub_text = (slide.subtitle or "BLUEPRINT ARCHITECTURE").replace("\ufffd", " • ").replace("  •  ", " • ").upper()
        sb = self.fonts["card_header"].getbbox(sub_text)
        sw = sb[2] - sb[0] + 32
        draw.rounded_rectangle([70, 155, 70 + sw, 195], radius=8, fill=self.CARD_BG, outline=self.ACCENT_BLUE, width=1)
        draw.text((86, 163), sub_text, font=self.fonts["card_header"], fill=self.ACCENT_BLUE)

        # Hero Hook Headline
        y = 215
        clean_title = slide.title.replace("\n", " ").strip()
        title_lines = self._wrap_text(clean_title, self.fonts["title_hero"], self.WIDTH - 140)
        for line in title_lines:
            draw.text((70, y), line, font=self.fonts["title_hero"], fill=self.TEXT_PRIMARY)
            y += 76

        y += 18

        # Extract problem, solution, and audience from body_bullets
        prob_text = ""
        fix_text = ""
        aud_text = "Engineered for Technical Marketers, Media Buyers & Growth Founders."

        for b in slide.body_bullets:
            if "Core Problem:" in b:
                prob_text = b.replace("Core Problem:", "").strip()
            elif "Architecture Fix:" in b:
                fix_text = b.replace("Architecture Fix:", "").strip()
            elif "Engineered for" in b:
                aud_text = b.strip()
            elif not prob_text:
                prob_text = b.strip()
            elif not fix_text:
                fix_text = b.strip()

        if not prob_text:
            prob_text = "Standard client-side browser tracking drops 30-45% of conversion events due to iOS privacy controls and ad blockers."
        if not fix_text:
            fix_text = "Deploy server-side tracking architecture via GTM Server Container to restore 1st-party cookie lifespan and signal integrity."

        # Card 1: Core Problem
        p_lines = self._wrap_text(prob_text, self.fonts["body"], self.WIDTH - 190)
        p_card_h = len(p_lines) * 44 + 80
        draw.rounded_rectangle([70, y, self.WIDTH - 70, y + p_card_h], radius=14, fill=self.CARD_BG, outline=self.CARD_BORDER, width=1)
        
        pb = self.fonts["card_header"].getbbox("THE PRODUCTION BOTTLENECK")
        draw.rounded_rectangle([95, y + 18, 95 + pb[2] - pb[0] + 28, y + 52], radius=6, fill=self.BADGE_BG, outline=self.ACCENT_ORANGE, width=1)
        draw.text((109, y + 24), "THE PRODUCTION BOTTLENECK", font=self.fonts["card_header"], fill=self.ACCENT_ORANGE)
        
        py = y + 68
        for pl in p_lines:
            draw.text((95, py), pl, font=self.fonts["body"], fill=self.TEXT_PRIMARY)
            py += 44

        y += p_card_h + 18

        # Card 2: Architecture Fix
        f_lines = self._wrap_text(fix_text, self.fonts["body"], self.WIDTH - 190)
        f_card_h = len(f_lines) * 44 + 80
        draw.rounded_rectangle([70, y, self.WIDTH - 70, y + f_card_h], radius=14, fill=self.CARD_BG, outline=self.ACCENT_BLUE_BORDER, width=1)
        
        fb = self.fonts["card_header"].getbbox("THE ARCHITECTURE FIX")
        draw.rounded_rectangle([95, y + 18, 95 + fb[2] - fb[0] + 28, y + 52], radius=6, fill=self.BADGE_BG, outline=self.ACCENT_BLUE, width=1)
        draw.text((109, y + 24), "THE ARCHITECTURE FIX", font=self.fonts["card_header"], fill=self.ACCENT_BLUE)
        
        fy_pos = y + 68
        for fl in f_lines:
            draw.text((95, fy_pos), fl, font=self.fonts["body"], fill=self.TEXT_PRIMARY)
            fy_pos += 44

        y += f_card_h + 18

        # Engineering / Target Audience Tag
        ab = self.fonts["card_header"].getbbox(aud_text)
        draw.rounded_rectangle([70, y, 70 + ab[2] - ab[0] + 46, y + 42], radius=8, fill=self.CARD_BG, outline=self.CARD_BORDER, width=1)
        draw.ellipse([88, y + 15, 100, y + 27], fill=self.ACCENT_GREEN)
        draw.text((112, y + 10), aud_text, font=self.fonts["card_header"], fill=self.TEXT_MUTED)

        self._draw_footer(draw, slide)
        return img

    def render_slide_2_problem(self, slide: Slide) -> Image.Image:
        """Slide 2: The Core Engineering Problem / Production Bottlenecks."""
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        self._draw_header(draw, slide, 2, canvas=img)

        y = 165
        draw.text((70, y), slide.title, font=self.fonts["title_large"], fill=self.TEXT_PRIMARY)
        y += 62
        if slide.subtitle:
            sub_clean = slide.subtitle.replace("\ufffd", " • ").replace("  •  ", " • ")
            draw.text((70, y), sub_clean, font=self.fonts["subtitle"], fill=self.TEXT_MUTED)
            y += 55

        bullets = slide.body_bullets or [
            "Client-Side Signal Loss: Standard browser pixels lose 30-45% of purchase events due to Safari ITP and ad blockers.",
            "Algorithmic Misalignment: Degraded signals feed corrupt datasets to Meta & Google AI bidders, causing erratic CPA spikes.",
            "Attribution Blind Spot: Shortened cookie lifespans break 7-day click attribution windows and ad scaling confidence."
        ]

        for i, b in enumerate(bullets[:3]):
            card_h = 195
            draw.rounded_rectangle([70, y, self.WIDTH - 70, y + card_h], radius=14, fill=self.CARD_BG, outline=self.CARD_BORDER, width=1)

            # Left index badge
            draw.rounded_rectangle([95, y + 25, 155, y + 80], radius=8, fill=self.BADGE_BG, outline=self.ACCENT_ORANGE, width=1)
            draw.text((108, y + 36), f"0{i+1}", font=self.fonts["body_bold"], fill=self.ACCENT_ORANGE)

            # Check if bullet has title prefix (e.g. "Title: Description")
            if ":" in b:
                parts = b.split(":", 1)
                b_title = parts[0].strip()
                # Remove leading number like "1. " if present
                if b_title and b_title[0].isdigit() and (b_title[1:3] in [". ", ") "]):
                    b_title = b_title[3:].strip()
                b_desc = parts[1].strip()
            else:
                b_title = f"Bottleneck 0{i+1}"
                b_desc = b.strip()

            draw.text((175, y + 26), b_title, font=self.fonts["body_bold"], fill=self.TEXT_PRIMARY)

            desc_lines = self._wrap_text(b_desc, self.fonts["body_small"], self.WIDTH - 270)
            dy = y + 72
            for dl in desc_lines:
                draw.text((175, dy), dl, font=self.fonts["body_small"], fill=self.TEXT_SUBTLE)
                dy += 36

            y += card_h + 20

        self._draw_footer(draw, slide)
        return img

    def render_slide_3_architecture(self, slide: Slide) -> Image.Image:
        """Slide 3: The Architecture Diagram / Executable Code Snippet Breakdown."""
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        self._draw_header(draw, slide, 3, canvas=img)

        y = 165
        draw.text((70, y), slide.title, font=self.fonts["title_large"], fill=self.TEXT_PRIMARY)
        y += 62
        if slide.subtitle:
            sub_clean = slide.subtitle.replace("\ufffd", " • ").replace("  •  ", " • ")
            draw.text((70, y), sub_clean, font=self.fonts["subtitle"], fill=self.TEXT_MUTED)
            y += 48

        # Actionable directive
        directive = slide.body_bullets[0] if slide.body_bullets else "Deploy this verified server-side script via GTM Server Container:"
        dir_lines = self._wrap_text(directive, self.fonts["body_small"], self.WIDTH - 140)
        for dl in dir_lines:
            draw.text((70, y), dl, font=self.fonts["body_small"], fill=self.ACCENT_CYAN)
            y += 34
        y += 10

        # Code Terminal Card
        term_w = self.WIDTH - 140
        term_h = 560
        draw.rounded_rectangle([70, y, 70 + term_w, y + term_h], radius=14, fill=self.CODE_BG, outline=self.CARD_BORDER, width=1)

        # Header Bar & Window Dots
        draw.line([(70, y + 46), (70 + term_w, y + 46)], fill=self.CARD_BORDER, width=1)
        draw.ellipse([95, y + 16, 111, y + 32], fill=(255, 95, 86))    # Red
        draw.ellipse([120, y + 16, 136, y + 32], fill=(255, 189, 46))  # Yellow
        draw.ellipse([145, y + 16, 161, y + 32], fill=(39, 201, 63))   # Green
        draw.text((term_w // 2 - 40, y + 14), "stape_capi_setup.js", font=self.fonts["small"], fill=self.TEXT_MUTED)

        # Code lines
        code_lines = (slide.code_snippet or "// Server-Side Tracking Snippet").split("\n")
        cy = y + 66
        line_no = 1
        for raw_line in code_lines:
            if cy > y + term_h - 40:
                break
            # Wrap long code lines
            if len(raw_line) > 58:
                sub_lines = [raw_line[:58], "    " + raw_line[58:]]
            else:
                sub_lines = [raw_line]

            for sub_idx, sline in enumerate(sub_lines):
                if sub_idx == 0:
                    draw.text((95, cy), f"{line_no:02d}", font=self.fonts["code"], fill=(80, 90, 105))
                    line_no += 1

                color = self.TEXT_PRIMARY
                strip_l = sline.strip()
                if strip_l.startswith("//") or strip_l.startswith("#"):
                    color = self.ACCENT_GREEN_BRIGHT
                elif any(k in sline for k in ["function ", "var ", "return ", "if ", "def ", "import ", "const ", "let "]):
                    color = self.ACCENT_PURPLE
                elif any(k in sline for k in ["getCookie", "setCookie", "Date.now", "Math.floor", "push", "subscribe"]):
                    color = self.ACCENT_BLUE
                elif "'" in sline or '"' in sline:
                    color = self.ACCENT_CYAN

                draw.text((145, cy), sline, font=self.fonts["code"], fill=color)
                cy += 38

        self._draw_footer(draw, slide)
        return img

    def render_slide_4_roi(self, slide: Slide) -> Image.Image:
        """Slide 4: Measurable Business ROI & Executive Impact Breakdown."""
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        self._draw_header(draw, slide, 4, canvas=img)

        y = 165
        draw.text((70, y), slide.title, font=self.fonts["title_large"], fill=self.TEXT_PRIMARY)
        y += 62
        if slide.subtitle:
            sub_clean = slide.subtitle.replace("\ufffd", " • ").replace("  •  ", " • ")
            draw.text((70, y), sub_clean, font=self.fonts["subtitle"], fill=self.TEXT_MUTED)
            y += 48

        # Benchmark Highlight Banner
        self._draw_checkmark(draw, 85, y + 14, r=10)
        lead_bullet = slide.body_bullets[0] if slide.body_bullets else "Primary Benchmark: Event Match Quality achieving 9.4 / 10"
        draw.text((110, y), lead_bullet, font=self.fonts["body"], fill=self.TEXT_PRIMARY)
        y += 45

        # 3 Metric Cards
        metrics = slide.metrics or []
        if not metrics:
            from state import SlideMetric
            metrics = [
                SlideMetric(label="Event Match Quality", value="9.4 / 10", subtext="From standard 4.8 baseline"),
                SlideMetric(label="Data Integrity", value="99.9%", subtext="Zero dropped CAPI signals"),
                SlideMetric(label="ROAS Impact", value="3.5x - 5.2x", subtext="Scale-ready attribution")
            ]

        card_w = (self.WIDTH - 140 - (len(metrics) - 1) * 20) // max(1, len(metrics))
        card_h = 265
        colors = [self.ACCENT_BLUE, self.ACCENT_GREEN_BRIGHT, self.ACCENT_ORANGE]

        for i, m in enumerate(metrics[:3]):
            cx = 70 + i * (card_w + 20)
            col = colors[i % len(colors)]

            draw.rounded_rectangle([cx, y, cx + card_w, y + card_h], radius=14, fill=self.CARD_BG, outline=self.CARD_BORDER, width=1)
            draw.rounded_rectangle([cx, y, cx + card_w, y + 8], radius=4, fill=col)

            # Auto-scale font size so metric value never overflows card
            val_str = str(m.value)
            val_size = 68
            while val_size > 36:
                val_font = ImageFont.truetype(self.fonts["metric_val"].path if hasattr(self.fonts["metric_val"], "path") else "assets/fonts/segoeuib.ttf", val_size)
                vb = val_font.getbbox(val_str)
                if vb[2] - vb[0] <= card_w - 40:
                    break
                val_size -= 4

            draw.text((cx + 25, y + 38), val_str, font=val_font, fill=col)
            draw.text((cx + 25, y + 130), m.label, font=self.fonts["metric_lbl"], fill=self.TEXT_PRIMARY)
            if m.subtext:
                draw.text((cx + 25, y + 175), m.subtext, font=self.fonts["small"], fill=self.TEXT_MUTED)

        y += card_h + 20

        # Executive Impact Card below
        ey = y
        takeaways = [
            "Eliminates 30-45% tracking blind spots caused by iOS 14.5+ and browser ad blockers.",
            "Feeds full-funnel conversion signals directly to Meta & Google Smart Bidding algorithms.",
            "Restores accurate multi-touch ROAS attribution to scale profitable ad spend with confidence."
        ]
        if len(slide.body_bullets) > 1:
            takeaways = [b.replace("Signal uplift:", "").strip() for b in slide.body_bullets[1:4]]

        total_lines = sum(len(self._wrap_text(t, self.fonts["body_small"], self.WIDTH - 220)) for t in takeaways)
        exec_h = 55 + total_lines * 34 + len(takeaways) * 8 + 15
        draw.rounded_rectangle([70, ey, self.WIDTH - 70, ey + exec_h], radius=14, fill=self.CARD_BG, outline=(35, 134, 54), width=1)
        draw.text((95, ey + 18), "EXECUTIVE ATTRIBUTION IMPACT", font=self.fonts["card_header"], fill=self.ACCENT_GREEN_BRIGHT)

        ty = ey + 54
        for t in takeaways:
            self._draw_checkmark(draw, 110, ty + 10, r=9)
            t_lines = self._wrap_text(t, self.fonts["body_small"], self.WIDTH - 220)
            for tl in t_lines:
                draw.text((135, ty), tl, font=self.fonts["body_small"], fill=self.TEXT_PRIMARY)
                ty += 34
            ty += 8

        self._draw_footer(draw, slide)
        return img

    def render_slide_5_checklist(self, slide: Slide) -> Image.Image:
        """Slide 5: Implementation Checklist + Tipu Sultan Author Authority Card."""
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        self._draw_header(draw, slide, 5, canvas=img)

        y = 155
        draw.text((70, y), slide.title, font=self.fonts["title_large"], fill=self.TEXT_PRIMARY)
        y += 60
        if slide.subtitle:
            sub_clean = slide.subtitle.replace("\ufffd", " • ").replace("  •  ", " • ")
            draw.text((70, y), sub_clean, font=self.fonts["subtitle"], fill=self.TEXT_MUTED)
            y += 40

        # Checklist Items Card
        items = slide.body_bullets or [
            "Deploy custom domain CNAME record pointing to GTM Server Container.",
            "Configure unique event_id generation across both browser and server tags.",
            "Hash user email and phone with SHA-256 for Advanced Matching parameters.",
            "Audit live signals using Meta Events Manager Test Events tool."
        ]

        card_y = y
        card_h = len(items[:4]) * 50 + 16
        draw.rounded_rectangle([70, card_y, self.WIDTH - 70, card_y + card_h], radius=14, fill=self.CARD_BG, outline=self.CARD_BORDER, width=1)

        iy = card_y + 16
        for item in items[:4]:
            self._draw_checkmark(draw, 105, iy + 14, r=10)
            # Remove numeric prefix like "1. " if present
            clean_item = item
            if clean_item and clean_item[0].isdigit() and clean_item[1:3] in [". ", ") "]:
                clean_item = clean_item[3:].strip()
            draw.text((135, iy), clean_item, font=self.fonts["body_small"], fill=self.TEXT_PRIMARY)
            iy += 50

        # Author Authority Profile Card
        auth_y = card_y + card_h + 20
        auth_h = 350
        draw.rounded_rectangle([70, auth_y, self.WIDTH - 70, auth_y + auth_h], radius=16, fill=self.CARD_BG, outline=self.ACCENT_BLUE_BORDER, width=2)

        avatar_lg = self._get_avatar(110)
        if avatar_lg:
            img.paste(avatar_lg, (100, auth_y + 24), mask=avatar_lg)

        draw.text((235, auth_y + 24), "TIPU SULTAN", font=self.fonts["auth_name"], fill=self.TEXT_PRIMARY)
        self._draw_checkmark(draw, 535, auth_y + 47, r=14)

        draw.text((235, auth_y + 74), "AI & Data-Driven Growth Architect", font=self.fonts["auth_role"], fill=self.ACCENT_BLUE)
        draw.text((235, auth_y + 110), "Web Analytics  •  Meta CAPI  •  Server-Side Tracking Specialist", font=self.fonts["auth_sub"], fill=self.TEXT_MUTED)

        draw.line([(100, auth_y + 160), (self.WIDTH - 100, auth_y + 160)], fill=self.CARD_BORDER, width=1)

        bio_sentence = "Empowering eCommerce brands to recover lost ad revenue & scale with AI."
        bio_lines = self._wrap_text(bio_sentence, self.fonts["body"], self.WIDTH - 200)
        by_pos = auth_y + 180
        for bl in bio_lines:
            draw.text((100, by_pos), bl, font=self.fonts["body"], fill=self.TEXT_PRIMARY)
            by_pos += 38

        draw.rounded_rectangle([100, auth_y + 265, self.WIDTH - 100, auth_y + 325], radius=12, fill=self.BADGE_BG, outline=self.ACCENT_BLUE, width=1)
        cta_text = "Save This Blueprint  •  Follow Tipu Sultan for Daily Tracking Architecture"
        cb = self.fonts["badge"].getbbox(cta_text)
        cw = cb[2] - cb[0]
        draw.text((100 + (self.WIDTH - 200 - cw) // 2, auth_y + 282), cta_text, font=self.fonts["badge"], fill=self.ACCENT_BLUE)

        self._draw_footer(draw, slide)
        return img

    def render_all(self, carousel: CarouselContent) -> Tuple[List[str], str]:
        """Renders all 5 slides to PNGs and compiles them into a single PDF document.

        Returns:
            Tuple of (List of 5 PNG image paths, compiled PDF file path).
        """
        png_paths = []
        renderers = [
            self.render_slide_1_hook,
            self.render_slide_2_problem,
            self.render_slide_3_architecture,
            self.render_slide_4_roi,
            self.render_slide_5_checklist,
        ]

        images: List[Image.Image] = []
        for i, (slide, renderer) in enumerate(zip(carousel.slides, renderers)):
            img = renderer(slide)
            img_path = os.path.join(self.output_dir, f"slide_{i+1}.png")
            img.save(img_path, "PNG", quality=95)
            png_paths.append(img_path)
            images.append(img)

        # Compile PDF using PyMuPDF (fitz) or native high-resolution Pillow
        pdf_path = os.path.join(self.output_dir, "growth_carousel.pdf")

        if HAVE_PYMUPDF:
            try:
                doc = fitz.open()
                for png_path in png_paths:
                    page_rect = fitz.Rect(0, 0, self.WIDTH, self.HEIGHT)
                    page = doc.new_page(width=self.WIDTH, height=self.HEIGHT)
                    page.insert_image(page_rect, filename=png_path)
                doc.save(pdf_path)
                doc.close()
            except Exception:
                images[0].save(pdf_path, "PDF", resolution=150.0, save_all=True, append_images=images[1:])
        else:
            images[0].save(pdf_path, "PDF", resolution=150.0, save_all=True, append_images=images[1:])

        return png_paths, pdf_path
