from google.cloud import translate_v2 as translate

def test_translation():
    client = translate.Client()
    text = "Hello, how are you?"
    
    result = client.translate(text, source_language="en", target_language="ko")
    print("번역 결과:", result["translatedText"])

test_translation()
