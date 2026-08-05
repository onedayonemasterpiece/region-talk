Репозиторий: https://github.com/onedayonemasterpiece/region-talk

Добавь в GitHub Actions Secrets существующий рабочий legacy Kaggle credential под точным именем:

```text
KAGGLE_KEY
```

`KAGGLE_USERNAME` уже настроен. Новый `KAGGLE_API_TOKEN` не создавай, если legacy API authentication smoke проходит.

Верни только подтверждение наличия имени секрета без значения. Не добавляй sealed-box keys, Supabase direct connection, dataset/kernel/model variables, bot/YDB credentials; они не нужны для первого Kaggle smoke. Не включай scheduler или publisher и не запускай workflow.
