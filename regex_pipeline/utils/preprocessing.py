from collections import OrderedDict
from bs4 import BeautifulSoup
from .constants import end_of_sentence_punc_list, open_quote_mark, close_quote_mark, generic_quote


def remove_all_html(text):
    """ Takes the full html of an article from CAPI and strips out all HTML tags. Tries to keep paragraph breaks by
        replacing the </p><p> and <br> tags with \n. 
        Also standardises the single quote marks (they appear in some names)

        :param text: the raw HTML of an article
        
        returns: the plain text of an article
        """

    soup = BeautifulSoup(text, features="html.parser")

    for h2 in soup.find_all('h2'):
        try:
            soup.h2.extract()
        except:
            pass

    for span in soup.find_all('span'):
        try:
            soup.span.extract()
        except:
            pass

    for aside in soup.find_all('aside'):
        try:
            soup.aside.extract()
        except:
            pass

    for figure in soup.find_all('figure'):
        try:
            soup.figure.extract()
        except:
            pass

    for a in soup.find_all('a'):
        a.unwrap()

    soup_string = str(soup)
    soup_string = soup_string.replace('</p><p>', '\n').replace('</p> <p>', '\n').replace('</p>  <p>', '\n')
    soup_string = soup_string.replace('<br/>', '\n')
    soup = BeautifulSoup(soup_string, features="html.parser")

    text = soup.get_text()

    text = text.replace('\n\n', '\n')

    # if a space gets lost, fix it.
    text = text.replace('”.“', '”. “')

    # regularise single quote marks for names like O'Grady
    text = text.replace("’", "'").replace("‘", "'")  ##.replace("“", '"').replace("”", '"')

    return text


def get_quote_indices(text_string):
    """ Get starting and ending index for quotation marks in `text_string`.
        Returns: list of lists containing start and end position of quotation marks with respect to `text_string`
    """
    quote_count = 0
    open_flag = False
    q_indices = []
    mq_indices = []
    for i, char in enumerate(text_string):
        if char == open_quote_mark and open_flag is False:
            open_flag = True
            open_quote_index = i
        elif char == close_quote_mark and open_flag is True:
            open_flag = False
            close_quote_index = i
            mq_indices.append([open_quote_index, close_quote_index])

    return mq_indices

def uniq(lst):
    """ Create list with unique values (~ordered set) 
        Returns: list
    """
    return list(OrderedDict.fromkeys(lst).keys())


def filter_certain_tags(df):
    """ Remove rows with undesirable tag from data frame.
        Returns: df
    """
    # Filtering to just news articles
    new_df = df[df['pillar_id'] == 'pillar/news']

    new_df = new_df[new_df['tracking_tag'].apply(lambda x: 'tracking/commissioningdesk/uk-weather' not in x)]
    new_df = new_df[
        new_df['tracking_tag'].apply(lambda x: 'tracking/commissioningdesk/uk-letters-and-leader-writers' not in x)]
    new_df = new_df[new_df['tracking_tag'].apply(lambda x: 'tracking/commissioningdesk/uk-obituaries' not in x)]

    return new_df


def sentencise_text(text):
    """ Splits text into sentences based no end of sentence punctuation. The spacy sentencisation wasn't working well
    so built an alternative. Sometimes '.' are used in currency values so this ignores instances where the following
    character is not a space."""

    sentences = []

    quote_open = False
    sentence_start_indices = [0]
    for i, char in enumerate(text):
        try:
            if char == open_quote_mark:
                quote_open = True
            elif char == close_quote_mark:
                quote_open = False

            # Manually prevent sentences ending when the organisation Which? is mentioned
            elif char == '?' and text[i - 5:i + 1] == 'Which?' and quote_open == False:
                pass

            elif char in end_of_sentence_punc_list and quote_open == False and (
                    text[i + 1] == ' ' or text[i + 1] == '\n'):
                sentence_start_indices.append(i + 1)

            elif quote_open is False and char == '\n':
                sentence_start_indices.append(i)

            elif char in end_of_sentence_punc_list and quote_open is True and text[i + 1] == close_quote_mark and text[
                i + 2] == ' ':
                pass

            elif char in end_of_sentence_punc_list and quote_open is True and text[i + 1] == close_quote_mark:
                sentence_start_indices.append(i + 2)
            else:
                pass
        except IndexError:
            pass

    for previous, current in zip(sentence_start_indices, sentence_start_indices[1:]):
        sentence = text[previous:current].lstrip()
        sentences.append(sentence)

    sentences.append(text[sentence_start_indices[-1] :len(text)])

    sentences = [sentence for sentence in sentences if sentence != '']

    return sentences
