escaped_chars = {"$", "^", "+", ".", "*", "(", ")", "|", "\\", "?", "{", "}", "[", "]"}


def glob_to_regex_pattern(glob: str) -> str:
    tokens = ["^"]
    in_group = False
    i = 0
    while i < len(glob):
        c = glob[i]
        if c == "\\" and i + 1 < len(glob):
            char = glob[i + 1]
            tokens.append("\\" + char if char in escaped_chars else char)
            i += 1
        elif c == "*":
            char_before = glob[i - 1] if i > 0 else None
            star_count = 1
            while i + 1 < len(glob) and glob[i + 1] == "*":
                star_count += 1
                i += 1
            if star_count > 1:
                char_after = glob[i + 1] if i + 1 < len(glob) else None
                if char_after == "/":
                    if char_before == "/":
                        tokens.append("((.+/)|)")
                    else:
                        tokens.append("(.*/)")
                    i += 1
                else:
                    tokens.append("(.*)")
            else:
                tokens.append("([^/]*)")
        elif c == "{":
            in_group = True
            tokens.append("(")
        elif c == "}":
            in_group = False
            tokens.append(")")
        elif c == ",":
            if in_group:
                tokens.append("|")
            else:
                tokens.append("\\" + c)
        else:
            tokens.append("\\" + c if c in escaped_chars else c)
        i += 1
    tokens.append("$")
    return "".join(tokens)
