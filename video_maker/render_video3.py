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
        p=[(x*S,y*S) for x,y in pts]; s.d.line(p,fill=s.v(a),width=int(w*S),joint="curve")
        for q in (p[0],p[-1]): r=w*S/2; s.d.ellipse([q[0]-r,q[1]-r,q[0]+r,q[1]+r],fill=s.v(a))
    def circ(s,x,y,r,w=4,a=1,fill=False):
        b=[(x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S]
        if fill: s.d.ellipse(b,fill=s.v(a))
        else: s.d.ellipse(b,outline=s.v(a),width=int(w*S))
    def rrect(s,x0,y0,x1,y1,r=10,w=4,a=1,fill=False):
        b=[x0*S,y0*S,x1*S,y1*S]
        if fill: s.d.rounded_rectangle(b,r*S,fill=s.v(a))
        else: s.d.rounded_rectangle(b,r*S,outline=s.v(a),width=int(w*S))
    def text(s,txt,cx,cy,sz,a=1,rise=0,dx=0):
        if a<=0: return
        f=F(sz); s.d.text(((cx+dx)*S,(cy+rise)*S),txt,font=f,fill=s.v(a),anchor="mm")
    def person(s,x,y,k=1,a=1,refl=False):  # x,y = feet
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
        pts=[]
        for i in range(10):
            ang=-math.pi/2+i*math.pi/5+rot; rr=r if i%2==0 else r*0.42
            pts.append(((x+rr*math.cos(ang))*S,(y+rr*math.sin(ang))*S))
        s.d.polygon(pts,fill=s.v(a))
    def rays(s,x,y,r0,r1,n,a=1,rot=0):
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
    if i==0:
        words_reveal(c,["ОНИ СПЯТ.","ТЫ РАБОТАЕШЬ."],t,a0,a0+d*0.85,110,92)
        bx0,bx1,by0=325,955,300
        c.line([(150,base),(1130,base)],4,A*prog(t,0,.5))
        c.rrect(bx0,by0,bx1,base,4,4,A*prog(t,0.1,.6))
        import random as _r; rr=_r.Random(5); order=list(range(24)); rr.shuffle(order)
        for r_ in range(4):
            for c_ in range(6):
                k=r_*6+c_; wx=bx0+30+c_*100; wy=by0+24+r_*74
                special=(r_==2 and c_==3)
                off=a0+0.3+order.index(k)*0.045
                lit=.5*(1-sm(prog(t,off,off+.25)))
                if special: lit=max(lit,sm(prog(t,a0+1.2,a0+1.7)))
                c.rrect(wx,wy,wx+70,wy+50,5,3,A*(.35+.35*lit) if not special else A)
                if lit>0.01: c.rrect(wx+4,wy+4,wx+66,wy+46,3,2,A*lit*(1 if special else .55),fill=True)
                if special and lit>.5: c.person(wx+35,wy+46,.62,0)
        # person silhouette inside lit window drawn dark
        wx=bx0+30+3*100; wy=by0+24+2*74; sp=sm(prog(t,a0+1.5,a0+2.0))
        if sp>0:
            c.d.ellipse([(wx+35-7)*S,(wy+14-7)*S,(wx+35+7)*S,(wy+14+7)*S],fill=0)
            c.d.rounded_rectangle([(wx+35-12)*S,(wy+24)*S,(wx+35+12)*S,(wy+46)*S],int(7*S),fill=0)
    if i==1:
        words_reveal(c,["НИКТО НЕ АПЛОДИРУЕТ","В ПЯТЬ УТРА."],t,a0,a0+d*0.8,100,76)
        for r_ in range(3):
            for k in range(13):
                x=220+k*70+(r_%2)*0; y=380+r_*60; tt=a0+0.2+(r_*13+k)*0.025
                c.rrect(x-20,y-15,x+20,y+15,6,3,A*.32*prog(t,tt,tt+.3))
        c.line([(150,base),(1130,base)],4,A)
        c.d.ellipse([(640-130)*S,(base-8)*S,(640+130)*S,(base+8)*S],outline=c.v(A*.5),width=int(3*S))
        c.line([(520,base),(600,505)],2,A*.3); c.line([(760,base),(680,505)],2,A*.3)
        c.person(640,base,1.2,A,refl=True)
        c.text("05:00",1100,330,46,A*.75*prog(t,a0+.3,a0+.8))
    if i==2:
        words_reveal(c,["РЕЗУЛЬТАТ ПРИХОДИТ ТИХО.","БЕЗ СВИДЕТЕЛЕЙ."],t,a0,a0+d*0.8,100,62,1.3)
        ax0,ax1,ay0,ay1=330,950,650,330
        c.line([(ax0,ay1-10),(ax0,ay0),(ax1,ay0)],3,A*.8)
        gp=ease(prog(t,a0+0.5,a1-0.2)); pts=[]
        for k in range(int(100*gp)+1):
            x=k/100; y=(math.exp(5*x)-1)/(math.exp(5)-1)
            pts.append((ax0+10+x*(ax1-ax0-30),ay0-8-y*(ay0-ay1-30)))
        if len(pts)>1: c.line(pts,5,A)
        if pts: c.circ(pts[-1][0],pts[-1][1],9,fill=True,a=A); c.circ(pts[-1][0],pts[-1][1],18,2,a=A*.5)
        c.text("ТИШИНА",470,ay0-30,26,A*.7*prog(t,a0+.8,a0+1.3)*(1-prog(t,a0+d*.75,a0+d*.9)*.6))
        c.text("РЕЗУЛЬТАТ",860,ay1+10,30,A*prog(gp,.85,.98))
    if i==3:
        words_reveal(c,["НЕТ СИЛ?","ВСЁ РАВНО ДЕЛАЙ."],t,a0,a0+d*0.85,110,92)
        c.rrect(490,395,790,545,18,6,A); c.rrect(790,445,812,495,6,4,A,fill=True)
        for k in range(5):
            off=a0+0.4+(4-k)*0.35 if k>0 else 99
            on=1-sm(prog(t,off,off+.2))
            if k==0: on=0.55+0.45*math.sin(t*6)
            c.rrect(506+k*56,411,506+k*56+44,529,6,3,A*on,fill=True)
        c.text("10%",640,605,38,A*.7)
    if i==4:
        words_reveal(c,["НЕ ОБЯЗАН ХОТЕТЬ.","ОБЯЗАН ДЕЛАТЬ."],t,a0,a0+d*0.9,110,84)
        on=ease(prog(t,a0+d*0.5,a0+d*0.5+0.5)); cy=470
        c.rrect(460,cy-60,820,cy+60,60,6,A*on,fill=True); c.rrect(460,cy-60,820,cy+60,60,6,A)
        kx=520+240*on
        c.circ(kx,cy,46,fill=True,a=A*(1-on)) 
        c.text("ХОЧУ",300,cy,48,A*(.75*(1-on)+.2)); c.text("НАДО",980,cy,48,A*(.2+.8*on))
    if i==5:
        words_reveal(c,["КАЖДЫЙ ПОВТОР — КИРПИЧ.","СТРОЙ."],t,a0,a0+d*0.9,110,74,1.2)
        c.line([(150,base),(1130,base)],4,A)
        c.person(400,base,1.6,A,refl=True)
        span=d-1.0
        for idx in range(25):
            r_,c_=divmod(idx,5); tt=a0+0.5+idx*span/25
            ap=prog(t,tt,tt+.2)
            if ap<=0: continue
            x=580+c_*90+(45 if r_%2 else 0); y=base-(r_+1)*40
            c.rrect(x+2,y+2,x+88,y+38,4,3,A*.45*(1-prog(t,tt,tt+.35))*ap,fill=True)
            c.rrect(x+2,y+2,x+88,y+38,4,3,A*ap)
    if i==6:
        words_reveal(c,["ЧЕРЕЗ СТО ДНЕЙ ТЫ","БУДЕШЬ ДРУГИМ ЧЕЛОВЕКОМ."],t,a0,a0+d*0.8,100,66,1.3)
        p=ease(prog(t,a0+0.5,a1-0.4)); cx,cy=640,480
        c.circ(cx,cy,118,6,A*.25); arc(c,cx,cy,118,p,8,A)
        c.text("ДЕНЬ",cx,cy-52,24,A*.7); c.text(str(1+int(99*p)),cx,cy+6,84,A)
        if p>.98: c.rays(cx,cy,140,165,18,A*.6*prog(t,a1-0.4,a1),t*.4)
    if i==7:
        words_reveal(c,["ТОГДА ОНИ СПРОСЯТ:","«КАК ТЫ ЭТО СДЕЛАЛ?»"],t,a0,a0+d*0.85,110,70,1.2)
        c.line([(100,base),(1180,base)],4,A)
        xs=[180,270,360,450,830,920,1010,1100]
        for k,x in enumerate(xs):
            tt=a0+0.4+k*0.18; ap=prog(t,tt,tt+.3)
            c.person(x,base,1.1,A*.55*ap,refl=True)
            q=prog(t,tt+.5,tt+.9)*(0.55+0.45*math.sin(t*4+k))
            c.text("?",x,base-100,36,A*q)
        gr=ease(prog(t,a0+0.3,a0+1.2)); c.person(640,base,2.2,A*gr,refl=True)
        st=(640,base-62*2.2-70); c.star(*st,22,A*gr,t*.5); c.rays(st[0],st[1],32,48,14,A*gr*.7,t*.6)
    if i==8:
        c.text("НЕ ОСТАНАВЛИВАЙСЯ.",640,190,104,A*prog(t,a0,a0+0.5),rise=(1-ease(prog(t,a0,a0+.5)))*20)
        for k in range(-1,12):
            x=k*120-(t*330)%120; c.line([(x,base),(x+70,base)],4,A*.85)
        for k,hh in enumerate([-30,-60,-95]):
            for m in range(4):
                x=(m*330+k*110-(t*700)%1320)%1320-20; c.line([(x,base+hh),(x+60,base+hh)],2,A*.18)
        c.person(640,base-4*abs(math.sin(t*5)),1.9,A*prog(t,a0,a0+.4),refl=True)

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
