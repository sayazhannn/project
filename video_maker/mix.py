import json,wave,numpy as np
m=json.load(open("a/meta.json")); tl=json.load(open("timeline.json")); sr=m["sr"]; SR=44100
tot=int(tl["total"]*SR); voice=np.zeros(tot,np.float32)
for i,s in enumerate(tl["starts"]):
    w=wave.open(f"a/{i}.wav"); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
    x=np.interp(np.arange(int(len(x)*SR/sr))*sr/SR,np.arange(len(x)),x)
    o=int(s*SR); voice[o:o+len(x)]+=x[:tot-o]
t=np.arange(tot)/SR
pad=sum(a*np.sin(2*np.pi*f*t+p) for f,a,p in [(110,1,0),(164.8,.7,1),(220,.5,2),(277.2,.25,3),(55,.9,0)])
pad*= (0.6+0.4*np.sin(2*np.pi*t/9)); pad/=np.abs(pad).max(); pad*=0.12
pad*=np.minimum(1,t/2)*np.minimum(1,(tl["total"]-t)/2)
def wr(n,x):
    x=np.clip(x,-1,1); w=wave.open(n,"wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype(np.int16).tobytes()); w.close()
for s in tl["starts"]:
    o=int(s*SR); n=int(0.6*SR); tt=np.arange(n)/SR
    hit=np.sin(2*np.pi*(48+40*np.exp(-tt*18))*tt)*np.exp(-tt*7)*0.9
    pad[o:o+n]+=hit[:max(0,len(pad)-o)][:n].astype(np.float32)*1.0 if False else 0
    voice_hit=hit
    thump=np.zeros(tot,np.float32); thump[o:o+n]=hit[:tot-o][:n]; globals().setdefault("TH",np.zeros(tot,np.float32)); TH+=thump
wr("thump.wav",TH)
wr("voice.wav",voice); wr("pad.wav",pad.astype(np.float32))
