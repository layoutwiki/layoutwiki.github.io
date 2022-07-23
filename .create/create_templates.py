import json
import re
from glob import glob
import os
from typing import Tuple, Union
from math import log1p


ROOT = os.path.dirname(os.path.dirname(__file__))


class Layout:
    def __init__(self, name, language):
        self.name = name
        self.language = language


def load_char_stats():
    with open('.create/char_stats.json', 'r', encoding='utf-8') as file:
        return json.load(file)


def load_layout_keys(formatted_name: str):
    with open(f'{formatted_name}/layout.kb', 'r', encoding='utf-8') as file:
        return "".join(file.read().split())


def get_key_info(char: str, freq_map: dict[float]) -> Tuple[str, str]:
    try:
        prevalence = freq_map[char]
    except KeyError:
        prevalence = 0.0
    
    color = prevalence*30 + log1p(prevalence*120)
    base = 95
    rgb = f"rgb({base*0.9 + round(color * 17)}, {base*1.3 - round(color * 10)}, {base*1.325 - round(color * 10)})"
    title = f"Key usage: {round(prevalence*100, ndigits=2)}%"
    return rgb, title


def build_keyboard(language: str, formatted_name: str) -> str:
    chars = load_layout_keys(formatted_name)
    char_stats = load_char_stats()[language]
    keys = []
    for i, char in enumerate(chars):
        rgb, title = get_key_info(char, char_stats)
        key = f'<div class="k" style="background-color: {rgb};" title="{title}">{char}</div>'
        keys.append(key)
        if i in [4, 14, 24]:
            keys.append('<div class="empty"></div>')
    return "\n\t\t\t\t".join(keys)


def get_text_contents(formatted_name: str) -> str:
    try:
        with open(f"{formatted_name}/text.md", 'r', encoding='utf-8') as file:
            return file.read()
    except:
        return ""


def text_to_section(text: str) -> Union[str, None]:
    n = "\n"
    r = "\n\t\t\t\t"
    t = "\t\t\t"
    header = "".join(text.split("\n")[0].replace(
        "#", "")).strip() if text[0] == "#" else None

    if header is not None:
        text = "\n".join(text.strip().split("\n")[1:])[1:]

    if len(text) > 0:
        paragraphs = "\n".join(
            [f"{t}<p>{r}{r.join(p.split(n))}\n{t}</p>" for p in re.split("\n{2,}", text)]
        )
        if header is not None:
            return f"""
        <h2>{header.capitalize()}</h2>
        <section>
{paragraphs}
        </section>"""
        else:
            return f"""
        <section>
{paragraphs}
        </section>"""
    else:
        return None


def parse_links(text: str, formatted_name: str) -> str:
    full_link = re.compile(
        r"\[((\w|\d| |-|_)+)\]\(((http(s)?://)?(\w+\.)?((\w|-|_|\d)+\.\w+((/\w+)+)?/?))\)")

    for link in re.finditer(r"(\[.*?\]\(.*?\))", text):
        link = link.group(0)
        if not re.search(full_link, link):
            print(
                f"-{' '.join([w.capitalize() for w in formatted_name.split('_')])}: possibly poorly formatted link '{link}'")
        else:
            if re.search(full_link, link).group(4) is None:
                new_link = re.sub(
                    full_link, r'<a href="https://\3">\1</a>', link)
            else:
                new_link = re.sub(full_link, r'<a href="\3">\1</a>', link)
            text = text.replace(link, new_link)

    return text


def parse_contents(formatted_name: str) -> Tuple[str, str]:
    text = get_text_contents(formatted_name)

    text.replace(r"\*", "$@@@&A").replace(r"\_", "$@@@&U").replace(r"\~", "$@@@&S").replace(r"\`", "$@@@&B")

    text = re.sub(r"\*{2}([^\s*]+)\*{2}", r"<b>\1</b>", text)
    text = re.sub(r"\*([^\s*]+)\*", r"<i>\1</i>", text)
    text = re.sub(r"__([^\s_]+)__", r"<u>\1</u>", text)
    text = re.sub(r"_([^\s_]+)_", r"<i>\1</i>", text)
    text = re.sub(r"~~([^\s~]+)~~", r"<s>\1</s>", text)
    text = re.sub(r"`([^\s_]+)`", r"<code>\1</code>", text)

    text.replace("$@@@&A", "*").replace("$@@@&U", "_").replace("$@@@&S", "~").replace("$@@@&B", "`")

    text = parse_links(text, formatted_name)

    sections = [text_to_section("#"+s) for s in re.split(r"#+", text) if len(s) > 0]
    return "".join(filter(lambda x: x is not None, sections))


def get_stats(formatted_name: str) -> str:
    with open(f'{formatted_name}/stats.txt', 'r', encoding='utf-8') as file:
        stats = file.read()
        res = stats.replace("\n", "<br>\n").replace("[", '&nbsp;&nbsp;&nbsp;&nbsp;[')
        res = re.sub(r"Sfb:\s*", "Sfb: &nbsp;", res)

        return "\n\t\t\t\t".join(res.split("\n"))


def create_template(layout_name: str, language: str, call_index=False):
    """
    NOTE THAT PUTTING BOTH put_in_folder AND call_index TO True will OVERWRITE THE CURRENT VERSION OF THE
    FILE THAT'S THERE

    :param layout_name: the name of the layout it should create a template for
    :param language: the lanugage the layout is made for
    :param call_index: whether to name the file index.html
    :return:
    """

    formatted_name = layout_name.lower().replace(" ", "_")
    contents = parse_contents(formatted_name)

    template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{layout_name}</title>
    <link rel="shortcut icon" href="../favicon.ico">
    <link rel="stylesheet" href="../styles.css">

    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300&display=swap" rel="stylesheet">
</head>
<body style="background-color: #222;">
    <div id="home-wrapper">
        <div id="home">Home</div>
        <a href="../index.html"><span id="home-link"></span></a>
    </div>
    <header>
        <h1>{layout_name}</h1>
    </header>
    <article>
        <div class="kb-wrapper">
            <div id="keyboard">
                {build_keyboard(language.lower(), formatted_name)}
            </div>
        </div>{contents}
        <h2>Analyzer stats</h2>
        <div id="stats-wrapper">
            <div class="stats">
                {get_stats(formatted_name)}
            </div>
        </div>
    </article>
</body>
</html>
    """.replace("    ", "\t")

    file_name = "index.html" if call_index else f'{formatted_name}_template.html'
    path = f"{ROOT}/{formatted_name}/{file_name}"
    with open(path, 'w+', encoding='utf-8') as file:
        file.write(template)


def ready_to_update():
    possible = [f for f in glob("*") if os.path.isdir(f)]
    res = []
    for p in possible:
        files = [f.replace("\\", "/") for f in glob(f"{p}/*")]
        files = [f.replace(f"{f.split('/')[0]}/", "") for f in files]
        if all([k in files for k in ['layout.kb', 'stats.txt', 'text.md']]):
            res.append(p)
        else:
            print(f"'{p}' doesn't have the layout.kb, stats.txt or text.md files necessary")
    return res


def to_update() -> list[Tuple[str, str]]:
    possible_languages = load_char_stats().keys()
    possible_to_update = ready_to_update()

    with open(".create/to_update.txt", 'r', encoding='utf-8') as file:
        lines = file.read().split('\n')
        res = []
        for line in lines:
            if re.match(rf"^(\w+| |_|-|;)+~ *({'|'.join(possible_languages)})$", line, re.IGNORECASE):
                thing = line.split('~')
                name, language = thing[0].strip(), thing[1].strip()
                if name.replace(' ', '_').lower() in possible_to_update:
                    res.append((name, language.lower()))
            else:
                if len(line) > 1:
                    print(f"line '{line}' in to_update.txt formatted incorrectly")
        return res


def didnt_update(name: str, language: str) -> str:
    return f"{name.capitalize().replace('_', ' ').replace('-', ' ')} ~ {language.capitalize()}"


def create_templates(): 
    still_needs_updating = []
    for name, language in to_update():
        try:
            create_template(name, language, True)
            print(f"'{name}' has been updated")
        except:
            print(name, 'failed to update')
            still_needs_updating.append(didnt_update(name, language))

    with open(".create/to_update.txt", 'w+', encoding='utf8') as txt:
        txt.write("\n".join(still_needs_updating))
    

def main():
    create_templates()


if __name__ == "__main__":
    main()
