# newspaper receipe

import argparse
import hashlib
import logging
import nltk

import pandas as pd
from nltk.corpus import stopwords

from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stop_words = set(stopwords.words('spanish'))

def main(filename):
  logger.info('Starting cleanning process')

  df = _read_data(filename)
  newspaper_uid = _extract_newspaper_uid(filename)
  df = _add_newspaper_uid_column(df, newspaper_uid)
  df = _extract_host(df)
  df = _fill_missing_titles(df)
  df = _generate_uids_for_rows(df)
  df = _remove_new_lines_from_title(df)
  df = _remove_new_lines_from_body(df)
  df = _count_significant_words_from_title(df)
  df = _count_significant_words_from_body(df)
  df = _remove_duplicate_entries(df, 'title')
  df = _drop_rows_with_missing_values(df)
  _save_data(df, filename)


  return df

def _read_data(filename):
  logger.info('reading file {}'.format(filename))

  return pd.read_csv(filename)


def _extract_newspaper_uid(filename: str) -> str:
  logger.info('Extracting newspaper uid')
  newspaper_uid = filename.split('_')[0]

  logger.info('Newspaper uid detected {}'.format(newspaper_uid))

  return newspaper_uid

def _add_newspaper_uid_column(df, newspapaer_uid):
  logger.info('Filling newspaper_uid column with {}'.format(newspapaer_uid))

  df['newspaper_uid'] = newspapaer_uid
  
  return df

def _extract_host(df):
  logger.info('Extracting host from urls')

  df['host'] = df['url'].apply(lambda url: urlparse(url).netloc)

  return df

def _fill_missing_titles(df):
  logger.info('Filling missing titles')

  missing_titles_mask = df['title'].isna()

  missing_titles = (df[missing_titles_mask]['url']
                    .str.extract(r'(?P<missing_titles>[^/]+)$')
                    .applymap(lambda title: title.split('-'))
                    .applymap(lambda title_word_list: ' '.join(title_word_list)))

  df.loc[missing_titles_mask, 'title'] = missing_titles.loc[:, 'missing_titles']

  return df

def _generate_uids_for_rows(df: pd.DataFrame):
  logger.info( 'Generating uids for each row')

  uids = (
    df
      .apply(lambda row: hashlib.md5(bytes(row['url'].encode())), axis=1)
      .apply(lambda hash_object: hash_object.hexdigest())
  )

  df['uid'] = uids
  df.set_index('uid', inplace=True)

  return df

def _remove_new_lines_from_body(df: pd.DataFrame) -> pd.DataFrame:
  logger.info('Remove new lines from body')

  stripped_body = (
    df
      .apply(lambda row: row['body'], axis=1)
      .apply(lambda body: list(body))
      .apply(lambda letters: list(map(lambda letter: letter.replace('\n', ' '), letters)))
      .apply(lambda letters: ''.join(letters))
  )

  df['body'] = stripped_body

  return df

def _remove_new_lines_from_title(df: pd.DataFrame) -> pd.DataFrame:
  logger.info('Remove new lines from title')

  stripped_title = (
    df
      .apply(lambda row: row['title'], axis=1)
      .apply(lambda title: list(title))
      .apply(lambda letters: list(map(lambda letter: letter.replace('\n', ' '), letters)))
      .apply(lambda letters: ''.join(letters))
      .apply(lambda title: title.strip())
)

  df['title'] = stripped_title

  return df

def _count_significant_words_from_title(df):
  logger.info('Counting the number of significant words in the title')
  df['n_tokens_tile'] = get_num_of_tokens_from('title', df)

  return df

def _count_significant_words_from_body(df):
  logger.info('counting the number of significant words in the title')
  df['n_tokens_body'] = get_num_of_tokens_from('body', df)

  return df

def get_num_of_tokens_from(column_name, df):
  return (
    df
      .dropna()
      .apply(lambda row: nltk.word_tokenize(row[column_name]), axis=1)
      .apply(lambda tokens: list(filter(lambda token: token.isalpha(),  tokens)))
      .apply(lambda tokens: list(map(lambda token: token.lower(), tokens)))
      .apply(lambda word_list: list(filter(lambda word: word not in stop_words, word_list)))
      .apply(lambda valid_word_list: len(valid_word_list))
  )

def _remove_duplicate_entries(df: pd.DataFrame, column_name):
  logger.info('Removing duplicate entries')
  return df.drop_duplicates(subset=column_name, keep='first')

def _drop_rows_with_missing_values(df):
  logger.info('Dropping rows with missing values')

  return df.dropna()

def _save_data(df: pd.DataFrame, filename):
  clean_filename = 'clean_{}'.format(filename)
  logger.info('Saving data at location: {}'.format(clean_filename))

  df.to_csv(clean_filename)

if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('filename', help='El path a los datos sucios', type=str)

  args = parser.parse_args()
  df = main(args.filename)

  # print(df)
