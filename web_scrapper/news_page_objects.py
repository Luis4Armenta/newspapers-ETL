import requests
import bs4

from common import config

class NewsPage:
  def __init__(self, news_site_uid, url) -> None:
    self._config = config()['news_sites'][news_site_uid]
    self._queries = self._config['queries']
    self._html = None
    self._url = url

    self._visit(url)

  def _select(self, query_string):
    return self._html.select(query_string)

  def _visit(self, url):
    response = requests.get(url)

    # arroja un error si la solicitud no fue completada correctamente
    response.raise_for_status()

    self._html = bs4.BeautifulSoup(response.text, 'html.parser')

class HomePage(NewsPage):
  def __init__(self, news_site_uid, url) -> None:
    super().__init__(news_site_uid, url)
    self._news_site_uid = news_site_uid

  @property
  def article_links(self):
    link_list = []
    
    for link in self._select(self._queries['homepage_article_links']):
      if link and link.has_attr('href'):

        # compleantdo los links en caso de ser necesario
        if(link['href'][:4] != 'http'):
          if self._news_site_uid == 'elpais':
            link['href'] = config()['news_sites'][self._news_site_uid]['url'][0:-7] + link['href']
          elif self._news_site_uid == 'bbc':
            link['href'] = config()['news_sites'][self._news_site_uid]['url'][0:-6] + link['href']
          else:
            link['href'] = config()['news_sites'][self._news_site_uid]['url'] + link['href']

        # filtrando links dentro del sitio web
        if(self._url in link['href']):
          link_list.append(link)

    return set(link['href'] for link in link_list)


class ArticlePage(NewsPage):
  def __init__(self, news_site_uid, url):
    super().__init__(news_site_uid, url)

  @property
  def title(self):
    result = self._select(self._queries['article_title'])[0].text;

    return result if len(result) else ''

  @property
  def body(self):
    ps = self._select(self._queries['article_body'])

    # print(ps[0].text)

    if len(ps) == 1:
      return ps[0]
    elif len(ps) == 0:
      return "No se ha encontrado ningun cuerpo dentro del articulo"
    else:
      for p in ps:
        if p.text.strip() != '':
          return p.text.strip()
    
    return 'No he tratado este caso'  

  @property
  def url(self):
    return self._url
