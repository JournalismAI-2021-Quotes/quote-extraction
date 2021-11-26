import spacy

from functools import reduce
from itertools import groupby
import requests, json
import re

from spacy.language import Language

from .preprocessing import sentencise_text, open_quote_mark, close_quote_mark


def get_person_by_sentence(text, nlp_model):
    person_list = []
    tokens = nlp_model(text)
    sentences = [sent.text.strip() for sent in tokens.sents]
    for sent in sentences:
        all_tags = nlp_model(sent)
        for ent in all_tags.ents:
            if ent.label_ == "PERSON":
                person_list.append(str(ent))
    return person_list


def get_life_peers(text):
    # find a nobel title and grab it with the following name
    names = re.compile(r'(Lord|Baroness|Lady|Baron)\s+([A-Za-z]+(?:-[A-Za-z]+)?)')
    names_with_titles = names.findall(text)
    life_peers = list(set(names_with_titles))
    empty_free = [(tuple(int(x) if x.isdigit() else x for x in _ if x)) for _ in life_peers]
    # remove duplicates based on the last index in tuples
    dupl_free = [max(reversed(list(v)), key=len) for k, v in groupby(empty_free, lambda x: x[0])]
    life_peers = list(set([' '.join(map(str, peer)) for peer in dupl_free]))
    peers_names = [name.rstrip() for name in life_peers]
    # filter for exceptions
    peers_names = [name for name in peers_names if
                   name not in ['Lord Lieutenant', 'Lord Justice Sir', 'Lord Chief Justice']]
    return peers_names


############################################################################################################
## Some titles and other things to remove to stop spacy being confused

replace = ['Mr ', 'Ms ', 'Mrs ', 'Miss ', 'Sir ', 'Prof ', 'Dr ', 'Det ', 'Sgt ', 'Maj ',
           'Gen ', 'Insp ', 'Secretary ', 'Capt ', 'Colonel ', 'Col ', 'Chief ', 'Inspector ',
           'Sergeant ', 'Captain ', ' Chairman', ' QC', ' PE', 'DS ', ' MEP', 'Con ',
           'Zanu-PF. ', 'YouTuber ', 'Businesswoman ', 'Celebrity ', 'PST', ' Show',
           'Fusilier ', 'Rev ', 'Brexiteer ', 'Constable ', 'Supt ', 'Britons ', 'Follow ', 'Barrister ', 'Remainer ',
           ' "', '.', '\n', '"', ';', '[', ']', '(', ')',
           'Prince ', 'Princess ', 'Dame ']  # New additions
drop = ['Church', 'Government', 'St', 'Court', 'Greater', 'Tower', 'House', 'Cottage', 'Police', 'Public', 'Campaign',
        'Champion', 'Stop', 'Analysis', 'Street', 'Line', 'Brexit',
        'Daily', 'Starbucks', 'Virgin', 'Panorama', 'London', 'Google', 'Facebook', 'Twitter', 'Youtube', 'Instagram',
        'Vitamin', 'Ombudsman', 'Centre']
remove = ['Sina Weibo', 'Greater Manchester', 'Porton Down', 'Parsons Green', 'Thomas Cook', 'Childline',
          'Sussex', 'Essex', 'Surrey', 'Facebook', 'Twitter', 'Brexit', 'Photographer', 'Royal', 'Tube',
          'West Sussex', 'Abbots Langley', 'Maundy Thursday', 'Amazon Marketplace', 'Human Planet', 'NHS England',
          'Knight Takeaway', 'Mear One', 'Cambridge Analytica', 'Old Bailey', 'Big Ben',
          'First Minister', 'Facebook Click', 'HM Treasury', 'Deep Purple', 'Westminster Abbey',
          'Plaid Cymru', 'Labour Party', 'Lib Dem', 'Lib Dems', 'Sinn Fein', 'Privacy Policy',
          'IPSOS Mori', 'Aston Martin', 'Grammys', 'Luton', 'Gatwick', 'Bitcoin', 'Wimbledon', 'Mrs', 'Mum',
          'Novichok', 'Vice', 'Tai Chi', 'Newsbeat', 'Sun', 'Met Office', 'Bloomberg', 'Ex', 'Cobra',
          'Lancashire', 'Devon', 'Met', 'Fifa',
          'Jim Crow', 'Grant Thornton', 'Covid', 'Green Day', 'Erasmus']  # New additions

royal_dict = {'The Queen': ['The Queen', 'Elizabeth II', 'Princess Elizabeth', 'the Queen'],
              'Prince Philip': ['Duke of Edinburgh', 'Prince Philip', 'Philip Mountbatten'],
              'Prince Charles': ['Prince of Wales', 'Prince Charles'],
              'Princess Diana': ['Princess Diana', 'Princess of Wales', 'Lady Diana Spencer', 'Diana Spencer',
                                 'Lady Diana'],
              'Prince William': ['Duke of Cambridge', 'Prince William'],
              'Kate Middleton': ['Duchess of Cambridge', 'Kate Middleton'],
              'Prince Harry': ['Duke of Sussex', 'Prince Harry', 'Prince Henry of Wales'],
              'Meghan Markle': ['Duchess of Sussex', 'Meghan Markle'],
              'Prince Andrew': ['Duke of York', 'Prince Andrew'],
              'Prince Michael of Kent': ['Duke of Kent', 'Prince Michael of Kent'],
              'Prince Edward': ['Prince Edward', 'Earl of Wessex'],
              'Princess Anne': ['Princess Anne', 'Princess Royal'],
              # MBS. New addition
              'Mohammed bin Salman': ['Prince Mohammed bin Salman', 'MbS', 'Crown Prince of Saudi Arabia',
                                      'Crown Prince']}


def cleaning_names(names):
    # remove twitter pictures
    twitter_pic_free = [re.sub(r'[^\s]*pic.twitter.com[^\s]*', '', name) for name in names]
    # remove parts from the replace list
    names_replace = [reduce(lambda str, e: str.replace(e, ''), replace, name) for name in twitter_pic_free]
    # remove strings with numbers
    no_digits = [name for name in names_replace if not re.search(r'\d', name)]
    # remove string in ALL lower
    no_lower = [name for name in no_digits if not name.islower()]
    # remove strings in ALL upper
    no_upper = [name for name in no_lower if not name.isupper()]
    # remove strings which start with 'the '
    no_the = [name for name in no_upper if name not in [name for name in no_upper if name.lower().startswith('the ')]]
    # remove words afrer '. ' when it grabs the beggining of the next sentence
    after_stop = [name.split('. ', 1)[0] for name in no_the]

    # split names separated by comma when Spacy grabs them together
    comma_free = []
    for name in after_stop:
        if ', ' not in name:
            comma_free.append(name)
        else:
            for i in range(len(name.split(', '))):
                comma_free.append(name.split(', ')[i])

    # remove ' - who' etc.
    no_hyphen = [re.sub(r'(\ - .*$)', '', name) for name in comma_free]
    # remove email addresses
    no_email = [re.sub(r'[^\s]*@[^\s]*', '', name) for name in no_hyphen]
    # remove strings with & char
    no_special_char = [name for name in no_email if '&' not in name]
    # remove words before ''s ' when it's not part of the name
    s_names = [name.split("'s ", 1)[-1] for name in no_special_char]
    # remove 's and ' at the end of the name
    names_s = [re.sub(r"'s$|'$", '', name) for name in s_names]
    # remove long -, (, +
    no_sintax = [re.sub(r'(\— )', '', name) for name in names_s]
    no_sintax = [re.sub(r'( \()', '', name) for name in no_sintax]
    no_sintax = [re.sub(r'(\+)', '', name) for name in no_sintax]
    # remove - from the end
    no_end_dash = [name[:-2] if name.endswith(' -') else name for name in no_sintax]
    # al-Assad == Assad == Al-Assad
    no_al = [re.sub(r'(al-)|(Al-)', '', name) for name in no_end_dash]
    # remove BBC, NHS etc. and MoJ etc. but not Smith-Porter
    no_abr = []
    for name in no_al:
        if not re.search(r'(\w*[A-Z]\w*[A-Z]\w*)', name):
            no_abr.append(name)
        elif re.search(r'(Mc[A-Z]|Mac[A-Z])', name):
            no_abr.append(name)

    # remove empty strings
    no_empty = [i for i in no_abr if len(i) > 0]

    # set to lower then back to capwords - Kim Jong-Un == Kim Jong-un
    names_cap = [name for name in no_empty if name.istitle() or name.title() not in no_empty]
    names_unique = list(set(names_cap))

    clean_names = [name for name in names_unique if name.lower() not in [e.lower() for e in remove]]

    # check surnames against full names
    lonely_names = [name.split(' ')[0] for name in clean_names if ' ' not in name]  # grab lonely(!) names

    double_surnames = [name.split(' ')[-2] + ' ' + name.split(' ')[-1] for name in clean_names \
                       if ' ' in name and len(name.split(' ')) == 3]

    first_double_surnames = [name.split(' ')[0] for name in double_surnames]
    second_double_surnames = [name.split(' ')[1] for name in double_surnames]

    first_names = [name.split(' ')[0] for name in clean_names if ' ' in name \
                   and name.split(' ')[0] not in first_double_surnames]  # grab first names from full names
    surnames = [name.split(' ')[-1] for name in clean_names if ' ' in name and len(name.split(' ')) == 2 \
                and name.split(' ')[1] not in second_double_surnames]  # grab last names

    # common in English where the surname is only the third name and the second shouldn't be included.
    surnames += second_double_surnames

    full_names = [name for name in clean_names if ' ' in name and name not in double_surnames]  # grab full names

    # Rule Osama Laden == Osama Bin Laden == Osama Laden
    names_to_drop = []
    for i in range(1, len(full_names)):

        if full_names[i].split(' ')[0] == full_names[i - 1].split(' ')[0] \
                and full_names[i].split(' ')[-1] == full_names[i - 1].split(' ')[-1]:
            names_to_drop.append(full_names[i])

    for name in names_to_drop:
        full_names.remove(name)

    first_names_surnamesfree = []
    for name in lonely_names:
        if name not in surnames and name not in second_double_surnames:
            first_names_surnamesfree.append(name)

    first_names_duplicatesfree = []
    for name in first_names_surnamesfree:
        if name not in first_names:
            first_names_duplicatesfree.append(name)

    names_unique_new = first_names_duplicatesfree + full_names

    # drop part of names from the drop list
    names_drop = [name for name in names_unique_new if not any(e.lower() in name.lower().split(' ') for e in drop)]
    # drop names from the removal list

    # list_of_names is a list of all PERSON entities in the article
    names_dict = {}
    names_with_middle = []
    for i in range(1, len(clean_names)):
        if clean_names[i].split(' ')[0] == clean_names[i - 1].split(' ')[0] \
                and clean_names[i].split(' ')[-1] == clean_names[i - 1].split(' ')[-1]:
            names_dict[clean_names[i]] = clean_names[i - 1]
            names_with_middle.append(clean_names[i])

    return names_drop, surnames, first_names_duplicatesfree


def remove_duplicate_names(names, other_names):
    out = []
    for name in names:
        names_split = name.split()
        for i in range(len(names_split) + 1, 0, -1):
            for n in range(0, len(names_split) + 1 - i):
                names_join = ' '.join(names_split[n:n + i])
                for n in names_split:
                    for name in other_names:
                        if re.search(r"\b" + n + r"\b", name):
                            out.append(names_join)
    clean_names = [name for name in names if name not in out]
    return clean_names


def clean_orgs(org_list):
    not_orgs_to_filter = ['Brexit', 'Chauvin', 'Cambridge', 'Rishi', 'Sunak', 'Greensill', 'Biden', 'Obama', 'Trump',
                          'Johnson', 'Noor']

    clean_org_list = [org for org in org_list if org not in not_orgs_to_filter]
    clean_org_list = [org[:-2] if org[-2:] == "'s" else org for org in clean_org_list]

    return clean_org_list


def get_people_and_orgs_by_sentence(text, nlp_model):
    person_list = []
    org_list = []
    sentences = [nlp_model(sent) for sent in sentencise_text(text)]
    for sent in sentences:
        for ent in sent.ents:
            if ent.label_ == "PERSON":
                person_list.append(str(ent))
            elif ent.label_ == 'ORG':
                org_list.append(ent.text)

    cleaned_orgs = clean_orgs(org_list)
    return person_list, cleaned_orgs, sentences


def get_complete_ents_list(text, nlp_model):
    """ Gets a complete list of entities in a text using a spacy model

       Returns:
           a cleaned list of full_names, surnames, lonely_names (names that only appear as a single word, not
           'first_name last_name', peers names and a list of sentences (the last one to save running some functions multiple
           times.
       """

    names, orgs, sents = get_people_and_orgs_by_sentence(text, nlp_model)
    peers_names = get_life_peers(text)

    clean_names_all, surnames, lonely_names = cleaning_names(names)
    clean_names = remove_duplicate_names(clean_names_all, peers_names)
    full_names = clean_names + peers_names

    return full_names, surnames, lonely_names, orgs, peers_names, sents

