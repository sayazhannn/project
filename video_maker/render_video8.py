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
def cage(c,A,gap,prg=1.0):
    for k in range(9):
        x=440+k*50; vis=1
        if gap and 3<=k<=5: vis=1-sm(gap)
        yb=330+(620-330)*clamp(prg*1.4-k*0.03)
        c.line([(x,330),(x,yb)],4,A*vis*(0.9))
    c.line([(440,330),(840,330)],5,A*prg)
def scene(i,t,c):
    d=D[i]; a0=LEAD; a1=LEAD+d
    exit=1-sm(prog(t,a1+PAD-0.2,a1+PAD)); enter=sm(prog(t,0,0.2)); A=enter*exit
    base=620
    if i==0:
        words_reveal(c,["ТЕБЕ НЕУДОБНО?","ОТЛИЧНО."],t,a0,a0+d*0.8,110,92)
        cx,cy,R=640,600,230
        pts=[(cx+R*math.cos(math.pi+math.pi*k/40),cy+R*math.sin(math.pi+math.pi*k/40)) for k in range(41)]
        c.line(pts[:21],5,A*.4); c.line(pts[20:],8,A)
        c.text("КОМФОРТ",cx-170,cy+34,26,A*.5); c.text("РОСТ",cx+170,cy+34,36,A)
        ang=math.pi+math.pi*(0.12+0.8*ease(prog(t,a0+0.6,a1-0.1)))
        c.line([(cx,cy),(cx+205*math.cos(ang),cy+205*math.sin(ang))],6,A); c.circ(cx,cy,14,fill=True,a=A)
    if i==1:
        words_reveal(c,["РОСТ НАЧИНАЕТСЯ","С ДИСКОМФОРТА."],t,a0,a0+d*0.8,110,86)
        c.rrect(560,380,760,640,10,3,A*.45*prog(t,a0,a0+.5)); c.text("ДИСКОМФОРТ",660,360,24,A*.7*prog(t,a0+.3,a0+.8))
        gp=ease(prog(t,a0+0.4,a1-0.1)); pts=[]
        for k in range(int(80*gp)+1):
            x=330+620*k/80; u=(x-560)/200; y=600-(0 if u<0 else 220*sm(clamp(u)))-(0 if u<1 else 150*(u-1)/2.0)
            pts.append((x,y))
        if len(pts)>1: c.line(pts,6,A)
        if pts: c.circ(pts[-1][0],pts[-1][1],10,fill=True,a=A)
    if i==2:
        words_reveal(c,["МЫШЦА РАСТЁТ,","КОГДА ТЯЖЕЛО."],t,a0,a0+d*0.85,110,92)
        c.line([(330,520),(950,520)],8,A)
        n=1+int(3*ease(prog(t,a0+0.5,a1-0.2)))
        for side in (-1,1):
            c.rrect(640+side*270-8,470,640+side*270+8,570,3,3,A,fill=True)
            for k in range(n):
                w=30-4*k; x=640+side*(270-24-k*26)
                c.rrect(x-w/2,520-70+ k*8,x+w/2,520+70-k*8,5,3,A*(.9-.1*k),fill=True)
    if i==3:
        words_reveal(c,["НАВЫК РАСТЁТ,","КОГДА ОШИБАЕШЬСЯ."],t,a0,a0+d*0.85,110,82)
        pts=[(260,base)]
        for k in range(8): pts+= [(260+k*100+40,base-k*34),(260+k*100+40,base-(k+1)*34),(260+k*100+140,base-(k+1)*34)]
        gp=ease(prog(t,a0+0.2,a0+1.2)); n=int(len(pts)*gp)+1; c.line(pts[:n],4,A)
        for k in range(8):
            tt=a0+0.5+k*0.2; ap=prog(t,tt,tt+.2)
            if ap>0:
                x=260+k*100+90; y=base-(k+1)*34-22
                c.line([(x-12,y-12),(x+12,y+12)],4,A*ap); c.line([(x+12,y-12),(x-12,y+12)],4,A*ap)
        cnt=min(8,max(0,int((t-a0-0.5)/0.2)+1)); c.text("ОШИБОК %d"%cnt,380,330,40,A*.8*prog(t,a0+.5,a0+.9))
    if i==4:
        words_reveal(c,["КОМФОРТ —","КРАСИВАЯ КЛЕТКА."],t,a0,a0+d*0.85,110,92)
        c.line([(150,base),(1130,base)],4,A)
        cage(c,A,0,ease(prog(t,a0+0.3,a0+1.1))); c.person(640,base,1.4,A)
    if i==5:
        words_reveal(c,["ВЫЙДИ ИЗ НЕЁ.","СЕЙЧАС."],t,a0,a0+d*0.85,110,96)
        c.line([(150,base),(1130,base)],4,A)
        g=prog(t,a0+0.3,a0+0.8); cage(c,A,g); p=ease(prog(t,a0+0.7,a1)); c.person(640+380*p,base,1.4,A,refl=False)
    if i==6:
        words_reveal(c,["СТРАШНО?","ДЕЛАЙ СО СТРАХОМ."],t,a0,a0+d*0.85,110,92)
        for k in range(-1,12):
            x=k*120-(t*260)%120; c.line([(x,base),(x+70,base)],4,A*.85)
        c.person(700,base-4*abs(math.sin(t*5)),1.8,A,refl=True)
        fx=520-t*60; fr=40-8*prog(t,a0,a1); c.circ(fx,base-60,fr,3,A*.6); c.text("СТРАХ",fx,base-60,18,A*.6) if fx>60 else None
    if i==7:
        words_reveal(c,["ЧЕРЕЗ ГОД ТЫ НЕ","ВСПОМНИШЬ СТРАХ."],t,a0,a0+d*0.85,110,80)
        c.line([(150,base),(1130,base)],4,A)
        fd=1-sm(prog(t,a0+0.6,a1)); c.circ(420,base-110,70,4,A*fd); c.text("СТРАХ",420,base-110,34,A*fd)
        for k in range(14):
            ang=k*math.pi*2/14; rr=70+60*(1-fd); c.circ(420+rr*math.cos(ang),base-110+rr*math.sin(ang),3,fill=True,a=A*(1-fd)*.7*(fd<0.98))
        c.person(820,base,2.0,A,refl=True)
    if i==8:
        words_reveal(c,["ВСПОМНИШЬ ТОЛЬКО:","НЕ ОСТАНОВИЛСЯ."],t,a0,a0+d*0.85,110,86)
        y=520; c.line([(200,y),(1080,y)],4,A*prog(t,0,.6))
        for k in range(6):
            x=200+k*176; tt=a0+0.5+k*0.3; ap=prog(t,tt,tt+.25)
            c.circ(x,y,12,fill=True,a=A*ap); c.circ(x,y,22,2,A*ap*.5)
        p=ease(prog(t,a0+0.5,a1)); c.person(200+880*p,y-14,1.2,A)

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
