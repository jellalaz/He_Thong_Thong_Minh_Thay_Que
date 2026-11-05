# Qwen3 1.7B local LoRA

This experiment trains adapters, not a model from scratch. No hosted inference service is used.

## Reproduce

1. Create `.venv-llm` using Python 3.12.
2. Install CUDA PyTorch 2.8.0 from the official cu128 index; install the remaining versions in `requirements-local-lock.txt`.
3. Run `.venv-llm/Scripts/python.exe experiments/local_qwen/train.py` from the repository root. Initial download requires internet; inference after download is offline.
4. Run `run-local-qwen.ps1` and open http://localhost:8766.

The base model stays in `.local-models/Qwen3-1.7B`. The training checkpoint is saved under `.local-training/qwen-lora/best`; the packaged adapter used by the app is `models/qwen_adapter` (about 6 MB). These large/cache directories are excluded from Git and Vercel. Training requires CUDA; the recorded run uses an RTX 4060 Laptop with 8 GB VRAM. All assets are free; no billing is enabled.

## Data and evaluation limits

`dataset.json`: 76 training, 21 validation and 16 test examples (8 knowledge and 8 dialogue). They are project-authored examples grounded in the cited KB, NOT independent clinical datasets or clinician-validated patient records. Validation shares source documents with training. Test questions are held out; related topics remain in training. Exact normalized question overlap is checked before training.

Checkpoints are chosen only by validation loss. `results/local_qwen` retains baseline/adapted answers, timings, learning curves and run metadata. The benchmark uses retrieved gold context to isolate generation; application tests separately exercise retrieval and routing. Lower loss alone does not prove safer medical answers. Numeric, medication and emergency requests remain handled by sourced deterministic rules.

Model: https://huggingface.co/Qwen/Qwen3-1.7B (Apache-2.0).

## Second conversation experiment

`conversation_round2.json` contains 20 new train, 6 validation, and 8 held-out social questions. `train_round2.py` starts from the first adapter and mixes 26/7/8 old train/validation/test examples. Results are in `results/local_qwen_round2`. The second checkpoint is intentionally **not deployed**: lower validation loss did not eliminate prompt copying or inappropriate social answers. The product retains the first adapter for grounded knowledge and routes social turns to checked responses.

On the local demo, helpful/not helpful feedback updates a separate two-action Q table for presentation style. This does not update Qwen weights or clinical rules. The file `.local-training/feedback_q.json` holds Q values and a rating count, not transcripts.
