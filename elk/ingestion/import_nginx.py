
import json
import re
from datetime import datetime
from pathlib import Path

SOURCE = Path(__file__).resolve().parent.parent / "samples/nginx-access-anonymized.log"
DESTINATION = Path(__file__).resolve().parent / "nginx-bulk.ndjson"

LOG_PATTERN = re.compile(
    r'^(?P<client_ip>\S+) \S+ \S+ '
    r'\[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<url>.*?) HTTP/(?P<http_version>[\d.]+)" '
    r'(?P<status>\d{3}) (?P<bytes>\d+|-) '
    r'"(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)"$'
)


def parse_log(line):
    # Une requête HTTP vide est remplacée temporairement
    # par une requête identifiable par notre expression régulière.
    empty_request = '""'
    placeholder = '"EMPTY / HTTP/1.1"'

    normalized_line = line.strip()

    if ' "" ' in normalized_line:
        normalized_line = normalized_line.replace(
            ' "" ', f' {placeholder} ', 1
        )

    match = LOG_PATTERN.match(normalized_line)

    if not match:
        return None

    data = match.groupdict()

    is_empty_request = data["method"] == "EMPTY"

    return {
        "@timestamp": datetime.strptime(
            data["timestamp"], "%d/%b/%Y:%H:%M:%S %z"
        ).isoformat(),
        "client_ip": data["client_ip"],
        "method": None if is_empty_request else data["method"],
        "url": None if is_empty_request else data["url"],
        "http_version": None if is_empty_request else data["http_version"],
        "status": int(data["status"]),
        "bytes": 0 if data["bytes"] == "-" else int(data["bytes"]),
        "referer": data["referer"],
        "user_agent": data["user_agent"],
    }

def main():
    imported = 0
    rejected = 0

    with SOURCE.open(encoding="utf-8") as source, \
         DESTINATION.open("w", encoding="utf-8") as destination:

        for line in source:
            document = parse_log(line)

            if document is None:
                rejected += 1
                continue

            destination.write(
                json.dumps({"index": {"_index": "nginx-access"}}) + "\n"
            )
            destination.write(json.dumps(document) + "\n")
            imported += 1

    print(f"Documents préparés : {imported}")
    print(f"Lignes non reconnues : {rejected}")
    print(f"Fichier généré : {DESTINATION}")

if __name__ == "__main__":
    main()
