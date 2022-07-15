from ast import Import
import string
import pyterrier as pt  

class Preprocessor(pt.transformer.TransformerBase):
  def __init__(self, tokeniser, stemmer=None, preprocessor=None, term_filter=None, text_fields=['title', 'text', 'body', 'query'], push_query=True):
    self.preprocessor = preprocessor
    self.tokeniser = tokeniser
    self.term_filter = term_filter
    self.stemmer = stemmer
    self.text_fields = [text_fields] if isinstance(text_fields, str) else text_fields
    self.push_query = push_query

  def transform(self, df):
    if self.push_query and 'query' in df.columns:
      pt.model.push_queries(df)
    if hasattr(df, 'parallel_apply'):
      df = df.assign(**{f: df[f].parallel_apply(self.process_text) for f in self.text_fields if f in df.columns})
    else:
      df = df.assign(**{f: df[f].apply(self.process_text) for f in self.text_fields if f in df.columns})
    return df

  def process_text(self, s):
    if self.preprocessor:
      s = self.preprocessor(s)
    toks = self.tokeniser(s)
    if self.term_filter:
      toks = filter(self.term_filter, toks)
    if self.stemmer:
      toks = map(self.stemmer, toks)
    return ' '.join(toks)


def fa(normalise=True, stem=True, remove_stops=True, remove_punct=True):
  try:
    import hazm
  except ImportError as e:
    raise ImportError("hazm module required to perform Farsi pre-processing please run 'pip install hazm'", e)
  stemmer = None
  if stem == 'lemma':
    stemmer = hazm.Lemmatizer().lemmatize
  elif stem:
    stemmer = hazm.Stemmer().stem
  term_filter = None
  if remove_stops or remove_punct:
    term_filter = lambda t: True
    if remove_stops:
      stops = set(hazm.stopwords_list())
      def filter_stops(f):
        return lambda t: f(t) and t not in stops
      term_filter = filter_stops(term_filter)
    if remove_punct:
      def filter_punct(f):
        return lambda t: f(t) and t not in string.punctuation
      term_filter = filter_punct(term_filter)
  return Preprocessor(hazm.word_tokenize, stemmer=stemmer, preprocessor=hazm.Normalizer().normalize if normalise else None, term_filter=term_filter)


def spacy_preprocessor(model, supports_stem=True, remove_punct=True, remove_stops=True):
  try:
    import spacy
  except ImportError as e:
      raise ImportError("Spacy module missing please run 'pip install spacy'", e)
  try:
    nlp = spacy.load(model, disable=['tok2vec', 'ner', 'tagger', 'parser'])
  except OSError as e:
      raise RuntimeError(f"Problem loading model {model} (you need to run 'python -m spacy download {model}' first)", e)
  if supports_stem:
    stemmer = lambda t: t.lemma_.lower()
  else:
    stemmer = lambda t: t.norm_
  term_filter = lambda t: True
  if remove_stops:
    def filter_stops(f):
      return lambda t: f(t) and not t.is_stop
    term_filter = filter_stops(term_filter)
  if remove_punct:
    def filter_punct(f):
      return lambda t: f(t) and not t.is_punct
    term_filter = filter_punct(term_filter)
  return Preprocessor(nlp, stemmer=stemmer, term_filter=term_filter)

def snowball_preprocessor(remove_punct=True, remove_stops=True):
  try:
    from nltk.stem.snowball import RussianStemmer
    from nltk.tokenize import word_tokenize  
    from nltk.corpus import stopwords
  except ImportError as e:
    raise ImportError("nltk module missing please run 'pip install nltk'", e)
  term_filter = lambda t: True
  if remove_stops:
    russian_stopwords = stopwords.words("russian")
    def filter_stops(f):
      return lambda t: f(t) and t not in russian_stopwords
    term_filter = filter_stops(term_filter)
  if remove_punct:
    def filter_punct(f):
      return lambda t: f(t) and t not in string.punctuation
    term_filter = filter_punct(term_filter)
  return Preprocessor(word_tokenize, stemmer=RussianStemmer().stem, term_filter=term_filter)

def jieba_preprocessor(remove_punct=True, remove_stops=True):
  try:
    import jieba
  except ImportError as e:
    raise ImportError("jieba module missing please run 'pip install jieba", e)
  try: 
    from stopwordsiso import stopwords
  except ImportError as e:
    raise ImportError("stopwordsiso module missing please run 'pip install stopwordsiso'",e)
  term_filter = lambda t: True
  if remove_stops:
    chinese_stopwords = stopwords(['zh'])
    def filter_stops(f):
      return lambda t: f(t) and t not in chinese_stopwords
    term_filter = filter_stops(term_filter)
  if remove_punct:
    def filter_punct(f):
      return lambda t: f(t) and t not in string.punctuation
    term_filter = filter_punct(term_filter)
  return Preprocessor(jieba.lcut, term_filter=term_filter)