import whisper # type: ignore

def load_whisper_model(name="base"):
    return whisper.load_model(name)

def transcribe(model, audio_path, lang="ja"):
    result = model.transcribe(audio_path, language=lang)
    return result['segments']

if __name__ == "__main__":
    # 간단 테스트 코드: 음성 파일을 넣고 자막 세그먼트 출력
    model = load_whisper_model("base")
    audio_file = "sample_audio.mp3"  # 본인 음성 파일 경로로 변경
    print(f"Transcribing {audio_file} ...")
    segments = transcribe(model, audio_file, lang="ja")
    for seg in segments[:3]:  # 앞 3개만 출력
        print(f"[{seg['start']:.1f}-{seg['end']:.1f}] {seg['text']}")