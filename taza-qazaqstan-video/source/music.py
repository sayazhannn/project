import numpy as np, wave, sys
SR=44100; DUR=float(sys.argv[1]) if len(sys.argv)>1 else 242.0
rng=np.random.default_rng(7)
n=int((DUR+4)*SR); L=np.zeros(n,np.float32); R=np.zeros(n,np.float32)
def hz(m): return 440*2**((m-69)/12)
def add(sig,t0,pan=0.5):
    i=int(t0*SR); j=min(n,i+len(sig))
    if i>=n: return
    s=sig[:j-i]; L[i:j]+=s*(1-pan)*1.4; R[i:j]+=s*pan*1.4
def pad(m,d):
    t=np.arange(int(d*SR))/SR; s=np.zeros_like(t)
    for det in (-0.07,0.0,0.07):
        f=hz(m)*2**(det/12)
        s+=np.sin(2*np.pi*f*t)+0.3*np.sin(2*np.pi*2*f*t)+0.08*np.sin(2*np.pi*3*f*t)
    a=np.minimum(1,t/2.5); r=np.minimum(1,(d-t)/3.0); return (s*a*r*0.05).astype(np.float32)
def bell(m,d=3.5):
    t=np.arange(int(d*SR))/SR; f=hz(m)
    s=np.sin(2*np.pi*f*t)*np.exp(-t*1.6)+0.35*np.sin(2*np.pi*2.01*f*t)*np.exp(-t*3)+0.12*np.sin(2*np.pi*3.99*f*t)*np.exp(-t*5)
    s*=np.minimum(1,t/0.01); return (s*0.11).astype(np.float32)
# gentle uplifting progression in C major: C  G  Am  F
prog=[[48,55,64,67,72],[43,55,62,67,74],[45,52,60,64,72],[41,53,60,65,69]]
ch=9.0; k=0; t=0.0
while t<DUR+2:
    for m in prog[k%4]: add(pad(m,ch+3.0),t,0.5+ (m%5-2)*0.08)
    t+=ch; k+=1
scale=[72,74,76,79,81,84,86]  # C pentatonic, upper register
t=2.0
while t<DUR:
    ch_i=int(t//ch)%4; chord=[m+12 for m in prog[ch_i]]
    for q in range(rng.integers(1,3)):
        m=int(rng.choice(scale+[c for c in chord if 72<=c<=86]))
        add(bell(m),t+q*0.5+rng.random()*0.1,float(rng.uniform(0.25,0.75)))
    t+=rng.choice([1.5,2.0,2.5,3.0])
# soft reverb
def reverb(x):
    ir=np.exp(-np.arange(int(2.2*SR))/SR*2.2)*rng.standard_normal(int(2.2*SR)); ir[:int(.03*SR)]*=0.2
    ir/=np.abs(ir).sum()
    N=1<<int(np.ceil(np.log2(len(x)+len(ir)))); y=np.fft.irfft(np.fft.rfft(x,N)*np.fft.rfft(ir,N),N)[:len(x)]
    return y.astype(np.float32)
Lw=reverb(L); Rw=reverb(R)
L=0.55*L+0.9*Lw; R=0.55*R+0.9*Rw
n0=int(DUR*SR); L=L[:n0]; R=R[:n0]
fi=int(3*SR); fo=int(5*SR)
env=np.ones(n0,np.float32); env[:fi]=np.linspace(0,1,fi)**2; env[-fo:]=np.linspace(1,0,fo)**2
L*=env; R*=env
pk=max(np.abs(L).max(),np.abs(R).max()); g=0.5/pk
out=(np.stack([L,R],1)*g*32767).astype(np.int16)
w=wave.open("music.wav","wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(out.tobytes()); w.close()
print("ok", out.shape)
