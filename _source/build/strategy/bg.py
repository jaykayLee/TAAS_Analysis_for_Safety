# -*- coding: utf-8 -*-
"""발표 자료 배경 이미지 생성(재현 가능, 고정 seed) — 차량 반도체 보안 주제: 칩(다이·핀) + 회로 배선 + 네트워크 노드, 흐리게(blur).
  python3 build/strategy/bg.py → build/_work/bg_dark.jpg(표지·구분), bg_light.jpg(본문, 아주 옅게)
외부 이미지를 쓰지 않는다(저작권·네트워크 없음) — 같은 seed면 같은 그림."""
import os, sys, random, math
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); WORK = os.path.join(os.path.dirname(HERE), "_work"); os.makedirs(WORK, exist_ok=True)
W, H, S = 1920, 1080, 2          # 2배로 그려 줄여서 매끈하게

def traces(draw, rnd, chip, col, n=150, wmin=2, wmax=5):
    cx0, cy0, cx1, cy1 = chip
    for _ in range(n):
        side = rnd.choice("LRTB")
        if side in "LR":
            y = rnd.uniform(cy0 + 20, cy1 - 20); x = cx0 if side == "L" else cx1; dx, dy = (-1 if side == "L" else 1), 0
        else:
            x = rnd.uniform(cx0 + 20, cx1 - 20); y = cy0 if side == "T" else cy1; dx, dy = 0, (-1 if side == "T" else 1)
        pts = [(x, y)]; w = rnd.randint(wmin, wmax) * S
        for seg in range(rnd.randint(2, 5)):
            L = rnd.uniform(60, 420) * S
            x, y = x + dx * L, y + dy * L; pts.append((x, y))
            if rnd.random() < 0.7:                                  # 45° 꺾임 후 원래 축과 직교
                d = rnd.uniform(30, 120) * S; s = rnd.choice((-1, 1))
                if dx: x, y = x + dx * d, y + s * d
                else: x, y = x + s * d, y + dy * d
                pts.append((x, y))
        draw.line(pts, fill=col, width=w, joint="curve")
        r = w * 1.8; ex, ey = pts[-1]; draw.ellipse((ex - r, ey - r, ex + r, ey + r), outline=col, width=max(2, w // 2))

def make(dark=True):
    rnd = random.Random(21434)
    big = (W * S, H * S)
    if dark:
        base = Image.new("RGB", big, (9, 22, 44)); g = ImageDraw.Draw(base)
        for i in range(H * S):                                      # 세로 그라데이션 + 오른쪽 위 빛
            t = i / (H * S); g.line([(0, i), (W * S, i)], fill=(int(9 + 10 * t), int(22 + 14 * t), int(44 + 26 * t)))
    else:
        base = Image.new("RGB", big, (247, 249, 252))
    lay = Image.new("RGBA", big, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    chip = (W * S * 0.60, H * S * 0.22, W * S * 0.86, H * S * 0.78)   # 오른쪽 칩(다이)
    tc = (0, 190, 200, 150) if dark else (23, 55, 94, 26)
    traces(d, rnd, chip, tc)
    x0, y0, x1, y1 = chip
    d.rounded_rectangle(chip, radius=40 * S, outline=(0, 210, 220, 210) if dark else (23, 55, 94, 34), width=6 * S, fill=(10, 40, 70, 200) if dark else (230, 236, 244, 120))
    pad = 70 * S; d.rounded_rectangle((x0 + pad, y0 + pad, x1 - pad, y1 - pad), radius=20 * S, outline=(90, 220, 230, 160) if dark else (23, 55, 94, 30), width=3 * S)
    for k in range(18):                                             # 핀
        for (ax, ay, bx, by) in (((x0 + (k + 1) * (x1 - x0) / 19), y0 - 30 * S, None, None), ((x0 + (k + 1) * (x1 - x0) / 19), y1, None, None)):
            d.rectangle((ax - 6 * S, ay, ax + 6 * S, ay + 30 * S), fill=(0, 200, 210, 170) if dark else (23, 55, 94, 30))
    for k in range(14):
        yy = y0 + (k + 1) * (y1 - y0) / 15
        for xx in (x0 - 30 * S, x1):
            d.rectangle((xx, yy - 6 * S, xx + 30 * S, yy + 6 * S), fill=(0, 200, 210, 170) if dark else (23, 55, 94, 30))
    # 네트워크 노드(왼쪽·위 영역에 흩어진 빛점)
    nodes = [(rnd.uniform(0, W * S * 0.95), rnd.uniform(0, H * S)) for _ in range(46)]
    for i, (ax, ay) in enumerate(nodes):
        for bx, by in nodes[i + 1:]:
            if math.hypot(ax - bx, ay - by) < 230 * S and rnd.random() < 0.55:
                d.line((ax, ay, bx, by), fill=(120, 200, 255, 70) if dark else (23, 55, 94, 16), width=2 * S)
        r = rnd.uniform(4, 10) * S; d.ellipse((ax - r, ay - r, ax + r, ay + r), fill=(150, 225, 255, 160) if dark else (23, 55, 94, 24))
    glow = lay.filter(ImageFilter.GaussianBlur(18 * S))             # 빛 번짐
    out = Image.alpha_composite(Image.alpha_composite(base.convert("RGBA"), glow), lay).convert("RGB")
    out = out.resize((W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(4 if dark else 6))   # 흐리게
    if dark:                                                        # 왼쪽(글자 영역)을 더 어둡게 — 가독성
        sh = Image.new("L", (W, H)); sd = ImageDraw.Draw(sh)
        for x in range(W): sd.line([(x, 0), (x, H)], fill=int(225 * max(0, 1 - x / (W * 0.58)) ** 0.8))
        out = Image.composite(Image.new("RGB", (W, H), (6, 16, 34)), out, sh)
    else:                                                           # 본문: 왼쪽·위를 거의 흰색으로
        sh = Image.new("L", (W, H)); sd = ImageDraw.Draw(sh)
        for x in range(W): sd.line([(x, 0), (x, H)], fill=int(200 * max(0, 1 - x / (W * 0.75))))
        out = Image.composite(Image.new("RGB", (W, H), (250, 251, 253)), out, sh)
        out = Image.blend(out, Image.new("RGB", (W, H), (250, 251, 253)), 0.45)     # 본문은 아주 옅게(내용이 주인공)
    p = os.path.join(WORK, "bg_dark.jpg" if dark else "bg_light.jpg"); out.save(p, quality=88); return p

if __name__ == "__main__":
    print(make(True)); print(make(False))
