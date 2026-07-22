#!/usr/bin/env python3
"""
Build the Windpack sponsorship packet (assets/pdfs/sponsors.pdf).

Run from the repo root:  python tools/make_sponsors_pdf.py

Everything you are likely to edit (copy, tier pricing, budget figures, the
company list) lives in the CONTENT block near the top. Company logos are
optional: drop a PNG named after the slug into tools/logos/ (for example
tools/logos/ge-vernova.png) and it will be used automatically. Without a
file, the company name is drawn as clean type instead.
"""

import os
import sys
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG = os.path.join(ROOT, "images")
COMP = os.path.join(IMG, "competition")
LOGO_DIR = os.path.join(ROOT, "tools", "logos")
OUT = os.path.join(ROOT, "assets", "pdfs", "sponsors.pdf")
TMP = os.path.join(ROOT, "tools", "_tmp")

# --------------------------------------------------------------------------
# Brand (matches assets/css/style.css)
# --------------------------------------------------------------------------
RED = (0.80, 0.00, 0.00)          # #cc0000
INK = (0.086, 0.086, 0.086)       # #161616
INK_SOFT = (0.227, 0.227, 0.227)  # #3a3a3a
MUTED = (0.42, 0.42, 0.44)        # #6c6c70
LINE = (0.906, 0.906, 0.914)      # #e7e7e9
BG_ALT = (0.965, 0.965, 0.969)    # #f6f6f7
DARK = (0.051, 0.051, 0.059)      # #0d0d0f
WHITE = (1, 1, 1)

W, H = 612.0, 792.0   # US Letter
M = 54.0              # page margin

# --------------------------------------------------------------------------
# CONTENT  -- edit here
# --------------------------------------------------------------------------
SEASON = "2026-2027"

TIERS = [
    # (name, label, placeholder amount)
    ("Breeze",   "Supporter",    "$250+"),
    ("Gust",     "Team Partner", "$1,000+"),
    ("Tailwind", "Lead Sponsor", "$2,500+"),
]

# Benefit rows: (label, breeze, gust, tailwind)
BENEFITS = [
    ("Logo on windpack.club",              1, 1, 1),
    ("Social media thank-you post",        1, 1, 1),
    ("End-of-season recap report",         1, 1, 1),
    ("Logo on team apparel",               0, 1, 1),
    ("Logo on competition banner",         0, 1, 1),
    ("Access to member resume book",       0, 1, 1),
    ("Premium logo on the turbine",        0, 0, 1),
    ("Dedicated info session / lab visit", 0, 0, 1),
    ("First access at recruiting events",  0, 0, 1),
]

# Budget: figures are placeholders. Replace the amounts before sending.
BUDGET = [
    ("Materials & fabrication", "$X,XXX", "Composites, filament, raw stock, and electronics for every prototype and revision."),
    ("Tools & equipment",       "$X,XXX", "Test rigs, sensors, and shop equipment so the team can build and validate in-house."),
    ("Travel to nationals",     "$X,XXX", "Registration, transport, and lodging to get the full team to the competition."),
    ("Outreach & operations",   "$X,XXX", "Community events, printing, and the day-to-day costs of running the team."),
]
BUDGET_TOTAL = "$XX,XXX"

# Where members have gone to work. Add entries here as alumni land roles.
# slug maps to tools/logos/<slug>.png when you have a real logo file.
COMPANIES = [
    ("GE Vernova",    "ge-vernova"),
    ("SAS Institute", "sas-institute"),
]
OPEN_SLOTS = 4   # empty tiles shown as room for more

CONTACT = {
    "email": "windpack-org@ncsu.edu",
    "site": "windpack.club",
    "instagram": "@ncstatewind",
    "linkedin": "linkedin.com/company/wolfpack-wind",
    "address": "Fitts-Woolard Hall, 1840 Entrepreneur Dr, Raleigh, NC 27606",
}

# --------------------------------------------------------------------------
# Fonts
# --------------------------------------------------------------------------
def register_fonts():
    """Use Arial / Arial Black when present, else fall back to Helvetica."""
    fdir = r"C:\Windows\Fonts"
    want = {
        "WP-Regular": "arial.ttf",
        "WP-Bold": "arialbd.ttf",
        "WP-Italic": "ariali.ttf",
        "WP-Black": "ariblk.ttf",
    }
    ok = {}
    for name, fn in want.items():
        p = os.path.join(fdir, fn)
        if os.path.exists(p):
            try:
                pdfmetrics.registerFont(TTFont(name, p))
                ok[name] = True
            except Exception:
                pass
    return {
        "reg": "WP-Regular" if "WP-Regular" in ok else "Helvetica",
        "bold": "WP-Bold" if "WP-Bold" in ok else "Helvetica-Bold",
        "italic": "WP-Italic" if "WP-Italic" in ok else "Helvetica-Oblique",
        "black": "WP-Black" if "WP-Black" in ok else "Helvetica-Bold",
    }

F = register_fonts()

# --------------------------------------------------------------------------
# Drawing helpers
# --------------------------------------------------------------------------
def fit_crop(src, w_pt, h_pt, dpi=150, bias=0.5):
    """Cover-crop to the target aspect ratio. bias 0=top, .5=centre, 1=bottom.
    Group shots usually want bias < .5 so heads are not cut off."""
    os.makedirs(TMP, exist_ok=True)
    im = Image.open(src).convert("RGB")
    target = w_pt / h_pt
    iw, ih = im.size
    if iw / ih > target:
        nw = int(ih * target)
        left = int((iw - nw) * 0.5)
        im = im.crop((left, 0, left + nw, ih))
    else:
        nh = int(iw / target)
        top = int((ih - nh) * bias)
        im = im.crop((0, top, iw, top + nh))
    im = im.resize((max(1, int(w_pt / 72 * dpi)), max(1, int(h_pt / 72 * dpi))), Image.LANCZOS)
    key = "%s_%dx%d_%d" % (os.path.splitext(os.path.basename(src))[0], w_pt, h_pt, bias * 100)
    out = os.path.join(TMP, "c_%s.jpg" % key)
    im.save(out, "JPEG", quality=88)
    return out


def photo(c, src, x, y, w, h, radius=8, bias=0.5):
    """Draw a cover-cropped photo with rounded corners."""
    path = fit_crop(src, w, h, bias=bias)
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, w, h, radius)
    c.clipPath(p, stroke=0, fill=0)
    c.drawImage(ImageReader(path), x, y, w, h, mask="auto")
    c.restoreState()


def wrap(text, font, size, maxw):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if pdfmetrics.stringWidth(t, font, size) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def para(c, text, x, y, maxw, font=None, size=10.2, leading=15.2, color=INK_SOFT):
    font = font or F["reg"]
    c.setFillColorRGB(*color)
    c.setFont(font, size)
    for ln in wrap(text, font, size, maxw):
        c.drawString(x, y, ln)
        y -= leading
    return y


def tracked(c, text, x, y, font, size, tracking, color):
    """Draw letterspaced text (the red kicker labels)."""
    c.setFillColorRGB(*color)
    c.setFont(font, size)
    for ch in text:
        c.drawString(x, y, ch)
        x += pdfmetrics.stringWidth(ch, font, size) + tracking
    return x


def tracked_width(text, font, size, tracking):
    return sum(pdfmetrics.stringWidth(ch, font, size) + tracking for ch in text) - tracking


def wordmark(c, x, y, size, light=False):
    """WINDPACK wordmark: 'WIND' in ink/white, 'PACK' in red. Returns width."""
    a, b = "WIND", "PACK"
    c.setFont(F["black"], size)
    c.setFillColorRGB(*(WHITE if light else INK))
    c.drawString(x, y, a)
    wa = pdfmetrics.stringWidth(a, F["black"], size)
    c.setFillColorRGB(*RED)
    c.drawString(x + wa, y, b)
    return wa + pdfmetrics.stringWidth(b, F["black"], size)


def card(c, x, y, w, h, radius=8, fill=None, border=True):
    if fill:
        c.setFillColorRGB(*fill)
    if border:
        c.setStrokeColorRGB(*LINE)
        c.setLineWidth(0.9)
    c.roundRect(x, y, w, h, radius, stroke=1 if border else 0, fill=1 if fill else 0)


def card_accent(c, x, y, w, h, radius=8, ah=3.4):
    """Red top accent clipped to the card's rounded corners."""
    c.saveState()
    p = c.beginPath()
    p.roundRect(x, y, w, h, radius)
    c.clipPath(p, stroke=0, fill=0)
    c.setFillColorRGB(*RED)
    c.rect(x, y + h - ah, w, ah, stroke=0, fill=1)
    c.restoreState()


def check(c, x, y, on):
    if on:
        c.setFillColorRGB(*RED)
        c.circle(x, y + 3, 5.2, stroke=0, fill=1)
        c.setStrokeColorRGB(1, 1, 1)
        c.setLineWidth(1.35)
        c.setLineCap(1)
        p = c.beginPath()
        p.moveTo(x - 2.5, y + 3.1)
        p.lineTo(x - 0.7, y + 1.3)
        p.lineTo(x + 2.6, y + 5.2)
        c.drawPath(p, stroke=1, fill=0)
    else:
        c.setStrokeColorRGB(0.80, 0.80, 0.82)
        c.setLineWidth(1.1)
        c.line(x - 3.2, y + 3, x + 3.2, y + 3)


def page_frame(c, kicker=None, title=None):
    """Standard interior page: red top rule, logo + wordmark, kicker, title."""
    c.setFillColorRGB(*RED)
    c.rect(0, H - 7, W, 7, stroke=0, fill=1)

    y = H - 7 - 34
    lg = os.path.join(IMG, "logo-black.png")
    lw = 0
    if os.path.exists(lg):
        im = Image.open(lg)
        lh = 26.0
        lw = lh * im.size[0] / im.size[1]
        c.drawImage(ImageReader(lg), M, y - lh + 6, lw, lh, mask="auto")
    wordmark(c, M + lw + 8, y - 3, 13.5)

    c.setFillColorRGB(*MUTED)
    c.setFont(F["reg"], 8)
    c.drawRightString(W - M, y - 2, "%s Sponsorship Packet" % SEASON)
    y -= 48

    if kicker:
        tracked(c, kicker.upper(), M, y, F["bold"], 8.4, 1.7, RED)
        y -= 20
    if title:
        c.setFillColorRGB(*INK)
        c.setFont(F["black"], 25)
        c.drawString(M, y - 18, title)
        y -= 34
        c.setStrokeColorRGB(*RED)
        c.setLineWidth(2.6)
        c.line(M, y, M + 46, y)
        y -= 22
    return y


def page_footer(c, page_no):
    c.setStrokeColorRGB(*LINE)
    c.setLineWidth(0.7)
    c.line(M, 44, W - M, 44)
    c.setFillColorRGB(*MUTED)
    c.setFont(F["reg"], 8)
    c.drawString(M, 32, "windpack.club")
    c.drawCentredString(W / 2, 32, "NC State Collegiate Wind Competition")
    c.drawRightString(W - M, 32, str(page_no))


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------
def page_cover(c):
    photo(c, os.path.join(COMP, "hero-team.jpg"), 0, 0, W, H, radius=0, bias=0.42)
    c.setFillColorRGB(*DARK)
    c.setFillAlpha(0.70)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillAlpha(1)

    c.setFillColorRGB(*RED)
    c.rect(0, H - 10, W, 10, stroke=0, fill=1)
    c.rect(0, 0, W, 10, stroke=0, fill=1)

    lg = os.path.join(IMG, "logo-outline.png")
    lw = 0
    if os.path.exists(lg):
        im = Image.open(lg)
        lh = 66.0
        lw = lh * im.size[0] / im.size[1]
        c.drawImage(ImageReader(lg), M, H - 158, lw, lh, mask="auto")
    wordmark(c, M + lw + 12, H - 135, 30, light=True)

    y = 452
    tracked(c, "NC STATE UNIVERSITY", M, y, F["bold"], 10, 2.6, WHITE)
    y -= 58
    c.setFillColorRGB(*WHITE)
    c.setFont(F["black"], 50)
    c.drawString(M, y, "SPONSORSHIP")
    c.setFillColorRGB(*RED)
    c.drawString(M, y - 52, "PACKET")

    c.setStrokeColorRGB(*RED)
    c.setLineWidth(3.4)
    c.line(M, y - 78, M + 96, y - 78)

    c.setFillColorRGB(*WHITE)
    c.setFont(F["bold"], 15)
    c.drawString(M, y - 108, "%s Season" % SEASON)
    c.setFillColorRGB(0.86, 0.86, 0.88)
    c.setFont(F["reg"], 11.5)
    c.drawString(M, y - 128, "Collegiate Wind Competition")

    c.setFillColorRGB(*WHITE)
    c.setFont(F["bold"], 10.5)
    c.drawString(M, 46, "windpack.club")
    c.setFillColorRGB(0.80, 0.80, 0.83)
    c.setFont(F["reg"], 10.5)
    c.drawRightString(W - M, 46, CONTACT["email"])
    c.showPage()


def page_who(c):
    y = page_frame(c, "Who we are", "NC State's wind energy team")
    colw = W - 2 * M

    y = para(c,
        "Windpack is a student-led team at NC State University competing in the Collegiate Wind "
        "Competition. Founded in 2025, we design, build, and test a complete wind turbine from "
        "scratch, and we build the full business case for a real wind farm alongside it.",
        M, y, colw)
    y -= 6
    y = para(c,
        "The competition is run by the non-profit REpowering Schools and draws university teams from "
        "across the country. Our members come from across engineering and beyond, and no prior "
        "experience is required to join. Students learn fabrication, power electronics, controls, "
        "wind resource analysis, and the project management that ties it together.",
        M, y, colw)

    y -= 16
    ph = 196
    photo(c, os.path.join(COMP, "about-team.jpg"), M, y - ph, colw, ph, bias=0.4)
    y -= ph + 30

    tracked(c, "THREE SPECIALIZED TEAMS", M, y, F["bold"], 8.4, 1.7, RED)
    y -= 20

    teams = [
        ("Mechanical", "Blade aerodynamics, drivetrain, hub, and the structural design that has to survive the wind tunnel."),
        ("Electrical", "Power electronics, generator integration, safety load circuits, and the control system."),
        ("Project Development", "Site selection, wind resource assessment, environmental review, and financials."),
    ]
    cw = (colw - 2 * 14) / 3.0
    ch = 116
    for i, (name, body) in enumerate(teams):
        x = M + i * (cw + 14)
        card(c, x, y - ch, cw, ch, fill=BG_ALT)
        card_accent(c, x, y - ch, cw, ch)
        c.setFillColorRGB(*INK)
        c.setFont(F["bold"], 11.6)
        c.drawString(x + 14, y - 28, name)
        para(c, body, x + 14, y - 46, cw - 28, size=8.9, leading=12.4, color=MUTED)
    y -= ch + 26

    stats = [("3", "Specialized teams"), ("25+", "Active members"),
             ("2025", "Founded"), ("1st", "Season complete")]
    sw = (colw - 3 * 12) / 4.0
    sh = 64
    for i, (num, label) in enumerate(stats):
        x = M + i * (sw + 12)
        card(c, x, y - sh, sw, sh)
        c.setFillColorRGB(*RED)
        c.setFont(F["black"], 21)
        c.drawCentredString(x + sw / 2, y - 32, num)
        c.setFillColorRGB(*MUTED)
        c.setFont(F["reg"], 8)
        c.drawCentredString(x + sw / 2, y - 50, label)

    page_footer(c, 2)
    c.showPage()


def page_competition(c):
    y = page_frame(c, "The competition", "What we compete in")
    colw = W - 2 * M

    y = para(c,
        "The Collegiate Wind Competition challenges student teams to design an innovative wind energy "
        "solution end to end. Teams are scored across three connected contests, so it takes engineers, "
        "analysts, and communicators working together. Windpack competes in all three.",
        M, y, colw)
    y -= 18

    contests = [
        ("Turbine Contest",
         "Design and build a scale turbine, then prove it in the wind tunnel. Judged on power performance, "
         "control, durability, and a full technical design report."),
        ("Project Development",
         "Plan a real wind farm: site selection, wind resource assessment, environmental and community "
         "review, financial modeling, and a complete development proposal."),
        ("Connection Creation",
         "Engage the community and industry through outreach, sharing the team's work and building "
         "support for wind energy beyond campus."),
    ]
    for name, body in contests:
        ch = 62
        card(c, M, y - ch, colw, ch, fill=BG_ALT)
        c.saveState()
        p = c.beginPath()
        p.roundRect(M, y - ch, colw, ch, 8)
        c.clipPath(p, stroke=0, fill=0)
        c.setFillColorRGB(*RED)
        c.rect(M, y - ch, 3.4, ch, stroke=0, fill=1)
        c.restoreState()
        c.setFillColorRGB(*INK)
        c.setFont(F["bold"], 12)
        c.drawString(M + 18, y - 22, name)
        para(c, body, M + 18, y - 38, colw - 36, size=9.1, leading=12.6, color=MUTED)
        y -= ch + 12

    y -= 10
    ph = 168
    gap = 12
    hw = (colw - gap) / 2
    photo(c, os.path.join(COMP, "comp-present2.jpg"), M, y - ph, hw, ph, bias=0.45)
    photo(c, os.path.join(COMP, "ig-1.jpg"), M + hw + gap, y - ph, hw, ph, bias=0.30)
    y -= ph + 26

    card(c, M, y - 74, colw, 74)
    c.setFillColorRGB(*INK)
    c.setFont(F["bold"], 11.6)
    c.drawString(M + 18, y - 26, "Our first season")
    para(c,
        "Windpack competed at nationals in May 2026, presenting to industry judges, running the turbine, "
        "and defending a full project development plan in our debut appearance.",
        M + 18, y - 44, colw - 36, size=9.2, leading=12.6, color=MUTED)

    page_footer(c, 3)
    c.showPage()


def page_budget(c):
    y = page_frame(c, "Where it goes", "How your support is used")
    colw = W - 2 * M

    y = para(c,
        "Windpack is funded almost entirely by sponsorship. Every contribution, financial or in-kind, "
        "goes directly into the team: the parts we machine, the equipment we test on, and getting "
        "students to the national competition.",
        M, y, colw)
    y -= 18

    for name, amt, body in BUDGET:
        rh = 56
        card(c, M, y - rh, colw, rh)
        c.setFillColorRGB(*INK)
        c.setFont(F["bold"], 11.4)
        c.drawString(M + 16, y - 21, name)
        c.setFillColorRGB(*RED)
        c.setFont(F["black"], 14)
        c.drawRightString(W - M - 16, y - 22, amt)
        para(c, body, M + 16, y - 36, colw - 130, size=8.8, leading=12, color=MUTED)
        y -= rh + 10

    y -= 6
    card(c, M, y - 46, colw, 46, fill=RED, border=False)
    c.setFillColorRGB(*WHITE)
    c.setFont(F["bold"], 12)
    c.drawString(M + 16, y - 28, "Estimated season total")
    c.setFont(F["black"], 17)
    c.drawRightString(W - M - 16, y - 30, BUDGET_TOTAL)
    y -= 46 + 20

    c.setFillColorRGB(*MUTED)
    c.setFont(F["italic"], 8.6)
    c.drawString(M, y, "In-kind support counts too: materials, machining time, components, and software licenses.")
    y -= 20

    ph = y - 66
    if ph > 110:
        photo(c, os.path.join(COMP, "ig-8.jpg"), M, y - ph, colw, ph, bias=0.30)

    page_footer(c, 4)
    c.showPage()


def page_outcomes(c):
    """Where our members have gone to work."""
    y = page_frame(c, "Talent pipeline", "Where our members go")
    colw = W - 2 * M

    y = para(c,
        "Sponsoring Windpack puts your brand in front of students who are already doing the work. Our "
        "members graduate with hands-on experience in fabrication, power electronics, controls, and "
        "energy project development, and they go on to roles across the energy and technology industry.",
        M, y, colw)
    y -= 4
    y = para(c, "Members of our team have gone on to work at:",
             M, y, colw, font=F["bold"], color=INK)
    y -= 12

    tiles = [(n, s) for n, s in COMPANIES] + [(None, None)] * OPEN_SLOTS
    cols, gap = 3, 14
    tw = (colw - gap * (cols - 1)) / cols
    th = 84
    for i, (name, slug) in enumerate(tiles):
        r, cidx = divmod(i, cols)
        x = M + cidx * (tw + gap)
        ty = y - r * (th + gap) - th
        if name:
            card(c, x, ty, tw, th, fill=WHITE)
            logo_path = os.path.join(LOGO_DIR, "%s.png" % slug)
            if os.path.exists(logo_path):
                im = Image.open(logo_path)
                maxw, maxh = tw - 30, th - 30
                sc = min(maxw / im.size[0], maxh / im.size[1])
                lw, lh = im.size[0] * sc, im.size[1] * sc
                c.drawImage(ImageReader(logo_path), x + (tw - lw) / 2, ty + (th - lh) / 2,
                            lw, lh, mask="auto")
            else:
                c.setFillColorRGB(*INK)
                c.setFont(F["bold"], 12.5)
                c.drawCentredString(x + tw / 2, ty + th / 2 + 3, name)
                c.setFillColorRGB(*MUTED)
                c.setFont(F["reg"], 7.2)
                c.drawCentredString(x + tw / 2, ty + th / 2 - 12, "[ logo ]")
        else:
            c.setStrokeColorRGB(0.84, 0.84, 0.86)
            c.setLineWidth(0.9)
            c.setDash(3, 3)
            c.roundRect(x, ty, tw, th, 8, stroke=1, fill=0)
            c.setDash()
            c.setFillColorRGB(0.72, 0.72, 0.75)
            c.setFont(F["reg"], 8.6)
            c.drawCentredString(x + tw / 2, ty + th / 2 - 2, "Room to grow")

    rows = (len(tiles) + cols - 1) // cols
    y -= rows * (th + gap) + 10

    c.setFillColorRGB(*MUTED)
    c.setFont(F["italic"], 8.4)
    c.drawString(M, y, "Company names reflect where team members have gone to work. This list grows every year.")
    y -= 26

    tracked(c, "WHAT SPONSORS GET ACCESS TO", M, y, F["bold"], 8.4, 1.7, RED)
    y -= 20

    perks = [
        ("Recruiting access", "Resume book access and first look at members entering the workforce."),
        ("On-campus presence", "Info sessions and lab visits with a team that already builds hardware."),
        ("Brand visibility", "Logo on the turbine, apparel, competition banner, and windpack.club."),
    ]
    cw = (colw - 2 * 14) / 3.0
    ch = 104
    for i, (name, body) in enumerate(perks):
        x = M + i * (cw + 14)
        card(c, x, y - ch, cw, ch, fill=BG_ALT)
        card_accent(c, x, y - ch, cw, ch)
        c.setFillColorRGB(*INK)
        c.setFont(F["bold"], 11.2)
        c.drawString(x + 13, y - 28, name)
        para(c, body, x + 13, y - 45, cw - 26, size=8.7, leading=12.2, color=MUTED)
    y -= ch + 24

    # closing band fills the remaining space with something useful
    bh = min(78.0, max(0.0, y - 62))
    if bh > 50:
        card(c, M, y - bh, colw, bh, fill=RED, border=False)
        c.setFillColorRGB(*WHITE)
        c.setFont(F["black"], 14)
        c.drawString(M + 20, y - 30, "Hiring engineers? Start here.")
        c.setFont(F["reg"], 9.6)
        c.setFillColorRGB(0.98, 0.88, 0.88)
        c.drawString(M + 20, y - 48, "Partner with us and meet the students building wind hardware at NC State.")
        c.setFillColorRGB(*WHITE)
        c.setFont(F["bold"], 10.4)
        c.drawRightString(W - M - 20, y - 40, CONTACT["email"])

    page_footer(c, 5)
    c.showPage()


def page_tiers(c):
    y = page_frame(c, "Sponsorship levels", "Ways to partner")
    colw = W - 2 * M

    y = para(c,
        "Levels can be met through financial or in-kind support. If none of these fit, reach out and "
        "we will tailor a partnership that works for your organization.",
        M, y, colw)
    y -= 16

    labelw = 214.0
    tw = (colw - labelw) / 3.0
    hh = 54
    c.setFillColorRGB(*INK)
    c.rect(M, y - hh, colw, hh, stroke=0, fill=1)
    for i, (name, label, amt) in enumerate(TIERS):
        cx = M + labelw + i * tw + tw / 2
        c.setFillColorRGB(*WHITE)
        c.setFont(F["black"], 12.5)
        c.drawCentredString(cx, y - 21, name)
        c.setFillColorRGB(0.98, 0.42, 0.42)
        c.setFont(F["bold"], 9)
        c.drawCentredString(cx, y - 34, amt)
        c.setFillColorRGB(0.72, 0.72, 0.76)
        c.setFont(F["reg"], 7.4)
        c.drawCentredString(cx, y - 46, label)
    y -= hh

    rh = 26.5
    for i, (label, b, g, t) in enumerate(BENEFITS):
        if i % 2 == 0:
            c.setFillColorRGB(*BG_ALT)
            c.rect(M, y - rh, colw, rh, stroke=0, fill=1)
        c.setFillColorRGB(*INK_SOFT)
        c.setFont(F["reg"], 9.4)
        c.drawString(M + 14, y - 17, label)
        for j, on in enumerate((b, g, t)):
            check(c, M + labelw + j * tw + tw / 2, y - 20, on)
        y -= rh

    c.setStrokeColorRGB(*LINE)
    c.setLineWidth(0.9)
    c.rect(M, y, colw, len(BENEFITS) * rh + hh, stroke=1, fill=0)
    for j in range(3):
        x = M + labelw + j * tw
        c.line(x, y, x, y + len(BENEFITS) * rh)
    y -= 26

    notes = [
        ("Recruiting access", "Gust and Tailwind sponsors receive our member resume book each semester."),
        ("Lab visits", "Tailwind sponsors get a dedicated session with the team and a look at the build."),
        ("In-kind welcome", "Materials, machining time, components, and software all count toward a level."),
    ]
    for name, body in notes:
        c.setFillColorRGB(*RED)
        c.circle(M + 3, y + 3.4, 2.6, stroke=0, fill=1)
        c.setFillColorRGB(*INK)
        c.setFont(F["bold"], 9.6)
        c.drawString(M + 14, y, name)
        wpx = pdfmetrics.stringWidth(name, F["bold"], 9.6)
        para(c, body, M + 14 + wpx + 7, y, colw - 30 - wpx, size=9.2, leading=12.4, color=MUTED)
        y -= 22

    y -= 8
    ph = y - 62
    if ph > 110:
        photo(c, os.path.join(COMP, "comp-hall.jpg"), M, y - ph, colw, ph, bias=0.42)

    page_footer(c, 6)
    c.showPage()


def page_contact(c):
    c.setFillColorRGB(*DARK)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.setFillColorRGB(*RED)
    c.rect(0, H - 10, W, 10, stroke=0, fill=1)
    c.rect(0, 0, W, 10, stroke=0, fill=1)

    lg = os.path.join(IMG, "logo-outline.png")
    lw = 0
    if os.path.exists(lg):
        im = Image.open(lg)
        lh = 54.0
        lw = lh * im.size[0] / im.size[1]
        c.drawImage(ImageReader(lg), (W - (lw + 12 + 118)) / 2, H - 126, lw, lh, mask="auto")
    wordmark(c, (W - (lw + 12 + 118)) / 2 + lw + 12, H - 110, 26, light=True)

    y = 596
    kw = tracked_width("LET'S BUILD SOMETHING", F["bold"], 9.4, 2.4)
    tracked(c, "LET'S BUILD SOMETHING", (W - kw) / 2, y, F["bold"], 9.4, 2.4, WHITE)
    y -= 44
    c.setFillColorRGB(*WHITE)
    c.setFont(F["black"], 33)
    c.drawCentredString(W / 2, y, "Partner with the Pack")
    y -= 28
    c.setFillColorRGB(0.80, 0.80, 0.84)
    c.setFont(F["reg"], 10.6)
    for ln in wrap("Your support puts real tools in students' hands and sends NC State to the "
                   "national stage. We would love to talk about what a partnership could look like.",
                   F["reg"], 10.6, 396):
        c.drawCentredString(W / 2, y, ln)
        y -= 15.5

    y -= 30
    rows = [
        ("Email", CONTACT["email"]),
        ("Website", CONTACT["site"]),
        ("Instagram", CONTACT["instagram"]),
        ("LinkedIn", CONTACT["linkedin"]),
    ]
    bw, bh = 392, 42
    bx = (W - bw) / 2
    for label, val in rows:
        c.setFillColorRGB(1, 1, 1)
        c.setFillAlpha(0.075)
        c.roundRect(bx, y - bh + 8, bw, bh - 6, 7, stroke=0, fill=1)
        c.setFillAlpha(1)
        c.setFillColorRGB(0.62, 0.62, 0.67)
        c.setFont(F["bold"], 7.6)
        c.drawString(bx + 18, y - 14, label.upper())
        c.setFillColorRGB(*WHITE)
        c.setFont(F["bold"], 11.2)
        c.drawRightString(bx + bw - 18, y - 14, val)
        y -= bh + 6

    y -= 12
    c.setFillColorRGB(0.60, 0.60, 0.65)
    c.setFont(F["reg"], 8.8)
    c.drawCentredString(W / 2, y, CONTACT["address"])
    y -= 26

    ph = y - 74
    if ph > 90:
        photo(c, os.path.join(COMP, "hero-plaza.jpg"), M, y - ph, W - 2 * M, ph, bias=0.34)

    c.setFillColorRGB(0.72, 0.72, 0.76)
    c.setFont(F["bold"], 9.6)
    c.drawCentredString(W / 2, 40, "Thank you for supporting student engineering at NC State.")
    c.showPage()


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    c = canvas.Canvas(OUT, pagesize=(W, H))
    c.setTitle("Windpack %s Sponsorship Packet" % SEASON)
    c.setAuthor("Windpack - NC State Collegiate Wind Competition")
    c.setSubject("Sponsorship opportunities")

    page_cover(c)
    page_who(c)
    page_competition(c)
    page_budget(c)
    page_outcomes(c)
    page_tiers(c)
    page_contact(c)

    c.save()

    if os.path.isdir(TMP):
        for f in os.listdir(TMP):
            try:
                os.remove(os.path.join(TMP, f))
            except OSError:
                pass
        try:
            os.rmdir(TMP)
        except OSError:
            pass

    print("Wrote %s (%.1f KB)" % (OUT, os.path.getsize(OUT) / 1024.0))


if __name__ == "__main__":
    sys.exit(main())
