import json, math, sys, subprocess, numpy as np, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,S=1280,720,30,3
OW,OH=1920,1080
meta=json.load(open("a/meta.json")); D=meta["durs"]; BEEP=meta["beep_at"]
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
    def cens(s,cx,cy,sz,a=1,rise=0):
        f=F(sz); parts=[("П",0)]+[("*",0.30)]*5+[("Ь",0)]
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
def leaf(c,px,py,sx,size,a):
    n=14; up=[];dn=[]
    for k in range(n+1):
        u=k/n; x=px+sx*size*u; yb=py-size*0.55*u; off=size*0.22*math.sin(math.pi*u)
        up.append((x,yb-off)); dn.append((x,yb+off))
    c.line(up+dn[::-1],3,a)
def chart(c,xmax,gp,fn,A,w=5):
    x0,x1,y0,y1=330,950,650,330
    c.line([(x0,y1-10),(x0,y0),(x1,y0)],3,A*.8)
    pts=[]; N=120
    for k in range(int(N*gp)+1):
        x=xmax*k/N; pts.append((x0+10+x*(x1-x0-30),y0-8-clamp(fn(x))*(y0-y1-30)))
    if len(pts)>1: c.line(pts,w,A)
    if pts: c.circ(pts[-1][0],pts[-1][1],9,fill=True,a=A); c.circ(pts[-1][0],pts[-1][1],18,2,a=A*.5)
    return pts[-1] if pts else (x0,y0)
GROW=lambda x:(1.01**(365*x)-1)/(1.01**365-1)
DECAY=lambda x:0.99**(365*x)
def scene(i,t,c):
    d=D[i]; a0=LEAD; a1=LEAD+d
    exit=1-sm(prog(t,a1+PAD-0.2,a1+PAD)); enter=sm(prog(t,0,0.2)); A=enter*exit
    base=620
    if i==0:
        words_reveal(c,["ТЫ ХОЧЕШЬ ВСЁ","И СРАЗУ."],t,a0,a0+d*0.8,110,92)
        c.line([(100,base),(1180,base)],4,A)
        c.rrect(900,330,1130,base,6,4,A*prog(t,.1,.7)); c.star(1015,285,24,A*prog(t,.3,.8),t*.5); c.rays(1015,285,36,52,12,A*.6*prog(t,.3,.8),t*.6)
        c.person(300,base,1.9,A,refl=True)
        u=ease(prog(t,a0+0.3,a0+1.1))
        for k in range(int(26*u)+1):
            v=k/26; x=330+560*v; y=540+80*v-4*170*v*(1-v); c.circ(x,y,5,fill=True,a=A*.8)
        xe=ease(prog(t,a0+1.1,a0+1.4))
        if xe>0: c.line([(838,572),(838+32*xe,572+32*xe)],6,A); c.line([(870,572),(870-32*xe,572+32*xe)],6,A)
    if i==1:
        words_reveal(c,["СРАЗУ НИЧЕГО","НЕ БЫВАЕТ."],t,a0,a0+d*0.8,110,92)
        c.line([(300,base),(980,base)],4,A)
        g=ease(prog(t,a0+0.4,a1)); h=190*g
        c.circ(640,base-2,7,fill=True,a=A)
        if h>3:
            pts=[(640+10*math.sin(v*3),base-h*v) for v in [k/20 for k in range(21)]]; c.line(pts,5,A)
        for k,(fr,sx) in enumerate([(.45,1),(.65,-1),(.85,1)]):
            if g>fr: s_=ease((g-fr)/(1-fr+1e-6)*1.4); yy=base-h*fr; leaf(c,640+10*math.sin(fr*3),yy,sx,70*s_,A)
    if i==2:
        words_reveal(c,["ОДИН ПРОЦЕНТ","В ДЕНЬ."],t,a0,a0+d*0.8,110,92)
        c.text("1%",640,450,230,A*ease(prog(t,a0+0.3,a0+0.9)))
        c.rrect(340,600,940,634,8,3,A*.4); c.rrect(340,600,346+4*ease(prog(t,a0+0.6,a0+1.0)),634,3,3,A,fill=True)
    if i==3:
        words_reveal(c,["КАЖЕТСЯ —","ЭТО НИЧЕГО."],t,a0,a0+d*0.8,110,92)
        gp=ease(prog(t,a0+0.4,a1-0.1)); p=chart(c,100/365,gp,GROW,A)
        c.text("ДЕНЬ 100 · ×2,7",p[0]+10,p[1]-50,30,A*prog(gp,.9,1)); 
    if i==4:
        words_reveal(c,["ЗА ГОД — ПОЧТИ","В 38 РАЗ БОЛЬШЕ."],t,a0,a0+d*0.7,110,86)
        gp=ease(prog(t,a0+0.4,a1-0.2)); p=chart(c,1,gp,GROW,A)
        c.text(("×%.1f"%(1.01**(365*gp))).replace(".",","),480,430,90,A*prog(gp,.05,.2)) 
    if i==5:
        words_reveal(c,["МИНУС ОДИН ПРОЦЕНТ","В ДЕНЬ — ТЫ ПОЧТИ НОЛЬ."],t,a0,a0+d*0.8,100,64,1.3)
        gp=ease(prog(t,a0+0.5,a1-0.1)); p=chart(c,1,gp,DECAY,A)
        c.text(("×%.2f"%(0.99**(365*gp))).replace(".",","),780,430,90,A*prog(gp,.05,.2))
    if i==6:
        words_reveal(c,["КАЖДЫЙ ДЕНЬ ТЫ","ВЫБИРАЕШЬ, КУДА ИДЁШЬ."],t,a0,a0+d*0.8,100,80)
        gp=ease(prog(t,a0+0.4,a0+1.4)); sx,sy=330,500
        def curve(ey):
            n=int(40*gp); return [(sx+620*k/40,sy+(ey-sy)*sm(k/40)) for k in range(n+1)]
        up=curve(340); dn=curve(650)
        if len(up)>1: c.line(up,5,A)
        if len(dn)>1: c.line(dn,4,A*.55*(1-.5*sm(prog(t,a0+d*.55,a0+d*.7))))
        c.text("ВВЕРХ",1050,340,32,A*prog(gp,.9,1)); c.text("ВНИЗ",1040,650,28,A*.6*prog(gp,.9,1))
        mv=ease(prog(t,a0+d*0.55,a1)); k_=int(40*mv); px=sx+620*k_/40; py=sy+(340-sy)*sm(k_/40)
        c.person(px,py,1.2,A) 
    if i==7:
        words_reveal(c,["МЕЛОЧИ","РЕШАЮТ ВСЁ."],t,a0,a0+d*0.8,110,96)
        idx=0
        for r_ in range(7,0,-1):
            for k in range(r_):
                tt=a0+0.2+idx*0.035; ap=prog(t,tt,tt+.2); idx+=1
                x=640+(k-(r_-1)/2)*44; y=620-(7-r_)*40-14
                c.circ(x,y,16,fill=True,a=A*ap*.9)
    if i==8:
        words_reveal(c,["НАЧНИ С ОДНОГО","ПРОЦЕНТА. СЕГОДНЯ."],t,a0,a0+d*0.8,110,86)
        bt=ease(prog(t,a0+d*0.6,a0+d*0.6+0.5)); pulse=.5+.5*math.sin(t*4); bw=190+10*pulse
        c.rrect(640-bw,430-85,640+bw,430+85,85,6,A*bt); c.text("+1%",640,422,140,A*bt)
        for k in range(20):
            ang=k*math.pi*2/20+t*.2; c.line([(640+(bw+40+8*pulse)*math.cos(ang),430+(125+8*pulse)*math.sin(ang)),(640+(bw+64)*math.cos(ang),430+(150)*math.sin(ang))],2,A*bt*.4)
        c.person(640,base+35,1.2,A*bt)

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
