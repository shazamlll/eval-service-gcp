"""Real local HTTP smoke; no external services, credentials, or paid APIs."""
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx


def main():
    root = Path(__file__).resolve().parents[1]
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False, timeout=2) as client:
            deadline = time.monotonic() + 15
            while True:
                if process.poll() is not None:
                    raise RuntimeError(process.stderr.read())
                try:
                    response = client.get("/health")
                    response.raise_for_status()
                    break
                except httpx.ConnectError:
                    if time.monotonic() >= deadline:
                        raise
                    time.sleep(0.05)
            assert response.json() == {"status": "ok"}
            assert client.get("/").json()["builtin_cases"] == 15
            for request_args in ({}, {"json": {}}, {"json": {"items": []}}):
                response = client.post("/evaluate", **request_args)
                response.raise_for_status()
                summary = response.json()["summary"]
                assert summary["passed"] == 13 and summary["failed"] == 2
                assert summary["verdict"] == "pass"
            response = client.post("/evaluate", json={"threshold": 0.8667})
            assert response.json()["summary"]["verdict"] == "fail"
            response = client.post("/evaluate", json={"items": [
                {"question": "Shipping cost?", "answer": "", "expected": "Shipping costs $5."}
            ]})
            assert response.status_code == 200
            assert response.json()["summary"]["verdict"] == "fail"
            assert client.post("/evaluate", json={"itmes": []}).status_code == 422
            response = client.post("/evaluate", content='{"threshold": NaN}',
                                   headers={"Content-Type": "application/json"})
            assert response.status_code == 422
            print("HTTP smoke PASS: health/info, absent/empty body, custom failure, threshold boundary, validation")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
        process.stderr.close()


if __name__ == "__main__":
    main()
