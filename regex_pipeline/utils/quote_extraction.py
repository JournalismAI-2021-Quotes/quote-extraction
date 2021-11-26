import logging
import re

from utils.classes import Quote
from utils.preprocessing import sentencise_text, get_quote_indices, uniq
from utils.functions_spacy3 import get_complete_ents_list


########################################################
## Regex definitions and quote verb list
########################################################

with open('utils/quote_verb_list.txt', 'r') as f:
    quote_verbs = [(line.strip()) for line in f]

quote_verb_boolean_list = [quote + "|" for quote in quote_verbs]
quote_verb_boolean_list = [quote + "|" for quote in quote_verbs if quote[-1:] in ['d', 'g', 's']]
quote_verb_boolean_string = ''.join(quote_verb_boolean_list)
quote_verb_boolean_string = quote_verb_boolean_string[:-1]

re_quote_someone_said = \
    r'(“[^“\n]+?[,?!]”) ([^\.!?]+?)[\n ]({cue_verbs})([^\.!?]*?)[\.,][\n ]{{0,2}}(“[\w\W]+?”){{0,1}}'.format(
    cue_verbs= quote_verb_boolean_string)
re_quote_said_someone = '(“[^“\n]+?[,?!]”)[\n ]({cue_verbs}) ([^\.!?]+?)[\.,](\s{{0,2}}“[^”]+?”){{0,1}}'.format(
    cue_verbs=quote_verb_boolean_string)
re_quote_someone_told_someone = \
    '(“[^“\n]+?[,?!]”)[\n ]([^\.!?]*?) ({cue_verbs}) ([^\.!?]*?)[\.,][\n ]{{0,2}}(“[\w\W]+?”){{0,1}}'.format(
    cue_verbs=quote_verb_boolean_string)
re_quote_someone_said_colon = \
    '([^“\n]+?) ({cue_verbs})( \w*?){{0,5}}: (“[\w\W]+?”){{1,1}}'.format(
    cue_verbs=quote_verb_boolean_string)
re_quote_someone_said_adding_colon = \
    '([\w\W]+?) (“[\w\W]+?”)([-–\’\s,\w]*?) (adding)( \w*?){0,5}: (“[\w\W]+?”){1,1}'

between_quotes = '“[^“”,]+?”'
between_quotes_sentence_start = '$“[^“”]+?”'
between_quotes_ends_with_comma = '“[^“”]+?,”'

QUOTE_TYPES = {
    'someone_said': 1,
    'said_someone': 2,
    'someone_told_someone': 3,
    'someone_said_colon': 4,
    'someone_said_adding_colon': 5
}
QUOTE_TYPES_PATTERNS = {
    1: {'quote_text': 0, 'speaker': 1, 'quote_text_optional_second_part': -1},
    2: {'quote_text': 0, 'speaker': 2, 'quote_text_optional_second_part': 3},
    3: {'quote_text': 0, 'speaker': 1, 'quote_text_optional_second_part': 4},
    4: {'quote_text': 3, 'speaker': 0},
    5: {'quote_text': 0, 'quote_text_optional_second_part': 1, 'additional_cue': 3, 'quote_text_optional_third_part': 4}
}

########################################################
## Function definitions
########################################################

def parse_sentence_quotes(sents, nlp_model, debug=False):
    """ Takes a list of sentences of the article and parses out quotes.
        Uses spacy's dependency parser:
        1) It replaces everything between quotes with a dummy phrase (to simplify the
        structure of the sentence that spacy needs to parse).
        2) It then checks each token. If a quote verb appears as the verb of a sentence, it finds the nsubj of the
           sentence, collects the subtree of the nsubj and stores them as the speaker.

        TO BE IMPROVED:
        For sentences that have two quotes within them, this process becomes quite difficult - current approach
        is to split the sentence in two at the end of the first quote but this won't work for all sentences.

        :param sents: the pre-processed text of an article split up into sentences
        :param nlp: spacy model

        returns: a list of sentence_parse_quotes:
                [quote_text, speaker (if possible), quote_verb, sent_index, start_index, end_index]
                start_index and end_index are for the quote text and relative to the sentence.
        """
    assert type(sents) == list

    sentence_parse_quotes = []
    for sent_index in range(len(sents)):
        sent = sents[sent_index]

        sentence_quote_indices = get_quote_indices(sent)
        if debug:
            logging.debug(sentence_quote_indices)
        if len(sentence_quote_indices) == 0:
            pass

        else:
            if sent[0] == '“':
                if sent.find(',”'):
                    modified_sent = re.sub(between_quotes_sentence_start, '“Dummy phrase,”', sent)
            else:
                if sent.find(',”'):
                    modified_sent = re.sub(between_quotes_ends_with_comma, '“dummy phrase,”', sent)
                else:
                    modified_sent = re.sub(between_quotes, '“dummy phrase”', sent)

            m_doc = nlp_model(modified_sent)
            logging.debug(sent)
            logging.debug(modified_sent)
            m_sentence_quote_indices = get_quote_indices(modified_sent)

        if len(sentence_quote_indices) == 1:
            for start_index, end_index in sentence_quote_indices:
                m_start_index, m_end_index = m_sentence_quote_indices[0]

                quote_text = sent[start_index:end_index + 1]

                for tok in m_doc:
                    if ((tok.head.idx < m_start_index or tok.head.idx > m_end_index) and
                            (tok.idx < m_start_index or tok.idx > m_end_index) and
                            tok.dep_ == 'nsubj' and tok.head.pos_ == 'VERB' and tok.head.text in quote_verbs
                    ):
                        subtree = [t for t in tok.subtree]
                        idxes = [t.idx for t in subtree]
                        speaker = modified_sent[idxes[0]:idxes[-1] + len(subtree[-1])]
                        speaker = speaker.replace('“', '').replace('”', '').replace('dummy phrase', '').replace(
                            'Dummy phrase', '').strip()
                        logging.debug(sent)
                        logging.debug(modified_sent)
                        logging.debug(speaker)

                        if speaker in ('He', 'She'):
                            speaker = speaker.lower()
                        quote_verb = tok.head.text
                        sentence_parse_quotes.append(
                            [quote_text, speaker, quote_verb, sent_index, start_index, end_index])
                        break

                try:
                    if quote_text != sentence_parse_quotes[-1][0] and quote_text[0] != '“' and quote_text[-1] != '”':
                        for tok in m_doc:
                            if (tok.head.pos_ == 'VERB' and tok.head.text in quote_verbs
                            ):
                                quote_verb = tok.head.text
                                sentence_parse_quotes.append(
                                    [quote_text, '', quote_verb, sent_index, start_index, end_index])
                                break

                except IndexError:
                    pass

        # deal with sentences with two quotes in by splitting the sentence in two
        elif len(sentence_quote_indices) == 2:

            first_quote_indices = sentence_quote_indices[0]
            second_quote_indices = sentence_quote_indices[1]
            end_of_first_quote = first_quote_indices[1] + 1

            m_sentence_quote_indices = get_quote_indices(modified_sent)
            if debug:
                logging.debug(m_sentence_quote_indices)
                logging.debug('sent: ', sent)
                logging.debug('modified_sent: ', modified_sent)
            m_first_quote_indices = m_sentence_quote_indices[0]
            m_second_quote_indices = m_sentence_quote_indices[1]
            m_end_of_first_quote = m_first_quote_indices[1] + 1

            quote_and_index_list = []
            for start_index, end_index in sentence_quote_indices:
                quote_text = sent[start_index:end_index + 1]
                quote_and_index_list.append([quote_text, start_index, end_index])

            for quote_text, start_index, end_index in quote_and_index_list:
                for tok in m_doc:
                    if start_index == first_quote_indices[0]:
                        m_start_index, m_end_index = m_first_quote_indices

                        if ((tok.head.idx < m_start_index or tok.head.idx > m_end_index) and
                                (tok.idx < m_start_index or tok.idx > m_end_index) and
                                tok.dep_ == 'nsubj' and tok.head.pos_ == 'VERB' and tok.head.text in quote_verbs and
                                tok.idx < m_end_of_first_quote
                        ):
                            subtree = [t for t in tok.subtree]
                            idxes = [t.idx for t in subtree]
                            speaker = modified_sent[idxes[0]:idxes[-1] + len(subtree[-1])]
                            speaker = speaker.replace('“', '').replace('”', '').replace('dummy phrase', '').replace(
                                'Dummy phrase', '').strip()

                            if speaker in ('He', 'She'):
                                speaker = speaker.lower()
                            quote_verb = tok.head.text
                            sentence_parse_quotes.append(
                                [quote_text, speaker, quote_verb, sent_index, start_index, end_index])
                            break
                    elif start_index == second_quote_indices[0]:
                        m_start_index, m_end_index = m_second_quote_indices
                        #                         logging.debug(m_start_index, m_end_index, tok, tok.idx, tok.dep_, 'HEAD:', tok.head, tok.head.idx, tok.head.pos_)
                        if ((tok.head.idx < m_start_index or tok.head.idx > m_end_index) and
                                (tok.idx < m_start_index or tok.idx > m_end_index) and
                                tok.dep_ == 'nsubj' and tok.head.pos_ == 'VERB' and tok.head.text in quote_verbs and
                                tok.idx >= m_end_of_first_quote
                        ):
                            subtree = [t for t in tok.subtree]
                            idxes = [t.idx for t in subtree]
                            speaker = modified_sent[idxes[0]:idxes[-1] + len(subtree[-1])]
                            speaker = speaker.replace('“', '').replace('”', '').strip()

                            if speaker in ('He', 'She'):
                                speaker = speaker.lower()
                            quote_verb = tok.head.text
                            sentence_parse_quotes.append(
                                [quote_text, speaker, quote_verb, sent_index, start_index, end_index])
                            break

                try:
                    if quote_text != sentence_parse_quotes[-1][0] and quote_text[0] != '“' and quote_text[-1] != '”':
                        for tok in m_doc:
                            if (tok.head.pos_ == 'VERB' and tok.head.text in quote_verbs
                            ):
                                quote_verb = tok.head.text
                                sentence_parse_quotes.append(
                                    [quote_text, '', quote_verb, sent_index, start_index, end_index])
                                break
                except IndexError:
                    pass

    return sentence_parse_quotes


def parse_quote(list_, quote_pattern):
    if quote_pattern is None:
        raise ValueError(f"Incorrect quote pattern provided for '{list_}'")
    return Quote(**dict((k, list_[quote_pattern[k]]) for k in quote_pattern))


def parse_regex_matches(matches, quote_type):
    results = []
    for match in matches:
        # clean_match = filter(None, match)
        quote = parse_quote(match, QUOTE_TYPES_PATTERNS.get(quote_type))
        quote.QUOTE_TYPE = quote_type
        results.append(quote)
    return results


def extract_quotes_sentence_regex(pattern, text):
    """ Extract matching groups and sentences from `text` based on regex `pattern` provided.
        Returns: list(tuple), list(str) – matched groups and sentences
    """
    groups = []
    sentences = []
    for match in re.finditer(pattern, text):
        groups.append(match.groups())
        sentences.append(text[match.start():match.end()])
    return groups, sentences

def extract_quotes_and_sentence_speaker(text, nlp_model, debug=False):
    """ Takes the pre-procsessed text of an article and returns a dictionary of attributed quotes, 
        unattributed_quotes and quote marks only (everything else between quotes)
        
        
        Uses: 
        1) The regular expressions defined above to capture well-defined quotes
        2) The parse_sentence_quotes function to capture quote fragments
        3) Finds orphan quotes - those that are whole paragraphs in quote marks - and attributes them to the named
           entity in the previous sentence (if available)
        
        For the regular expression quotes, if the sentence is also parsed well, it replaces the speaker from the 
        regex quote with that from the sentence parsing because it includes less noise.
        
        
        
        :param sents: the pre-processed text of an article split up into sentences
        :param nlp: spacy model
        
        returns: a dictionary of quotes:
                {'attributed_quotes': those that can be given a speaker
                  ,'unattributed_quotes': those that can't be given a speaker
                  ,'just_quote_marks': Everything else. This will include quote fragments that can't be parsed 
                                       correctly, so wrongly missed quotes are usually in here.
                  }
        """

    sentences = sentencise_text(text)
    if len(sentences) == 0:
        logging.warning(f"Cannot sentencise '{sentences}'")
        quotes_dict = {'attributed_quotes': [],
                       'unattributed_quotes': [],
                       'just_quote_marks': []
                       }
        return quotes_dict

    all_regex_quotes = {}
    all_regex_sentences = {}

    all_regex_quotes['someone_said'], all_regex_sentences['someone_said'] = extract_quotes_sentence_regex(re_quote_someone_said, text)
    all_regex_quotes['said_someone'], all_regex_sentences['said_someone'] = extract_quotes_sentence_regex(re_quote_said_someone, text)
    all_regex_quotes['someone_told_someone'],  all_regex_sentences['someone_told_someone'] = extract_quotes_sentence_regex(re_quote_someone_told_someone, text)
    all_regex_quotes['someone_said_colon'],  all_regex_sentences['someone_said_colon'] = extract_quotes_sentence_regex(re_quote_someone_said_colon, text)
    article_quote_indices = get_quote_indices(text)
    article_quote_texts = [text[quote_pair[0]:quote_pair[1] + 1] for quote_pair in article_quote_indices]

    if debug:
        logging.debug('someone_saids:', all_regex_quotes['someone_said'])
        logging.debug('said_someones:', all_regex_quotes['said_someone'])
        logging.debug('someone_told_someones:', all_regex_quotes['someone_told_someone'])
        logging.debug('someone_said_colons:', all_regex_quotes['someone_said_colon'])

    # Parse the sentence out using spacy dependency and attribute using that
    sentence_parse_quotes = parse_sentence_quotes(sentences, nlp_model)

    # Orphan quotes: quotes that are entire paragraphs that follow on from a non-quote sentence
    orphan_quotes = []
    for quote in article_quote_texts:

        for sent_index in range(len(sentences)):
            sent = sentences[sent_index]
            if quote == sent:
                previous_sent = sentences[sent_index - 1]
                sent_ents = get_complete_ents_list(previous_sent, nlp_model)
                if '“' not in previous_sent and '”' not in previous_sent:
                    doc = nlp_model(previous_sent)
                    found = False
                    for tok in doc:
                        if (tok.dep_ == 'nsubj' and tok.head.pos_ == 'VERB' and tok.head.text in quote_verbs):
                            subtree = [t for t in tok.subtree]
                            idxes = [t.idx for t in subtree]
                            speaker = previous_sent[idxes[0]:idxes[-1] + len(subtree[-1])]
                            if speaker in ('He', 'She'):
                                speaker = speaker.lower()
                            quote_verb = tok.head.text
                            orphan_quotes.append([quote, speaker, quote_verb, sent_index, sent_ents])
                            found = True
                            break
                    if found == False:
                        orphan_quotes.append([quote, '', '', sent_index, sent_ents])


    # Parse regex quotes
    regex_quotes = []
    for qt_name, matches in all_regex_quotes.items():
        regex_quotes.extend(parse_regex_matches(matches, QUOTE_TYPES.get(qt_name)))


    if debug:
        logging.debug('sentence_parse_quotes:')
        logging.debug(sentence_parse_quotes)

        logging.debug('regex_quotes:')
        logging.debug(regex_quotes)


    extra_adding_regex_quotes = []
    for sentence in sentences:
        if len(get_quote_indices(sentence)) > 1:
            extra_adding_regex_quote = re.findall(re_quote_someone_said_adding_colon, sentence)
            if len(extra_adding_regex_quote) > 0: extra_adding_regex_quotes.extend(parse_regex_matches(extra_adding_regex_quote, QUOTE_TYPES['someone_said_adding_colon']))

    logging.debug('extra_adding_regex_quotes:')
    logging.debug(extra_adding_regex_quotes)

    logging.debug('final regex_quotes:')
    logging.debug(regex_quotes)

    # Return quotes and sentences after removing duplicates
    regex_sentences = [_ for sublist in all_regex_sentences.values() for _ in sublist]
    return list(set(regex_quotes)) + list(set(extra_adding_regex_quotes)) + orphan_quotes, list(set(regex_sentences))
