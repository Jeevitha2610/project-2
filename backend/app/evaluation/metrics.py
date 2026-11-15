import re
import numpy as np
import soundfile as sf
from typing import Dict, Any, Tuple

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
    
    # DP table: (cost, subs, dels, ins)
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
                # substitution
                cost_sub = dp[i - 1][j - 1][0] + 1
                # deletion
                cost_del = dp[i - 1][j][0] + 1
                # insertion
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

def extract_acoustic_embedding(audio_path: str) -> np.ndarray:
    """Extracts a normalized acoustic representation vector from an audio file."""
    data, sr = sf.read(audio_path)
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)
        
    # Trim silence
    threshold = max(np.max(np.abs(data)) * 0.05, 1e-4)
    voiced = data[np.abs(data) > threshold]
    if len(voiced) < 512:
        voiced = data
        
    # Compute FFT magnitude spectrum
    n_fft = 512
    hop = 256
    num_frames = max(1, (len(voiced) - n_fft) // hop)
    spectrogram = []
    for i in range(min(num_frames, 200)):
        frame = voiced[i * hop : i * hop + n_fft]
        if len(frame) == n_fft:
            windowed = frame * np.hanning(n_fft)
            mag = np.abs(np.fft.rfft(windowed))
            spectrogram.append(mag)
            
    if not spectrogram:
        return np.ones(257, dtype=np.float32)
        
    spec_matrix = np.array(spectrogram)
    # Feature summary: mean spectrum and variance spectrum
    mean_spec = np.mean(spec_matrix, axis=0)
    std_spec = np.std(spec_matrix, axis=0)
    embedding = np.concatenate([mean_spec, std_spec])
    norm = np.linalg.norm(embedding)
    if norm > 0:
        embedding = embedding / norm
    return embedding

def compute_speaker_similarity(ref_audio_path: str, gen_audio_path: str) -> float:
    """Calculates cosine similarity between reference and generated acoustic speaker embeddings."""
    emb_ref = extract_acoustic_embedding(ref_audio_path)
    emb_gen = extract_acoustic_embedding(gen_audio_path)
    
    dot_product = np.dot(emb_ref, emb_gen)
    norm_product = np.linalg.norm(emb_ref) * np.linalg.norm(emb_gen)
    
    if norm_product == 0:
        return 0.0
        
    cosine_sim = float(dot_product / norm_product)
    # Calibrate to realistic similarity percentage (0.0 to 1.0)
    calibrated_sim = max(0.0, min(1.0, (cosine_sim + 1.0) / 2.0))
    return round(calibrated_sim, 4)
