#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR=
PYTHON_BIN=
LLAMAFACTORY_CLI="${LLAMAFACTORY_CLI:-llamafactory-cli}"
DATA_DIR="${PROJECT_DIR}/llamafactory_config/data"
CONFIG_FILE="${PROJECT_DIR}/llamafactory_config/train_qwen25_7b_lora_sft_1k.yaml"
NPROC_PER_NODE="${NPROC_PER_NODE:-2}"

"${PYTHON_BIN}" "${PROJECT_DIR}/scripts/build_mgbie_sharegpt_data.py" \
  --input_file "${PROJECT_DIR}/dataset/train.json" \
  --output_file "${DATA_DIR}/mgbie_train_sharegpt.json"

"${PYTHON_BIN}" "${PROJECT_DIR}/scripts/build_mgbie_sharegpt_data.py" \
  --input_file "${PROJECT_DIR}/dataset/val.json" \
  --output_file "${DATA_DIR}/mgbie_val_sharegpt.json"

CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-1,2}" \
FORCE_TORCHRUN=1 \
NNODES=1 \
NPROC_PER_NODE="${NPROC_PER_NODE}" \
MASTER_ADDR="${MASTER_ADDR:-127.0.0.1}" \
MASTER_PORT="${MASTER_PORT:-29500}" \
PATH="/bin:$PATH" \
"${LLAMAFACTORY_CLI}" train "${CONFIG_FILE}"
