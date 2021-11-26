# Annotation scripts

This folder contains the custom scripts created by the Guardian to annotate quotes in news articles to create training data. These are based on the original `ner` recipes from prodigy, with the addition of a `text_input` feedback field. Expand the dropdowns below for usage notes.

We used three entity types for quote extraction:

1. `Source`
2. `Cue`
3. `Content`


Further reading can be found in [our blog post](https://www.theguardian.com/info/2021/nov/25/talking-sense-using-machine-learning-to-understand-quotes).

## Requirements
Developed with Python v3.8.3. All requirements are listed in the `requirements.txt` file.

Please note that you will need a copy of [Prodigy](https://prodi.gy/) (v1.11.5) which is proprietary software.


# Annotation recipes

Customised annotation recipes for different use cases can be found below.   
We standardised the user interface between the different tasks as far as possible in order to improve user experience.

<img width="1160" alt="Cutsom Prodigy User Interface" src="https://user-images.githubusercontent.com/64908337/143288033-f83c2ff0-2119-47a9-845b-702d2df5e9ba.png">

## `quotes.manual`

Mark entity spans in a text by highlighting them and selecting the respective labels. 
The model is used to tokenize the text to allow less sensitive highlighting, since the token boundaries are used to set the entity spans.

<details>
<summary>Expand for details</summary>

Example: `prodigy quotes.manual <dataset> blank:en <input-data> -l Source,Content,Cue -U -F quotes.py`
```
prodigy quotes.manual dataset spacy_model source [-h] [-lo None] [-l None] [-e None] [-U] -F quotes.py

positional arguments:
  dataset               Dataset to save annotations to
  spacy_model           Loadable spaCy pipeline for tokenization or blank:lang (e.g. blank:en)
  source                Data to annotate (file path or '-' to read from standard input)

optional arguments:
  -h, --help            show this help message and exit
  -lo None, --loader None
                        Loader (guessed from file extension if not set)
  -l None, --label None
                        Comma-separated label(s) to annotate or text file with one label per line
  -e None, --exclude None
                        Comma-separated list of dataset IDs whose annotations to exclude
  -U, --unsegmented     Don't split sentences
```
</details>

## `quotes.correct`

Correct model's predictions.

<details>
<summary>Expand for details</summary>

Example: `prodigy quotes.correct <dataset> <your-model> <input-data> --update -l Source,Content,Cue -U -F quotes.py`
```
prodigy quotes.correct dataset spacy_model source [-h] [-lo None] [-l None] [-UP] [-e None] [-U] -F quotes.py

positional arguments:
  dataset               Dataset to save annotations to
  spacy_model           Loadable spaCy pipeline with an entity recognizer
  source                Data to annotate (file path or '-' to read from standard input)

optional arguments:
  -h, --help            show this help message and exit
  -lo None, --loader None
                        Loader (guessed from file extension if not set)
  -l None, --label None
                        Comma-separated label(s) to annotate or text file with one label per line
  -UP, --update         Whether to update the model during annotation
  -e None, --exclude None
                        Comma-separated list of dataset IDs whose annotations to exclude
  -U, --unsegmented     Don't split sentences
```

</details>

## `quotes.teach`

Collect the best possible training data with the model in the loop.
<details>
<summary>Expand for details</summary>

Example: `prodigy quotes.teach <dataset> <your-model> <input-data> -l Source,Content,Cue -U -F quotes.py`
```
prodigy quotes.teach dataset spacy_model source [-h] [-lo None] [-l None] [-e None] [-U]  -F quotes.py

positional arguments:
  dataset               Dataset to save annotations to
  spacy_model           Loadable spaCy pipeline with an entity recognizer
  source                Data to annotate (file path or '-' to read from standard input)

optional arguments:
  -h, --help            show this help message and exit
  -lo None, --loader None
                        Loader (guessed from file extension if not set)
  -l None, --label None
                        Comma-separated label(s) to annotate or text file with one label per line
  -e None, --exclude None
                        Comma-separated list of dataset IDs whose annotations to exclude
  -U, --unsegmented     Don't split sentences
```
</details>

## `quotes.mark`

Review already-annotated data.
<details>
<summary>Expand for details</summary>

Example: `prodigy quotes.mark <dataset> <input-data> -l Source,Content,Cue -F quotes.py`
```
prodigy quotes.mark dataset spacy_model source [-h] [-l None] [-lo None] [-e None] -F quotes.py

positional arguments:
  dataset               Dataset to save annotations to
  source                Data to annotate (file path or '-' to read from standard input)

optional arguments:
  -h, --help            show this help message and exit
  -l None, --label None
                        Comma-separated label(s) to annotate or text file with one label per line
  -lo None, --loader None
                        Loader (guessed from file extension if not set)
  -e None, --exclude None
                        Comma-separated list of dataset IDs whose annotations to exclude
```
</details>


## Data format

The expected input data format is JSONL.
<details>
<summary>Code snippet to convert JSON to JSONL with python</summary>

```
import json
with open('/path/to/validation_data_articles_prodigy.json', 'r') as f:
    file = json.load(f)
    
result = [json.dumps(r) for r in file]
with open('/path/to/validation_data_articles_prodigy.jsonl', 'w') as obj:
    for i in result:
        obj.write(i+'\n')
```
</details>
