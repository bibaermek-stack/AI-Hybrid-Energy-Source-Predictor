# 🚀 Railway 24/7 Бұлтты Деплоймент және Мобильді Интеграция Нұсқаулығы

Жобаңызды **Railway.app** платформасына тегін орналастырып, **24 сағат / 7 күн** бойы үзіліссіз жұмыс істету және оны **EcoPredict AI Mobile (Android APK)** қолданбасына қосу нұсқаулығы.

---

## 1. Жобаның Бұлтқа Дайындығы

Жоба түбінде 24/7 серверге арналған барлық файлдар дайын:
- `Dockerfile` — Python 3.11 ортасы мен ML кітапханалары.
- `Procfile` — Сервердің іске қосылу командасы (`web: python run_app.py`).
- `run_app.py` — FastAPI AI Backend мен Басқару Панелін 1 контейнерде біріктіреді.

---

## 2. Railway-ге 3 Адымда 24/7 Орналастыру

### 1-адым: GitHub репозиторийге жүктеу
Жобаңызды GitHub-қа push жасаңыз:
```bash
git add .
git commit -m "Deploy to Railway"
git push origin main
```

### 2-адым: Railway-де жаңа жоба ашу
1. [https://railway.app](https://railway.app) сайтына кіріп, тіркеліңіз (GitHub арқылы).
2. **"New Project"** ➔ **"Deploy from GitHub repo"** батырмасын басыңыз.
3. Осы `AI-Hybrid-Energy-Source-Predictor` репозиториын таңдаңыз.
4. Railway автоматты түрде құрастыруды бастайды (Build & Deploy).

### 3-адым: Жария Домен (Public HTTPS URL) Алу
1. Railway панеліндегі сервисіңізді басыңыз.
2. **"Settings" ➔ "Networking"** бөліміне өтіңіз.
3. **"Generate Domain"** батырмасын басыңыз.
4. Сізге сілтеме беріледі (мысалы: `https://ecopredict-ai-production.up.railway.app`).

---

## 3. Мобильді қосымшаға арналған API сервисі

Мобильді қосымша **тек бір** серверге қосылады — осы репозиторийден деплой болатын Railway сервисі:
`https://ecopradict-mobile-production.up.railway.app` (`mobile/config.py`). Қосымшада URL енгізудің
қажеті жоқ — ол қосымшаның ішіне жазылған.

Бұл сервис толық API-ды беруі үшін Railway-де мына баптаулар керек:

| Railway баптауы | Мәні |
|---|---|
| **Settings → Source → Root Directory** | бос (репозиторий түбірі). `mobile` тұрса — тек `/health` жұмыс істейді, қалғаны 404 |
| **Settings → Deploy → Custom Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Variables** | `WEATHERAPI_KEY`, `ECOPREDICT_API_KEY`, `SOLARMAN_APP_ID`, `SOLARMAN_APP_SECRET`, `SOLARMAN_EMAIL`, `SOLARMAN_PASSWORD` (қалауы бойынша `SOLARMAN_DEVICE_SN`) |

> Түбірдегі `Procfile` (`python run_app.py`) жария портта Streamlit-ті іске қосады, API-ды емес —
> сондықтан мобильді сервис үшін Start Command-ты міндетті түрде жоғарыдағыдай көрсетіңіз.

**Тексеру:** браузерде `https://ecopradict-mobile-production.up.railway.app/health` ашыңыз.
Жауапта `"api": "full"` (немесе `"forecast_backend"`) болуы тиіс. `"api": "stub"` — Root Directory әлі `mobile`.
Бұл тексеріс автоматты түрде де жүреді: `.github/workflows/backend-health.yml` (әр 6 сағат сайын; Actions → Backend health → Run workflow).

Репозиторий **private** болса, Railway-дің GitHub қосымшасына осы репоға қолжетімділік беріңіз
(GitHub → Settings → Applications → Railway → Repository access), әйтпесе жаңа деплой басталмайды.

---

## 4. Не Түзеледі?

- ✅ Компьютерді өшіріп қойсаңыз да, телефондағы қолданба **24/7 жұмыс істейді**.
- ✅ Әлемнің кез келген нүктесінен (Мобильді интернет 4G/5G немесе басқа Wi-Fi) байланысады.
- ✅ Барлық Solar ML, Wind ML, XGBoost Forecast және AI Кеңесші бұлтта 100% есептеледі.
