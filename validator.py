import time
import warnings

from bs4 import BeautifulSoup

# read_from = open("a.txt", "r", encoding="utf-8")
read_from = open("LEXICO_US.txt", "r", encoding="utf-8")
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
        raise RuntimeError(word, " has no name in entry head.")

    i = 0
    for entry in entry_heads:
        i += 1
        validate_entry(word, entry, i)


def validate_entry(word, entry, i):
    sections = []
    ns = entry.next_sibling
    while ns.name == 'section':
        sections.append(ns)
        ns = ns.next_sibling

    grambs = list(filter(lambda item: 'gramb' in item['class'], sections))
    if len(grambs) == 0:
        raise RuntimeError(f"{word} {i} should have gramb.")
    for gramb in grambs:
        validate_gramb(word, gramb, i)


def validate_gramb(word, gramb, i):
    if gramb.h3.span is None:
        raise RuntimeError(f"{word} {i} should have part of speech.")
    hul_part = gramb.find('ul', class_='semb')
    es_part = gramb.find('div', class_='empty_sense')

    if es_part is None and hul_part is None:
        print(f"{word} {i} has no semb and empty_sense part")
        return
    elif es_part is not None and hul_part is not None:
        print(f"{word} {i} has both semb and empty_sense part.")
        return

    if hul_part is not None:
        i = 0
        # validate_semb(word, hul_part, i)
    else:
        validate_empty_sense(word, es_part, i)


def validate_semb(word, hul, i):
    main_defi = hul.li.div.p.find('span', class_='ind')
    if main_defi is None:
        cross_ref = hul.li.div.find('div', class_='crossReference')
        if cross_ref is None:
            print(f"{word} {i} entry has no main def and cross reference.")


def validate_empty_sense(word, es, i):
    if es.find('div', class_="crossReference") is None and es.find('p', class_='derivative_of') is None:
        print(f"{word} {i} entry empty sense has no cross reference or derivative_of.")


def check_if_file_is_good():
    while True:
        word = read_from.readline().strip()
        styled_content = read_from.readline().strip()
        end_tag = read_from.readline().strip()
        if word == "":
            break

        # write_to.write(word + "\n")
        check_dom_for_parse(word, styled_content)
        check_end_tag(end_tag)
        # break


if __name__ == '__main__':
    start = time.time()
    check_if_file_is_good()
    end = time.time()
    print("Validation is complete. Let's go parsing.")
    print(f"secs {end-start}s")
    print(f"mins {(end-start)/60.0}m")
