import subprocess, wave, json, numpy as np, os
M="../tts/vits-piper-ru_RU-denis-medium/ru_RU-denis-medium.onnx"
lines=[
"Хватит ждать мотивацию.",
"Она не придёт. Никто не придёт за тебя.",
"Мотивация — это вспышка. Через два дня её нет.",
"Дисциплина — это ступени. Ты поднимаешься по ним каждый день. Без исключений.",
"Не хочется? Плевать. Делай.",
"Один шаг. Ещё один. И ещё.",
"Забудь про оправдания. Просто действуй. Каждый день.",
"Через месяц ты не узнаешь себя. Если не остановишься.",
"Хватит думать. Начни сейчас.",
]
os.makedirs("a",exist_ok=True); durs=[]
for i,t in enumerate(lines):
    subprocess.run(["python3","-m","piper","-m",M,"--length-scale","0.98","--sentence-silence","0.25","-f",f"a/{i}.wav"],input=t.encode(),check=True,capture_output=True)
    w=wave.open(f"a/{i}.wav"); durs.append(w.getnframes()/w.getframerate()); sr=w.getframerate()
print(durs,sr)
json.dump({"durs":durs,"sr":sr},open("a/meta.json","w"))
