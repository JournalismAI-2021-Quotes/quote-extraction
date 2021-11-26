# Quotes Extraction – Reguar Expression model
Regular Expression quote extraction pipeline from The Guardian.


# Requirements
- Python 3.8
- All other dependencies are listed in the `requirements.txt` file.

# Run

Create a folder `data/` in your working directory - this is where the results will be saved.

To process some text, run either of the following in the CLI:  
`python main.py file.txt` to process the text in a file,  

or  

`python main.py "<input text>"` to process text straight from the command line.


Example:  
`python main.py "“We need to invest around £100bn in the electricity system alone by 2020,” Flint told the Observer."`

The output will be piped into a file (`quotes_results.jsonl`) in the `data/` folder in 
[JSON lines](https://jsonlines.org/) format.

### Sample output 
```JSON
{   
    "quote_text":"“We need to invest around £100bn in the electricity system alone by 2020,”",
    "speaker":"Flint",
    "quote_text_optional_second_part":"",
    "QUOTE_TYPE":1
}
```