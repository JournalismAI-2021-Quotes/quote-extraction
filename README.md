# Journalism AI – Quotes extraction for modular journalism

This repo contains the code for [the Guardian](https://www.theguardian.com) and [AFP](https://www.afp.com/) contribution for the [JournalismAI Festival 2021](https://www.journalismaifestival.com/).

Further reading can be found in [our blog post](https://www.theguardian.com/info/2021/nov/25/talking-sense-using-machine-learning-to-understand-quotes).


The aim of the project is to extract quotes from news articles using Named Entity Recognition, add coreferencing 
information and format the results for an exploratory search tool.

The contribution consists of several self-contained pieces of work, namely:
1. a regular expression pipeline attempting to extract quotes by matching patterns
2. a rule set to define different types of quotes and guide the quote annotation
3. custom annotation recipes for the [Prodigy](https://prodi.gy/) software enabling quick and efficient data annotation
4. a post-processing pipeline for extracting quotes using a trained [Spacy](https://spacy.io/) model and adding coreferencing information
5. example data and data schema for displaying the extracted quote information in a [search tool](https://github.com/JournalismAI-2021-Quotes/search-interface)  

# Repo structure

Each folder in this repo reflects one of the pieces of work mentioned above.

- `regex_pipeline/` – code to run the regular expression-based quote extraction 
- `annotation_rules/` – document with rules and definitions to guide the quote annotation step
- `annotation_scripts/` – custom annotation scripts for [Prodigy](https://prodi.gy/)
- `coreference/` – proof of concept for rules-based coreferencing tool
- `schema/` – data output schema and example data 

Each folder contains a separate `README` file with instructions to set up and run each piece of work.

