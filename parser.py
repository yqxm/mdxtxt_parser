import time

from bs4 import BeautifulSoup

# read_from = open("a.txt", "r", encoding="utf-8")
read_from = open("LEXICO_US.txt", "r", encoding="utf-8")
write_to = open("result.txt", "w", encoding="utf-8")

OELD_BODY = 'OELDBody'
ENTRY_WRAPPER = 'entryWrapper'
ENTRY_HEAD = 'entryHead'
SEMB = 'semb'
EMPTY_SENSE = 'empty_sense'
CROSS_REFERENCE = 'crossReference'
DERIVATIVE_OF = 'derivative_of'

CURR_WORD = ''
CURR_ENTRY = 0


def parse_styled_content(st):
    soup = BeautifulSoup(st, 'html.parser')
    oeld_body = soup.find('div', class_=OELD_BODY)
    entry_wrapper = oeld_body.find('div', class_=ENTRY_WRAPPER)
    entry_heads = entry_wrapper.find_all('div', class_=ENTRY_HEAD)

    word = entry_heads[0].div.div.em.string
    write_to.write(f'{word}\n')

    global CURR_WORD
    global CURR_ENTRY
    CURR_WORD = word
    CURR_ENTRY = 0

    for entry in entry_heads:
        CURR_ENTRY += 1
        parse_entry_head(entry)


def parse_entry_head(entry):
    sections = []
    ns = entry.next_sibling
    while ns.name == 'section':
        sections.append(ns)
        ns = ns.next_sibling

    depth = 1
    grambs = list(filter(lambda item: 'gramb' in item['class'], sections))
    for gramb in grambs:
        parse_gramb(gramb, depth)


INDENT = '\t'


def parse_gramb(gramb, depth):
    pos = gramb.h3.span.string
    write_to.write(f"{INDENT * depth}{pos}\n")

    semb_part = gramb.find('ul', class_=SEMB)
    es_part = gramb.find('div', class_=EMPTY_SENSE)

    if semb_part is not None:
        parse_semb(semb_part, depth + 1)
    else:
        parse_empty_sense(es_part, depth + 1)


def parse_semb(semb, depth):
    main_defi = semb.li.div.p.find('span', class_='ind')
    if main_defi is None:
        cross_ref = semb.li.div.find('div', class_='crossReference')
        write_to.write(f'{INDENT * depth}{cross_ref.get_text()}\n')
    else:
        trgs = map(lambda li: li.div, semb.contents)
        for trg in trgs:
            parse_trgs(trg, depth)


def parse_trgs(trg, depth):
    defi = trg.p.find('span', class_='ind')
    if defi is None:
        cross_ref = trg.find('div', class_=CROSS_REFERENCE)
        if cross_ref is None:
            print(f'{CURR_WORD} {CURR_ENTRY} trg has no cross ref')
            return
        write_to.write(f'{INDENT * depth}{cross_ref.get_text()}\n')
    else:
        write_to.write(f'{INDENT * depth}{defi.get_text()}\n')


def parse_empty_sense(es, depth):
    if es.contents is None or len(es.contents) == 0:
        print(f"{CURR_WORD} {CURR_ENTRY} empty sense part is blank")

    cross_ref = es.find('div', class_=CROSS_REFERENCE)
    if cross_ref is not None:
        write_to.write(f'{INDENT * depth}{cross_ref.get_text()}\n')
        return

    derivative_of = es.find('p', class_=DERIVATIVE_OF)
    if derivative_of is not None:
        write_to.write(f'{INDENT * depth}{derivative_of.get_text()}\n')


def parse():
    print("start parsing...")
    while True:
        word_head = read_from.readline().strip()
        styled_content = read_from.readline().strip()
        end_tag = read_from.readline().strip()
        if word_head == "":
            break
        parse_styled_content(styled_content)


if __name__ == '__main__':
    start = time.time()
    parse()
    end = time.time()
    print("Parsing is complete.")
    print(f"secs {end - start}s")
    print(f"mins {(end - start) / 60.0}m")
