import subprocess, wave, json
M="../tts/vits-piper-ru_RU-denis-medium/ru_RU-denis-medium.onnx"
lines=["Они спят. Ты работаешь.","Никто не аплодирует в пять утра.","Результат приходит тихо. Без свидетелей.",
"Нет сил? Всё равно делай.","Ты не обязан хотеть. Ты обязан делать.","Каждый повтор — кирпич. Строй.",
"Через сто дней ты будешь другим человеком.","Тогда они спросят: как ты это сделал?","Не останавливайся."]
durs=[]
for i,t in enumerate(lines):
    subprocess.run(["python3","-m","piper","-m",M,"--length-scale","0.98","--sentence-silence","0.25","-f",f"a/{i}.wav"],input=t.encode(),check=True,capture_output=True)
    w=wave.open(f"a/{i}.wav"); durs.append(w.getnframes()/w.getframerate()); sr=w.getframerate()
json.dump({"durs":durs,"sr":sr,"beep_at":0},open("a/meta.json","w")); print([round(d,1) for d in durs],sum(durs))
