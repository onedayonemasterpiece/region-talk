# Region Talk

Автономный CPU-only контур поиска, проверки, редакционной подготовки, операторского согласования и публикации внешних материалов о Калининградской области.

> Текущий статус: private repository, bootstrap установлен, repository validation проходит. Scheduler и publisher выключены. Runtime workers, YDB migration и первый полный pipeline run ещё не завершены.

## Продуктовый результат

Система должна непрерывно, пусть и не мгновенно:

1. находить внешние русскоязычные публикации о Калининградской области;
2. принимать вручную исследованные статьи через versioned JSON intake;
3. обрабатывать текст отдельными CPU-контурами E5 и BGE-M3;
4. проверять источник, региональность, содержательность, рекламу, новости, визуал и редакционную пригодность;
5. готовить точную media-first ревизию публикации;
6. отправлять её в закрытый Telegram review chat;
7. связывать `👍/❤️`, `👎` и `✍` с точной ревизией текста и медиа;
8. планировать только согласованные ревизии с учётом расписания, разнообразия и идемпотентности;
9. публиковать в целевой Telegram-канал;
10. сохранять историю для воспроизведения ошибок и измерения продуктовой эффективности.

## Главные архитектурные решения

- **Каноническое продуктовое состояние:** SQLite snapshot в private versioned Kaggle Dataset.
- **Тяжёлое исполнение:** отдельные private Kaggle CPU kernels.
- **E5 и BGE-M3:** разные kernels; одновременная загрузка в один production worker запрещена.
- **Единственный коммиттер:** GitHub Actions reconciler; workers возвращают immutable deltas.
- **Оркестрация:** короткий catch-up controller каждые 15 минут после принятия ручного полного run.
- **Supabase:** в первой версии только существующий canonical Google AI limiter; новый Region Talk control-plane не обязателен.
- **История:** полный диагностический run bundle каждой стадии забирается и архивируется GitHub Actions.
- **YDB:** временный read-only источник миграции и rollback, затем выводится из рабочего цикла.
- **Публикация:** outbox + exact revision fingerprint + повторная проверка реакций + idempotency key.
- **Редакционный стиль:** спокойный культурный навигатор с редакционным теплом; факты и CTA не могут быть стилистически выдуманы.

## Топология

```text
private GitHub repository
  ├─ code / schemas / policies / research JSON
  ├─ short controller + reconciler
  └─ current compact reports
                  │
                  ▼
       private Kaggle CPU workers
 Candidate/E5 ──► BGE ──► Image ──► Profile
                  │ immutable deltas + logs
                  ▼
        GitHub Actions reconciler
 base-version check → SQLite transaction → invariants
 → new private state dataset version
                  │
      ┌───────────┴──────────────┐
      ▼                          ▼
private Kaggle state       existing Supabase
and run history            Google AI limiter only
      │
      ▼
Telegram review chat → schedule → publisher
      │
      ▼
@kalinigrad_visit
```

## Репозиторная карта

- `SETUP.md` — только реально внешние параметры.
- `docs/architecture.md` — границы системы и потоки данных.
- `docs/orchestrator.md` — state machine, cron и recovery.
- `docs/state-history-observability.md` — SQLite, manifests, logs и retention.
- `docs/supabase-boundary.md` — минимальная граница Supabase.
- `docs/ydb-migration.md` — одноразовая миграция и сверка.
- `docs/research-intake.md` — добавление исследований через JSON.
- `docs/review-publishing.md` — review chat, реакции, очередь и publisher.
- `docs/testing-debugging.md` — testing, fault injection и расследования.
- `docs/product-metrics.md` — метрики готовых публикаций и funnel.
- `docs/first-full-run.md` — обязательный разбор первого цикла.
- `docs/security-and-secrets.md` — stage-scoped credentials и leak prevention.
- `docs/editorial/` — редакционная политика и Writer contract.
- `sql/sqlite/` — canonical operational schema.
- `sql/supabase/` — optional future compact control projection.
- `schemas/` — run/delta/log/research contracts.

## Release gates

До первого production-поста обязательны:

1. GitHub и Kaggle assets подтверждены private;
2. secrets отсутствуют в outputs, logs, artifacts и state;
3. YDB export и SQLite import совпадают по row counts и hashes;
4. повтор delta даёт zero changes, stale-base delta блокируется;
5. E5 и BGE проходят отдельные CPU smoke runs;
6. полный run bundle скачан и разобран;
7. review reactions доказаны на exact reviewer IDs;
8. private test-channel publisher canary проходит media/idempotency gates;
9. первый полный цикл разобран по product funnel;
10. только затем публикуется один явно согласованный production canary.
