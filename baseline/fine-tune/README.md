# MGBIE

当前主流程只保留两部分：
- 训练
- 评估

## 训练相关文件

- `scripts/build_mgbie_sharegpt_data.py`
- `scripts/train_mgbie_qwen25_lora_llamafactory.sh`
- `llamafactory_config/train_qwen25_7b_lora_sft_smoke.yaml`
- `llamafactory_config/train_qwen25_7b_lora_sft_1k.yaml`
- `llamafactory_config/data/llamafactory_dataset_registry.json`
- `llamafactory_config/data/mgbie_train_sharegpt.json`
- `llamafactory_config/data/mgbie_val_sharegpt.json`

## 评估相关文件

- `scripts/evaluate_mgbie_qwen_lora.py`

## 数据文件

- `dataset/train.json`
- `dataset/val.json`
- `dataset/test.json`

## 输出目录

- `outputs/llamafactory_qwen2_5_7b_lora_sft_1000_400/`

## 训练启动方式

```bash
bash scripts/train_mgbie_qwen25_lora_llamafactory.sh
```

## 评估启动方式

```bash
CUDA_VISIBLE_DEVICES=1,2 TOKENIZERS_PARALLELISM=false python scripts/evaluate_mgbie_qwen_lora.py evaluate \
  --input_file dataset/val.json \
  --model_name Qwen2.5-7B-Instruct \
  --adapter_path outputs/llamafactory_qwen2_5_7b_lora_sft_1000_400 \
  --output_file outputs/llamafactory_qwen2_5_7b_lora_sft_1000_400/val_vllm_predictions.json \
  --engine vllm \
  --tensor_parallel_size 2 \
  --torch_dtype bf16 \
  --max_length 2048 \
  --max_new_tokens 1024 \
  --batch_size 2 \
  --gpu_memory_utilization 0.85 \
  --vllm_max_model_len 4096
```
