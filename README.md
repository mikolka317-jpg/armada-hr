# ARMADA HR

Рекрутингове агентство: офіційне працевлаштування українців у готелях Польщі
(Mercure Szczyrk Resort, Aries Hotel & Spa — Щирк та Вісла).

## Складові репозиторію

| Шлях | Що це |
|------|-------|
| `index.html` | Лендінг з вакансіями, умовами та контактами (статичний, без збірки) |
| `privacy.html` | Політика конфіденційності (вимога Facebook App) |
| `data-deletion.html` | Інструкція з видалення даних (вимога Facebook App) |
| `robots.txt` | Дозвіл індексації пошуковикам |
| `shorts-studio/` | Генератор вірусних відео для TikTok/YouTube Shorts у 4 мовах |
| `DOCUMENTATION.md` | Повна технічна документація та база знань проєкту |

## Запуск локально

Сайт статичний — достатньо відкрити `index.html` у браузері або:

```bash
python3 -m http.server 8080   # → http://localhost:8080
```

Генерація відео: див. [`shorts-studio/README.md`](shorts-studio/README.md).

Повна документація: [`DOCUMENTATION.md`](DOCUMENTATION.md).
