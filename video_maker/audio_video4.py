import subprocess, wave, json
M="../tts/vits-piper-ru_RU-denis-medium/ru_RU-denis-medium.onnx"
lines=["Завтра. С понедельника. С нового года.","Ты говоришь это уже много лет.","Идеального момента не существует.",
"Страх уйдёт только после первого шага.","Не готов? Начинай неготовым.","Десять минут. Прямо сейчас.",
"Лучшее время было год назад. Второе лучшее — сегодня.","Встань. Сделай первое действие.","Не завтра. Сегодня."]
durs=[]
for i,t in enumerate(lines):
    subprocess.run(["python3","-m","piper","-m",M,"--length-scale","0.98","--sentence-silence","0.25","-f",f"a/{i}.wav"],input=t.encode(),check=True,capture_output=True)
    w=wave.open(f"a/{i}.wav"); durs.append(w.getnframes()/w.getframerate()); sr=w.getframerate()
json.dump({"durs":durs,"sr":sr,"beep_at":0},open("a/meta.json","w")); print([round(d,1) for d in durs],sum(durs))
