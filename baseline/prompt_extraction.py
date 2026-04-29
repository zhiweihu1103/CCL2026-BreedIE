import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import requests
import json
from dotenv import load_dotenv
load_dotenv()

API_KEY = os.getenv("VENDOR_API_KEY", "").strip()
BASE_URL = os.getenv("VENDOR_BASE_URL", "").strip().rstrip("/")
MODEL = os.getenv("VENDOR_MODEL", "").strip()

INPUT_JSON = Path(os.getenv("INPUT_JSON", "val.json"))
OUTPUT_JSONL = Path(os.getenv("OUTPUT_JSONL", "extraction_output.jsonl"))
OUTPUT_JSON = Path(os.getenv("OUTPUT_JSON", "extraction_output.json"))
FAILED_LOG = Path(os.getenv("FAILED_LOG", "failed.log"))

EXTRACT_MAX_ITEMS = int(os.getenv("EXTRACT_MAX_ITEMS", os.getenv("REVIEW_MAX_ITEMS", "2000")))
EXTRACT_START_INDEX = int(os.getenv("EXTRACT_START_INDEX", os.getenv("REVIEW_START_INDEX", "0")))

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "5"))
SLEEP_BETWEEN = float(os.getenv("SLEEP_BETWEEN", "3.0"))
TIMEOUT = int(os.getenv("TIMEOUT", "300"))
USE_RESPONSE_FORMAT = os.getenv("USE_RESPONSE_FORMAT", "1").strip().lower() in {"1", "true", "yes"}
TEMPERATURE = float(os.getenv("TEMPERATURE", "0.0"))
RATE_LIMIT_WAIT = int(os.getenv("RATE_LIMIT_WAIT", "30"))
DEBUG_API = os.getenv("DEBUG_API", "0").strip().lower() in {"1", "true", "yes"}

CHAT_ENDPOINT = f"{BASE_URL}/v1/chat/completions"

PROMPT_TEMPLATE = """你是杂粮育种领域的信息抽取专家。你将收到 val.json 样本中的 text、entities、relations 字段。

你的任务是严格依据 text，从原文中抽取实体 mention 和实体之间的关系，并填充 entities 和 relations。

【基本要求】
1. 只依据原文，不使用外部知识或常识补充。
2. 只抽取原文中实际出现且有直接证据支持的实体和关系。
3. 不因同句、同段、同主题或实验背景共现而推断关系。
4. 实体边界应“最小但完整”，不翻译、不改写、不归一化。
5. start/end 使用 Python 字符偏移，左闭右开，必须保证 text[start:end] 与实体 text 完全一致。
6. entities 按 start 升序排列。
7. relations 只能引用已输出的 entities。

【实体标签定义】
仅允许以下 12 类：

1. CROP：作物名称、物种名称、作物类别名称。
例：sorghum, foxtail millet, Tartary buckwheat, Setaria italica

2. VAR：具体品种、材料、品系、栽培品种、基因型、资源、突变体、转基因材料等育种对象。
例：Jingu 21, An04-4783, LN-sensitive genotype, transgenic lines

3. TRT：具体表型、农艺、品质、抗性/耐性、生理生化指标等性状。
例：plant height, seed yield, kernel weight, drought resistance, chlorophyll content

4. GST：生育时期、生长阶段、发育阶段、调查阶段、测定阶段。
例：seedling stage, maturity stage, grain-filling stage, heading stage

5. GENE：具体基因、候选基因、基因家族成员、稳定基因符号或名称。
例：Waxy, EP2, SiCST1, SbSNAC1, FtMYB10

6. QTL：QTL、遗传位点、定位区间、MQTL、遗传座位、明确位点对象。
例：qPH3.1, MQTL, resistance locus, QTL for SDW, 6H QTL

7. MRK：具体分子标记，如 SSR、SNP、InDel、KASP、DArT 等。
例：SNP_rs12345, GBM1498, KDH, SB3344, KASP_Chr2_15Mb

8. CHR：染色体、连锁群、染色体编号、染色体区段名称。
例：Chr1, chromosome 2H, LG10, SBI-03, 6H

9. BM：育种方法、筛选方法、检测方法、组学/测序/定位分析方法、技术路线。
例：hybridization, QTL mapping, RNA-Seq, genome-wide association studies

10. CROSS：亲本/父母本组合、杂交组合、来源组合表达。
例：A × B, Prisma x Apex, Yugu 5 x Jigu 31

11. ABS：非生物胁迫、逆境处理、非生物处理条件。
例：drought stress, salt stress, heat stress, PEG-mediated drought treatment

12. BIS：生物胁迫、病虫草害、病原物、虫害对象。
例：stem rust, aphids, southern root-knot nematodes, bulk Pca inoculum

【关系标签定义】
仅允许以下 6 类：

1. CON：归属、从属、对应、别名、简称/全称、学名/俗名、同位说明关系。
例：CROP → VAR；全称 ↔ 简称；学名 ↔ 俗名。

2. USE：使用、采用、借助某方法/技术/材料进行分析、筛选、育种、检测、定位等。
常见触发语义：using, used, applied, via, through, by, with。

3. HAS：某对象明确具有、表现出、具备、拥有某性状。
例：VAR → TRT；CROP → TRT。
常见触发语义：showed, had, exhibited, possessed, tolerant, resistant。

4. AFF：影响、调控、促进、抑制、响应、敏感、耐受、抗性等方向性作用关系。
例：ABS → TRT；BIS → TRT；GENE → TRT。
常见触发语义：regulate, affect, enhance, suppress, induce, inhibit, improve, reduce, increase, decrease, responsive to, sensitive to, tolerant to, resistant to, damaged by, infected by。

5. OCI：发生于、测定于、调查于、处理于某生育时期或阶段。
例：TRT → GST；ABS → GST；BIS → GST。
常见触发语义：at seedling stage, at maturity, during heading stage, measured at。

6. LOI：定位、映射、连锁、位于、关联、候选对应等分子证据关系。
例：QTL → TRT；QTL → CHR；MRK → QTL；MRK → CHR；MRK → TRT；GENE → CHR；GENE → TRT。
常见触发语义：associated with, linked to, mapped to, located on, flanked by, candidate for, co-localized with。

【输出格式】
只输出 JSON，不输出 markdown 或解释文字。格式如下：
{
  "text": "",
  "entities": [
    {
      "start": 0,
      "end": 0,
      "text": "",
      "label": ""
    }
  ],
  "relations": [
    {
      "head": "",
      "head_start": 0,
      "head_end": 0,
      "head_type": "",
      "tail": "",
      "tail_start": 0,
      "tail_end": 0,
      "tail_type": "",
      "label": ""
    }
  ]
}

【输出约束】
1. text 字段必须与输入原始 text 完全一致。
2. 若没有实体，entities 输出空数组。
3. 若没有关系，relations 输出空数组。
4. 不输出额外字段、markdown 或解释文字。

【输入文本】
__TEXT__

【输入 entities 字段，通常为空】
__ENTITIES__

【输入 relations 字段，通常为空】
__RELATIONS__
"""
ALLOWED_ENTITY_LABELS = {
    "CROP", "VAR", "TRT", "GST", "GENE", "QTL", "MRK", "CHR", "BM", "CROSS", "ABS", "BIS"
}
ALLOWED_REL_LABELS = {"CON", "USE", "HAS", "AFF", "OCI", "LOI"}


def require_env():
    if not API_KEY or not BASE_URL or not MODEL:
        raise RuntimeError("Missing required env vars: VENDOR_API_KEY, VENDOR_BASE_URL, VENDOR_MODEL")


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: Path, obj: Any):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def append_jsonl(path: Path, obj: Any):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def read_processed_count(path: Path) -> int:
    """Count successful incremental output lines for simple line-count resume.

    The public output schema intentionally contains only text/entities/relations,
    so result files do not store ids or review metadata.
    """
    if not path.exists():
        return 0
    count = 0
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict) and set(obj.keys()).issubset({"text", "entities", "relations"}):
                count += 1
    return count

def collect_jsonl(path: Path) -> List[Dict[str, Any]]:
    items = []
    if not path.exists():
        return items
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                items.append(json.loads(line))
            except Exception:
                continue
    return items

def normalize_input_record(rec: Dict[str, Any], idx: int) -> Dict[str, Any]:
    rid = rec.get("id", idx)
    text = rec.get("text") or rec.get("data", {}).get("text") or ""

    entities = rec.get("entities", [])
    relations = rec.get("relations", [])

    if (not entities and not relations) and rec.get("annotations"):
        ann = rec["annotations"][0]
        results = ann.get("result", [])
        id2ent = {}
        ents = []
        rels = []

        # First pass: collect entities so relation order in result does not matter.
        for r in results:
            if r.get("type") != "labels":
                continue
            value = r.get("value", {})
            labels = value.get("labels") or [""]
            ent = {
                "start": value.get("start"),
                "end": value.get("end"),
                "text": value.get("text", ""),
                "label": labels[0],
            }
            ents.append(ent)
            if r.get("id"):
                id2ent[r["id"]] = ent

        # Second pass: resolve relations against the completed entity map.
        for r in results:
            if r.get("type") != "relation":
                continue
            label = (r.get("labels") or [""])[0]
            head = id2ent.get(r.get("from_id"))
            tail = id2ent.get(r.get("to_id"))
            if head and tail:
                rels.append({
                    "head": head["text"],
                    "head_start": head["start"],
                    "head_end": head["end"],
                    "head_type": head["label"],
                    "tail": tail["text"],
                    "tail_start": tail["start"],
                    "tail_end": tail["end"],
                    "tail_type": tail["label"],
                    "label": label,
                })

        entities, relations = ents, rels

    return {
        "id": rid,
        "text": text,
        "entities": entities or [],
        "relations": relations or [],
    }

def parse_json_strict(text: str) -> Dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z0-9]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except Exception:
                pass
    raise ValueError("Model response is not valid JSON")

def call_api(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "temperature": TEMPERATURE,
        "messages": [{"role": "user", "content": prompt}],
    }
    if USE_RESPONSE_FORMAT:
        payload["response_format"] = {"type": "json_object"}

    if DEBUG_API:
        print(f"[DEBUG] endpoint={CHAT_ENDPOINT}")
        print(f"[DEBUG] model={MODEL}")
        print(f"[DEBUG] use_response_format={USE_RESPONSE_FORMAT}")

    resp = requests.post(
        CHAT_ENDPOINT,
        headers=headers,
        json=payload,
        timeout=(20, 120),
    )

    if DEBUG_API:
        print(f"[DEBUG] http_status={resp.status_code}")
        preview = resp.text[:800].replace("\n", " ")
        print(f"[DEBUG] response_preview={preview}")

    resp.raise_for_status()
    data = resp.json()
    choices = data.get("choices", [])
    if not choices:
        raise ValueError(f"No choices returned: {data}")
    msg = choices[0].get("message", {})
    content = msg.get("content")
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
        content = "".join(parts)
    if not content:
        raise ValueError(f"No message content returned: {choices[0]}")
    return content


def entity_key(ent: Dict[str, Any]) -> Tuple[Any, Any, Any, Any]:
    return (ent.get("start"), ent.get("end"), ent.get("text"), ent.get("label"))


def relation_key(rel: Dict[str, Any]) -> Tuple[Any, ...]:
    return (
        rel.get("head"), rel.get("head_start"), rel.get("head_end"), rel.get("head_type"),
        rel.get("tail"), rel.get("tail_start"), rel.get("tail_end"), rel.get("tail_type"),
        rel.get("label"),
    )


def sort_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        entities,
        key=lambda x: (
            x.get("start", 10**9) if isinstance(x.get("start"), int) else 10**9,
            x.get("end", 10**9) if isinstance(x.get("end"), int) else 10**9,
            x.get("text", ""),
            x.get("label", ""),
        ),
    )


def validate_entity(ent: Dict[str, Any], source_text: str) -> bool:
    try:
        start = ent["start"]
        end = ent["end"]
        text = ent["text"]
        label = ent["label"]
    except KeyError:
        return False
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end <= start:
        return False
    if label not in ALLOWED_ENTITY_LABELS:
        return False
    if end > len(source_text):
        return False
    return source_text[start:end] == text


def sanitize_entities(entities: List[Dict[str, Any]], source_text: str) -> List[Dict[str, Any]]:
    clean = []
    seen = set()
    for ent in entities or []:
        if not isinstance(ent, dict):
            continue
        if not validate_entity(ent, source_text):
            continue
        k = entity_key(ent)
        if k in seen:
            continue
        seen.add(k)
        clean.append({
            "start": ent["start"],
            "end": ent["end"],
            "text": ent["text"],
            "label": ent["label"],
        })
    return sort_entities(clean)


def entity_index(entities: List[Dict[str, Any]]) -> Dict[Tuple[Any, Any, Any, Any], Dict[str, Any]]:
    return {entity_key(e): e for e in entities}


def validate_relation(rel: Dict[str, Any], ent_map: Dict[Tuple[Any, Any, Any, Any], Dict[str, Any]], source_text: str) -> bool:
    required = [
        "head", "head_start", "head_end", "head_type",
        "tail", "tail_start", "tail_end", "tail_type",
        "label",
    ]
    for k in required:
        if k not in rel:
            return False
    if rel["label"] not in ALLOWED_REL_LABELS:
        return False

    hk = (rel["head_start"], rel["head_end"], rel["head"], rel["head_type"])
    tk = (rel["tail_start"], rel["tail_end"], rel["tail"], rel["tail_type"])
    if hk not in ent_map or tk not in ent_map:
        return False

    hs, he = rel["head_start"], rel["head_end"]
    ts, te = rel["tail_start"], rel["tail_end"]
    if not all(isinstance(x, int) for x in [hs, he, ts, te]):
        return False
    if source_text[hs:he] != rel["head"]:
        return False
    if source_text[ts:te] != rel["tail"]:
        return False
    return True


def sanitize_relations(relations: List[Dict[str, Any]], entities: List[Dict[str, Any]], source_text: str) -> List[Dict[str, Any]]:
    ent_map = entity_index(entities)
    clean = []
    seen = set()
    for rel in relations or []:
        if not isinstance(rel, dict):
            continue
        if not validate_relation(rel, ent_map, source_text):
            continue

        item = {
            "head": rel["head"],
            "head_start": rel["head_start"],
            "head_end": rel["head_end"],
            "head_type": rel["head_type"],
            "tail": rel["tail"],
            "tail_start": rel["tail_start"],
            "tail_end": rel["tail_end"],
            "tail_type": rel["tail_type"],
            "label": rel["label"],
        }
        k = relation_key(item)
        if k in seen:
            continue
        seen.add(k)
        clean.append(item)
    clean.sort(key=lambda r: (r["head_start"], r["head_end"], r["tail_start"], r["tail_end"], r["label"]))
    return clean

def build_prompt(text: str, entities: List[Dict[str, Any]], relations: List[Dict[str, Any]]) -> str:
    return (
        PROMPT_TEMPLATE
        .replace("__TEXT__", text)
        .replace("__ENTITIES__", json.dumps(entities, ensure_ascii=False, indent=2))
        .replace("__RELATIONS__", json.dumps(relations, ensure_ascii=False, indent=2))
    )

def process_one(record: Dict[str, Any]) -> Dict[str, Any]:
    text = record["text"]
    prompt = build_prompt(text, record["entities"], record["relations"])
    raw = call_api(prompt)
    parsed = parse_json_strict(raw)

    entities = sanitize_entities(parsed.get("entities", []), text)
    relations = sanitize_relations(parsed.get("relations", []), entities, text)

    return {
        "text": text,
        "entities": entities,
        "relations": relations,
    }


def main():
    require_env()

    if not INPUT_JSON.exists():
        raise FileNotFoundError(f"{INPUT_JSON} not found")

    raw_records = load_json(INPUT_JSON)
    input_is_list = isinstance(raw_records, list)
    if isinstance(raw_records, dict):
        raw_records = [raw_records]
    elif not isinstance(raw_records, list):
        raise ValueError("Input JSON must be a dict or a list of dicts")

    records = [normalize_input_record(rec, idx + 1) for idx, rec in enumerate(raw_records)]
    selected = records[EXTRACT_START_INDEX: EXTRACT_START_INDEX + EXTRACT_MAX_ITEMS]
    processed_count = read_processed_count(OUTPUT_JSONL)

    total = len(selected)
    print(f"[INFO] endpoint={CHAT_ENDPOINT}")
    print(f"[INFO] model={MODEL}")
    print(f"[INFO] use_response_format={USE_RESPONSE_FORMAT}")
    print(f"[INFO] Selected {total} records, resume found {processed_count} completed output lines.")

    for idx, record in enumerate(selected, start=1):
        if idx <= processed_count:
            print(f"[{idx}/{total}] already processed, skip.")
            continue

        print(f"[{idx}/{total}] extracting id={record['id']} ...")
        done = False
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = process_one(record)
                append_jsonl(OUTPUT_JSONL, result)
                done = True
                time.sleep(SLEEP_BETWEEN)
                break
            except requests.HTTPError as e:
                code = getattr(e.response, "status_code", None)
                body = ""
                try:
                    body = e.response.text[:2000]
                except Exception:
                    pass

                if code in (429, 502, 503, 504):
                    print(f"HTTP {code} on id={record['id']}, body={body}")
                    if code == 429:
                        time.sleep(RATE_LIMIT_WAIT)
                    else:
                        time.sleep(min(8.0, 0.8 * (2 ** (attempt - 1))))
                else:
                    print(f"HTTPError on id={record['id']}, attempt={attempt}, code={code}, body={body}")
                    time.sleep(min(8.0, 0.8 * (2 ** (attempt - 1))))
            except Exception as e:
                print(f"Error on id={record['id']}, attempt={attempt}: {e}")
                time.sleep(min(8.0, 0.8 * (2 ** (attempt - 1))))

        if not done:
            # Keep the public output schema exactly text/entities/relations even on failure.
            fail_item = {
                "text": record["text"],
                "entities": [],
                "relations": [],
            }
            append_jsonl(OUTPUT_JSONL, fail_item)
            with open(FAILED_LOG, "a", encoding="utf-8") as flog:
                flog.write(f"{record['id']}\n")

    all_items = collect_jsonl(OUTPUT_JSONL)
    if input_is_list:
        final_output = all_items
    else:
        final_output = all_items[0] if all_items else {"text": records[0]["text"], "entities": [], "relations": []}
    dump_json(OUTPUT_JSON, final_output)

    print(f"[OK] wrote {OUTPUT_JSONL}")
    print(f"[OK] wrote {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
