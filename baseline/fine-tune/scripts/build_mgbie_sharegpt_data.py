import argparse
import json
from pathlib import Path

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


def load_records(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_target(record):
    entities = [
        {
            "start": entity["start"],
            "end": entity["end"],
            "text": record["text"][entity["start"] : entity["end"]],
            "label": entity["label"],
        }
        for entity in record["entities"]
    ]
    relations = [
        {
            "head": relation["head"],
            "head_start": relation["head_start"],
            "head_end": relation["head_end"],
            "head_type": relation["head_type"],
            "tail": relation["tail"],
            "tail_start": relation["tail_start"],
            "tail_end": relation["tail_end"],
            "tail_type": relation["tail_type"],
            "label": relation["label"],
        }
        for relation in record["relations"]
    ]
    return json.dumps({"entities": entities, "relations": relations}, ensure_ascii=False)


def build_user_content(text: str):
    return (
        "Extract entities and relations from the following text. "
        f"Allowed entity labels: {', '.join(ENTITY_LABELS)}. "
        f"Allowed relation labels: {', '.join(RELATION_LABELS)}.\n"
        "Text:\n"
        f"{text}"
    )


def convert_records(records):
    converted = []
    for idx, record in enumerate(records):
        converted.append(
            {
                "id": str(idx),
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": build_user_content(record["text"])},
                    {"role": "assistant", "content": build_target(record)},
                ],
                "source_index": idx,
            }
        )
    return converted


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", required=True)
    parser.add_argument("--output_file", required=True)
    args = parser.parse_args()

    input_path = Path(args.input_file)
    output_path = Path(args.output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    records = load_records(input_path)
    converted = convert_records(records)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(converted, f, ensure_ascii=False, indent=2)

    print(json.dumps({"records": len(converted), "output_file": str(output_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
