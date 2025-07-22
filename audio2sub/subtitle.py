import srt
import datetime

def segments_to_srt(segments, output_path):
    subs = []
    for i, seg in enumerate(segments):
        start = datetime.timedelta(seconds=seg["start"])
        end = datetime.timedelta(seconds=seg["end"])
        content = seg["text"].strip()
        subs.append(srt.Subtitle(index=i+1, start=start, end=end, content=content))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt.compose(subs))


if __name__ == "__main__":
    # 테스트용 더미 세그먼트 만들고 SRT 파일 생성
    dummy_segments = [
        {"start": 0.0, "end": 3.5, "text": "안녕하세요."},
        {"start": 4.0, "end": 7.0, "text": "테스트 자막입니다."},
    ]
    output_file = "test_output.srt"
    print(f"Saving dummy segments to {output_file}")
    segments_to_srt(dummy_segments, output_file)
    print("Done!")