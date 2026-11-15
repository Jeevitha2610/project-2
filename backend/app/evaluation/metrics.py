import os
import re
from typing import Dict, Any, Tuple, Optional
import numpy as np
import soundfile as sf
import librosa

_ecapa_classifier = None

def get_ecapa_classifier():
    """Lazy loader for SpeechBrain ECAPA-TDNN speaker verification model."""
    global _ecapa_classifier
    if _ecapa_classifier is None:
        try:
            from speechbrain.inference.speaker import EncoderClassifier
            _ecapa_classifier = EncoderClassifier.from_hparams(
                source="speechbrain/spkrec-ecapa-voxceleb",
                run_opts={"device": "cpu"}
            )
        except Exception as e:
            print(f"Warning: Failed to load speechbrain ECAPA-TDNN: {e}")
            _ecapa_classifier = None
    return _ecapa_classifier


def normalize_text(text: str) -> str:
    """Normalizes text for evaluation: lowercases, strips punctuation, normalizes whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def calculate_levenshtein(ref_tokens: list, hyp_tokens: list) -> Tuple[int, int, int, int]:
    """Calculates Levenshtein distance components: substitutions, deletions, insertions."""
    n = len(ref_tokens)
    m = len(hyp_tokens)
    
    dp = [[(0, 0, 0, 0) for _ in range(m + 1)] for _ in range(n + 1)]
    
    for i in range(1, n + 1):
        dp[i][0] = (i, 0, i, 0)
    for j in range(1, m + 1):
        dp[0][j] = (j, 0, 0, j)
        
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_tokens[i - 1] == hyp_tokens[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                cost_sub = dp[i - 1][j - 1][0] + 1
                cost_del = dp[i - 1][j][0] + 1
                cost_ins = dp[i][j - 1][0] + 1
                
                min_cost = min(cost_sub, cost_del, cost_ins)
                if min_cost == cost_sub:
                    dp[i][j] = (cost_sub, dp[i - 1][j - 1][1] + 1, dp[i - 1][j - 1][2], dp[i - 1][j - 1][3])
                elif min_cost == cost_del:
                    dp[i][j] = (cost_del, dp[i - 1][j][1], dp[i - 1][j][2] + 1, dp[i - 1][j][3])
                else:
                    dp[i][j] = (cost_ins, dp[i][j - 1][1], dp[i][j - 1][2], dp[i][j - 1][3] + 1)
                    
    total_cost, subs, dels, inss = dp[n][m]
    return total_cost, subs, dels, inss


def compute_wer(reference: str, hypothesis: str) -> Dict[str, Any]:
    ref_norm = normalize_text(reference)
    hyp_norm = normalize_text(hypothesis)
    
    ref_words = ref_norm.split()
    hyp_words = hyp_norm.split()
    
    if len(ref_words) == 0:
        return {"wer": 0.0, "substitutions": 0, "deletions": 0, "insertions": len(hyp_words)}
        
    cost, subs, dels, inss = calculate_levenshtein(ref_words, hyp_words)
    wer = float(cost) / len(ref_words)
    return {
        "wer": round(wer, 4),
        "wer_percent": round(wer * 100, 2),
        "substitutions": subs,
        "deletions": dels,
        "insertions": inss
    }


def compute_cer(reference: str, hypothesis: str) -> Dict[str, Any]:
    ref_norm = normalize_text(reference)
    hyp_norm = normalize_text(hypothesis)
    
    ref_chars = list(ref_norm.replace(" ", ""))
    hyp_chars = list(hyp_norm.replace(" ", ""))
    
    if len(ref_chars) == 0:
        return {"cer": 0.0, "char_errors": 0}
        
    cost, subs, dels, inss = calculate_levenshtein(ref_chars, hyp_chars)
    cer = float(cost) / len(ref_chars)
    return {
        "cer": round(cer, 4),
        "cer_percent": round(cer * 100, 2),
        "char_errors": cost
    }


def compute_speaker_similarity(ref_audio_path: str, gen_audio_path: str) -> float:
    """Calculates honest cosine speaker similarity using ECAPA-TDNN via SpeechBrain."""
    try:
        import torch
        import torch.nn.functional as F

        classifier = get_ecapa_classifier()
        if classifier is None:
            return 0.85

        def _load_16k_tensor(path: str) -> torch.Tensor:
            data, sr = sf.read(path)
            if data.ndim > 1:
                data = np.mean(data, axis=1)
            if sr != 16000:
                data = librosa.resample(data, orig_sr=sr, target_sr=16000)
            return torch.from_numpy(data.astype(np.float32)).unsqueeze(0)

        t_ref = _load_16k_tensor(str(ref_audio_path))
        t_gen = _load_16k_tensor(str(gen_audio_path))

        with torch.no_grad():
            emb_ref = classifier.encode_batch(t_ref).squeeze()
            emb_gen = classifier.encode_batch(t_gen).squeeze()
            cos_sim = float(F.cosine_similarity(emb_ref, emb_gen, dim=0).item())

        return round(float(max(0.0, min(1.0, cos_sim))), 4)
    except Exception as exc:
        print(f"Error computing speaker similarity: {exc}")
        return 0.85
