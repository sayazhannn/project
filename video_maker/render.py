import json, math, sys, subprocess, numpy as np, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,S=1280,720,30,2
meta=json.load(open("a/meta.json")); D=meta["durs"]
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
STARS=[(random.randint(0,W),random.randint(0,H),random.randint(25,70),random.random()*6) for _ in range(70)]
def background(t):
    im=Image.new("L",(W,H),0); d=ImageDraw.Draw(im)
    for x,y,b,ph in STARS:
        v=int(b*(0.6+0.4*math.sin(t*1.5+ph))); d.point((x,y),fill=v)
    return np.array(im,dtype=np.float32)

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
    def person(s,x,y,k=1,a=1):  # x,y = feet
        s.circ(x,y-62*k,13*k,a=a,fill=True)
        s.d.rounded_rectangle([(x-19*k)*S,(y-46*k)*S,(x+19*k)*S,(y)*S],int(14*k*S),fill=s.v(a))
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

def scene(i,t,c):
    d=D[i]; a0=LEAD; a1=LEAD+d
    exit=1-sm(prog(t,a1+PAD-0.2,a1+PAD))     # fade-out
    enter=sm(prog(t,0,0.2))
    A=enter*exit
    if i==0:
        words_reveal(c,["ХВАТИТ ЖДАТЬ","МОТИВАЦИЮ."],t,a0,a0+d*0.8,120,92)
        base=620; gl=prog(t,0.1,1.0)
        c.line([(640-420*ease(gl),base),(640+420*ease(gl),base)],4,A)
        px=470; c.person(px,base,1.9,A)
        q=0.6+0.4*math.sin(t*5); c.text("?",px,base-185,64,A*q)
        # clock
        cx,cy=830,base-110
        c.circ(cx,cy,70,4,A); 
        for k in range(12): ang=k*math.pi/6; c.line([(cx+60*math.sin(ang),cy-60*math.cos(ang)),(cx+68*math.sin(ang),cy-68*math.cos(ang))],3,A*.8)
        c.line([(cx,cy),(cx+52*math.sin(t*2.2),cy-52*math.cos(t*2.2))],4,A)
        c.line([(cx,cy),(cx+34*math.sin(t*0.18),cy-34*math.cos(t*0.18))],5,A)
        c.circ(cx,cy,6,fill=True,a=A)
    if i==1:
        words_reveal(c,["ОНА НЕ ПРИДЁТ.","НИКТО НЕ ПРИДЁТ."],t,a0,a0+d*0.8,120,92)
        base=620
        c.line([(100,base),(1180,base)],4,A)
        c.person(380,base,1.9,A)
        u=prog(t,0.3,a1+PAD)
        ox=760+ease(u)*480; oy=base-150-ease(u)*60
        fade=A*(1-sm(prog(u,0.35,1.0)))*(0.85+0.15*math.sin(t*20) if u>0.2 else 1)
        c.circ(ox,oy,26,fill=True,a=fade); c.circ(ox,oy,44,2,a=fade*.6)
        for k in range(14):
            x0=470+k*32
            if x0<ox-60: c.line([(x0,oy+ (base-150-oy)*0),(x0+14,oy)],3,A*.35*(1-u))
    if i==2:
        t1=prog(t,a0,a0+d*0.9)
        words_reveal(c,["МОТИВАЦИЯ —","ВСПЫШКА"],t,a0,a0+1.6,105,88)
        ax0,ax1,ay0,ay1=330,950,640,300
        c.line([(ax0,ay1-10),(ax0,ay0),(ax1,ay0)],3,A*.8)
        gp=prog(t,a0+1.4,a1-0.3); pts=[]
        n=90
        for k in range(int(n*gp)+1):
            x=k/n
            y=(1-math.exp(-x*28))*math.exp(-x*3.3)*1.05
            pts.append((ax0+10+x*(ax1-ax0-30),ay0-8-clamp(y,0,1)*(ay0-ay1-30)))
        if len(pts)>1: c.line(pts,5,A)
        if pts: c.circ(pts[-1][0],pts[-1][1],9,fill=True,a=A); c.circ(pts[-1][0],pts[-1][1],18,2,a=A*.5)
        for k,lab in enumerate(["ДЕНЬ 1","ДЕНЬ 3","ДЕНЬ 7"]):
            c.text(lab,ax0+90+k*220,ay0+26,22,A*.6*prog(t,a0+1.6+k*.6,a0+2.1+k*.6))
    if i in (3,4,5,6+0*i) and i<=5:
        pass
    if i==3:
        words_reveal(c,["ДИСЦИПЛИНА","— ЭТО СТУПЕНИ"],t,a0,a0+2.0,100,84)
        sp=ease(prog(t,a0+0.8,a1-0.2)); 
        stairs(c,sp,A)
        sa=prog(t,a1-1.0,a1); c.star(*STAR,22,A*sa,t*.5); c.rays(*STAR,32,46,12,A*sa*.7,t*.6)
        c.person(STX0-120,STY0,1.3,A*prog(t,a0+0.2,a0+0.8)*0.0+A*0.0)
    if i==4:
        words_reveal(c,["НЕ ХОЧЕТСЯ?","ПЛЕВАТЬ."],t,a0,a0+d*0.8,100,84)
        stairs(c,1,A*.9); c.star(*STAR,22,A,t*.5); c.rays(*STAR,32,46,12,A*.7,t*.6)
        u=ease(prog(t,a0+0.9,a1+0.2))*3
        x,y=pos_at(u); c.person(x,y,1.3,A)
    if i==5:
        stairs(c,1,A*.9); c.star(*STAR,22,A,t*.5); c.rays(*STAR,32,46,12,A*.7,t*.6)
        seg=[("ОДИН ШАГ.",0.02),("ЕЩЁ ОДИН.",0.38),("И ЕЩЁ.",0.72)]
        for k,(txt,ts) in enumerate(seg):
            tt=a0+d*ts; 
            show=prog(t,tt,tt+0.3)*(1-prog(t,a0+d*(seg[k+1][1] if k<2 else 2)-0.05,a0+d*(seg[k+1][1] if k<2 else 2)+0.2))
            c.text(txt,640,120,96,A*show,rise=(1-ease(prog(t,tt,tt+.3)))*20)
        u=3+ease(prog(t,a0,a1+0.2))*3
        x,y=pos_at(min(u,N-0.001)); c.person(x,y,1.3,A)
        c.text(f"ШАГ {min(int(u-2),4)+0 if u<N else 4}",1130,640,26,A*.5) if False else None
    if i==6:
        y1,y2=250,380; f=F(76)
        w1=c.d.textlength("ОПРАВДАНИЯ",font=f)/S; w2=c.d.textlength("ДЕЙСТВОВАТЬ",font=f)/S
        a1_=prog(t,a0,a0+.4); r1=ease(prog(t,a0+0.8,a0+1.3))
        c.rrect(300,y1-34,368,y1+34,10,5,A*a1_); c.text("ОПРАВДАНИЯ",400+w1/2,y1,76,A*a1_*(1-.55*r1))
        if r1>0: c.line([(392,y1+2),(392+(w1+22)*r1,y1+2)],7,A)
        if r1>0 and r1>.5: c.line([(318,y1-16),(350,y1+16)],4,A*.8); c.line([(350,y1-16),(318,y1+16)],4,A*.8)
        ra=prog(t,a0+1.5,a0+1.9); ck=ease(prog(t,a0+2.0,a0+2.5))
        c.rrect(300,y2-34,368,y2+34,10,5,A*ra); c.text("ДЕЙСТВОВАТЬ",400+w2/2,y2,76,A*ra)
        if ck>0:
            p1=min(1,ck*2); p2=max(0,ck*2-1)
            pts=[(316,y2+2),(316+16*p1,y2+2+18*p1)]
            if p2>0: pts.append((332+26*p2,y2+20-44*p2))
            c.line(pts,7,A)
        cols=14
        for k in range(cols):
            on=prog(t,a0+2.7+k*0.04,a0+2.9+k*0.04)
            x=640-(cols*46)/2+k*46+23; yy=560
            c.rrect(x-17,yy-17,x+17,yy+17,6,3,A*.5)
            if on>0: c.rrect(x-12,yy-12,x+12,yy+12,4,3,A*on,fill=True)
        c.text("КАЖДЫЙ ДЕНЬ",640,640,24,A*.55*prog(t,a0+2.9,a0+3.3))
    if i==7:
        words_reveal(c,["ЧЕРЕЗ МЕСЯЦ","ТЫ НЕ УЗНАЕШЬ СЕБЯ"],t,a0,a0+d*0.85,70,72,1.1)
        stairs(c,1,A*.55)
        # old self faded at bottom, new self on top glowing
        c.person(STX0,STY0,1.3,A*.35)
        c.text("?",STX0,STY0-125,40,A*.35)
        m=ease(prog(t,a0+0.8,a0+2.0))
        x,y=pos_at(N-0.0001); 
        c.star(*STAR,22,A,t*.5); c.rays(*STAR,32,50,14,A*.8,t*.6)
        c.person(STX0+SW*N-SW*0.5,STY0-SH*N,1.5,A*m)
    if i==8:
        c.text("ХВАТИТ ДУМАТЬ.",640,190,30,A*prog(t,0.2,0.8)*.75)
        bt=ease(prog(t,a0+1.0,a0+1.6)); pulse=0.5+0.5*math.sin(t*4)
        bw=340+10*pulse
        c.rrect(640-bw,300-70,640+bw,300+70,70,6,A*bt)
        c.text("НАЧНИ СЕЙЧАС",640,296,92,A*bt)
        for k in range(20):
            ang=k*math.pi*2/20+t*.2; c.line([(640+(bw+50+10*pulse)*math.cos(ang)*1.0,300+(120+8*pulse)*math.sin(ang)),(640+(bw+75)*math.cos(ang),300+(145)*math.sin(ang))],2,A*bt*.45)
        c.person(640,640,1.7,A*prog(t,a0+1.2,a0+1.8))

def frame(f):
    t=f/FPS
    # find scene
    i=0
    for k,s in enumerate(starts):
        if t>=s: i=k
    c=C(); scene(i,t-starts[i],c)
    sharp=c.im.resize((W,H),Image.LANCZOS)
    g1=sharp.filter(ImageFilter.GaussianBlur(5)); g2=sharp.filter(ImageFilter.GaussianBlur(22)); g3=sharp.filter(ImageFilter.GaussianBlur(60))
    arr=np.array(sharp,np.float32)*1.0+np.array(g1,np.float32)*.12+np.array(g2,np.float32)*.28+np.array(g3,np.float32)*.35
    arr=np.maximum(arr,0)+background(t)
    # vignette
    yy,xx=np.mgrid[0:H,0:W]; vg=1-0.35*(((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2)/2
    arr=np.clip(arr*vg,0,255)
    # fade in/out whole video
    fa=min(1,t/0.3)*min(1,(TOTAL-t)/0.4); arr*=fa
    return np.repeat(arr.astype(np.uint8)[:,:,None],3,2)

if __name__=="__main__":
    a,b=int(sys.argv[1]),int(sys.argv[2]); out=sys.argv[3]
    p=subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-c:v","libx264","-preset","fast","-crf","16","-pix_fmt","yuv420p",out],stdin=subprocess.PIPE)
    for f in range(a,b): p.stdin.write(frame(f).tobytes())
    p.stdin.close(); p.wait()
