import sys
import requests.api
from bs4 import BeautifulSoup
from pprint import pprint

def fetch_page(word):
    response = requests.api.get('https://en.wiktionary.org/wiki/{}'.format(word))
    if response.status_code == 200:
        return BeautifulSoup(
            response.text,
            'html.parser',
        )
    else:
        raise RuntimeError("No page for {} was found".format(word))

def parse_toc_for_declensions(node):
    declension_ids = []

    if not hasattr(node, 'children'):
        if node.text == 'Declension':
            return [node.parent.parent['href'].replace('#', '')]
        else:
            return []
    else:
        for child in node.children:
            ids = parse_toc_for_declensions(child)
            declension_ids.extend(ids)

        return declension_ids

def parse_toc(node):
    declensions = []

    if not hasattr(node, 'children'):
        if node.text == 'Russian':
            ids = parse_toc_for_declensions(node.parent.parent.parent)
            return ids
        else:
            return []
    else:
        for child in node.children:
            decls = parse_toc(child)
            declensions.extend(decls)

        return declensions

def parse_declensions(tables):
    ds = []
    for table in tables:
        tds = table.find_all('td')
        ds.append(parse_declension(tds))

    return ds

def handle_case(case):
    match case:
        case 'nom':
            return 'Nominative'
        case 'gen':
            return 'Genitive'
        case 'dat':
            return 'Dative'
        case 'acc':
            return 'Accusative'
        case 'ins':
            return 'Instrumental'
        case 'pre':
            return 'Prepositional'
        case 'loc':
            return 'Locative'
        case 'par':
            return 'Partitive'
        case 'short':
            return 'Short'

def handle_gender(gender, is_sing):
    match gender: 
        case 'm':
            return ['Masculine']
        case 'f':
            return ['Feminine']
        case 'n':
            return ['Neuter']
        case 'm//n':
            return ['Masculine', 'Neuter']
        case None:
            if is_sing:
                return ['Singular']
            else:
                return ['Plural']

def handle_fragments(d, cyrl, fragments):
    is_ann = None
    gender = None
    case = None
    is_sing = None
    for fragment in fragments:
        match fragment:
            case 'm' | 'f' | 'n' | 'm//n':
                gender = fragment
            case 'an':
                is_ann = True
            case 'in':
                is_ann = False
            case 'nom' | 'gen' | 'dat' | 'acc' | 'ins' | 'pre' | 'loc' | 'par' | 'short':
                case = fragment
            case 's-form-of':
                is_sing = True
            case 'p-form-of':
                is_sing = False

    case = handle_case(case)
    genders = handle_gender(gender, is_sing)

    for gender in genders:
        if gender not in d:
            d[gender] = {}
        if is_ann is None:
            if case not in d[gender]:
                d[gender][case] = cyrl
        elif is_ann:
            if case not in d[gender]:
                d[gender][case] = {}
            if 'Animate' not in d[gender][case]:
                d[gender][case]['Animate'] = cyrl
        else:
            if case not in d[gender]:
                d[gender][case] = {}
            if 'Inanimate' not in d[gender][case]:
                d[gender][case]['Inanimate'] = cyrl

def parse_declension(table):
    tds = table.find_all('td')

    d = {}

    for td in tds:
        for span in td.find_all('span'):
            if span['lang'] == 'ru':
                fragments = td.span['class'][3].split('|')
                cyrl = span.text
                handle_fragments(d, cyrl, fragments)

    return d

def parse_html(html):
    tables = []
    declensions = parse_toc(html.find('div', {'id': 'toc'}))

    for declension in declensions:
        parent = html.find('span', {'id': declension}).parent
        node = parent.next_sibling
        while node.name is None:
            node = node.next_sibling
        table = parse_declension(node.find('table'))

        tables.append(table)

    return tables

def parse_tables(tables):
    for table in tables:
        pprint(table)

def main():
    try:
        try:
            word = sys.argv[1]
        except IndexError as e:
            print('Russian word required: {}'.format(e), file=sys.stderr)
            sys.exit(1)

        html = fetch_page(word)
        tables = parse_html(html)

        parse_tables(tables)
    except Exception as e:
        print("{}".format(e))
        sys.exit(1)

if __name__ == '__main__':
    main()
