# Region Talk — prompt для нового исследования внешних публикаций

Скопируй этот текст в отдельный запуск Deep Research.

Задача: найти внерегиональные русскоязычные публикации о Калининградской области, которые могут стать входом для Region Talk. Результат должен быть не статьёй и не теорией, а строгим JSON-кандидатным пакетом для дальнейшей обработки пайплайном.

## Перед поиском

1. Открой актуальные файлы из приватного репозитория `onedayonemasterpiece/region-talk`:
   - `research/intake/README.md`
   - `schemas/research-intake.schema.json`
   - `reports/current/seen-publications.json`, если есть
   - `reports/current/research-registry.json`, если есть
2. Используй их как duplicate guard: не добавляй уже известные URL, DOI, canonical title+authors и очевидные зеркала.

## Что искать

Ищи внешние материалы, где Калининградская область является главным или существенным предметом:
- travel / architecture / history / culture / nature / city-life;
- нерегиональные медиа, журналы, авторские каналы, блоги, профессиональные площадки;
- публикации с конкретной пользой, впечатлением, маршрутом, визуальным или культурным зерном.

Не включай:
- региональные новости Калининграда как основной источник;
- происшествия, политику, криминал, трэш;
- рекламу, туры, бронирования, промокоды, affiliate-материалы;
- мульти-региональные подборки, где Калининград — случайный пункт;
- материалы без доступного первоисточника или без достаточного evidence.

## Для каждого результата

Проверь первоисточник, canonical URL, дату, автора/издание, локальность источника, доступность текста, DOI при наличии, title+authors identity, commercial/news/politics risk, связь материала именно с Калининградской областью.

Каждый retained result должен иметь downstream status только:
- `candidate_report` — можно отправлять в обычный Region Talk pipeline;
- `excluded` — сохранить для duplicate guard;
- `unresolved` — сохранить как незавершённое evidence, но не как кандидат.

Запрещено возвращать `ready_for_queue`, `approved`, `autopublish`, `publication_permission_granted` или любой статус, который обходит E5 → BGE → fusion → image/profile → finalizer → review.

## Формат результата

Верни один JSON-файл, валидный относительно текущей схемы `research-intake.schema.json`.

Обязательные свойства пакета:
- новый уникальный `request_id`;
- `created_at_utc`;
- `research_scope`;
- `registry_snapshot` / `seen_publications_snapshot`, если доступно;
- массив `results`;
- SHA/evidence fields, предусмотренные схемой;
- для каждого результата: canonical identity, source profile evidence, policy classification, locality evidence, access status, reason for inclusion/exclusion.

Не создавай markdown-отчёт вместо JSON. Не обещай будущую обработку. Не утверждай, что материал опубликован или согласован. Итоговый JSON будет добавлен в `research/intake/region-talk-external-research-result-<request_id>.json`, после merge он будет импортирован в SQLite state и обработан обычным scheduler pipeline.
