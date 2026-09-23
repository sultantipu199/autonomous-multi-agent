"""Advanced Carousel & Visual Rendering Engine.

Renders 5-slide high-retention technical carousels (1080x1080 aesthetic dark-theme #0D1117)
using Pillow, featuring clean typography, syntax-highlighted code terminals, ROI metric cards,
and compiles them into LinkedIn-ready PDF documents via PyMuPDF (fitz).
"""

import os
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
try:
    import fitz  # PyMuPDF
    HAVE_PYMUPDF = True
except Exception:
    HAVE_PYMUPDF = False

from state import CarouselContent, Slide


class CarouselEngine:
    """Renders 1080x1080 aesthetic dark-theme slides and compiles PDF carousels."""

    # Aesthetic Color Palette (GitHub Dark / Linear theme)
    BG_COLOR = (13, 17, 23)        # #0D1117
    CARD_BG = (22, 27, 34)         # #161B22
    CARD_BORDER = (48, 54, 61)     # #30363D
    CODE_BG = (9, 13, 18)          # #090D12
    TEXT_PRIMARY = (240, 246, 252) # #F0F6FC
    TEXT_MUTED = (139, 148, 158)   # #8B949E
    ACCENT_BLUE = (88, 166, 255)   # #58A6FF
    ACCENT_GREEN = (46, 160, 67)   # #2EA043
    ACCENT_ORANGE = (240, 136, 62) # #F0883E
    ACCENT_PURPLE = (210, 168, 255)# #D2A8FF
    BADGE_BG = (33, 38, 45)        # #21262D
    LINE_COLOR = (33, 38, 45)      # Separator lines

    WIDTH = 1080
    HEIGHT = 1080

    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        self.fonts = self._load_fonts()

    def _load_fonts(self) -> dict:
        """Loads crisp system fonts with fallbacks."""
        font_dir = "C:/Windows/Fonts"
        fonts = {}

        def try_font(names: List[str], size: int) -> ImageFont.FreeTypeFont:
            for name in names:
                path = os.path.join(font_dir, name)
                if os.path.exists(path):
                    try:
                        return ImageFont.truetype(path, size)
                    except Exception:
                        pass
            return ImageFont.load_default()

        fonts["title_hero"] = try_font(["segoeuib.ttf", "arialbd.ttf"], 58)
        fonts["title_large"] = try_font(["segoeuib.ttf", "arialbd.ttf"], 44)
        fonts["subtitle"] = try_font(["segoeui.ttf", "arial.ttf"], 28)
        fonts["body_bold"] = try_font(["segoeuib.ttf", "arialbd.ttf"], 26)
        fonts["body"] = try_font(["segoeui.ttf", "arial.ttf"], 24)
        fonts["badge"] = try_font(["segoeuib.ttf", "arialbd.ttf"], 19)
        fonts["code"] = try_font(["consola.ttf", "arial.ttf"], 21)
        fonts["metric_val"] = try_font(["segoeuib.ttf", "arialbd.ttf"], 60)
        fonts["metric_lbl"] = try_font(["segoeui.ttf", "arial.ttf"], 22)
        fonts["small"] = try_font(["segoeui.ttf", "arial.ttf"], 18)
        fonts["auth_name"] = try_font(["segoeuib.ttf", "arialbd.ttf"], 36)
        fonts["auth_role"] = try_font(["segoeuib.ttf", "arialbd.ttf"], 24)
        fonts["auth_sub"] = try_font(["segoeui.ttf", "arial.ttf"], 22)
        fonts["cta"] = try_font(["segoeuib.ttf", "arialbd.ttf"], 21)

        return fonts

    def _get_avatar(self, size: int = 54) -> Optional[Image.Image]:
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
            from PIL import ImageOps
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

    def _draw_header(self, draw: ImageDraw.ImageDraw, slide: Slide, current: int, total: int = 5, canvas: Optional[Image.Image] = None):
        """Draws top brand badge, author avatar, and pagination tracker."""
        x0 = 70
        if canvas is not None:
            avatar = self._get_avatar(54)
            if avatar:
                canvas.paste(avatar, (70, 58), mask=avatar)
                x0 = 136

        # Top Brand Badge
        badge_text = slide.badge.upper()
        badge_bbox = self.fonts["badge"].getbbox(badge_text)
        badge_w = badge_bbox[2] - badge_bbox[0] + 32
        badge_h = badge_bbox[3] - badge_bbox[1] + 18

        y0 = 65
        # Badge background pill
        draw.rounded_rectangle(
            [x0, y0, x0 + badge_w, y0 + badge_h],
            radius=8,
            fill=self.BADGE_BG,
            outline=self.ACCENT_BLUE,
            width=1,
        )
        draw.text(
            (x0 + 16, y0 + 7),
            badge_text,
            font=self.fonts["badge"],
            fill=self.ACCENT_BLUE,
        )

        # Pagination: 01 / 05
        page_str = f"0{current} / 0{total}"
        draw.text(
            (self.WIDTH - 170, 72),
            page_str,
            font=self.fonts["badge"],
            fill=self.TEXT_MUTED,
        )

        # Subtle decorative glowing top bar
        draw.line([(70, 125), (self.WIDTH - 70, 125)], fill=self.CARD_BORDER, width=1)

    def _draw_footer(self, draw: ImageDraw.ImageDraw, slide: Slide):
        """Draws bottom branding and swipe indicator with Tipu Sultan's verified authority (STRICT ZERO LINK)."""
        y = self.HEIGHT - 80
        draw.line([(70, y), (self.WIDTH - 70, y)], fill=self.CARD_BORDER, width=1)

        # Tipu Sultan Authority Branding (Anti-spam zero outbound link)
        draw.text(
            (70, y + 22),
            "TIPU SULTAN  •  AI & DATA GROWTH ARCHITECT",
            font=self.fonts["small"],
            fill=self.TEXT_MUTED,
        )

        cta_right = "Save & Follow →" if slide.slide_number == 5 else "Swipe next →"
        cta_bbox = self.fonts["badge"].getbbox(cta_right)
        cta_w = cta_bbox[2] - cta_bbox[0]
        draw.text(
            (self.WIDTH - 70 - cta_w, y + 20),
            cta_right,
            font=self.fonts["badge"],
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
        """Slide 1: High-contrast Hook + Author Brand Badge + Subtitle."""
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        self._draw_header(draw, slide, 1, canvas=img)

        # Hero Hook Headline
        y = 220
        title_lines = self._wrap_text(slide.title, self.fonts["title_hero"], self.WIDTH - 140)
        for line in title_lines:
            draw.text((70, y), line, font=self.fonts["title_hero"], fill=self.TEXT_PRIMARY)
            y += 75

        y += 20
        # Subtitle Pill Card
        if slide.subtitle:
            sub_lines = self._wrap_text(slide.subtitle, self.fonts["subtitle"], self.WIDTH - 180)
            card_h = len(sub_lines) * 44 + 32
            draw.rounded_rectangle(
                [70, y, self.WIDTH - 70, y + card_h],
                radius=12,
                fill=self.CARD_BG,
                outline=self.CARD_BORDER,
                width=1,
            )
            sy = y + 16
            for sline in sub_lines:
                draw.text((94, sy), sline, font=self.fonts["subtitle"], fill=self.ACCENT_BLUE)
                sy += 44
            y += card_h + 35

        # Key takeaway bullet previews
        for bullet in slide.body_bullets[:3]:
            blines = self._wrap_text(bullet, self.fonts["body"], self.WIDTH - 200)
            draw.ellipse([80, y + 10, 92, y + 22], fill=self.ACCENT_ORANGE)
            by = y
            for bline in blines:
                draw.text((115, by), bline, font=self.fonts["body"], fill=self.TEXT_PRIMARY)
                by += 38
            y = by + 12

        self._draw_footer(draw, slide)
        return img

    def render_slide_2_problem(self, slide: Slide) -> Image.Image:
        """Slide 2: The Core Engineering Problem / Live Tech Trend."""
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        self._draw_header(draw, slide, 2, canvas=img)

        y = 180
        # Title & Subtitle
        draw.text((70, y), slide.title, font=self.fonts["title_large"], fill=self.TEXT_PRIMARY)
        y += 60
        if slide.subtitle:
            draw.text((70, y), slide.subtitle, font=self.fonts["subtitle"], fill=self.TEXT_MUTED)
            y += 60

        y += 20
        # Problem Cards
        for i, bullet in enumerate(slide.body_bullets):
            card_h = 160
            draw.rounded_rectangle(
                [70, y, self.WIDTH - 70, y + card_h],
                radius=14,
                fill=self.CARD_BG,
                outline=self.CARD_BORDER,
                width=1,
            )
            # Problem index badge
            draw.rounded_rectangle(
                [95, y + 25, 145, y + 65],
                radius=6,
                fill=self.BADGE_BG,
                outline=self.ACCENT_ORANGE,
                width=1,
            )
            draw.text(
                (110, y + 30),
                f"0{i+1}",
                font=self.fonts["body_bold"],
                fill=self.ACCENT_ORANGE,
            )

            # Bullet text
            blines = self._wrap_text(bullet, self.fonts["body"], self.WIDTH - 260)
            by = y + 25
            for bline in blines:
                draw.text((165, by), bline, font=self.fonts["body"], fill=self.TEXT_PRIMARY)
                by += 36

            y += card_h + 24

        self._draw_footer(draw, slide)
        return img

    def render_slide_3_architecture(self, slide: Slide) -> Image.Image:
        """Slide 3: The Architecture Diagram / Code Snippet breakdown."""
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        self._draw_header(draw, slide, 3, canvas=img)

        y = 175
        draw.text((70, y), slide.title, font=self.fonts["title_large"], fill=self.TEXT_PRIMARY)
        y += 55
        if slide.subtitle:
            draw.text((70, y), slide.subtitle, font=self.fonts["subtitle"], fill=self.TEXT_MUTED)
            y += 50

        # Bullets
        for b in slide.body_bullets[:2]:
            draw.text((70, y), f"• {b}", font=self.fonts["body"], fill=self.TEXT_PRIMARY)
            y += 40

        y += 15
        # Code Terminal Card (Mac style window controls)
        terminal_w = self.WIDTH - 140
        terminal_h = 510
        draw.rounded_rectangle(
            [70, y, 70 + terminal_w, y + terminal_h],
            radius=12,
            fill=self.CODE_BG,
            outline=self.CARD_BORDER,
            width=1,
        )

        # Terminal Header Bar
        draw.line([(70, y + 42), (70 + terminal_w, y + 42)], fill=self.CARD_BORDER, width=1)
        # Window dots
        draw.ellipse([92, y + 15, 106, y + 29], fill=(255, 95, 86))    # Red
        draw.ellipse([114, y + 15, 128, y + 29], fill=(255, 189, 46))  # Yellow
        draw.ellipse([136, y + 15, 150, y + 29], fill=(39, 201, 63))   # Green
        draw.text((terminal_w // 2 - 20, y + 12), "dataLayer_setup.js", font=self.fonts["small"], fill=self.TEXT_MUTED)

        # Code lines
        code_lines = (slide.code_snippet or "# Production Architecture Code").split("\n")
        cy = y + 60
        for i, line in enumerate(code_lines[:14]):
            # Line number
            draw.text((95, cy), f"{i+1:2d}", font=self.fonts["code"], fill=(70, 78, 90))
            # Basic syntax coloring based on tokens
            color = self.TEXT_PRIMARY
            if line.strip().startswith("#"):
                color = self.TEXT_MUTED
            elif any(k in line for k in ["import ", "from ", "def ", "class ", "with ", "return "]):
                color = self.ACCENT_PURPLE
            elif any(k in line for k in ["StateGraph", "SqliteSaver", "AgentState", "compile"]):
                color = self.ACCENT_BLUE
            elif "'" in line or '"' in line:
                color = (165, 214, 255)

            draw.text((140, cy), line, font=self.fonts["code"], fill=color)
            cy += 31

        self._draw_footer(draw, slide)
        return img

    def render_slide_4_roi(self, slide: Slide) -> Image.Image:
        """Slide 4: Business Value & Measurable ROI (Bridging Tech & Marketing)."""
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        self._draw_header(draw, slide, 4, canvas=img)

        y = 180
        draw.text((70, y), slide.title, font=self.fonts["title_large"], fill=self.TEXT_PRIMARY)
        y += 55
        if slide.subtitle:
            draw.text((70, y), slide.subtitle, font=self.fonts["subtitle"], fill=self.TEXT_MUTED)
            y += 60

        # Highlight bullet
        for b in slide.body_bullets[:2]:
            draw.text((70, y), f"✓ {b}", font=self.fonts["body"], fill=self.TEXT_PRIMARY)
            y += 44

        y += 30
        # Metrics Grid (1x3 or 2x2 cards)
        metrics = slide.metrics or []
        card_w = (self.WIDTH - 140 - (len(metrics) - 1) * 20) // max(1, len(metrics))
        card_h = 240

        colors = [self.ACCENT_BLUE, self.ACCENT_GREEN, self.ACCENT_ORANGE]

        for i, m in enumerate(metrics):
            cx = 70 + i * (card_w + 20)
            col = colors[i % len(colors)]

            draw.rounded_rectangle(
                [cx, y, cx + card_w, y + card_h],
                radius=14,
                fill=self.CARD_BG,
                outline=self.CARD_BORDER,
                width=1,
            )

            # Top accent bar
            draw.rounded_rectangle([cx, y, cx + card_w, y + 8], radius=4, fill=col)

            # Value
            val_bbox = self.fonts["metric_val"].getbbox(m.value)
            val_w = val_bbox[2] - val_bbox[0]
            draw.text((cx + 30, y + 45), m.value, font=self.fonts["metric_val"], fill=col)

            # Label
            draw.text((cx + 30, y + 130), m.label, font=self.fonts["body_bold"], fill=self.TEXT_PRIMARY)

            # Subtext
            if m.subtext:
                draw.text((cx + 30, y + 175), m.subtext, font=self.fonts["small"], fill=self.TEXT_MUTED)

        self._draw_footer(draw, slide)
        return img

    def render_slide_5_checklist(self, slide: Slide) -> Image.Image:
        """Slide 5: Implementation Checklist + Tipu Sultan Author Authority Card."""
        img = Image.new("RGB", (self.WIDTH, self.HEIGHT), self.BG_COLOR)
        draw = ImageDraw.Draw(img)
        self._draw_header(draw, slide, 5, canvas=img)

        y = 155
        draw.text((70, y), slide.title, font=self.fonts["title_large"], fill=self.TEXT_PRIMARY)
        y += 55
        if slide.subtitle:
            draw.text((70, y), slide.subtitle, font=self.fonts["body"], fill=self.TEXT_MUTED)
            y += 50

        # Checklist Items Card
        items = slide.body_bullets or [
            "Deploy custom domain CNAME record pointing to GTM Server Container.",
            "Configure unique event_id generation across both browser and server tags.",
            "Hash user email and phone with SHA-256 for Advanced Matching parameters.",
            "Audit live signals using Meta Events Manager Test Events tool."
        ]

        card_y = y
        card_h = len(items) * 54 + 20
        draw.rounded_rectangle(
            [70, card_y, self.WIDTH - 70, card_y + card_h],
            radius=14,
            fill=self.CARD_BG,
            outline=self.CARD_BORDER,
            width=1,
        )

        iy = card_y + 20
        for item in items:
            draw.ellipse([105, iy + 6, 119, iy + 20], fill=self.ACCENT_GREEN)
            draw.text((135, iy), item, font=self.fonts["body"], fill=self.TEXT_PRIMARY)
            iy += 54

        # Author Authority Profile Card (Tipu Sultan Brand Identity)
        auth_y = card_y + card_h + 30
        auth_h = 340
        draw.rounded_rectangle(
            [70, auth_y, self.WIDTH - 70, auth_y + auth_h],
            radius=16,
            fill=self.CARD_BG,
            outline=self.ACCENT_BLUE,
            width=2,
        )

        # Large Circular Avatar of Tipu Sultan
        avatar_lg = self._get_avatar(124)
        if avatar_lg:
            img.paste(avatar_lg, (105, auth_y + 30), mask=avatar_lg)

        # Author Name & Verified Badge
        draw.text((255, auth_y + 35), "TIPU SULTAN", font=self.fonts["auth_name"], fill=self.TEXT_PRIMARY)
        v_cx, v_cy = 500, auth_y + 55
        draw.ellipse([v_cx - 13, v_cy - 13, v_cx + 13, v_cy + 13], fill=self.ACCENT_BLUE)
        draw.line([(v_cx - 6, v_cy), (v_cx - 2, v_cy + 4), (v_cx + 5, v_cy - 5)], fill=self.BG_COLOR, width=3)

        # Author Role & Specialty
        draw.text((255, auth_y + 85), "AI & Data-Driven Growth Architect", font=self.fonts["auth_role"], fill=self.ACCENT_BLUE)
        draw.text((255, auth_y + 120), "Web Analytics  •  Meta CAPI  •  Server-Side Tracking Specialist", font=self.fonts["auth_sub"], fill=self.TEXT_MUTED)

        # Divider line inside card
        draw.line([(105, auth_y + 185), (self.WIDTH - 105, auth_y + 185)], fill=self.CARD_BORDER, width=1)

        # Value Sentence
        draw.text((105, auth_y + 205), "Empowering eCommerce brands to recover lost ad revenue & scale with AI.", font=self.fonts["body"], fill=self.TEXT_PRIMARY)

        # Follow & Save Action Pill (Zero external URL)
        draw.rounded_rectangle(
            [105, auth_y + 250, self.WIDTH - 105, auth_y + 315],
            radius=12,
            fill=self.BADGE_BG,
            outline=self.ACCENT_BLUE,
            width=1,
        )
        cta_text = "Save This Blueprint  •  Follow Tipu Sultan for Daily Tracking Architecture"
        cta_bbox = self.fonts["cta"].getbbox(cta_text)
        cta_w = cta_bbox[2] - cta_bbox[0]
        draw.text((105 + (self.WIDTH - 210 - cta_w) // 2, auth_y + 268), cta_text, font=self.fonts["cta"], fill=self.ACCENT_BLUE)

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
                # Fallback to Pillow if PyMuPDF fails at runtime
                images[0].save(pdf_path, "PDF", resolution=150.0, save_all=True, append_images=images[1:])
        else:
            # Native high-resolution Pillow PDF compilation
            images[0].save(pdf_path, "PDF", resolution=150.0, save_all=True, append_images=images[1:])

        return png_paths, pdf_path
