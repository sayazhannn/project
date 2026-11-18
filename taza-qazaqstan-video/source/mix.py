import numpy as np, wave, subprocess
BEAT=60/95.0; PH=0.27; SR=44100
subprocess.run(["ffmpeg","-y","-loglevel","error","-i","track.mp3","-ac","2","-ar",str(SR),"track_st.wav"],check=True)
w=wave.open("track_st.wav"); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).astype(np.float32)/32768
N=len(x); print("track",N/SR)
jb,ja=32,144
b0=int((PH+jb*BEAT)*SR); a_end=int((PH+ja*BEAT)*SR)
# refine join: align tail of A with the audio just before b0
m=x.mean(1); L=int(0.25*SR); ref=m[a_end-L:a_end]
best=None
for d in range(-int(0.05*SR),int(0.05*SR)+1,4):
    seg=m[b0-L+d:b0+d]
    c=float(np.dot(ref,seg)/(np.linalg.norm(ref)*np.linalg.norm(seg)+1e-9))
    if best is None or c>best[0]: best=(c,d)
print("join corr %.3f shift %.1f ms"%(best[0],best[1]/SR*1000))
b0+=best[1]
A=x[:a_end]; B=x[b0:]
cf=int(0.03*SR); fo=np.linspace(1,0,cf)[:,None]; fi=1-fo
mid=A[-cf:]*fo+B[:cf]*fi
out=np.concatenate([A[:-cf],mid,B[cf:]])
print("mix length %.2f s"%(len(out)/SR))
o=(np.clip(out,-1,1)*32767).astype(np.int16)
w=wave.open("music_mix.wav","wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(o.tobytes()); w.close()
