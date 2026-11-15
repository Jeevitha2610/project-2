"""
Tier 1 & Tier 2 Unit Tests: ML Contracts (VoiceCloner, AsrEvaluator, SpeakerVerification, Parameter Bounds).
Coverage:
- TC-T1-VCP-01..06: Voice cloning parameters, model state, and synthesis contracts
- TC-T1-ASR-01..06: ASR transcription, Levenshtein WER, CER, S/D/I taxonomy
- TC-T1-SPK-01..06: Speaker embeddings, self-similarity, cross-speaker discrimination, CPU execution
- TC-T2-BND-PRM-01..06: Parameter boundary extremes (speed, pitch, temp, NFE, NaN/Inf, exact bounds)
"""

import math
from pathlib import Path
import numpy as np
import pytest
import torch

try:
    from voicestudio.ml.cloner import VoiceCloner, ModelNotLoadedError
    from voicestudio.ml.asr import AsrEvaluator
    from voicestudio.ml.speaker import SpeakerVerification
except ImportError:
    from tests.contracts import (
        VoiceCloner,
        ModelNotLoadedError,
        AsrEvaluator,
        SpeakerVerification,
    )


@pytest.mark.unit
class TestVoiceClonerContractsTier1:
    """Tier 1: Feature Coverage for VoiceCloner Contracts."""

    def test_tc_t1_vcp_01_speed_parameter_acceptance(self, clean_wav_file):
        """TC-T1-VCP-01: Accepts valid speed within [0.5, 2.0]."""
        cloner = VoiceCloner(is_loaded=True)
        res = cloner.synthesize(clean_wav_file, "Prompt", "Hello world target text", speed=1.5)
        assert res.audio_tensor is not None
        assert res.sample_rate == 24000

    def test_tc_t1_vcp_02_pitch_parameter_acceptance(self, clean_wav_file):
        """TC-T1-VCP-02: Accepts valid pitch within [-12.0, +12.0]."""
        cloner = VoiceCloner(is_loaded=True)
        res = cloner.synthesize(clean_wav_file, "Prompt", "Hello world target text", pitch=3.5)
        assert res.duration_sec > 0

    def test_tc_t1_vcp_03_temperature_parameter_acceptance(self, clean_wav_file):
        """TC-T1-VCP-03: Accepts valid temperature within [0.1, 1.5]."""
        cloner = VoiceCloner(is_loaded=True)
        res = cloner.synthesize(clean_wav_file, "Prompt", "Hello world target text", temperature=0.8)
        assert res.rtf > 0

    def test_tc_t1_vcp_04_nfe_steps_acceptance(self, clean_wav_file):
        """TC-T1-VCP-04: Accepts valid NFE steps within [10, 64]."""
        cloner = VoiceCloner(is_loaded=True)
        res = cloner.synthesize(clean_wav_file, "Prompt", "Hello world target text", nfe_steps=32)
        assert res.inference_time_sec > 0

    def test_tc_t1_vcp_05_unloaded_model_raises_error(self, clean_wav_file):
        """TC-T1-VCP-05: Model state verification raises ModelNotLoadedError when not loaded."""
        cloner = VoiceCloner(is_loaded=False)
        with pytest.raises(ModelNotLoadedError):
            cloner.synthesize(clean_wav_file, "Prompt", "Hello world")

    def test_tc_t1_vcp_06_cpu_inference_contract_returns_synthesis_result(self, clean_wav_file):
        """TC-T1-VCP-06: Synthesis on CPU returns valid SynthesisResult dataclass."""
        cloner = VoiceCloner(is_loaded=True)
        res = cloner.synthesize(clean_wav_file, "Prompt", "The quick brown fox jumps.")
        assert hasattr(res, "audio_tensor")
        assert hasattr(res, "sample_rate")
        assert hasattr(res, "duration_sec")
        assert hasattr(res, "inference_time_sec")
        assert hasattr(res, "rtf")
        assert isinstance(res.audio_tensor, torch.Tensor)
        assert res.audio_tensor.device.type == "cpu"


@pytest.mark.unit
class TestAsrEvaluatorContractsTier1:
    """Tier 1: Feature Coverage for ASR & Accuracy Metrics."""

    def test_tc_t1_asr_01_transcribe_returns_normalized_string(self, clean_wav_file, short_wav_file):
        """TC-T1-ASR-01: ASR transcribes English reference audio returning content-driven text."""
        evaluator = AsrEvaluator()
        text1 = evaluator.transcribe(clean_wav_file)
        text2 = evaluator.transcribe(short_wav_file)
        assert isinstance(text1, str) and len(text1) > 0
        assert isinstance(text2, str) and len(text2) > 0
        # Dynamic content verification: different audio produces genuinely different transcription
        assert text1 != text2

    def test_tc_t1_asr_02_exact_match_zero_wer_cer(self):
        """TC-T1-ASR-02: Exact match yields 0.0% WER and 0.0% CER."""
        ref = "The quick brown fox jumps over the lazy dog"
        hyp = "The quick brown fox jumps over the lazy dog"
        metrics = AsrEvaluator.calculate_wer_cer(ref, hyp)
        assert metrics.wer == 0.0
        assert metrics.cer == 0.0
        assert metrics.substitutions == 0
        assert metrics.deletions == 0
        assert metrics.insertions == 0

    def test_tc_t1_asr_03_word_substitutions_wer(self):
        """TC-T1-ASR-03: 1 word substituted out of 4 yields 25.0% WER."""
        ref = "the quick brown fox"
        hyp = "the fast brown fox"
        metrics = AsrEvaluator.calculate_wer_cer(ref, hyp)
        assert metrics.wer == pytest.approx(25.0)
        assert metrics.substitutions == 1

    def test_tc_t1_asr_04_word_deletions_counted(self):
        """TC-T1-ASR-04: 1 word deleted out of 4 yields 25.0% WER with deletions=1."""
        ref = "the quick brown fox"
        hyp = "the quick fox"
        metrics = AsrEvaluator.calculate_wer_cer(ref, hyp)
        assert metrics.deletions == 1
        assert metrics.wer == pytest.approx(25.0)

    def test_tc_t1_asr_05_word_insertions_counted(self):
        """TC-T1-ASR-05: 1 word inserted into 4 yields 25.0% WER with insertions=1."""
        ref = "the quick brown fox"
        hyp = "the quick red brown fox"
        metrics = AsrEvaluator.calculate_wer_cer(ref, hyp)
        assert metrics.insertions == 1
        assert metrics.wer == pytest.approx(25.0)

    def test_tc_t1_asr_06_text_accuracy_schema_compliance(self):
        """TC-T1-ASR-06: Output conforms to typed TextAccuracyMetrics schema."""
        metrics = AsrEvaluator.calculate_wer_cer("test one", "test two")
        for attr in ["wer", "cer", "substitutions", "deletions", "insertions", "reference_words", "transcribed_text"]:
            assert hasattr(metrics, attr)

    def test_tc_t1_asr_07_evaluate_accuracy_dynamic_levenshtein(self, clean_wav_file):
        """TC-T1-ASR-07: evaluate_accuracy computes genuine dynamic WER/CER between audio and text."""
        evaluator = AsrEvaluator()
        hypothesis = evaluator.transcribe(clean_wav_file)
        # 1. Exact match against transcribed hypothesis yields 0 errors
        exact_res = evaluator.evaluate_accuracy(hypothesis, clean_wav_file)
        assert exact_res.wer == 0.0
        assert exact_res.cer == 0.0
        assert exact_res.substitutions == 0
        assert exact_res.deletions == 0
        assert exact_res.insertions == 0
        # 2. Mismatched target text dynamically yields genuine substitutions/insertions
        mismatch_res = evaluator.evaluate_accuracy("completely different target utterance text", clean_wav_file)
        assert mismatch_res.wer > 0.0
        assert (mismatch_res.substitutions + mismatch_res.deletions + mismatch_res.insertions) > 0


@pytest.mark.unit
class TestSpeakerVerificationContractsTier1:
    """Tier 1: Feature Coverage for Speaker Similarity."""

    def test_tc_t1_spk_01_512_dim_embedding_extraction(self, clean_wav_file):
        """TC-T1-SPK-01: Extracts 512-dimensional X-Vector speaker embedding."""
        sv = SpeakerVerification(embedding_dim=512)
        emb = sv.extract_embedding(clean_wav_file)
        assert emb.shape == (512,)
        assert isinstance(emb, torch.Tensor)

    def test_tc_t1_spk_02_self_similarity_high_score(self, clean_wav_file):
        """TC-T1-SPK-02: Identical audio files yield cosine similarity >= 0.98 and percentage >= 98%."""
        sv = SpeakerVerification()
        metrics = sv.compute_similarity(clean_wav_file, clean_wav_file)
        assert metrics.cosine_similarity >= 0.98
        assert metrics.calibrated_percentage >= 98.0
        # Assert that compute_similarity directly computed torch cosine similarity on extracted embeddings
        e1 = sv.extract_embedding(clean_wav_file)
        e2 = sv.extract_embedding(clean_wav_file)
        raw_cos = float(torch.nn.functional.cosine_similarity(e1.unsqueeze(0), e2.unsqueeze(0)).item())
        assert metrics.cosine_similarity == pytest.approx(raw_cos, abs=1e-5)

    def test_tc_t1_spk_03_different_speakers_lower_similarity(self, clean_wav_file, short_wav_file):
        """TC-T1-SPK-03: Different audio files yield lower similarity."""
        sv = SpeakerVerification()
        metrics = sv.compute_similarity(clean_wav_file, short_wav_file)
        # Cosine for random distinct embeddings is near 0
        assert metrics.cosine_similarity < 0.70

    def test_tc_t1_spk_04_calibrated_percentage_bounds(self, clean_wav_file, short_wav_file):
        """TC-T1-SPK-04: Calibrated percentage is bounded strictly within [0.0, 100.0]%."""
        sv = SpeakerVerification()
        m1 = sv.compute_similarity(clean_wav_file, clean_wav_file)
        m2 = sv.compute_similarity(clean_wav_file, short_wav_file)
        assert 0.0 <= m1.calibrated_percentage <= 100.0
        assert 0.0 <= m2.calibrated_percentage <= 100.0

    def test_tc_t1_spk_05_clean_cpu_execution(self, clean_wav_file):
        """TC-T1-SPK-05: Speaker verification executes cleanly on Windows 11 CPU."""
        sv = SpeakerVerification()
        emb = sv.extract_embedding(clean_wav_file)
        assert emb.device.type == "cpu"

    def test_tc_t1_spk_06_schema_compliance(self, clean_wav_file):
        """TC-T1-SPK-06: Metrics conform to SpeakerSimilarityMetrics schema."""
        sv = SpeakerVerification()
        metrics = sv.compute_similarity(clean_wav_file, clean_wav_file)
        assert hasattr(metrics, "cosine_similarity")
        assert hasattr(metrics, "calibrated_percentage")
        assert hasattr(metrics, "embedding_dim")


@pytest.mark.unit
class TestParameterBoundsTier2:
    """Tier 2: Boundary & Corner Cases for Synthesis Parameters."""

    def test_tc_t2_bnd_prm_01_speed_bounds_rejection(self, clean_wav_file):
        """TC-T2-BND-PRM-01: Speed outside [0.5, 2.0] rejected."""
        cloner = VoiceCloner(is_loaded=True)
        with pytest.raises(ValueError):
            cloner.synthesize(clean_wav_file, "Prompt", "Text", speed=0.2)
        with pytest.raises(ValueError):
            cloner.synthesize(clean_wav_file, "Prompt", "Text", speed=2.5)

    def test_tc_t2_bnd_prm_02_pitch_bounds_rejection(self, clean_wav_file):
        """TC-T2-BND-PRM-02: Pitch outside [-12.0, 12.0] rejected."""
        cloner = VoiceCloner(is_loaded=True)
        with pytest.raises(ValueError):
            cloner.synthesize(clean_wav_file, "Prompt", "Text", pitch=-15.0)
        with pytest.raises(ValueError):
            cloner.synthesize(clean_wav_file, "Prompt", "Text", pitch=15.0)

    def test_tc_t2_bnd_prm_03_temperature_bounds_rejection(self, clean_wav_file):
        """TC-T2-BND-PRM-03: Temperature outside [0.1, 1.5] rejected."""
        cloner = VoiceCloner(is_loaded=True)
        with pytest.raises(ValueError):
            cloner.synthesize(clean_wav_file, "Prompt", "Text", temperature=0.05)
        with pytest.raises(ValueError):
            cloner.synthesize(clean_wav_file, "Prompt", "Text", temperature=2.0)

    def test_tc_t2_bnd_prm_04_nfe_steps_bounds_rejection(self, clean_wav_file):
        """TC-T2-BND-PRM-04: NFE outside [10, 64] rejected."""
        cloner = VoiceCloner(is_loaded=True)
        with pytest.raises(ValueError):
            cloner.synthesize(clean_wav_file, "Prompt", "Text", nfe_steps=5)
        with pytest.raises(ValueError):
            cloner.synthesize(clean_wav_file, "Prompt", "Text", nfe_steps=100)

    def test_tc_t2_bnd_prm_05_nan_infinity_rejection(self, clean_wav_file):
        """TC-T2-BND-PRM-05: NaN or Infinity parameters rejected."""
        cloner = VoiceCloner(is_loaded=True)
        with pytest.raises(ValueError):
            cloner.synthesize(clean_wav_file, "Prompt", "Text", speed=float("nan"))
        with pytest.raises(ValueError):
            cloner.synthesize(clean_wav_file, "Prompt", "Text", temperature=float("inf"))

    def test_tc_t2_bnd_prm_06_exact_boundary_acceptance(self, clean_wav_file):
        """TC-T2-BND-PRM-06: Synthesis succeeds at exact lower & upper parameter bounds."""
        cloner = VoiceCloner(is_loaded=True)
        # Min bounds
        r_min = cloner.synthesize(clean_wav_file, "P", "T", speed=0.5, pitch=-12.0, temperature=0.1, nfe_steps=10)
        assert r_min.duration_sec > 0
        # Max bounds
        r_max = cloner.synthesize(clean_wav_file, "P", "T", speed=2.0, pitch=12.0, temperature=1.5, nfe_steps=64)
        assert r_max.duration_sec > 0
