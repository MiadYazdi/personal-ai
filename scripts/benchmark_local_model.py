from __future__ import annotations

import gc
import json
import sys
import time
from pathlib import Path

from llama_cpp import Llama


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_DIR = PROJECT_ROOT / "models" / "qwen3-8b"
MODEL_PATH = MODEL_DIR / "Qwen3-8B-Q4_K_M.gguf"
MANIFEST_PATH = MODEL_DIR / "manifest.json"

N_CTX = 2048
N_THREADS = 8
MIN_AVAILABLE_GIB = 7.0


def memory_available_gib() -> float:
    meminfo = Path("/proc/meminfo").read_text(encoding="utf-8")
    for line in meminfo.splitlines():
        if line.startswith("MemAvailable:"):
            kib = int(line.split()[1])
            return kib / 1024 / 1024
    raise RuntimeError("MemAvailable was not found in /proc/meminfo")


def print_response(label: str, response: dict, elapsed_seconds: float) -> None:
    choice = response["choices"][0]
    message = choice.get("message", {})
    content = message.get("content") or ""
    usage = response.get("usage", {})

    print(f"\n--- {label} ---")
    print(content.strip())
    print(f"Elapsed seconds: {elapsed_seconds:.2f}")
    print(f"Usage: {json.dumps(usage, ensure_ascii=False)}")


def main() -> None:
    print("=== Local Qwen3 8B benchmark ===")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Model path: {MODEL_PATH}")
    print(f"Context window: {N_CTX}")
    print(f"CPU threads: {N_THREADS}")
    print("GPU layers: 0")

    if not MODEL_PATH.is_file():
        print("ERROR: Model file was not found.")
        return

    if not MANIFEST_PATH.is_file():
        print("ERROR: Model manifest was not found.")
        return

    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    print(f"Manifest model: {manifest.get('model_id')}")
    print(f"Manifest SHA-256: {manifest.get('sha256')}")

    available_gib = memory_available_gib()
    print(f"Available RAM before loading: {available_gib:.2f} GiB")

    if available_gib < MIN_AVAILABLE_GIB:
        print(
            f"ERROR: At least {MIN_AVAILABLE_GIB:.1f} GiB available RAM is required "
            "for this controlled test. Close unnecessary applications and try again."
        )
        return

    llm = None

    try:
        load_started = time.perf_counter()

        llm = Llama(
            model_path=str(MODEL_PATH),
            n_ctx=N_CTX,
            n_threads=N_THREADS,
            n_threads_batch=N_THREADS,
            n_gpu_layers=0,
            seed=42,
            verbose=False,
        )

        load_elapsed = time.perf_counter() - load_started
        print(f"Model load seconds: {load_elapsed:.2f}")

        persian_started = time.perf_counter()
        persian_response = llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful personal assistant. "
                        "Answer only in Persian. Be concise."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "فقط در یک جملهٔ کوتاه و دوستانه بگو که "
                        "برای کمک به برنامه‌ریزی و کدنویسی آماده‌ای."
                    ),
                },
            ],
            temperature=0.1,
            max_tokens=80,
        )
        print_response(
            "Persian response",
            persian_response,
            time.perf_counter() - persian_started,
        )

        coding_started = time.perf_counter()
        coding_response = llm.create_chat_completion(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a precise Python programming assistant. "
                        "Return only executable Python code."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Write a Python function named add that accepts "
                        "two integers and returns their sum."
                    ),
                },
            ],
            temperature=0.0,
            max_tokens=80,
        )
        print_response(
            "English coding response",
            coding_response,
            time.perf_counter() - coding_started,
        )

        print("\nSUCCESS: Local model loaded and generated both test responses.")

    except Exception as error:
        print(f"\nERROR: {type(error).__name__}: {error}")
        raise

    finally:
        if llm is not None:
            del llm
            gc.collect()
            print("Model object released from the Python process.")


if __name__ == "__main__":
    main()
