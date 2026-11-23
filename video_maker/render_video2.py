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
    exit=1-sm(prog(t,a1+PAD-0.2,a1+PAD)); enter=sm(prog(t,0,0.2)); A=enter*exit
    base=620
    if i==0:
        words_reveal(c,["ХВАТИТ ЖАЛЕТЬ","СЕБЯ."],t,a0,a0+d*0.8,120,92)
        c.line([(640-420*ease(prog(t,0.1,1)),base),(640+420*ease(prog(t,0.1,1)),base)],4,A)
        px=640; c.person(px,base,2.0,A)
        for k in range(3):
            ph=(t*0.7+k/3)%1; y=base-150+ph*140; c.circ(px-22+k*22,y,6,fill=True,a=A*(1-ph)*.9)
        c.text("ЖАЛОСТЬ",px,base+34,22,A*.45)
    if i==1:
        words_reveal(c,["ВСЕМ НА ТВОИ ПРОБЛЕМЫ","[ПИИП]"],t,a0,a0+d*0.9,110,72,1.2)
        c.line([(100,base),(1180,base)],4,A)
        c.person(330,base,2.0,A)
        for k in range(8):
            x=640+k*75+prog(t,0,a1+PAD)*220
            if x<1250: c.person(x,base,0.9,A*.55*max(0,1-(x-1000)/250 if x>1000 else 1))
        c.text("?",330,base-190,52,A*(0.6+0.4*math.sin(t*5)))
    if i==2:
        words_reveal(c,["НИКТО НЕ СДЕЛАЕТ","ЭТО ЗА ТЕБЯ."],t,a0,a0+d*0.8,110,86)
        c.line([(100,base),(1180,base)],4,A)
        wp=ease(prog(t,a0+0.3,a0+1.6)); wx0,wx1=800,940; wh=260*wp
        if wh>2:
            c.rrect(wx0,base-wh,wx1,base,4,4,A)
            for r_ in range(1,int(wh//40)+1):
                yy=base-40*r_; c.line([(wx0,yy),(wx1,yy)],2,A*.6)
                off=35 if r_%2 else 0
                for xx in (wx0+off+35,wx0+off+105):
                    if xx<wx1: c.line([(xx,yy),(xx,min(base,yy+40))],2,A*.6) if False else c.line([(xx,yy),(xx,yy+40)],2,A*.6)
        c.text("ПРОБЛЕМЫ",870,base-wh-26,24,A*.7*wp)
        mv=ease(prog(t,a0+1.0,a1)); c.person(520+mv*190,base,2.0,A)
    if i==3:
        words_reveal(c,["НЕ ХОЧЕТСЯ?","ВСТАВАЙ."],t,a0+0.9,a0+d*0.95,100,92)
        cx,cy=640,470
        c.circ(cx,cy,100,5,A); c.circ(cx-80,cy-90,28,5,A); c.circ(cx+80,cy-90,28,5,A)
        c.line([(cx-55,cy+100),(cx-75,cy+125)],5,A); c.line([(cx+55,cy+100),(cx+75,cy+125)],5,A)
        c.line([(cx,cy),(cx,cy-70)],5,A); c.line([(cx,cy),(cx,cy+48)],7,A); c.circ(cx,cy,7,fill=True,a=A)
        for k in range(12): ang=k*math.pi/6; c.line([(cx+86*math.sin(ang),cy-86*math.cos(ang)),(cx+94*math.sin(ang),cy-94*math.cos(ang))],3,A*.7)
        ring=prog(t,a0,a0+d)
        for k in (0,1,2):
            ph=(t*3+k/3)%1; r_=125+ph*55
            for sgn in (-1,1):
                ax=cx+sgn*r_*1.0; 
                c.line([(cx+sgn*(r_+10),cy-20),(cx+sgn*(r_+22),cy-6),(cx+sgn*(r_+10),cy+8)],3,A*(1-ph)*.8)
        c.text("06:00",cx,cy+185,40,A*.8)
    if i==4:
        words_reveal(c,["БОЛЬ ДИСЦИПЛИНЫ — ВРЕМЕННАЯ","БОЛЬ СОЖАЛЕНИЯ — НАВСЕГДА"],t,a0,a0+d*0.9,90,56,1.35)
        x0=200; L=880
        b1=ease(prog(t,a0+0.2,a0+1.6))*0.22; b2=ease(prog(t,a0+2.4,a1))*1.0
        c.text("ДИСЦИПЛИНА",x0+90,430,24,A*.7); c.rrect(x0,450,x0+L,490,6,3,A*.35); c.rrect(x0,450,x0+max(8,L*b1),490,6,3,A,fill=True)
        c.text("СОЖАЛЕНИЕ",x0+80,550,24,A*.7); c.rrect(x0,570,x0+L,610,6,3,A*.35); c.rrect(x0,570,x0+max(8,L*b2),610,6,3,A,fill=True)
        if b2>.97: c.text("∞",x0+L+60,590,60,A) if False else c.text("НАВСЕГДА",x0+L-90,590,24,0)
    if i==5:
        words_reveal(c,["КАЖДЫЙ ДЕНЬ","ТЫ ВЫБИРАЕШЬ."],t,a0,a0+d*0.55,100,86)
        up=[(500,560),(620,560),(760,440),(1020,440)]; dn=[(620,560),(760,650),(1020,650)]
        gp=ease(prog(t,a0+0.5,a0+1.4)); 
        def part(pts,p):
            L=[0]
            for k in range(1,len(pts)): L.append(L[-1]+math.dist(pts[k-1],pts[k]))
            tg=L[-1]*p; out=[pts[0]]
            for k in range(1,len(pts)):
                if L[k]<=tg: out.append(pts[k])
                else:
                    f=(tg-L[k-1])/(L[k]-L[k-1]); out.append((pts[k-1][0]+(pts[k][0]-pts[k-1][0])*f,pts[k-1][1]+(pts[k][1]-pts[k-1][1])*f)); break
            return out
        c.line([(160,560),(620,560)],4,A*prog(t,0,.5)); 
        late=1-.6*sm(prog(t,a0+d*0.6,a0+d*0.8))
        c.line(part(dn,gp),4,A*late*.7); c.line(part(up,gp),5,A)
        c.person(300,560,1.6,A) if t<a0+d*0.55 else None
        mv=ease(prog(t,a0+d*0.55,a1)); 
        if t>=a0+d*0.55:
            px=300+(1020-300)*0 
            seg=[(300,560),(620,560),(760,440),(1000,440)]
            tot=sum(math.dist(seg[k],seg[k+1]) for k in range(3)); tg=tot*mv; pos=seg[0]
            for k in range(3):
                dl=math.dist(seg[k],seg[k+1])
                if tg<=dl: f=tg/dl; pos=(seg[k][0]+(seg[k+1][0]-seg[k][0])*f,seg[k][1]+(seg[k+1][1]-seg[k][1])*f); break
                tg-=dl; pos=seg[k+1]
            c.person(pos[0],pos[1],1.6,A)
        c.text("УСИЛИЕ",1130,436,34,A*gp)
        c.text("ОПРАВДАНИЕ",1000,620,28,A*gp*late*.6)
    if i==6:
        words_reveal(c,["СДЕЛАЙ СЕГОДНЯ ТО,","ЧЕГО ДРУГИЕ НЕ ХОТЯТ."],t,a0,a0+2.6,100,78)
        cols,rows=10,3; cs=58; gx=640-cols*cs/2; gy=380
        n=int(ease(prog(t,a0+2.4,a1-0.1))*cols*rows)
        for k in range(cols*rows):
            x=gx+(k%cols)*cs+cs/2; y=gy+(k//cols)*cs+cs/2
            c.rrect(x-20,y-20,x+20,y+20,6,3,A*.5)
            if k<n: c.rrect(x-14,y-14,x+14,y+14,4,3,A,fill=True)
        c.text("30 ДНЕЙ",640,590,30,A*.6*prog(t,a0+2.4,a0+3))
    if i==7:
        words_reveal(c,["ЧЕРЕЗ ГОД ТЫ","СКАЖЕШЬ СЕБЕ СПАСИБО."],t,a0,a0+d*0.6,95,72)
        c.line([(100,base),(1180,base)],4,A)
        c.person(380,base,1.5,A*.35); c.text("?",380,base-135,40,A*.35); c.text("ЖДАЛ",380,base+30,22,A*.45)
        gr=ease(prog(t,a0+0.6,a0+3.0)); k=1.5+1.4*gr
        c.person(860,base,k,A); st=(860,base-62*k-70)
        c.star(*st,18+8*gr,A*gr,t*.5); c.rays(st[0],st[1],28+8*gr,42+10*gr,12,A*gr*.7,t*.6)
        c.text("ДЕЛАЛ",860,base+30,22,A*.7)
    if i==8:
        c.text("ХВАТИТ НЫТЬ.",640,170,60,A*prog(t,a0,a0+0.4))
        bt=ease(prog(t,a0+0.8,a0+1.4)); pulse=.5+.5*math.sin(t*4); bw=300+10*pulse
        c.rrect(640-bw,320-70,640+bw,320+70,70,6,A*bt); c.text("ВСТАВАЙ. ИДИ.",640,316,88,A*bt)
        for k in range(20):
            ang=k*math.pi*2/20+t*.2; c.line([(640+(bw+40+8*pulse)*math.cos(ang),320+(112+8*pulse)*math.sin(ang)),(640+(bw+64)*math.cos(ang),320+(136)*math.sin(ang))],2,A*bt*.4)
        c.line([(100,640),(1180,640)],4,A*.5)
        wk=prog(t,a0+0.3,a1+PAD); c.person(200+880*wk,640,1.5,A*prog(t,a0+.3,a0+.8))

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
