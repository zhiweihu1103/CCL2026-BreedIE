import argparse
import json
import random
from pathlib import Path

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

SYSTEM_PROMPT = (
    "You are an information extraction model for agricultural biology literature. "
    "Extract entities and relations from the given text. "
    "Return JSON only with keys entities and relations. "
    "Each entity must contain start, end, text, label. "
    "Each relation must contain head, head_start, head_end, head_type, tail, tail_start, tail_end, tail_type, label. "
    "Do not output any explanation."
)

ENTITY_LABELS = ["ABS", "BIS", "BM", "CHR", "CROP", "CROSS", "GENE", "GST", "MRK", "QTL", "TRT", "VAR"]
RELATION_LABELS = ["AFF", "CON", "HAS", "LOI", "OCI", "USE"]

def seed_everything(seed: int):
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    set_seed(seed)

def load_records(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def limit_records(records, max_samples: int | None):
    if max_samples is None:
        return records
    return records[:max_samples]

def build_messages(text: str, target: str | None = None):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Extract entities and relations from the following text. "
                f"Allowed entity labels: {', '.join(ENTITY_LABELS)}. "
                f"Allowed relation labels: {', '.join(RELATION_LABELS)}.\n"
                "Text:\n"
                f"{text}"
            ),
        },
    ]
    if target is not None:
        messages.append({"role": "assistant", "content": target})
    return messages

def build_prompt(tokenizer, text: str):
    return tokenizer.apply_chat_template(build_messages(text), tokenize=False, add_generation_prompt=True)

def entity_key(entity):
    return entity["start"], entity["end"], entity["label"]

def relation_key(relation):
    return (
        relation["head_start"],
        relation["head_end"],
        relation["head_type"],
        relation["tail_start"],
        relation["tail_end"],
        relation["tail_type"],
        relation["label"],
    )

def compute_prf(gold_set, pred_set):
    tp = len(gold_set & pred_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }

def extract_first_json_object(text: str):
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_string = False
    escape = False
    for index in range(start, len(text)):
        ch = text[index]
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def parse_model_output(text: str):
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) >= 3:
            candidate = "\n".join(lines[1:-1]).strip()
    json_text = extract_first_json_object(candidate)
    if json_text is None:
        return None
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return None


def parse_int(value):
    try:
        return int(value)
    except Exception:
        return None


def is_valid_span(start, end, text):
    return start is not None and end is not None and 0 <= start < end <= len(text)


def find_all_spans(text, needle):
    if not needle:
        return []
    spans = []
    start = 0
    while True:
        index = text.find(needle, start)
        if index < 0:
            return spans
        spans.append((index, index + len(needle)))
        start = index + 1


def choose_best_span(candidates, preferred_start):
    if not candidates:
        return None
    if preferred_start is None:
        return candidates[0]
    return min(candidates, key=lambda item: (abs(item[0] - preferred_start), item[0], item[1]))


def resolve_entity_span(text, raw_text, raw_start, raw_end):
    if is_valid_span(raw_start, raw_end, text):
        exact_text = text[raw_start:raw_end]
        if not raw_text or exact_text == raw_text:
            return raw_start, raw_end, "exact"
    if not raw_text:
        return None, None, None
    search_text = raw_text.strip()
    if not search_text:
        return None, None, None
    candidates = find_all_spans(text, search_text)
    if not candidates:
        return None, None, None
    best = choose_best_span(candidates, raw_start)
    return best[0], best[1], "backfilled"


def build_entity_indexes(entities):
    span_lookup = {(item["start"], item["end"], item["label"]): item for item in entities}
    text_lookup = {}
    for item in entities:
        text_lookup.setdefault((item["text"], item["label"]), []).append(item)
    return span_lookup, text_lookup


def resolve_entity_reference(raw_text, raw_label, raw_start, raw_end, text, span_lookup, text_lookup):
    if raw_label not in ENTITY_LABELS:
        return None, None
    if is_valid_span(raw_start, raw_end, text):
        item = span_lookup.get((raw_start, raw_end, raw_label))
        if item is not None:
            return item, "span"
    if not raw_text:
        return None, None
    candidates = text_lookup.get((raw_text.strip(), raw_label), [])
    if not candidates:
        return None, None
    if raw_start is None:
        return candidates[0], "text"
    item = min(candidates, key=lambda candidate: (abs(candidate["start"] - raw_start), candidate["start"], candidate["end"]))
    return item, "text"


def normalize_entities(prediction, text):
    raw_entities = prediction.get("entities", []) if isinstance(prediction, dict) else []
    normalized = []
    seen = set()
    stats = {"exact_span_matches": 0, "text_backfilled": 0, "backfill_failed": 0}
    for entity in raw_entities:
        if not isinstance(entity, dict):
            continue
        label = str(entity.get("label", ""))
        if label not in ENTITY_LABELS:
            continue
        raw_text = str(entity.get("text", ""))
        raw_start = parse_int(entity.get("start"))
        raw_end = parse_int(entity.get("end"))
        start, end, source = resolve_entity_span(text, raw_text, raw_start, raw_end)
        if source is None:
            stats["backfill_failed"] += 1
            continue
        item = {
            "start": start,
            "end": end,
            "text": text[start:end],
            "label": label,
        }
        key = entity_key(item)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
        if source == "exact":
            stats["exact_span_matches"] += 1
        else:
            stats["text_backfilled"] += 1
    normalized.sort(key=lambda item: (item["start"], item["end"], item["label"]))
    return normalized, stats


def normalize_relations(prediction, text, entities):
    raw_relations = prediction.get("relations", []) if isinstance(prediction, dict) else []
    span_lookup, text_lookup = build_entity_indexes(entities)
    normalized = []
    seen = set()
    stats = {"span_resolved": 0, "text_resolved": 0, "resolve_failed": 0}
    for relation in raw_relations:
        if not isinstance(relation, dict):
            continue
        label = str(relation.get("label", ""))
        if label not in RELATION_LABELS:
            continue
        head, head_source = resolve_entity_reference(
            str(relation.get("head", "")),
            str(relation.get("head_type", "")),
            parse_int(relation.get("head_start")),
            parse_int(relation.get("head_end")),
            text,
            span_lookup,
            text_lookup,
        )
        tail, tail_source = resolve_entity_reference(
            str(relation.get("tail", "")),
            str(relation.get("tail_type", "")),
            parse_int(relation.get("tail_start")),
            parse_int(relation.get("tail_end")),
            text,
            span_lookup,
            text_lookup,
        )
        if head is None or tail is None or entity_key(head) == entity_key(tail):
            stats["resolve_failed"] += 1
            continue
        item = {
            "head": head["text"],
            "head_start": head["start"],
            "head_end": head["end"],
            "head_type": head["label"],
            "tail": tail["text"],
            "tail_start": tail["start"],
            "tail_end": tail["end"],
            "tail_type": tail["label"],
            "label": label,
        }
        key = relation_key(item)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)
        if head_source == "text" or tail_source == "text":
            stats["text_resolved"] += 1
        else:
            stats["span_resolved"] += 1
    normalized.sort(
        key=lambda item: (
            item["head_start"],
            item["head_end"],
            item["tail_start"],
            item["tail_end"],
            item["label"],
        )
    )
    return normalized, stats


def build_dtype(dtype_name: str):
    if dtype_name == "bf16":
        return torch.bfloat16
    if dtype_name == "fp16":
        return torch.float16
    return torch.float32


def load_tokenizer(model_name_or_path: str, padding_side: str):
    tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = padding_side
    return tokenizer


def batch_generate(model, tokenizer, prompts, max_length, max_new_tokens):
    encoded = tokenizer(
        prompts,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=max_length,
    )
    device = next(model.parameters()).device
    encoded = {key: value.to(device) for key, value in encoded.items()}
    input_width = encoded["input_ids"].shape[1]
    with torch.no_grad():
        generated = model.generate(
            **encoded,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    generated_only = generated[:, input_width:]
    return tokenizer.batch_decode(generated_only, skip_special_tokens=True)


def batch_generate_vllm(llm, sampling_params, lora_request, prompts):
    outputs = llm.generate(prompts, sampling_params, lora_request=lora_request)
    generations = []
    for output in outputs:
        if output.outputs:
            generations.append(output.outputs[0].text)
        else:
            generations.append("")
    return generations


def evaluate(args):
    seed_everything(args.seed)
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = limit_records(load_records(args.input_file), args.max_samples)
    tokenizer_source = args.adapter_path if (Path(args.adapter_path) / "tokenizer.json").exists() else args.model_name
    tokenizer = load_tokenizer(tokenizer_source, padding_side="left")
    model = None
    llm = None
    sampling_params = None
    lora_request = None
    if args.engine == "hf":
        torch_dtype = build_dtype(args.torch_dtype)
        base_model = AutoModelForCausalLM.from_pretrained(args.model_name, torch_dtype=torch_dtype)
        model = PeftModel.from_pretrained(base_model, args.adapter_path)
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device)
        model.eval()
    else:
        from vllm import LLM, SamplingParams
        from vllm.lora.request import LoRARequest

        llm = LLM(
            model=args.model_name,
            tokenizer=tokenizer_source,
            enable_lora=True,
            tensor_parallel_size=args.tensor_parallel_size,
            dtype={"bf16": "bfloat16", "fp16": "float16", "fp32": "float32"}[args.torch_dtype],
            gpu_memory_utilization=args.gpu_memory_utilization,
            max_model_len=max(args.vllm_max_model_len, args.max_length + args.max_new_tokens),
            enforce_eager=True,
        )
        sampling_params = SamplingParams(
            temperature=0.0,
            max_tokens=args.max_new_tokens,
            skip_special_tokens=True,
        )
        lora_request = LoRARequest("mgbie_lora", 1, args.adapter_path)

    predictions = []
    raw_generations = []
    parse_success = 0
    gold_entities = set()
    pred_entities = set()
    gold_relations = set()
    pred_relations = set()
    entity_stats = {"exact_span_matches": 0, "text_backfilled": 0, "backfill_failed": 0}
    relation_stats = {"span_resolved": 0, "text_resolved": 0, "resolve_failed": 0}
    total_batches = (len(records) + args.batch_size - 1) // args.batch_size

    for batch_idx, start in enumerate(range(0, len(records), args.batch_size), start=1):
        batch_records = records[start : start + args.batch_size]
        prompts = [build_prompt(tokenizer, record["text"]) for record in batch_records]
        if args.engine == "hf":
            generations = batch_generate(model, tokenizer, prompts, args.max_length, args.max_new_tokens)
        else:
            generations = batch_generate_vllm(llm, sampling_params, lora_request, prompts)

        for record_idx, (record, generation) in enumerate(zip(batch_records, generations), start=start):
            parsed = parse_model_output(generation)
            if parsed is not None:
                parse_success += 1
            entities, entity_record_stats = normalize_entities(parsed or {}, record["text"])
            relations, relation_record_stats = normalize_relations(parsed or {}, record["text"], entities)
            for key, value in entity_record_stats.items():
                entity_stats[key] += value
            for key, value in relation_record_stats.items():
                relation_stats[key] += value
            source_index = record.get("_source_index", record_idx)
            predictions.append(
                {
                    "source_index": source_index,
                    "text": record["text"],
                    "entities": entities,
                    "relations": relations,
                }
            )
            raw_generations.append(
                {
                    "source_index": source_index,
                    "text": record["text"],
                    "raw_response": generation,
                    "parsed": parsed is not None,
                }
            )

            for entity in record["entities"]:
                gold_entities.add((record_idx, *entity_key(entity)))
            for entity in entities:
                pred_entities.add((record_idx, *entity_key(entity)))
            for relation in record["relations"]:
                gold_relations.add((record_idx, *relation_key(relation)))
            for relation in relations:
                pred_relations.add((record_idx, *relation_key(relation)))
        if batch_idx % 10 == 0 or batch_idx == total_batches:
            print(
                f"evaluate progress: {batch_idx}/{total_batches} batches, "
                f"records {min(start + len(batch_records), len(records))}/{len(records)}",
                flush=True,
            )

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(predictions, f, ensure_ascii=False, indent=2)

    metrics = {
        "entity": compute_prf(gold_entities, pred_entities),
        "relation": compute_prf(gold_relations, pred_relations),
        "parse_success_rate": parse_success / len(records) if records else 0.0,
        "records": len(records),
        "normalization": {
            "entity": entity_stats,
            "relation": relation_stats,
        },
    }
    metrics_path = output_path.with_name(output_path.stem + "_metrics.json")
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    raw_path = output_path.with_name(output_path.stem + "_raw_generations.json")
    with raw_path.open("w", encoding="utf-8") as f:
        json.dump(raw_generations, f, ensure_ascii=False, indent=2)

    print(json.dumps(metrics, ensure_ascii=False, indent=2))
    print(f"Predictions saved to: {output_path}")
    print(f"Metrics saved to: {metrics_path}")
    print(f"Raw generations saved to: {raw_path}")


def build_parser():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    eval_parser = subparsers.add_parser("evaluate")
    eval_parser.add_argument("--input_file", required=True)
    eval_parser.add_argument("--model_name", required=True)
    eval_parser.add_argument("--adapter_path", required=True)
    eval_parser.add_argument("--output_file", required=True)
    eval_parser.add_argument("--max_length", type=int, default=2048)
    eval_parser.add_argument("--max_new_tokens", type=int, default=1024)
    eval_parser.add_argument("--batch_size", type=int, default=2)
    eval_parser.add_argument("--seed", type=int, default=42)
    eval_parser.add_argument("--torch_dtype", choices=["bf16", "fp16", "fp32"], default="bf16")
    eval_parser.add_argument("--max_samples", type=int)
    eval_parser.add_argument("--engine", choices=["hf", "vllm"], default="hf")
    eval_parser.add_argument("--tensor_parallel_size", type=int, default=1)
    eval_parser.add_argument("--gpu_memory_utilization", type=float, default=0.85)
    eval_parser.add_argument("--vllm_max_model_len", type=int, default=4096)
    eval_parser.set_defaults(func=evaluate)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
