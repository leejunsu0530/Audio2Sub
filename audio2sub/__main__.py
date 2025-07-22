import whisper # type: ignore
import srt # type: ignore
import datetime
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, TaskProgressColumn

# === GPU 성능 확인 및 최적 모델 선택 ===
def check_gpu():
    if not torch.cuda.is_available():
        print("❌ GPU를 사용할 수 없습니다. CPU 모드로 실행합니다.")
        return "cpu", 0
    mem = torch.cuda.get_device_properties(0).total_memory // (1024 ** 2)  # MB
    print(f"✅ GPU 사용 가능: {torch.cuda.get_device_name(0)} - {mem}MB")
    return "cuda", mem

def load_best_translation_model(device: str, mem_mb: int):
    if device == "cuda" and mem_mb >= 12000:
        model_name = "facebook/nllb-200-3.3B"
        print("🚀 고성능 GPU 환경 - nllb-200-3.3B 모델 선택")
    else:
        model_name = "facebook/nllb-200-distilled-600M"
        print("⚙️ CPU 또는 중간급 GPU 환경 - distilled-600M 모델 선택")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
    return tokenizer, model

# === 1. 오디오에서 자막 세그먼트 추출 ===
def transcribe_audio(audio_path: str, lang: str = "ja") -> list[dict]:
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language=lang)
    return result['segments']

# === 2. 세그먼트를 SRT 형식으로 저장 ===
def segments_to_srt(segments: list[dict], output_path: str):
    subs = []
    for i, seg in enumerate(segments):
        start = datetime.timedelta(seconds=seg["start"])
        end = datetime.timedelta(seconds=seg["end"])
        content = seg["text"].strip()
        subs.append(srt.Subtitle(index=i + 1, start=start, end=end, content=content))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subs))

# === 3. SRT 자막을 한국어로 번역 (문맥 고려 + rich 프로그레스 포함) ===
def translate_srt_to_korean(srt_path: str, output_path: str):
    device, mem = check_gpu()
    tokenizer, model = load_best_translation_model(device, mem)

    with open(srt_path, "r", encoding="utf-8") as f:
        subtitles = list(srt.parse(f.read()))

    texts = [sub.content for sub in subtitles]
    batch_size = 8
    translated_texts = []

    progress = Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn()
    )

    with progress:
        task = progress.add_task("번역 중...", total=len(texts))

        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            inputs = tokenizer(batch_texts, return_tensors="pt", padding=True, truncation=True).to(device)
            ko_id = tokenizer.lang_code_to_id.get("kor") or tokenizer.lang_code_to_id.get("ko")
            outputs = model.generate(**inputs, forced_bos_token_id=ko_id)
            results = tokenizer.batch_decode(outputs, skip_special_tokens=True)
            translated_texts.extend(results)
            progress.update(task, advance=len(batch_texts))

    for sub, trans in zip(subtitles, translated_texts):
        sub.content = trans

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subtitles))
