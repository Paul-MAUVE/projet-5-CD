
import ipaddress
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "samples/nginx-access.log"
DESTINATION = ROOT / "samples/nginx-access-anonymized.log"

PATTERN = re.compile(
    r'^(\S+ \S+ \S+ \[[^\]]+\] )'
    r'"([^"]*)" '
    r'(\d{3} \S+) '
    r'"[^"]*" "[^"]*"$'
)

ip_mapping = {}


def anonymize_ip(original_ip):
    if original_ip not in ip_mapping:
        index = len(ip_mapping) + 1
        ip_mapping[original_ip] = str(
            ipaddress.IPv4Address(int(ipaddress.IPv4Address("10.0.0.0")) + index)
        )
    return ip_mapping[original_ip]


def clean_request(request):
    if not request:
        return ""

    parts = request.split(" ", 2)

    if len(parts) != 3:
        return ""

    method, url, protocol = parts

    path = urlsplit(url).path
    path = re.sub(r"/\d+(?=/|$)", "/{id}", path)
    path = re.sub(r"(?<=/)[^/]{32,}(?=/|$)", "{segment}", path)

    return f"{method} {path} {protocol}"


def main():
    total = 0

    with SOURCE.open(encoding="utf-8") as source, \
         DESTINATION.open("w", encoding="utf-8") as destination:

        for line_number, line in enumerate(source, start=1):
            match = PATTERN.match(line.rstrip("\n"))

            if not match:
                raise ValueError(f"Format invalide à la ligne {line_number}")

            prefix, request, response = match.groups()
            fields = prefix.split(" ", 1)

            ip = anonymize_ip(fields[0])
            remaining_prefix = fields[1]

            cleaned_request = clean_request(request)

            destination.write(
                f'{ip} {remaining_prefix}'
                f'"{cleaned_request}" {response} "-" "-"\n'
            )

            total += 1

    print(f"Lignes traitées : {total}")
    print(f"IP remplacées : {len(ip_mapping)}")
    print(f"Fichier généré : {DESTINATION}")


if __name__ == "__main__":
    main()
