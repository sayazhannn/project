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
def phone(c,cx,cy,w,h,a):
    c.rrect(cx-w/2,cy-h/2,cx+w/2,cy+h/2,26,5,a); c.line([(cx-22,cy-h/2+16),(cx+22,cy-h/2+16)],4,a*.8)
def feed(c,cx,cy,w,h,t,a):
    for k in range(7):
        y=cy-h/2+50+((k*52-t*95)%(h-80)); c.rrect(cx-w/2+22,y,cx+w/2-22,y+18,8,3,a*.55,fill=True)
def scene(i,t,c):
    d=D[i]; a0=LEAD; a1=LEAD+d
    exit=1-sm(prog(t,a1+PAD-0.2,a1+PAD)); enter=sm(prog(t,0,0.2)); A=enter*exit
    base=620
    if i==0:
        words_reveal(c,["ТЫ БЕРЁШЬ ТЕЛЕФОН","НА МИНУТУ."],t,a0,a0+d*0.8,110,86)
        phone(c,640,470,200,330,A); feed(c,640,470,200,330,t,A)
        c.text("1 МИН",930,470,52,A*prog(t,a0+0.8,a0+1.2))
    if i==1:
        words_reveal(c,["ПРОСЫПАЕШЬСЯ","ЧЕРЕЗ ЧАС."],t,a0,a0+d*0.8,110,92)
        phone(c,420,470,200,330,A); feed(c,420,470,200,330,t*2.5,A)
        cx,cy=880,470; c.circ(cx,cy,95,5,A)
        for k in range(12): ang=k*math.pi/6; c.line([(cx+82*math.sin(ang),cy-82*math.cos(ang)),(cx+92*math.sin(ang),cy-92*math.cos(ang))],3,A*.7)
        c.line([(cx,cy),(cx+70*math.sin(t*9),cy-70*math.cos(t*9))],4,A); c.line([(cx,cy),(cx+44*math.sin(t*.75),cy-44*math.cos(t*.75))],6,A)
        c.text("1 ЧАС",cx,cy+150,44,A*prog(t,a0+0.8,a0+1.2))
    if i==2:
        words_reveal(c,["ЧЕТЫРЕ ЧАСА","В ДЕНЬ."],t,a0,a0+d*0.8,110,92)
        for k in range(24):
            x=262+(k%12)*64; y=430+(k//12)*72; on=prog(t,a0+0.1+k*0.17,a0+0.3+k*0.17) if k<4 else 0
            c.rrect(x-24,y-24,x+24,y+24,6,3,A*.4); 
            if on>0: c.rrect(x-24,y-24,x+24,y+24,6,3,A*on,fill=True)
        c.text("24 ЧАСА",640,590,34,A*.6)
    if i==3:
        words_reveal(c,["ЭТО 60 ДНЕЙ","В ГОДУ."],t,a0,a0+d*0.8,110,92)
        n=int(ease(prog(t,a0+0.6,a1-0.1))*61)
        for k in range(365):
            x=299+(k%31)*22+11; y=388+(k//31)*22
            if k<n: c.circ(x,y,7,fill=True,a=A)
            else: c.circ(x,y,5,fill=True,a=A*.28)
        c.text("61 ДЕНЬ",1130,500,64,A*prog(t,a0+1.0,a0+1.5))
    if i==4:
        words_reveal(c,["ДВА МЕСЯЦА ЖИЗНИ.","В ЭКРАНЕ."],t,a0,a0+d*0.8,110,80)
        c.rrect(440,340,840,650,30,5,A); feed(c,640,495,400,310,t,A*.5)
        c.person(640,640,1.4,A)
        c.text("ТЫ",640,420,34,A*.7*prog(t,a0+0.8,a0+1.2))
    if i==5:
        words_reveal(c,["ПОКА ТЫ ЛИСТАЕШЬ,","КТО-ТО СТРОИТ."],t,a0,a0+d*0.8,110,84)
        c.line([(100,base),(1180,base)],4,A)
        c.person(300,base,1.6,A,refl=True); phone(c,380,545,50,80,A*.8)
        span=d-0.8
        for idx in range(25):
            r_,c_=divmod(idx,5); tt=a0+0.4+idx*span/25; ap=prog(t,tt,tt+.2)
            if ap<=0: continue
            x=700+c_*90+(45 if r_%2 else 0); y=base-(r_+1)*40
            c.rrect(x+2,y+2,x+88,y+38,4,3,A*.45*(1-prog(t,tt,tt+.35))*ap,fill=True); c.rrect(x+2,y+2,x+88,y+38,4,3,A*ap)
    if i==6:
        words_reveal(c,["УДАЛИ ЛИШНЕЕ.","УБЕРИ ТЕЛЕФОН."],t,a0,a0+d*0.8,110,92)
        phone(c,640,500,250,350,A)
        for k in range(12):
            x=640+(k%3-1)*70; y=395+(k//3)*68; off=a0+0.5+k*0.15
            if k in (4,9): vis=1
            else: vis=1-sm(prog(t,off,off+.25))
            c.rrect(x-24,y-24,x+24,y+24,8,3,A*vis*.9,fill=True)
            if k not in (4,9):
                fl=prog(t,off-.1,off+.1)*(1-prog(t,off+.1,off+.3))
                if fl>0: c.line([(x-20,y-20),(x+20,y+20)],4,A*fl); c.line([(x+20,y-20),(x-20,y+20)],4,A*fl)
    if i==7:
        words_reveal(c,["ВЕРНИ СЕБЕ","ПЕРВЫЙ ЧАС ДНЯ."],t,a0,a0+d*0.8,110,92)
        c.line([(100,base),(1180,base)],4,A)
        p=ease(prog(t,a0+0.3,a1)); sy=560-130*p
        c.circ(760,sy,64,fill=True,a=A); c.rays(760,sy,84,112,18,A*.7,t*.3)
        c.person(420,base,1.6,A,refl=True); c.text("06:00",1050,330+60,48,A*.7*prog(t,a0+0.6,a0+1.0))
    if i==8:
        words_reveal(c,["ПОЛОЖИ ТЕЛЕФОН.","НАЧНИ ЖИТЬ."],t,a0,a0+d*0.8,110,96)
        for k in range(-1,12):
            x=k*120-(t*330)%120; c.line([(x,base),(x+70,base)],4,A*.85)
        c.rrect(160,base-22,360,base-2,6,3,A*.45*prog(t,a0,a0+.4))
        wk=ease(prog(t,a0+0.4,a1+PAD)); px=420+520*wk
        c.person(px,base-4*abs(math.sin(t*5)),1.7,A*prog(t,a0,a0+.4),refl=True)

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
