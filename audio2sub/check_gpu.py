import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from typing import Any, Literal


def check_gpu() -> tuple[Literal['cpu'], Literal[0]] | tuple[Literal['cuda'], Any]:
    if not torch.cuda.is_available():
        print("❌ GPU를 사용할 수 없습니다. CPU 모드로 실행합니다.")
        return "cpu", 0

    capability = torch.cuda.get_device_capability(0)
    mem = torch.cuda.get_device_properties(
        0).total_memory // (1024 ** 2)  # MB 단위
    print(f"✅ GPU 사용 가능: {torch.cuda.get_device_name(0)}")
    print(f"    - Compute Capability: {capability}")
    print(f"    - GPU 메모리: {mem}MB")
    return "cuda", mem


def load_best_nllb_model(device: str, mem_mb: int):
    # 고성능 GPU 환경이면 큰 모델 사용
    if device == "cuda" and mem_mb >= 12000:
        model_name = "facebook/nllb-200-3.3B"
        print("🚀 고성능 GPU 환경 - nllb-200-3.3B 모델 선택")
    else:
        model_name = "facebook/nllb-200-distilled-600M"
        print("⚙️ CPU 또는 중간급 GPU 환경 - distilled-600M 모델 선택")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
    return tokenizer, model


def translate_ja_to_ko(text: str, tokenizer, model, device: str) -> str:
    inputs = tokenizer(text, return_tensors="pt", padding=True).to(device)
    ko_id = tokenizer.lang_code_to_id["kor"]
    outputs = model.generate(**inputs, forced_bos_token_id=ko_id)
    translated = tokenizer.batch_decode(outputs, skip_special_tokens=True)
    return translated[0]


# 실행 예시
if __name__ == "__main__":
    device, mem = check_gpu()
    tokenizer, model = load_best_nllb_model(device, mem)

    ja_text = "今日はとても楽しかったです。明日もまた会いましょう。"
    ko_text = translate_ja_to_ko(ja_text, tokenizer, model, device)

    print("\n[원문]", ja_text)
    print("[번역]", ko_text)
