# chgk_rating_client
Клиент для [API](https://rating.chgk.info/api-doc) сайта рейтинга спортивного ЧГК с кэшем в Redis или локальных файлах.

Сохраняет почти все неточности и странности API (например, числа остаются строками).

Установка:

```
pip3 install chgk_rating_client
```

Использование:

```
from chgk_rating_client import Rating

client = Rating()
```

Использование с кэшированием в редисе:

```
client = Rating(redis_host='localhost')
```

Использование с кэшированием в локальных файлах:

```
client = Rating(file_cache=True)
```

Можно включить и оба одновременно, это же ваши диск и редис.

Теперь можно делать запросы:

```
rosters = client.tournament_rosters(5773)
player = client.player(40393)
```

Умной очистки кэша пока нет, поэтому можно удалить либо все записи:

```
client.clear_cache()
```

Либо по маске:

```
client.clear_cache("*rosters*")
client.clear_cache("*40393")
```
