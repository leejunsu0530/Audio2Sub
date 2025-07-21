import whisperx
import os
import tempfile
import subprocess
import srt
from datetime import timedelta
from transformers import MarianMTModel, MarianTokenizer

# 1. Extract audio from video
def extract_audio(video_path, audio_path):
    subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", audio_path], check=True)

# 2. Transcribe Japanese audio to subtitles (.srt)
def transcribe_to_srt(audio_path, srt_path, device="cuda" if torch.cuda.is_available() else "cpu"):
    model = whisperx.load_model("large-v2", device=device, language="ja")
    result = model.transcribe(audio_path)
    model_a, metadata = whisperx.load_align_model(language_code="ja", device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio_path, device=device)
    
    # Convert to SRT format
    srt_list = []
    for seg in result["segments"]:
        srt_list.append(srt.Subtitle(index=seg['id'] + 1,
                                     start=timedelta(seconds=seg['start']),
                                     end=timedelta(seconds=seg['end']),
                                     content=seg['text'].strip()))
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(srt_list))
    return srt_list

# 3. Translate Japanese to Korean using MarianMT
def translate_subtitles(subs, model_name="Helsinki-NLP/opus-mt-ja-ko"):
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model = MarianMTModel.from_pretrained(model_name)

    texts = [sub.content for sub in subs]
    translated = []
    for i in range(0, len(texts), 8):  # batch size = 8
        batch = texts[i:i+8]
        inputs = tokenizer(batch, return_tensors="pt", padding=True, truncation=True)
        outputs = model.generate(**inputs)
        translated_texts = tokenizer.batch_decode(outputs, skip_special_tokens=True)
        translated.extend(translated_texts)

    # Attach translations to the original subs
    for i, sub in enumerate(subs):
        sub.content = translated[i]
    return subs

# 4. Main logic
def main(video_path):
    with tempfile.TemporaryDirectory() as tmpdir:
        audio_path = os.path.join(tmpdir, "audio.wav")
        srt_path = os.path.splitext(video_path)[0] + "_ja.srt"
        srt_ko_path = os.path.splitext(video_path)[0] + "_ko.srt"

        print("🔊 Extracting audio...")
        extract_audio(video_path, audio_path)

        print("📝 Transcribing...")
        subs = transcribe_to_srt(audio_path, srt_path)

        print("🌐 Translating to Korean...")
        subs_ko = translate_subtitles(subs)

        with open(srt_ko_path, "w", encoding="utf-8") as f:
            f.write(srt.compose(subs_ko))

        print(f"✅ Japanese SRT: {srt_path}")
        print(f"✅ Korean SRT: {srt_ko_path}")

# Example usage
if __name__ == "__main__":
    main("your_video.mp4")  # Replace with your actual video file
