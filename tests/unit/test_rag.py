import sys
sys.path.insert(0, "../../backend")
from app.services.rag import keyword_score, build_context

def test_keyword_score():
    assert keyword_score("hello world", "hello there world") > 0.5
    assert keyword_score("xyz", "hello world") == 0
    print("keyword_score ok")

def test_build_context():
    chunks = [
        {"chunk_type":"transcript","content":"hello world","timestamp":1.5},
        {"chunk_type":"frame","content":"a cat","timestamp":2.0},
    ]
    ctx = build_context(chunks)
    assert "[1]" in ctx and "1.5s" in ctx
    print("build_context ok")

if __name__ == "__main__":
    test_keyword_score()
    test_build_context()
    print("All unit tests passed")
