import re, numpy as np, torch, torchaudio, jiwer
from faster_whisper import WhisperModel
from pocket_tts import TTSModel
REF="C:/Users/meteh/AppData/Local/Temp/mref.wav"
m=TTSModel.load_model(language="english"); v=m.get_state_for_audio_prompt(REF); asr=WhisperModel("base.en",device="cpu",compute_type="int8")
norm=lambda t:" ".join(re.sub(r"[^a-z0-9' ]+"," ",t.lower()).split())
for text in ["University of Oklahoma meteorologist John Snow said debris like this can rise to thirty thousand or forty thousand feet and ride the winds.",
             "University of Oklahoma meteorologist John Snow said debris like this can rise to thirty or forty thousand feet and ride the winds."]:
  bad=0
  for seed in range(6):
    torch.manual_seed(seed); a=m.generate_audio(v,text).numpy().reshape(-1)
    w=torchaudio.functional.resample(torch.from_numpy(a),m.sample_rate,16000).numpy()
    said=" ".join(s.text for s in asr.transcribe(w,language="en",beam_size=5)[0]); e=jiwer.wer(norm(text),norm(said)); bad+=e>0.05
    if e>0.05: print(seed, round(e,2), said.strip())
  print("BAD",bad,"/6 :", text[60:110])
