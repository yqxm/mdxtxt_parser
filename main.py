import time

from bs4 import BeautifulSoup

read_from = open("a.txt", "r", encoding="utf-8")
# read_from = open("LEXICO_US.txt", "r", encoding="utf-8")
write_to = open("w.txt", "w", encoding="utf-8")


def check_end_tag(end_tag):
    if end_tag == '</>':
        return True
    else:
        raise RuntimeError("not good end of word section")


def check_dom_for_parse(word, st):
    soup = BeautifulSoup(st, 'html.parser')
    body_list = soup.find_all("div", class_="OELDBody")
    if len(body_list) != 1:
        raise RuntimeError(word + " should have only one OELDBody.")

    oeld_body = body_list[0]
    entry_wrapper_list = oeld_body.find_all("div", class_="entryWrapper")
    if (len(entry_wrapper_list)) != 1:
        raise RuntimeError(word + " should have only one entry wrapper.")

    entry_wrapper = entry_wrapper_list[0]
    entry_heads = entry_wrapper.find_all("div", class_="entryHead")
    if (len(entry_heads)) == 0:
        raise RuntimeError(word + " should have at least one entry head.")

    if entry_heads[0].div.div.em.string is None:
        raise RuntimeError(word , " has no name in entry head.")
    for entry in entry_heads:
        validate_entry(word, entry)


def validate_entry(word, entry):
    sections = []
    ns = entry.next_sibling
    while ns.name == 'section':
        sections.append(ns)
        ns = ns.next_sibling
    grambs = list(filter(lambda item: 'gramb' in item['class'], sections))
    if len(grambs) == 0:
        raise RuntimeError(word + " should have gramb.")


def check_if_file_is_good():
    while True:
        word = read_from.readline().strip()
        styled_content = read_from.readline().strip()
        end_tag = read_from.readline().strip()
        if word == "":
            break

        write_to.write(word + "\n")
        check_dom_for_parse(word, styled_content)
        check_end_tag(end_tag)
        # break


if __name__ == '__main__':
    start = time.time()
    check_if_file_is_good()
    end = time.time()
    print("secs ", end - start, "s")
    print("mins ", (end - start) / 60.0, "m")
