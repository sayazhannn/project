import json, math, sys, subprocess, numpy as np, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,S=1280,720,30,3
OW,OH=1920,1080
meta=json.load(open("a/meta.json")); D=meta["durs"]; BEEP=meta["beep_at"]; AFTER=meta["after_at"]
LEAD,PAD=0.15,0.3
starts=[];t=0.0
for d in D: starts.append(t); t+=LEAD+d+PAD
TOTAL=t+0.2
import os
if os.path.exists('scenes.json'):
    _s=json.load(open('scenes.json')); starts=_s['starts']; D=_s['D']; TOTAL=_s['total']
json.dump({"starts":[s+LEAD for s in starts],"total":TOTAL},open("timeline.json","w"))

def font(sz):
    f=ImageFont.truetype("Oswald.ttf",int(sz*S)); f.set_variation_by_name("Bold"); return f
FC={}
def F(sz):
    if sz not in FC: FC[sz]=font(sz)
    return FC[sz]
clamp=lambda x,a=0,b=1:max(a,min(b,x))
def ease(x): x=clamp(x); return 1-(1-x)**3
def sm(x): x=clamp(x); return x*x*(3-2*x)
def prog(t,a,b): return clamp((t-a)/(b-a))

random.seed(3)
STARS=[(random.uniform(0,W),random.uniform(0,H),random.uniform(.25,.7),random.random()*6) for _ in range(90)]
DUST=[(random.uniform(0,W),random.uniform(0,H),random.uniform(6,16),random.uniform(1.2,2.6),random.uniform(.10,.24),random.random()*6) for _ in range(26)]
yy_,xx_=np.mgrid[0:OH,0:OW].astype(np.float32)
RR=(((xx_-OW/2)/(OW/2))**2+((yy_-OH*0.46)/(OH/2))**2)
BG=(14*np.clip(1-RR*0.9,0,1)**2).astype(np.float32)
VIG=(1-0.30*np.clip(RR/2,0,1)).astype(np.float32)
def dust(c,t):
    for x,y,b,ph in STARS: c.circ(x,y,0.9,a=b*(0.65+0.35*math.sin(t*1.4+ph))*.55,fill=True)
    for x,y,sp,r,al,ph in DUST: c.circ(x+14*math.sin(t*.35+ph),(y-t*sp)%H,r,a=al,fill=True)

class C:
    def __init__(s): s.im=Image.new("L",(W*S,H*S),0); s.d=ImageDraw.Draw(s.im)
    def v(s,a): return int(255*clamp(a))
    def line(s,pts,w=4,a=1):
        if a<=0.004: return
        p=[(x*S,y*S) for x,y in pts]; s.d.line(p,fill=s.v(a),width=int(w*S),joint="curve")
        for q in (p[0],p[-1]): r=w*S/2; s.d.ellipse([q[0]-r,q[1]-r,q[0]+r,q[1]+r],fill=s.v(a))
    def circ(s,x,y,r,w=4,a=1,fill=False):
        if a<=0.004: return
        b=[(x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S]
        if fill: s.d.ellipse(b,fill=s.v(a))
        else: s.d.ellipse(b,outline=s.v(a),width=int(w*S))
    def rrect(s,x0,y0,x1,y1,r=10,w=4,a=1,fill=False):
        if a<=0.004: return
        b=[x0*S,y0*S,x1*S,y1*S]
        if fill: s.d.rounded_rectangle(b,r*S,fill=s.v(a))
        else: s.d.rounded_rectangle(b,r*S,outline=s.v(a),width=int(w*S))
    def text(s,txt,cx,cy,sz,a=1,rise=0,dx=0):
        if a<=0: return
        f=F(sz); s.d.text(((cx+dx)*S,(cy+rise)*S),txt,font=f,fill=s.v(a),anchor="mm")
    def person(s,x,y,k=1,a=1,refl=False):  # x,y = feet
        if a<=0.004: return
        if refl:
            s.circ(x,y+62*k,13*k,a=a*.13,fill=True); s.d.rounded_rectangle([(x-19*k)*S,(y)*S,(x+19*k)*S,(y+46*k)*S],int(14*k*S),fill=s.v(a*.13))
        s.circ(x,y-62*k,13*k,a=a,fill=True)
        s.d.rounded_rectangle([(x-19*k)*S,(y-46*k)*S,(x+19*k)*S,(y)*S],int(14*k*S),fill=s.v(a))
    def cens(s,cx,cy,sz,a=1,rise=0,stars=5,last="Ь"):
        f=F(sz); parts=[("П",0)]+[("*",0.30)]*stars+([(last,0)] if last else [])
        adv=[s.d.textlength(ch,font=f)/S*(1.25 if ch=="*" else 1.02) for ch,_ in parts]; x=cx-sum(adv)/2
        for (ch,dy),w in zip(parts,adv):
            s.d.text(((x+w/2)*S,(cy+dy*sz+rise)*S),ch,font=f,fill=s.v(a),anchor="mm"); x+=w
    def star(s,x,y,r,a=1,rot=0):
        if a<=0.004: return
        pts=[]
        for i in range(10):
            ang=-math.pi/2+i*math.pi/5+rot; rr=r if i%2==0 else r*0.42
            pts.append(((x+rr*math.cos(ang))*S,(y+rr*math.sin(ang))*S))
        s.d.polygon(pts,fill=s.v(a))
    def rays(s,x,y,r0,r1,n,a=1,rot=0):
        if a<=0.004: return
        for i in range(n):
            ang=rot+i*2*math.pi/n; s.line([(x+r0*math.cos(ang),y+r0*math.sin(ang)),(x+r1*math.cos(ang),y+r1*math.sin(ang))],2,a)

def words_reveal(c,lines,t,t0,t1,y0,sz,gap=1.15):
    """lines: list of strings. words appear progressively between t0..t1"""
    allw=[(li,w) for li,l in enumerate(lines) for w in l.split(" ")]
    n=len(allw); shown={}
    for i,(li,w) in enumerate(allw):
        ts=t0+(t1-t0)*i/max(n,1); shown.setdefault(li,[]).append((w,prog(t,ts,ts+0.35)))
    for li,ws in shown.items():
        f=F(sz); full=" ".join(w for w,_ in ws); wid=c.d.textlength(full,font=f)/S
        xx=640-wid/2
        for w,a in ws:
            ww=c.d.textlength(w+" ",font=f)/S
            if a>0: c.text(w,xx+c.d.textlength(w,font=f)/S/2,y0+li*sz*gap,sz,a,rise=(1-ease(a))*18)
            xx+=ww

# ---- staircase geometry
STX0,STY0,SW,SH,N=250,610,130,48,6
def step_pt(i): return (STX0+SW*i+SW/2, STY0-SH*i)   # standing point on step i (i=0 is ground)
def stairs(c,p,a=1):
    pts=[(STX0-150,STY0)]
    for i in range(N+1): pts+= [(STX0+SW*i,STY0-SH*i),(STX0+SW*(i+1),STY0-SH*i)] if False else []
    pts=[(STX0-170,STY0),(STX0+SW*0.5,STY0)]
    for i in range(1,N+1): pts+=[(STX0+SW*i-SW*0.5,STY0-SH*(i-1)),(STX0+SW*i-SW*0.5,STY0-SH*i),(STX0+SW*i+SW*0.5,STY0-SH*i)]
    # draw partial polyline by progress
    L=[0]
    for i in range(1,len(pts)): L.append(L[-1]+math.dist(pts[i-1],pts[i]))
    tgt=L[-1]*p; out=[pts[0]]
    for i in range(1,len(pts)):
        if L[i]<=tgt: out.append(pts[i])
        else:
            f=(tgt-L[i-1])/(L[i]-L[i-1]); out.append((pts[i-1][0]+(pts[i][0]-pts[i-1][0])*f,pts[i-1][1]+(pts[i][1]-pts[i-1][1])*f)); break
    if len(out)>1: c.line(out,4,a)
def stand(i): # person feet position when standing on level i (level 0 = ground)
    x=STX0+SW*i+(0 if i>0 else 0); 
    return (STX0+SW*i-(SW*0.0) if i>0 else STX0+SW*0.0-0, STY0-SH*i)
def pos_at(u): # u in [0,N] continuous level, x moves with hop
    i=int(min(u,N-1e-9)); f=u-i
    x0=STX0 if i==0 else STX0+SW*i; x1=STX0+SW*(i+1)
    # place person centered on each tread
    xa=STX0+SW*i-(SW*0.0)+ (0 if i>0 else 0)
    xa=(STX0+SW*i if i>0 else STX0); xb=STX0+SW*(i+1)
    x=xa+(xb-xa)*sm(f); y=STY0-SH*i-SH*sm(f)-math.sin(f*math.pi)*26
    return x,y
STAR=(STX0+SW*N+60,STY0-SH*N-70)

def arc(c,cx,cy,rad,p,w,a):
    n=max(2,int(120*p)); pts=[(cx+rad*math.cos(-math.pi/2+2*math.pi*p*k/n),cy+rad*math.sin(-math.pi/2+2*math.pi*p*k/n)) for k in range(n+1)]
    if p>0.003: c.line(pts,w,a)
def scene(i,t,c):
    d=D[i]; a0=LEAD; a1=LEAD+d
    exit=1-sm(prog(t,a1+PAD-0.2,a1+PAD)); enter=sm(prog(t,0,0.2)); A=enter*exit
    base=620
    def cross(x0,y0,x1,y1,p,a):
        if p>0: c.line([(x0,y0),(x0+(x1-x0)*min(1,p*2),y0+(y1-y0)*min(1,p*2))],5,a)
        if p>.5: q=(p-.5)*2; c.line([(x1,y0),(x1+(x0-x1)*q,y0+(y1-y0)*q)],5,a)
    if i==0:
        words_reveal(c,["ЗАВТРА. С ПОНЕДЕЛЬНИКА.","С НОВОГО ГОДА."],t,a0,a0+d*0.9,105,78)
        labs=["ЗАВТРА","ПОНЕДЕЛЬНИК","НОВЫЙ ГОД"]; ap_t=[a0+0.1,a0+1.0,a0+2.1]; cr_t=[a0+1.1,a0+2.2,a1-0.2]
        for k in range(3):
            x=340+k*300; y0_,y1_=400,560; ap=prog(t,ap_t[k],ap_t[k]+.3); crp=ease(prog(t,cr_t[k],cr_t[k]+.4))
            c.rrect(x-120,y0_,x+120,y1_,10,4,A*ap)
            c.line([(x-120,y0_+34),(x+120,y0_+34)],3,A*ap*.8)
            for m in range(3): c.circ(x-98+m*16,y0_+17,4,fill=True,a=A*ap*.8)
            c.text(labs[k],x,y0_+98,34,A*ap*(1-.6*crp))
            cross(x-95,y0_+55,x+95,y1_-15,crp,A)
    if i==1:
        words_reveal(c,["ТЫ ГОВОРИШЬ ЭТО","УЖЕ МНОГО ЛЕТ."],t,a0,a0+d*0.8,110,90)
        c.line([(150,base),(1130,base)],4,A)
        for k,yr in enumerate(["2023","2024","2025","2026"]):
            x=310+k*220; tt=a0+0.3+k*0.3; ap=prog(t,tt,tt+.25)
            c.text(yr,x,390,54,A*ap); c.person(x,base,1.4,A*ap*(1 if k==3 else .55),refl=True)
            c.text("ЗАВТРА НАЧНУ",x,base+34,20,A*ap*.5)
    if i==2:
        words_reveal(c,["ИДЕАЛЬНОГО МОМЕНТА","НЕ СУЩЕСТВУЕТ."],t,a0,a0+d*0.85,110,86)
        c.line([(100,base),(1180,base)],4,A)
        p=ease(prog(t,a0+0.3,a1)); px=250+270*p; ox=880+270*p; oy=470-30*p
        c.person(px,base,1.9,A,refl=True)
        for k in range(26):
            x0=px+60+k*26
            if x0<ox-50: c.line([(x0,oy+10),(x0+12,oy+10)],2,A*.3)
        fade=A*(1-.5*p); c.circ(ox,oy,30,fill=True,a=fade); c.circ(ox,oy,50,2,a=fade*.6); c.rays(ox,oy,62,84,14,fade*.5,t*.5)
    if i==3:
        words_reveal(c,["СТРАХ УЙДЁТ ПОСЛЕ","ПЕРВОГО ШАГА."],t,a0,a0+d*0.8,110,86)
        c.line([(100,base),(1180,base)],4,A)
        p=prog(t,a0+0.8,a1); steps=ease(p)*3; hop=math.sin((steps%1)*math.pi)*20 if p<1 else 0
        px=300+steps*115; c.person(px,base-hop,1.9,A,refl=True)
        r_=150-110*ease(p); fx,fy=900,470
        c.circ(fx,fy,r_,fill=True,a=A*.16); c.circ(fx,fy,r_,4,A*(.7+.3*math.sin(t*6)))
        c.text("СТРАХ",fx,fy,max(14,int(46*r_/150)),A*.9)
    if i==4:
        words_reveal(c,["НЕ ГОТОВ?"],t,a0,a0+BEEP*0.8,100,76)
        cb=prog(t,a0+BEEP-0.05,a0+BEEP+0.2); c.cens(640,100+75,76,A*cb,rise=(1-ease(cb))*22,stars=4,last="")
        words_reveal(c,["НАЧИНАЙ НЕГОТОВЫМ."],t,a0+AFTER,a0+AFTER+0.9,100+185,76)
        x0=200; L=880
        b1=ease(prog(t,a0+0.2,a0+1.2))*0.38; b2=ease(prog(t,a0+AFTER,a1))*1.0
        c.text("ГОТОВНОСТЬ",x0+95,445,24,A*.7); c.rrect(x0,462,x0+L,502,6,3,A*.35)
        c.rrect(x0,462,x0+max(8,L*b1),502,6,3,A*(.55+.2*math.sin(t*5)),fill=True)
        c.text("ДЕЙСТВИЕ",x0+75,555,24,A*.7); c.rrect(x0,572,x0+L,612,6,3,A*.35)
        c.rrect(x0,572,x0+max(8,L*b2),612,6,3,A,fill=True)
    if i==5:
        words_reveal(c,["ДЕСЯТЬ МИНУТ.","ПРЯМО СЕЙЧАС."],t,a0,a0+d*0.8,110,96)
        p=ease(prog(t,a0+0.5,a1-0.1)); cx,cy=640,500
        c.circ(cx,cy,118,6,A*.25); arc(c,cx,cy,118,1-p,8,A)
        rem=int(600*(1-p)); c.text("%02d:%02d"%(rem//60,rem%60),cx,cy,72,A)
    if i==6:
        words_reveal(c,["ЛУЧШЕЕ ВРЕМЯ — ГОД НАЗАД.","ВТОРОЕ — СЕГОДНЯ."],t,a0,a0+d*0.9,100,62,1.3)
        y=520; lp=ease(prog(t,a0+0.1,a0+0.8))
        c.line([(200,y),(200+880*lp,y)],4,A)
        m1=prog(t,a0+0.4,a0+0.9); c.circ(320,y,20,4,A*m1); c.text("ГОД НАЗАД",320,y+60,28,A*.7*m1)
        m2=prog(t,a0+d*0.55,a0+d*0.55+0.4)
        c.circ(960,y,20,fill=True,a=A*m2); c.circ(960,y,34,2,A*m2*.6); c.rays(960,y,44,62,14,A*m2*.6,t*.5)
        c.text("СЕГОДНЯ",960,y+70,32,A*m2)
    if i==7:
        words_reveal(c,["ВСТАНЬ.","СДЕЛАЙ ПЕРВОЕ ДЕЙСТВИЕ."],t,a0,a0+d*0.9,110,86)
        f=F(48); wl=c.d.textlength("ПЕРВОЕ ДЕЙСТВИЕ",font=f)/S; x0=640-(100+wl)/2; y=490
        ap=prog(t,a0+0.5,a0+1.0)
        c.rrect(x0,y-45,x0+90,y+45,12,5,A*ap); c.text("ПЕРВОЕ ДЕЙСТВИЕ",x0+120+wl/2,y,48,A*ap)
        ck=ease(prog(t,a0+d*0.6,a0+d*0.6+0.5))
        if ck>0:
            p1=min(1,ck*2); p2=max(0,ck*2-1); pts=[(x0+18,y+2),(x0+18+22*p1,y+2+24*p1)]
            if p2>0: pts.append((x0+40+34*p2,y+26-58*p2))
            c.line(pts,9,A)
    if i==8:
        tx=c.d.textlength("НЕ ЗАВТРА.",font=F(104))/S
        c.text("НЕ ЗАВТРА.",640,170,104,A*prog(t,a0,a0+0.4),rise=(1-ease(prog(t,a0,a0+.4)))*20)
        sp=ease(prog(t,a0+d*0.35,a0+d*0.35+0.35)); c.line([(640-tx/2-10,172),(640-tx/2-10+(tx+20)*sp,172)],8,A*(sp>0))
        bt=ease(prog(t,a0+d*0.5,a0+d*0.5+0.5)); pulse=.5+.5*math.sin(t*4); bw=270+10*pulse
        c.rrect(640-bw,420-70,640+bw,420+70,70,6,A*bt); c.text("СЕГОДНЯ.",640,416,92,A*bt)
        for k in range(20):
            ang=k*math.pi*2/20+t*.2; c.line([(640+(bw+40+8*pulse)*math.cos(ang),420+(112+8*pulse)*math.sin(ang)),(640+(bw+64)*math.cos(ang),420+(136)*math.sin(ang))],2,A*bt*.4)
        c.person(640,base+10,1.6,A*prog(t,a0+d*0.6,a0+d*0.6+.5))

def frame(f):
    t=f/FPS
    i=0
    for k,s in enumerate(starts):
        if t>=s: i=k
    loc=t-starts[i]; dur=(starts[i+1] if i<len(starts)-1 else TOTAL)-starts[i]
    c=C(); scene(i,loc,c); dust(c,t)
    sharp=c.im.resize((OW,OH),Image.LANCZOS)
    z=1+0.04*sm(clamp(loc/dur))
    sharp=sharp.transform((OW,OH),Image.AFFINE,(1/z,0,OW/2*(1-1/z),0,1/z,OH*0.46*(1-1/z)),Image.BICUBIC)
    sx=np.array(sharp,np.float32)
    g1=np.array(sharp.filter(ImageFilter.GaussianBlur(7)),np.float32)
    g2=np.array(sharp.resize((OW//2,OH//2),Image.BOX).filter(ImageFilter.GaussianBlur(16)).resize((OW,OH),Image.BICUBIC),np.float32)
    g3=np.array(sharp.resize((OW//4,OH//4),Image.BOX).filter(ImageFilter.GaussianBlur(26)).resize((OW,OH),Image.BICUBIC),np.float32)
    arr=(sx+g1*.12+g2*.26+g3*.34+BG)*VIG
    fa=min(1,t/0.3)*min(1,(TOTAL-t)/0.4); arr*=fa
    arr+=np.random.default_rng(f).normal(0,1.5,arr.shape).astype(np.float32)
    return np.repeat(np.clip(arr,0,255).astype(np.uint8)[:,:,None],3,2)

if __name__=="__main__":
    a,b=int(sys.argv[1]),int(sys.argv[2]); out=sys.argv[3]
    p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{OW}x{OH}","-r",str(FPS),"-i","-","-c:v","libx264","-preset","medium","-crf","13","-pix_fmt","yuv420p",out],stdin=subprocess.PIPE)
    for f in range(a,b): p.stdin.write(frame(f).tobytes())
    p.stdin.close(); p.wait()
