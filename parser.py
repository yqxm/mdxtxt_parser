import time
import json
import pymysql

from bs4 import BeautifulSoup
from pymysql import MySQLError

db = pymysql.connect(host='localhost', user='root', password='123456', database='word_dictionary')
cursor = db.cursor()

# read_from = open("part_of_dict.txt", "r", encoding="utf-8")
read_from = open("LEXICO_US.txt", "r", encoding="utf-8")
doc_write = open("lexi.txt", "w", encoding="utf-8")
json_write = open("json.txt", "w", encoding="utf-8")

OELD_BODY = 'OELDBody'
ENTRY_WRAPPER = 'entryWrapper'
ENTRY_HEAD = 'entryHead'
SEMB = 'semb'
EMPTY_SENSE = 'empty_sense'
CROSS_REFERENCE = 'crossReference'
DERIVATIVE_OF = 'derivative_of'
SUB_SENSES = 'subSenses'
Sub_Sense = 'subSense'

CURR_WORD = ''
CURR_ENTRY = 0

INDENT = '  '
DEF_PREFIX = '* '
SUB_DEF_PREFIX = '- '


class OTJ:
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__)


class Word(OTJ):
    def __init__(self):
        self.text = ''
        self.entries = []


class Entry(OTJ):
    def __init__(self):
        self.pos = ''
        self.defs = []


class Def(OTJ):
    def __init__(self):
        self.definition = ''
        self.sub_defs = []


def parse_styled_content(st):
    soup = BeautifulSoup(st, 'html.parser')
    oeld_body = soup.find('div', class_=OELD_BODY)
    entry_wrapper = oeld_body.find('div', class_=ENTRY_WRAPPER)
    entry_heads = entry_wrapper.find_all('div', class_=ENTRY_HEAD)

    word = entry_heads[0].div.div.em.string
    doc_write.write(f'{word}\n')

    w = Word()
    w.text = word
    w.entries = []

    global CURR_WORD
    global CURR_ENTRY
    CURR_WORD = word
    CURR_ENTRY = 0

    content = ''
    for entry in entry_heads:
        CURR_ENTRY += 1
        entry_content = parse_entry_head(entry)
        w.entries.append(reparse_entry_content(entry_content))
        content += entry_content
    if content == '':
        # print(f'{word} has no content')
        content = '\n'
    doc_write.write(content)
    json_write.write(f"{w.toJSON()}\n")
    insert_to_db(w)


TABLE_NAME = 'lexico'


def insert_to_db(w):
    sql = 'INSERT INTO lexico (text, json_text, create_time, update_time) VALUES (%s, %s, now(), now())'
    try:
        cursor.execute(sql, (w.text, w.toJSON()))
        db.commit()
    except MySQLError as e:
        print('error {!r}, errno is {}, word {}'.format(e, e.args[0], w.text))
        db.rollback()


def reparse_entry_content(entry_content):
    entry = Entry()
    content_list = entry_content.split('\n')

    entry.pos = content_list[0].strip()
    k = 1
    length = len(content_list)
    while k < length:
        if content_list[k].startswith(f'{INDENT * 2}{DEF_PREFIX}'):
            defi = Def()
            defi.definition = content_list[k].replace(f'{INDENT * 2}{DEF_PREFIX}', '').strip()
            lk = k + 1
            while lk < length and content_list[lk].startswith(f'{INDENT * 3}{SUB_DEF_PREFIX}'):
                defi.sub_defs.append(content_list[lk].replace(f'{INDENT * 3}{SUB_DEF_PREFIX}', '').strip())
                lk += 1
            entry.defs.append(defi)
        k += 1
    return entry


def parse_entry_head(entry):
    sections = []
    entry_content = ''
    ns = entry.next_sibling
    while ns.name == 'section':
        sections.append(ns)
        ns = ns.next_sibling

    depth = 1
    grambs = list(filter(lambda item: 'gramb' in item['class'], sections))
    for gramb in grambs:
        entry_content += parse_gramb(gramb, depth)
    return entry_content


def parse_gramb(gramb, depth):
    pos = gramb.h3.span.string
    pos_content = f"{INDENT * depth}{pos}\n"

    semb_part = gramb.find('ul', class_=SEMB)
    es_part = gramb.find('div', class_=EMPTY_SENSE)

    if semb_part is not None:
        semb_content = parse_semb(semb_part, depth + 1)
        if semb_content == '':
            return ''
        return pos_content + semb_content
    else:
        es_content = parse_empty_sense(es_part, depth + 1)
        if es_content == '':
            return ''
        return pos_content + es_content


def parse_semb(semb, depth):
    main_defi = semb.li.div.p.find('span', class_='ind')
    semb_content = ''
    # if main_defi is None:
    #     cross_ref = semb.li.div.find('div', class_=CROSS_REFERENCE)
    #     return f'{INDENT * depth}{DEF_PREFIX}{cross_ref.get_text()}\n'
    # else:
    trgs = map(lambda li: li.div, semb.contents)
    for trg in trgs:
        semb_content += parse_trgs(trg, depth)
    return semb_content


def parse_trgs(trg, depth):
    defi = trg.p.find('span', class_='ind')
    trg_content = ''
    if defi is None:
        cross_ref = trg.find('div', class_=CROSS_REFERENCE)
        if cross_ref is None:
            return ''
        trg_content += f'{INDENT * depth}{DEF_PREFIX}{cross_ref.get_text()}\n'
    else:
        trg_content += f'{INDENT * depth}{DEF_PREFIX}{defi.get_text()}\n'
    sub_senses = trg.find('ol', class_=SUB_SENSES)
    if sub_senses is not None:
        # print(f'{CURR_WORD} has sub senses')
        trg_content += parse_sub_senses(sub_senses, depth + 1)
    return trg_content


def parse_sub_senses(sub_senses, depth):
    ss_list = sub_senses.find_all('li', class_=Sub_Sense)

    for sub in ss_list:
        sub_def = sub.find('span', class_='ind')
        if sub_def is not None:
            return f'{INDENT * depth}{SUB_DEF_PREFIX}{sub_def.get_text()}\n'
        else:
            sub_cross = sub.find('div', class_='trg').div
            return f'{INDENT * depth}{SUB_DEF_PREFIX}{sub_cross.get_text()}\n'


def parse_empty_sense(es, depth):
    # if es.contents is None or len(es.contents) == 0:
    #     return ''
    cross_ref = es.find('div', class_=CROSS_REFERENCE)
    if cross_ref is not None:
        return f'{INDENT * depth}{DEF_PREFIX}{cross_ref.get_text()}\n'

    derivative_of = es.find('p', class_=DERIVATIVE_OF)
    if derivative_of is not None:
        return f'{INDENT * depth}{DEF_PREFIX}{derivative_of.get_text()}\n'
    return ''


def db_init():
    cursor.execute("DROP TABLE IF EXISTS lexico;")
    create_table = """CREATE TABLE lexico(
                        id BIGINT primary key auto_increment,
                        text VARCHAR(128) not null,
                        json_text VARCHAR(4096) not null ,
                        create_time timestamp not null ,
                        update_time timestamp not null
                    );"""
    cursor.execute(create_table)


def parse():
    print("start parsing...")
    db_init()
    while True:
        word_head = read_from.readline().strip()
        styled_content = read_from.readline().strip()
        end_tag = read_from.readline().strip()
        if word_head == "":
            break
        parse_styled_content(styled_content)
    db.close()


if __name__ == '__main__':
    start = time.time()
    parse()
    end = time.time()
    print("Parsing is complete.")
    print(f"secs {end - start}s")
    print(f"mins {(end - start) / 60.0}m")
