from transcribe import load_whisper_model, transcribe
from subtitle import segments_to_srt
from translate import check_gpu, load_translation_model, chunk_text, translate_chunks
import srt

class AudioTranslatorApp:
    def __init__(self):
        self.whisper_model = load_whisper_model("base")
        self.device, self.mem = check_gpu()
        self.tokenizer, self.translation_model = load_translation_model(self.device, self.mem)

    def transcribe_audio(self, audio_path, lang="ja"):
        return transcribe(self.whisper_model, audio_path, lang)

    def save_srt(self, segments, srt_path):
        segments_to_srt(segments, srt_path)

    def translate_srt(self, srt_input_path, srt_output_path):
        with open(srt_input_path, "r", encoding="utf-8") as f:
            subtitles = list(srt.parse(f.read()))
        texts = [sub.content for sub in subtitles]
        chunks = chunk_text(texts)
        translated_chunks = translate_chunks(chunks, self.tokenizer, self.translation_model, self.device)

        new_subs = []
        offset = 0
        for chunk in translated_chunks:
            lines = chunk.split(". ")
            for line in lines:
                if offset < len(subtitles):
                    sub = subtitles[offset]
                    sub.content = line.strip()
                    new_subs.append(sub)
                    offset += 1
        while offset < len(subtitles):
            new_subs.append(subtitles[offset])
            offset += 1

        with open(srt_output_path, "w", encoding="utf-8") as f:
            f.write(srt.compose(new_subs))

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m your_project path_to_audio")
        exit(1)

    app = AudioTranslatorApp()
    audio_file = sys.argv[1]

    print("Transcribing...")
    segments = app.transcribe_audio(audio_file)

    srt_file = "output_original.srt"
    print("Saving original SRT...")
    app.save_srt(segments, srt_file)

    translated_srt_file = "output_translated.srt"
    print("Translating SRT...")
    app.translate_srt(srt_file, translated_srt_file)

    print("Done!")
