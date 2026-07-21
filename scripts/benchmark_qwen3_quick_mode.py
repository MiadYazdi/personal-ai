from __future__ import annotations

import gc
import json
import time
from pathlib import Path

from llama_cpp import Llama


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = PROJECT_ROOT / "models" / "qwen3-8b" / "Qwen3-8B-Q4_K_M.gguf"

N_CTX = 2048
N_THREADS = 8
MIN_AVAILABLE_GIB = 7.0


def memory_available_gib() -> float:
    for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1]) / 1024 / 1024
    raise RuntimeError("MemAvailable was not found")


def run_case(llm: Llama, label: str, system: str, user: str, max_tokens: int) -> None:
    started = time.perf_counter()

    response = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.1,
        max_tokens=max_tokens,
    )

    elapsed = time.perf_counter() - started
    choice = response["choices"][0]
    content = (choice.get("message", {}).get("content") or "").strip()
    usage = response.get("usage", {})
    completion_tokens = usage.get("completion_tokens", 0)
    tokens_per_second = completion_tokens / elapsed if elapsed > 0 else 0

    print(f"\n--- {label} ---")
    print(content)
    print(f"Elapsed seconds: {elapsed:.2f}")
    print(f"Usage: {json.dumps(usage, ensure_ascii=False)}")
    print(f"Completion tokens per second: {tokens_per_second:.2f}")

    if "<think>" in content:
        print("WARNING: Thinking text was still returned in Quick mode.")


def main() -> None:
    print("=== Qwen3 Quick-mode benchmark ===")
    print(f"Model path: {MODEL_PATH}")
    print(f"Context window: {N_CTX}")
    print(f"CPU threads: {N_THREADS}")

    if not MODEL_PATH.is_file():
        print("ERROR: Model file was not found.")
        return

    available_gib = memory_available_gib()
    print(f"Available RAM before loading: {available_gib:.2f} GiB")

    if available_gib < MIN_AVAILABLE_GIB:
        print(f"ERROR: Less than {MIN_AVAILABLE_GIB:.1f} GiB RAM is available.")
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

        print(f"Model load seconds: {time.perf_counter() - load_started:.2f}")

        run_case(
            llm,
            "Quick Persian response",
            "You are a helpful personal assistant. Answer only in Persian. Be concise.",
            (
                "فقط در یک جملهٔ کوتاه و دوستانه بگو که برای کمک به "
                "برنامه‌ریزی و کدنویسی آماده‌ای.\n/no_think"
            ),
            96,
        )

        run_case(
            llm,
            "Quick English coding response",
            "You are a precise Python assistant. Return only executable Python code.",
            (
                "Write a Python function named add that accepts two integers "
                "and returns their sum.\n/no_think"
            ),
            128,
        )

        print("\nSUCCESS: Quick-mode local inference completed.")

    finally:
        if llm is not None:
            del llm
            gc.collect()
            print("Model object released from the Python process.")


if __name__ == "__main__":
    main()
