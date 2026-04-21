import re
import codecs
from collections.abc import Iterable


def _decode_model_escapes(text: str) -> str:
    try:
        return codecs.decode(text, "unicode_escape")
    except Exception:
        return text


def parse_expected_values(raw: str, expected_keys: Iterable[str]) -> dict[str, str]:
    expected_keys = list(dict.fromkeys(expected_keys))
    if not expected_keys:
        return {}

    key_pattern = "|".join(re.escape(key) for key in sorted(expected_keys, key=len, reverse=True))

    entry_pattern = re.compile(
        rf'(?P<full>'
        rf'(?P<prefix>(?:^|[{{,])\s*)'
        rf'(?P<kq>[\'"])'
        rf'(?P<key>{key_pattern})'
        rf'(?P=kq)\s*:\s*'
        rf'(?P<vq>[\'"])'
        rf')',
        re.DOTALL,
    )

    matches = list(entry_pattern.finditer(raw))
    if not matches:
        raise ValueError("No expected keys found in output.")

    found: dict[str, str] = {}

    for i, match in enumerate(matches):
        key = match.group("key")
        value_start = match.end()

        if i + 1 < len(matches):
            value_end = matches[i + 1].start()
        else:
            value_end = len(raw)

        value = raw[value_start:value_end]

        value = value.rstrip()

        if i + 1 < len(matches):
            value = value.rstrip()
            if value.endswith(","):
                value = value[:-1].rstrip()
        else:
            while value.endswith("}") or value.endswith(" ") or value.endswith("\n") or value.endswith("\t"):
                if value.endswith("}"):
                    value = value[:-1]
                else:
                    value = value[:-1]

        if value.endswith(("'", '"')):
            value = value[:-1]

        found[key] = _decode_model_escapes(value)

    missing = [key for key in expected_keys if key not in found]
    if missing:
        raise ValueError(f"Missing expected keys: {missing}")

    return {key: found[key] for key in expected_keys}