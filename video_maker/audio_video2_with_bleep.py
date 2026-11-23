import subprocess, wave, json, numpy as np
M="../tts/vits-piper-ru_RU-denis-medium/ru_RU-denis-medium.onnx"
def tts(t,out): subprocess.run(["python3","-m","piper","-m",M,"--length-scale","0.98","--sentence-silence","0.25","-f",out],input=t.encode(),check=True,capture_output=True)
def rd(p):
    w=wave.open(p); return np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768, w.getframerate()
lines=["Хватит жалеть себя.",None,"Никто не сделает это за тебя.","Просыпайся в шесть. Не хочется? Вставай.",
"Боль дисциплины временная. Боль сожаления навсегда.","Каждый день ты выбираешь. Усилие или оправдание.",
"Сделай сегодня то, чего другие не хотят. И завтра будешь жить так, как они не могут.",
"Через год ты скажешь себе спасибо. Или будешь жалеть.","Хватит ныть. Вставай. Иди."]
durs=[]
for i,t in enumerate(lines):
    if t is None:
        tts("Всем на твои проблемы","a/1a.wav"); tts("похер","a/1b.wav")
        a,sr=rd("a/1a.wav"); b,_=rd("a/1b.wav")
        n=len(b); tt=np.arange(n)/sr
        beep=np.sin(2*np.pi*1000*tt)*0.35; beep[:200]*=np.linspace(0,1,200); beep[-200:]*=np.linspace(1,0,200)
        x=np.concatenate([a,np.zeros(int(sr*0.08)),beep]).astype(np.float32)
        w=wave.open("a/1.wav","wb");w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((x*32767).astype(np.int16).tobytes());w.close()
        durs.append(len(x)/sr)
    else:
        tts(t,f"a/{i}.wav"); a,sr=rd(f"a/{i}.wav"); durs.append(len(a)/sr)
json.dump({"durs":durs,"sr":sr},open("a/meta.json","w")); print([round(d,1) for d in durs],sum(durs))
