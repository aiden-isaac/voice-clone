# voice-clone
voice cloning with weak hardware

steps:

- prepare audio for training;
    - ensure no background noise or other voices
    - consistent talking
    - no breath noises or laughs

- put audios in audio folder, run split script

- run transcribe script

- go to training/piper/src/python

training command:

export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

python3 -m piper_train     --dataset-dir ~/Repositories/voice-clone/output/     --accelerator 'gpu'     --gpus 1     --batch-size 8     --validation-split 0.1     --num-test-examples 0     --max_epochs 4000     --resume_from_checkpoint [pretrained/other checkpoints]     --checkpoint-epochs 50     --precision 16     --max-phoneme-ids 400     --quality medium 2>&1 | grep -v "FutureWarning\|torch.load\|weights_only\|pickle"

export command:

python3 -m piper_train.export_onnx     ~/Repositories/voice-clone/output/lightning_logs/version_5/checkpoints/epoch\=2799-step\=1369510.ckpt     ~/Repositories/voice-clone/voices/voice.onnx

inference command:

echo "Hello World!" | piper -m voice.onnx --output_file test.wav