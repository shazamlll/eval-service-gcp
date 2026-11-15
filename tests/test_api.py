from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_returns_service_info():
    r = client.get("/")
    assert r.status_code == 200
    body = r.json()
    assert body["service"] == "eval-service-gcp"
    assert body["version"] == "0.1.0"
    assert body["builtin_cases"] == 15
    assert "/evaluate" in body["endpoints"]


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_evaluate_builtin_set():
    r = client.post("/evaluate", json={})
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total"] == 15
    # 13 good sample answers pass; the 2 deliberately weak ones fail.
    assert body["summary"]["passed"] == 13
    assert body["summary"]["failed"] == 2
    assert body["summary"]["pass_rate"] == round(13 / 15, 4)
    assert body["summary"]["threshold"] == 0.8
    assert body["summary"]["verdict"] == "pass"
    # Per-case scores are in range and the weak cases really failed.
    failed_ids = {res["id"] for res in body["results"] if not res["passed"]}
    assert failed_ids == {"bks-14", "bks-15"}
    for res in body["results"]:
        assert set(res["scores"]) == {"groundedness", "relevance", "accuracy"}
        assert all(0 <= v <= 2 for v in res["scores"].values())
        assert res["total"] == sum(res["scores"].values())


def test_evaluate_custom_items_good_answer_passes():
    r = client.post(
        "/evaluate",
        json={
            "items": [
                {
                    "question": "How much is shipping to Canada?",
                    "answer": "Shipping to Canada is $6.99 and takes 5-8 business days.",
                    "expected": "Shipping to Canada costs $6.99 and takes 5-8 business days.",
                }
            ]
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total"] == 1
    assert body["summary"]["passed"] == 1
    assert body["summary"]["verdict"] == "pass"
    assert body["results"][0]["id"] is None


def test_evaluate_custom_items_bad_answer_fails():
    r = client.post(
        "/evaluate",
        json={
            "items": [
                {
                    "question": "What is the price of 'The Midnight Bakery' paperback?",
                    "answer": "It is a great book and everyone loves it.",
                    "expected": "The paperback of 'The Midnight Bakery' costs $14.99.",
                }
            ]
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["passed"] == 0
    assert body["summary"]["verdict"] == "fail"
    assert body["results"][0]["total"] <= 1


def test_threshold_logic():
    # 1 good + 1 bad = 50% pass rate. Default threshold 0.8 -> fail.
    payload = {
        "items": [
            {
                "question": "Can I gift-wrap my order?",
                "answer": "Yes, we offer gift wrapping for $3.50 per order.",
                "expected": "Yes, gift wrapping is available for $3.50 per order.",
            },
            {
                "question": "Can I pick up my order in store?",
                "answer": "Our store is open every day.",
                "expected": "Yes, in-store pickup is available at our Portland location with 2 hours notice.",
            },
        ]
    }
    r = client.post("/evaluate", json=payload)
    assert r.status_code == 200
    assert r.json()["summary"]["pass_rate"] == 0.5
    assert r.json()["summary"]["verdict"] == "fail"

    # Same payload with a 0.5 threshold -> pass.
    r = client.post("/evaluate", json={**payload, "threshold": 0.5})
    assert r.status_code == 200
    assert r.json()["summary"]["threshold"] == 0.5
    assert r.json()["summary"]["verdict"] == "pass"


def test_evaluate_empty_answer_scores_zero():
    r = client.post(
        "/evaluate",
        json={
            "items": [
                {
                    "question": "Do you sell ebooks?",
                    "answer": "",
                    "expected": "Yes, most titles are available as ebooks in EPUB and PDF formats.",
                }
            ]
        },
    )
    assert r.status_code == 200
    res = r.json()["results"][0]
    assert res["scores"] == {"groundedness": 0, "relevance": 0, "accuracy": 0}
    assert res["passed"] is False


def test_evaluate_rejects_bad_threshold():
    r = client.post("/evaluate", json={"threshold": 1.5})
    assert r.status_code == 422
