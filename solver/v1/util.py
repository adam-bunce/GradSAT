def course_level(course: str) -> int:
    buf = ""
    for c in course:
        if c.isnumeric():
            buf += c

    if buf == "":
        return -1

    res = int(buf[0])
    if res > 4:
        return 4

    return res


def is_science(course: str) -> bool:
    prefixes = ["BIOL", "CHEM", "CSCI", "ENVS", "FSCI", "MATH", "NCSI", "PHY", "STAT"]
    for prefix in prefixes:
        if course.startswith(prefix):
            return True
    return False


def get_code(course: str) -> str:
    buf = ""
    for c in course:
        if c.isnumeric():
            break
        buf += c
    return buf
