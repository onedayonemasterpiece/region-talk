# Что требуется от владельца продукта

Секретные значения не нужно писать в issue, PR, обычный чат или документацию. Их следует передать кодовому агенту через одобренный secret-management контур либо добавить напрямую в GitHub/Kaggle UI.

## Обязательные данные/решения

1. **Kaggle owner/username** для новых private datasets и kernels.
2. **Kaggle API token** — установить как GitHub Secret `KAGGLE_API_TOKEN`.
3. **Kaggle User Secret** `REGION_TALK_SEALED_BOX_PRIVATE_KEY` после генерации пары ключей агентом; в GitHub Variables помещается только public key.
4. **Supabase** — разрешение использовать существующий dedicated limiter project и применить туда схему `region_talk_control`.
5. **Google limiter registry** — подтвердить точный набор активных `GOOGLE_API_KEY*` и соответствие каждому реальному Google Cloud `quota_scope`; значения устанавливаются только как secrets.
6. **Telegram review chat numeric ID**.
7. **Telegram user IDs операторов**, чьи реакции имеют силу.
8. **Telegram target channel numeric ID** и подтверждение, что bot/publisher identity имеет необходимые admin/send-media права. Username по текущему контракту: `@kalinigrad_visit`.
9. **Publication slots**: принять defaults `11:30` и `18:30` Europe/Kaliningrad с одной article и одной social публикацией в день либо дать другие значения.
10. **VK first rollout**: default `disabled`; включать только отдельным решением после canary.
11. **Temporary YDB migration access**: approved read-only identity/OIDC path и bounded window, пока autonomous scheduler remains disabled.
12. **Production canary approval**: после private-channel canary выбрать одну точную approved revision для первой целевой публикации.

## Что агент должен переиспользовать, а не спрашивать заново при наличии доступа

- существующие Telegram application credentials;
- существующие role-scoped DISCOVERY1/DISCOVERY2 bundles;
- существующий dedicated Supabase limiter URL/key;
- existing active Google keys and metadata registry;
- existing Region Talk review/target configuration from protected events-bot environments;
- current YDB target database identity from incident/migration records.

Если GitHub Secrets нельзя прочитать, агент не должен заявлять, что они скопированы. В таком случае он создаёт exact missing-secret report, а владелец добавляет значения вручную.
