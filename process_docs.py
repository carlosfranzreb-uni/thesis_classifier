""" Process the publications retrieved from OpenAlex, as was done with the
documents of the repositories. Then, vectorize them with the pretrained
fasttext word vectors. This latter step is also done for the documents of the
repositories. """


import json
from os import listdir
import logging
from string import ascii_lowercase as letters

from flair.data import Sentence
from flair.tokenization import SpacyTokenizer
from flair.models import SequenceTagger
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import spacy


class DataProcessor:
  def __init__(self, tokenizer, tagger, lemmatizer):
    self.tokenizer = tokenizer
    self.tagger = tagger
    self.lemmatizer = lemmatizer

  def process_docs(self, docs):
    """ Process documents. """
    processed = {}
    for subject in docs:
      processed[subject] = []
      for doc in docs[subject]:
        processed[subject].append({
          'data': self.process(Sentence(doc['data'])),
          'subjects': doc['subjects']
        })
    return processed

  def process(self, sentence):
    """ Given a Sentence object, lower-case and lemmatize the words. """
    self.tagger.predict(sentence)
    tag_dict = {
      'ADJ': wordnet.ADJ,
      'NOUN': wordnet.NOUN,
      'VERB': wordnet.VERB,
      'ADV': wordnet.ADV
    }
    lemmas = []
    for token in sentence:
      if token.labels[0].value in tag_dict:
        lemmas.append(self.lemmatizer.lemmatize(
          token.text.lower(), tag_dict[token.labels[0].value])
        )
      else:
        lemmas.append(token.text.lower())
    return lemmas


def process_docs():
  tokenizer = SpacyTokenizer('en_core_web_sm')
  lemmatizer = WordNetLemmatizer()
  tagger = SequenceTagger.load('upos-fast')
  processor = DataProcessor(tokenizer, tagger, lemmatizer)
  doc_folder = 'data/openalex/docs'
  dump_folder = 'data/openalex/processed_docs'
  for file in listdir(doc_folder):
    docs = json.load(open(f'{doc_folder}/{file}', encoding='utf-8'))
    processed = processor.process_docs(docs)
    json.dump(processed, open(f'{dump_folder}/{file}', 'w', encoding='utf-8'))


def filter_docs():
  """ Remove stopwords, numbers, symbols and punctuation from the processed
  texts. """
  stopwords = spacy.load('en_core_web_sm').Defaults.stop_words
  processed_folder = 'data/openalex/processed_docs'
  dump_folder = 'data/openalex/filtered_docs'
  for file in listdir(processed_folder):
    processed = json.load(open(f'{processed_folder}/{file}', encoding='utf-8'))
    filtered = {}
    for subject, docs in processed.items():
      filtered[subject] = []
      for doc in docs:
        filtered[subject].append({
          'data': filter_text(doc['data'], stopwords),
          'subjects': doc['subjects']
        })
    json.dump(filtered, open(f'{dump_folder}/{file}', 'w', encoding='utf-8'))


def filter_text(text, stopwords):
  """ A word is removed if it either has less than three letters or if it is
  in the given stopwords list. Check only for lower-cased letters, as the
  texts were lower-cased during processing. """
  filtered = []
  for token in text:
    cnt_letters = sum([char in letters for char in token])
    if cnt_letters > 2 and token not in stopwords:
      filtered.append(token)
  return filtered    


def get_vecs():
  """ Retrieve the vectors of the docs and dump them in another folder. """
  docs_folder = 'data/openalex/docs'
  vecs_folder = 'data/openalex/vecs'
  fname = 'data/pretrained_vecs/wiki-news-300d-1M-subword.vec'
  fin = open(fname, encoding='utf-8', newline='\n', errors='ignore')
  pretrained = {}
  fin.readline()  # skip first line
  for line in fin:
    tokens = line.rstrip().split(' ')
    pretrained[tokens[0]] = list(map(float, tokens[1:]))
  for file in listdir(docs_folder):
    docs = json.load(open(f'{docs_folder}/{file}', encoding='utf-8'))
    vecs = {}
    for subject in docs:
      vecs[subject] = []
      for doc in docs[subject]:
        vecs[subject].append({'data': [], 'subjects': doc['subjects']})
        for w in doc['data']:
          if w in pretrained:
            vecs[subject][-1]['data'].append(pretrained[w])
        found = len(vecs[subject][-1]["data"])
        logging.info(f'Found {found} vecs for {len(doc["data"])} words')
    json.dump(vecs, open(f'{vecs_folder}/{file}', 'w', encoding='utf-8'))


def vectorize_repos(data_file, dump_folder):
  """ Vectorize the documents of the repositories with the fasttext vectors.
  The docs should already be lemmatized, and are filtered here with the same
  function used for the OpenAlex docs, filter_texts. """
  data = json.load(open(data_file))
  stopwords = spacy.load('en_core_web_sm').Defaults.stop_words
  fname = 'data/pretrained_vecs/wiki-news-300d-1M-subword.vec'
  fin = open(fname, encoding='utf-8', newline='\n', errors='ignore')
  pretrained, vecs = {}, {}
  fin.readline()  # skip first line
  cnt, file_nr = 0, 1
  for line in fin:
    tokens = line.rstrip().split(' ')
    pretrained[tokens[0]] = list(map(float, tokens[1:]))
  for doc, data in data.items():
    texts = []
    for t in ('title', 'abstract'):
      if data[t] is not None:
        texts += data[t]    
      if len(texts) == 0:
        continue
    filtered = filter_text(texts, stopwords)
    vecs[doc] = []
    for w in filtered:
      if w in pretrained:
        vecs[doc].append(pretrained[w])
    logging.info(f'Found {len(vecs[doc])} vecs for {len(filtered)} words')
    cnt += 1
    if cnt % 2000 == 0:
      json.dump(
        vecs, open(f'{dump_folder}/{file_nr}.json', 'w', encoding='utf-8')
      )
      vecs = {}
      file_nr += 1
  if len(vecs) > 0:
    json.dump(
      vecs, open(f'{dump_folder}/{file_nr}.json', 'w', encoding='utf-8')
    )
  

if __name__ == '__main__':
  logging.basicConfig(
    level=logging.INFO, 
    handlers=[logging.FileHandler('logs/get_all_vecs.log', 'w', 'utf-8')],
    format='%(message)s'
  )
  get_vecs()
  logging.info('\n\n--- SWITCH TO REPO DATA ---\n\n')
  vectorize_repos(
    'data/json/dim/all/data_lemmas.json',
    'data/pretrained_vecs/data'
  )
