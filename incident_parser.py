import re

def parse_short_description(text: str) -> dict:
    """
    Extract:
    - state
    - line
    - company
    - txn_type (optional)
    - erw_code
    """

    if not text:
        return {}

    tokens = text.split()

    state = None
    line = None
    company = None
    txn_type = None
    erw_code = None

    # ERW pattern like NVUAPHC-14
    erw_pattern = re.compile(r"[A-Z0-9]+-\d+")

    # Basic positional extraction
    if len(tokens) >= 3:
        state = tokens[0]
        line = tokens[1]
        company = tokens[2]

    # Find ERW anywhere in the string
    for token in tokens:
        if erw_pattern.match(token):
            erw_code = token
            break

    # Detect txn_type if ERW appears at position 4
    if len(tokens) >= 5 and tokens[4] == erw_code:
        txn_type = tokens[3]

    return {
        "state": state,
        "line": line,
        "company": company,
        "txn_type": txn_type,
        "erw_code": erw_code
    }
