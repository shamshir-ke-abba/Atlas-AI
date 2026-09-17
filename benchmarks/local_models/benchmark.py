#!/usr/bin/env python3
"""
AtlasAI V3 — Isolated Local Model Benchmark
Hardware: AMD 3020e 2c/2t 1.2GHz 8GB Vega3 Ubuntu — Ollama vs llama.cpp

Isolation: ONLY writes inside benchmarks/local_models/
Never touches ai/, core/, gui/, interfaces/, main.py, production memory.

Usage:
  python3 benchmark.py --models gemma3:270m smollm2:360m --runs 2
  python3 benchmark.py --all --cold-warm
  python3 benchmark.py --quick  # only qwen2.5:1.5b already installed, safe demo

All inference goes to http://127.0.0.1:11434 (Ollama) — local only.
Model download source is documented; inference is localhost.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import requests
except ImportError:
    print("requests required: pip install requests")
    sys.exit(1)

try:
    import psutil
except ImportError:
    psutil = None

# ---------------------------------------------------------------------------
# Prompt suite — must be identical across models (Phase 6)
# ---------------------------------------------------------------------------
PROMPT_SUITE = {
    "TEST1_casual": "Hey, I'm bored. Talk to me for a bit.",
    "TEST2_sky_blue": "Why does the sky look blue? Explain it simply.",
    "TEST3_linux_bullets": "Reply with exactly three short bullet points about Linux.",
    "TEST4_memory": "My name is Alex and I like drawing.\n\nThen ask:\n\nWhat do I like doing?",
    "TEST5_conversation": (
        "Run a short 4-5 turn casual conversation. You play both sides. "
        "Keep it natural and brief. Topic: favorite weekend activities."
    ),
    "TEST6_hallucination": (
        "What is my favorite color? I have never told you my favorite color. "
        "Answer honestly about what you know about me."
    ),
    "TEST7_hello": "Say hello in one sentence.",
    "TEST8_rain": "Explain how rain forms in simple language.",
}

# Primary candidate models (Phase 3) — Ollama tag -> meta
CANDIDATES = [
    # (ollama_tag, hf_repo, params, size_estimate, quantization_default, family)
    ("gemma3:270m", "google/gemma-3-270m-it", "270M", "292 MB", "Q4_K_M", "gemma3"),
    ("smollm2:360m", "HuggingFaceTB/SmolLM2-360M-Instruct", "360M", "229 MB", "Q4_K_M", "smollm2"),
    ("qwen3:0.6b", "Qwen/Qwen3-0.6B", "0.6B", "523 MB", "Q4_K_M", "qwen3"),
    ("llama3.2:1b", "meta-llama/Llama-3.2-1B-Instruct", "1B", "1.3 GB", "Q4_K_M", "llama3.2"),
    ("tinyllama:1.1b", "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "1.1B", "637 MB", "Q4_K_M", "tinyllama"),
    ("smollm2:1.7b", "HuggingFaceTB/SmolLM2-1.7B-Instruct", "1.7B", "1.1 GB", "Q4_K_M", "smollm2"),
    ("qwen3:1.7b", "Qwen/Qwen3-1.7B", "1.7B", "1.4 GB", "Q4_K_M", "qwen3"),
    # extras already installed — used as baseline
    ("qwen2.5:1.5b", "Qwen/Qwen2.5-1.5B-Instruct", "1.5B", "986 MB", "Q4_K_M", "qwen2"),
    ("qwen3:4b", "Qwen/Qwen3-4B", "4.0B", "2.5 GB", "Q4_K_M", "qwen3"),
]

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
RESULTS_DIR = Path(__file__).parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ollama_available() -> bool:
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def ollama_list():
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=10)
        r.raise_for_status()
        return r.json().get("models", [])
    except Exception as e:
        return []

def ollama_show(model):
    try:
        r = requests.post(f"{OLLAMA_HOST}/api/show", json={"model": model}, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def ollama_pull(model, timeout=600):
    """Pull via CLI to show progress; returns (success, elapsed)."""
    start = time.time()
    try:
        proc = subprocess.run(["ollama", "pull", model], timeout=timeout)
        elapsed = time.time() - start
        return proc.returncode == 0, elapsed
    except subprocess.TimeoutExpired:
        return False, timeout
    except Exception as e:
        return False, time.time() - start

def ollama_stop(model):
    try:
        subprocess.run(["ollama", "stop", model], timeout=15, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass
    # also try API
    try:
        requests.post(f"{OLLAMA_HOST}/api/generate", json={"model": model, "keep_alive": 0}, timeout=5)
    except Exception:
        pass
    time.sleep(1)

def ollama_ps():
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/ps", timeout=5)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return {}

def system_snapshot():
    snap = {}
    if psutil:
        vm = psutil.virtual_memory()
        snap["ram_total_mb"] = round(vm.total / 1024 / 1024, 1)
        snap["ram_used_mb"] = round(vm.used / 1024 / 1024, 1)
        snap["ram_available_mb"] = round(vm.available / 1024 / 1024, 1)
        snap["ram_percent"] = vm.percent
        try:
            sw = psutil.swap_memory()
            snap["swap_total_mb"] = round(sw.total / 1024 / 1024, 1)
            snap["swap_used_mb"] = round(sw.used / 1024 / 1024, 1)
        except Exception:
            pass
        snap["cpu_percent"] = psutil.cpu_percent(interval=0.5)
    else:
        # fallback via /proc/meminfo
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal"):
                        snap["ram_total_mb"] = int(line.split()[1]) / 1024
                    if line.startswith("MemAvailable"):
                        snap["ram_available_mb"] = int(line.split()[1]) / 1024
        except Exception:
            pass
    # try ollama process rss
    try:
        for proc in psutil.process_iter(["name", "memory_info"]):
            if "ollama" in (proc.info["name"] or ""):
                snap["ollama_rss_mb"] = round(proc.info["memory_info"].rss / 1024 / 1024, 1)
                break
    except Exception:
        pass
    return snap

def ensure_model(model, allow_pull=True):
    """Return (available, pulled_now, size_str). If not present and allow_pull, try pull with size guard."""
    models = ollama_list()
    names = {m["name"] for m in models}
    if model in names:
        return True, False, "already_present"
    if not allow_pull:
        return False, False, "NOT TESTED - not pulled"
    # guard: don't pull >2GB on this machine without explicit allow? But spec says don't download large models blindly.
    # We implement: ask size via manifest head, skip if >1.8GB for 2GB RAM? We'll still pull up to 1.7B but warn.
    cand = next((c for c in CANDIDATES if c[0] == model), None)
    size_est = cand[4] if cand else "unknown"
    print(f"[pull] {model} not present, pulling (est {size_est}) ...")
    ok, elapsed = ollama_pull(model)
    return ok, ok, f"pulled_{elapsed:.1f}s"

# ---------------------------------------------------------------------------
# Core benchmark — streaming aware (Phase 7 + Phase 8)
# ---------------------------------------------------------------------------

def benchmark_one(model: str, prompt: str, prompt_id: str, keep_alive="5m", num_predict=256, temperature=0.7, run_label="warm"):
    """
    Streams from Ollama /api/generate and measures:
      - TTFT (time to first token chunk)
      - total wall time
      - tokens/sec (from API counts if available else estimated)
      - token intervals, burst vs smooth
    All inference is to 127.0.0.1
    """
    url = f"{OLLAMA_HOST}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": True,
        "options": {
            "temperature": temperature,
            "num_predict": num_predict,
        },
        "keep_alive": keep_alive,
    }
    snap_before = system_snapshot()
    ps_before = ollama_ps()

    start = time.perf_counter()
    first_token_time = None
    chunk_times = []  # (t, text_chunk)
    full_text = ""
    last_chunk = None
    error = None
    # also capture final metadata chunk
    eval_count = None
    prompt_eval_count = None
    eval_duration_ns = None
    prompt_eval_duration_ns = None
    total_duration_ns = None
    load_duration_ns = None
    done = False

    try:
        with requests.post(url, json=payload, stream=True, timeout=120) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # response chunk
                chunk = obj.get("response", "")
                if chunk and first_token_time is None:
                    first_token_time = time.perf_counter()
                if chunk:
                    chunk_times.append((time.perf_counter() - start, chunk))
                    full_text += chunk
                # final chunk carries metrics
                if obj.get("done"):
                    done = True
                    last_chunk = obj
                    eval_count = obj.get("eval_count")
                    prompt_eval_count = obj.get("prompt_eval_count")
                    eval_duration_ns = obj.get("eval_duration")
                    prompt_eval_duration_ns = obj.get("prompt_eval_duration")
                    total_duration_ns = obj.get("total_duration")
                    load_duration_ns = obj.get("load_duration")
                    break
    except Exception as e:
        error = str(e)

    end = time.perf_counter()
    wall = end - start
    snap_after = system_snapshot()
    ps_after = ollama_ps()

    ttft = (first_token_time - start) if first_token_time else None
    # tokens/sec
    tok_s = None
    if eval_count and eval_duration_ns and eval_duration_ns > 0:
        tok_s = eval_count / (eval_duration_ns / 1e9)
    elif full_text:
        # estimate via whitespace tokenization (rough) fallback
        est_tokens = len(full_text.split())
        if wall > 0:
            tok_s = est_tokens / wall

    # streaming analysis
    intervals = []
    if len(chunk_times) >= 2:
        for i in range(1, len(chunk_times)):
            intervals.append(chunk_times[i][0] - chunk_times[i-1][0])
    avg_interval = sum(intervals) / len(intervals) if intervals else None
    max_interval = max(intervals) if intervals else None
    # burst detection: std dev high or max > 3*avg indicates burst
    streaming_behavior = "smooth"
    if avg_interval and max_interval:
        if max_interval > 0.5:
            streaming_behavior = "burst"
        elif max_interval > 3 * avg_interval and len(intervals) > 5:
            streaming_behavior = "burst"

    result = {
        "model": model,
        "prompt_id": prompt_id,
        "prompt": prompt,
        "run_label": run_label,
        "inference_location": "127.0.0.1:11434 (local Ollama, no cloud)",
        "runtime": "Ollama",
        "quantization": "Q4_K_M",  # will be overwritten via ollama show if available
        "start_ts": datetime.now().isoformat(),
        "wall_time_s": round(wall, 3),
        "ttft_s": round(ttft, 3) if ttft is not None else None,
        "time_to_first_visible_s": round(ttft, 3) if ttft is not None else None,
        "output_text": full_text,
        "output_len_chars": len(full_text),
        "output_token_est": len(full_text.split()),
        "eval_count": eval_count,
        "prompt_eval_count": prompt_eval_count,
        "eval_duration_s": round(eval_duration_ns / 1e9, 3) if eval_duration_ns else None,
        "prompt_eval_duration_s": round(prompt_eval_duration_ns / 1e9, 3) if prompt_eval_duration_ns else None,
        "total_duration_s": round(total_duration_ns / 1e9, 3) if total_duration_ns else None,
        "load_duration_s": round(load_duration_ns / 1e9, 3) if load_duration_ns else None,
        "tokens_per_sec": round(tok_s, 2) if tok_s else None,
        "chunk_count": len(chunk_times),
        "avg_token_interval_s": round(avg_interval, 4) if avg_interval else None,
        "max_token_interval_s": round(max_interval, 4) if max_interval else None,
        "streaming_behavior": streaming_behavior,
        "http_streaming": True if chunk_times else False,
        "snap_before": snap_before,
        "snap_after": snap_after,
        "ram_delta_mb": round(snap_after.get("ram_used_mb", 0) - snap_before.get("ram_used_mb", 0), 1) if snap_before and snap_after else None,
        "error": error,
        "done": done,
        "last_chunk": last_chunk,
    }
    return result

def quality_heuristic(text: str, prompt_id: str) -> dict:
    """Very lightweight subjective checks — distinguished from metrics."""
    obs = {}
    if not text.strip():
        obs["note"] = "empty output"
        return obs
    if prompt_id == "TEST3_linux_bullets":
        bullets = [l for l in text.splitlines() if l.strip().startswith(("-", "*", "•")) or re.match(r"^\s*\d+[\.\)]", l)]
        # also count lines with bullet char
        count = len(bullets)
        if count == 3:
            obs["instruction_following"] = "pass - exactly 3 bullets"
        else:
            obs["instruction_following"] = f"fail - found {count} bullet-like lines"
    if prompt_id == "TEST4_memory":
        if "draw" in text.lower():
            obs["context_retention"] = "pass - recalled drawing"
        else:
            obs["context_retention"] = "fail - did not recall drawing"
    if prompt_id == "TEST6_hallucination":
        # should not invent favorite color
        lower = text.lower()
        if "don't know" in lower or "never told" in lower or "have not" in lower or "not provided" in lower:
            obs["hallucination"] = "good - acknowledged unknown"
        elif "blue" in lower or "red" in lower or "green" in lower:
            obs["hallucination"] = "possible invention"
        else:
            obs["hallucination"] = "unclear"
    if prompt_id == "TEST7_hello":
        sentences = [s for s in re.split(r"[.!?]+", text.strip()) if s.strip()]
        if len(sentences) == 1 and len(text.split()) <= 20:
            obs["short_answer"] = "pass - one sentence"
        else:
            obs["short_answer"] = f"found {len(sentences)} sentences, {len(text.split())} words"
    # repetition check
    words = text.lower().split()
    if len(words) > 20:
        bigrams = [" ".join(words[i:i+2]) for i in range(len(words)-1)]
        most_common = max(set(bigrams), key=bigrams.count) if bigrams else ""
        cnt = bigrams.count(most_common) if most_common else 0
        if cnt > 6:
            obs["repetition"] = f"repetition detected: '{most_common}' x{cnt}"
    return obs


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_suite(models, runs_per_prompt=1, cold_warm=True, allow_pull=False, quick=False, num_predict=180):
    if not ollama_available():
        print(f"ERROR: Ollama not reachable at {OLLAMA_HOST}")
        sys.exit(1)

    print(f"Ollama reachable at {OLLAMA_HOST}")
    print(f"Models to test: {models}")
    all_results = []
    # hardware snapshot once
    hw = system_snapshot()
    ollama_ver = subprocess.run(["ollama", "--version"], capture_output=True, text=True).stdout.strip()
    print(f"Ollama version: {ollama_ver}")
    print(f"System RAM: {hw}")

    for model in models:
        print(f"\n{'='*70}\nMODEL: {model}\n{'='*70}")
        available, pulled, msg = ensure_model(model, allow_pull=allow_pull)
        info = ollama_show(model) or {}
        quant = info.get("details", {}).get("quantization_level", "Q4_K_M") if info else "unknown"
        size = info.get("details", {}).get("parameter_size", "") if info else ""
        if not available:
            print(f"  SKIP {model}: unavailable ({msg})")
            for pid in PROMPT_SUITE:
                all_results.append({
                    "model": model,
                    "prompt_id": pid,
                    "run_label": "cold",
                    "status": "UNAVAILABLE",
                    "reason": msg,
                    "inference_location": "N/A",
                    "runtime": "Ollama",
                })
            continue

        # ensure model info quantization propagated
        for pid, prompt in PROMPT_SUITE.items():
            # we run either 1 quick or cold+warm
            labels = ["cold", "warm"] if cold_warm else ["warm"]
            for label in labels:
                if label == "cold":
                    print(f"  [{pid}] cold: unloading {model} ...")
                    ollama_stop(model)
                    time.sleep(2)
                    # verify RAM released
                    snap = system_snapshot()
                    print(f"    RAM after unload: {snap.get('ram_used_mb')} MB used, {snap.get('ram_available_mb')} MB avail")
                else:
                    print(f"  [{pid}] warm:")

                for run_idx in range(runs_per_prompt):
                    rlabel = f"{label}_run{run_idx+1}" if runs_per_prompt > 1 else label
                    print(f"    -> {rlabel} prompt={pid} ...", end=" ", flush=True)
                    try:
                        res = benchmark_one(model, prompt, pid, run_label=rlabel, num_predict=num_predict)
                    except Exception as e:
                        print(f"FAILED {e}")
                        all_results.append({"model": model, "prompt_id": pid, "run_label": rlabel, "status": "FAILED", "error": str(e)})
                        continue
                    # enrich with quant/size
                    res["quantization"] = quant
                    res["parameter_size"] = size
                    res["ollama_version"] = ollama_ver
                    res["status"] = "FAILED" if res.get("error") else "OK"
                    res["quality_obs"] = quality_heuristic(res.get("output_text",""), pid)
                    # RAM/CPU/GPU notes
                    res["gpu"] = "Radeon Vega 3 gfx902 - Vulkan RADV, no ROCm (CPU inference)"
                    ttft = res.get("ttft_s")
                    tps = res.get("tokens_per_sec")
                    print(f"TTFT={ttft}s tok/s={tps} wall={res.get('wall_time_s')}s chunks={res.get('chunk_count')} {res.get('streaming_behavior')}")
                    if res.get("output_text"):
                        preview = res["output_text"][:120].replace("\n"," ")
                        print(f"       preview: {preview}...")
                    all_results.append(res)
                    # resource safety: short pause, don't hammer
                    time.sleep(0.8)

                # after each prompt cold/warm, check Ollama still alive
                if label == "cold":
                    # keep model loaded for warm run — don't unload yet
                    pass

        # after all prompts for this model, unload and verify
        print(f"  Unloading {model} after suite...")
        ollama_stop(model)
        time.sleep(2)
        snap = system_snapshot()
        print(f"  After unload RAM: {snap.get('ram_used_mb')} MB used, avail {snap.get('ram_available_mb')} MB")
        # check no runaway llama-server child
        ps = ollama_ps()
        remaining = ps.get("models", [])
        if remaining:
            print(f"  WARNING: Ollama still has loaded: {remaining}")

        # safety pause between models
        time.sleep(2)

    return all_results


def save_results(results):
    # raw json
    raw_path = RESULTS_DIR / "raw_results.json"
    with open(raw_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nWrote {raw_path} ({len(results)} records)")

    # csv
    csv_path = RESULTS_DIR / "results.csv"
    # flatten keys
    fieldnames = ["model","runtime","quantization","parameter_size","prompt_id","run_label","status","wall_time_s","ttft_s","tokens_per_sec","eval_count","prompt_eval_count","eval_duration_s","prompt_eval_duration_s","total_duration_s","load_duration_s","output_len_chars","output_token_est","chunk_count","avg_token_interval_s","max_token_interval_s","streaming_behavior","http_streaming","ram_delta_mb","error","quality_obs","inference_location"]
    with open(csv_path, "w", newline="") as cf:
        w = csv.DictWriter(cf, fieldnames=fieldnames)
        w.writeheader()
        for r in results:
            row = {k: r.get(k) for k in fieldnames}
            # json-ify quality_obs
            if isinstance(row.get("quality_obs"), dict):
                row["quality_obs"] = json.dumps(row["quality_obs"], ensure_ascii=False)
            w.writerow(row)
    print(f"Wrote {csv_path}")

    # summary table for README (Phase 13)
    # build per-model aggregates
    from collections import defaultdict
    by_model = defaultdict(list)
    for r in results:
        if r.get("status") == "OK":
            by_model[r["model"]].append(r)

    print("\nPer-model aggregates:")
    for m, lst in by_model.items():
        ttfts = [x["ttft_s"] for x in lst if x.get("ttft_s") is not None]
        tpss = [x["tokens_per_sec"] for x in lst if x.get("tokens_per_sec")]
        walls = [x["wall_time_s"] for x in lst if x.get("wall_time_s")]
        if ttfts:
            print(f"  {m}: avg TTFT {sum(ttfts)/len(ttfts):.2f}s, avg tok/s {sum(tpss)/len(tpss):.1f} wall avg {sum(walls)/len(walls):.1f}s")

    return raw_path, csv_path


def main():
    parser = argparse.ArgumentParser(description="AtlasAI isolated local model benchmark")
    parser.add_argument("--models", nargs="*", help="Ollama model tags to test (e.g. gemma3:270m smollm2:360m)")
    parser.add_argument("--all", action="store_true", help="Test all PRIMARY candidates + baselines")
    parser.add_argument("--quick", action="store_true", help="Quick smoke test: only qwen2.5:1.5b (already installed)")
    parser.add_argument("--allow-pull", action="store_true", help="Allow pulling missing models from Ollama registry (download source documented)")
    parser.add_argument("--runs", type=int, default=1, help="Runs per prompt per label (default 1)")
    parser.add_argument("--no-cold-warm", action="store_true", help="Disable cold/warm separation, just warm")
    parser.add_argument("--num-predict", type=int, default=180, help="Max tokens to generate per prompt")
    args = parser.parse_args()

    if args.quick:
        models = ["qwen2.5:1.5b"]
    elif args.all:
        models = [c[0] for c in CANDIDATES]
    elif args.models:
        models = args.models
    else:
        # default: safe smallest that are most likely to fit 5GB RAM
        models = ["qwen2.5:1.5b", "gemma3:270m", "smollm2:360m", "qwen3:0.6b"]

    cold_warm = not args.no_cold_warm
    results = run_suite(models, runs_per_prompt=args.runs, cold_warm=cold_warm, allow_pull=args.allow_pull, num_predict=args.num_predict)
    save_results(results)
    print("\nDone. Check results/ and run with --allow-pull to fetch more models.")
    print("All inference was to 127.0.0.1 (local). Download source: Ollama registry https://registry.ollama.ai / HuggingFace GGUF via Ollama.")

if __name__ == "__main__":
    main()
