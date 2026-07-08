# -*- coding: utf-8 -*-
# Oramuje syrove demo snimky (_raw/) do Google Play store screenshots.
# navy pozadi + titulek + zaobleny snimek + stin. Telefon 1080x2160 (2:1 MAX!), tablet 1600x2560.
# Spusteni: python docs/google_play_grafika/frame_screenshots.py   (po capture_demo.mjs)
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SH = os.path.join(HERE, "_raw")
OUT = HERE
F = "C:/Windows/Fonts/"

PHONE = [
    ("ph_aplikace.png", "Všechny firemní moduly", "docházka, lidé, výroba i AI na jednom místě"),
    ("ph_dochazka.png", "Píchni docházku z mobilu", "zakázka, činnost a Makat jedním klikem"),
    ("ph_tyden.png",    "Přehled tvé docházky",    "plán vs. realita, týden po týdnu"),
    ("ph_napoveda.png", "Vše po ruce s průvodcem", "hlasový návod krok za krokem"),
    ("ph_ukoly.png",    "Úkoly a oznámení",        "nic ti neuteče"),
]
TAB = [PHONE[0], PHONE[1], PHONE[3]]

def bg_gradient(W, H):
    img = Image.new("RGB", (W, H)); px = img.load()
    c0=(0x0a,0x15,0x22); c1=(0x11,0x22,0x33)
    for y in range(H):
        t=y/(H-1); r=int(c0[0]+(c1[0]-c0[0])*t); g=int(c0[1]+(c1[1]-c0[1])*t); b=int(c0[2]+(c1[2]-c0[2])*t)
        for x in range(W): px[x,y]=(r,g,b)
    return img

def rounded(im, rad):
    m=Image.new("L", im.size, 0); ImageDraw.Draw(m).rounded_rectangle((0,0,im.size[0]-1,im.size[1]-1),radius=rad,fill=255)
    out=im.convert("RGBA"); out.putalpha(m); return out

def center(draw,cx,y,text,font,fill): w=draw.textlength(text,font=font); draw.text((cx-w/2,y),text,font=font,fill=fill)

def make(src,title,sub,W,H,tsz,ssz,top,out_path):
    canvas=bg_gradient(W,H).convert("RGBA"); d=ImageDraw.Draw(canvas)
    tf=ImageFont.truetype(F+"segoeuib.ttf",tsz); sf=ImageFont.truetype(F+"segoeui.ttf",ssz)
    center(d,W//2,int(top*0.30),title,tf,(255,255,255,255))
    center(d,W//2,int(top*0.30)+tsz+18,sub,sf,(88,211,160,255))
    shot=Image.open(os.path.join(SH,src)).convert("RGB")
    aw,ah=W-116,H-top-60; sc=min(aw/shot.width,ah/shot.height); nw,nh=int(shot.width*sc),int(shot.height*sc)
    shot=rounded(shot.resize((nw,nh),Image.LANCZOS),38)
    br=Image.new("RGBA",(nw,nh),(0,0,0,0)); ImageDraw.Draw(br).rounded_rectangle((0,0,nw-1,nh-1),radius=38,outline=(70,90,110,180),width=2)
    x=(W-nw)//2; y=top+(ah-nh)//2
    sh=Image.new("RGBA",canvas.size,(0,0,0,0)); ImageDraw.Draw(sh).rounded_rectangle((x,y+10,x+nw,y+nh+10),radius=38,fill=(0,0,0,120))
    canvas=Image.alpha_composite(canvas,sh.filter(ImageFilter.GaussianBlur(24)))
    canvas.alpha_composite(shot,(x,y)); canvas.alpha_composite(br,(x,y))
    canvas.convert("RGB").save(out_path,quality=95); print("saved",os.path.basename(out_path),f"{W}x{H}")

for i,(s,t,su) in enumerate(PHONE,1): make(s,t,su,1080,2160,60,36,300,os.path.join(OUT,f"play_phone_{i}.png"))
for i,(s,t,su) in enumerate(TAB,1):   make(s,t,su,1600,2560,76,44,380,os.path.join(OUT,f"play_tablet_{i}.png"))
print("HOTOVO — pak: python scripts/play_api_upload.py screenshots")
