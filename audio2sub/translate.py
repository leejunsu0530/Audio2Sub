import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn, TimeRemainingColumn, TaskProgressColumn


def check_gpu():
    if not torch.cuda.is_available():
        print("❌ No GPU, using CPU")
        return "cpu", 0
    mem = torch.cuda.get_device_properties(0).total_memory // (1024**2)
    print(f"✅ GPU found: {torch.cuda.get_device_name(0)} with {mem} MB")
    return "cuda", mem


def load_translation_model(device, mem_mb):
    if device == "cuda" and mem_mb >= 12000:
        model_name = "facebook/nllb-200-3.3B"
        print("🚀 Using high-end model")
    else:
        model_name = "facebook/nllb-200-distilled-600M"
        print("⚙️ Using distilled model")

    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_name).to(device)
    return tokenizer, model


def chunk_text(texts, chunk_char_limit=800):
    chunks = []
    current = ""
    for line in texts:
        if len(current) + len(line) + 1 <= chunk_char_limit:
            current += line + " "
        else:
            chunks.append(current.strip())
            current = line + " "
    if current:
        chunks.append(current.strip())
    return chunks


def translate_chunks(chunks, tokenizer, model, device):
    translated_texts = []
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
    ) as progress:
        task = progress.add_task("[green]Translating...", total=len(chunks))
        for chunk in chunks:
            inputs = tokenizer(chunk, return_tensors="pt",
                               truncation=True, padding=True).to(device)
            try:
                lang_token = "kor_Hang"
                token_id = tokenizer.convert_tokens_to_ids(lang_token)
                outputs = model.generate(
                    **inputs, forced_bos_token_id=token_id)
            except:
                print("Warning: Cannot force target language. Proceeding with default.")
                outputs = model.generate(**inputs)
            decoded = tokenizer.decode(outputs[0], skip_special_tokens=True)
            translated_texts.append(decoded)
            progress.update(task, advance=1)
    return translated_texts


if __name__ == "__main__":
    # 간단 테스트: 한글 번역 (영어->한국어 예시)
    device_, mem_ = check_gpu()
    tokenizer_, model_ = load_translation_model(device_, mem_)
    test_texts = [
        "Hello, how are you?",
        "This is a test sentence for translation."
    ]
    print("Chunking texts...")
    chunks_ = chunk_text(test_texts, chunk_char_limit=50)
    print("Translating chunks...")
    results = translate_chunks(chunks_, tokenizer_, model_, device_)
    print("\nTranslation results:")
    for res in results:
        print(res)
