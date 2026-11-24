import subprocess, wave, json, numpy as np
M="../tts/vits-piper-ru_RU-denis-medium/ru_RU-denis-medium.onnx"
def tts(t,out): subprocess.run(["python3","-m","piper","-m",M,"--length-scale","0.98","--sentence-silence","0.25","-f",out],input=t.encode(),check=True,capture_output=True)
def rd(p):
    w=wave.open(p); return np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768, w.getframerate()
lines=["Завтра. С понедельника. С нового года.","Ты говоришь это уже много лет.","Идеального момента не существует.",
"Страх уйдёт только после первого шага.",None,"Десять минут. Прямо сейчас.",
"Лучшее время было год назад. Второе лучшее — сегодня.","Встань. Сделай первое действие.","Не завтра. Сегодня."]
durs=[]; extra={}
for i,t in enumerate(lines):
    if t is None:
        tts("Не готов? Да","a/4a.wav"); tts("похер","a/4b.wav"); tts("Начинай неготовым.","a/4c.wav")
        a,sr=rd("a/4a.wav"); b,_=rd("a/4b.wav"); c,_=rd("a/4c.wav")
        n=len(b); tt=np.arange(n)/sr
        beep=np.sin(2*np.pi*1000*tt)*0.35; beep[:200]*=np.linspace(0,1,200); beep[-200:]*=np.linspace(1,0,200)
        g1=np.zeros(int(sr*0.25)); g2=np.zeros(int(sr*0.2))
        x=np.concatenate([a,g1,beep,g2,c]).astype(np.float32)
        extra={"beep_at":(len(a)+len(g1))/sr,"after_at":(len(a)+len(g1)+n+len(g2))/sr}
        w=wave.open("a/4.wav","wb");w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((x*32767).astype(np.int16).tobytes());w.close()
        durs.append(len(x)/sr)
    else:
        tts(t,f"a/{i}.wav"); a,sr=rd(f"a/{i}.wav"); durs.append(len(a)/sr)
json.dump({"durs":durs,"sr":sr,**extra},open("a/meta.json","w")); print([round(d,1) for d in durs],extra)
