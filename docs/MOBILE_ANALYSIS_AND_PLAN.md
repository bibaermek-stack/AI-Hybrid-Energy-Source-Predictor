# EcoPredict AI Mobile — толық талдау және даму жоспары (Android + iOS)

> Күні: 2026-09-25 · Тармақ: `claude/mobile-version-analysis-plan-48vgtz`
> Талданған репозиторийлер: `AI-Hybrid-Energy-Source-Predictor` (негізгі), `EcoPradict-Ai`, `CACER_Simulator`

---

## 0. Қабылданған шешімдер және ағымдағы күй

| Шешім | Не жасалды |
|---|---|
| **Flet 1.0-ге көшеміз** | `ft.ElevatedButton` → `ft.Button` (6 экран); `flet==1.0.1` бекітілді (`mobile/pyproject.toml`, `requirements.txt`, `mobile/requirements.txt`). 12 экранның бәрі 1.0.1-де ескертусіз құрастырылады; веб-режимде 11 экран нақты іске қосылып, скриншотпен тексерілді |
| **Backend — осы репоның Railway сервисі** | Клиент тек `https://ecopradict-mobile-production.up.railway.app`-ке қосылады; басқа репо сервистеріне (`ecopradict-ai-production`, `ecopredict.kz`) үнсіз ауысу алынды. Жергілікті тест үшін `ECOPREDICT_API_BASE` айнымалысы. Railway баптаулары: `RAILWAY_DEPLOYMENT.md` 3-бөлім |
| **Репозиторий private болуы керек** | Көрінуді тек GitHub баптауларынан иесі өзгерте алады (Settings → General → Danger Zone → Change visibility). Git тарихында құпия кілт табылмады (үлгі бойынша іздеу) |

0-кезеңнен жасалғаны:
- iOS workflow қайта жазылды: жарамды флагтар, `mobile/` жолы, тек `flet[cli]` орнатылады, қолмен немесе `v*` тегімен іске қосылады. Signing secrets болмаса — Simulator build, болса — App Store IPA.
- Жаңа Android workflow: `mobile/` өзгерген әр push-та APK; `v*` тегінде keystore secrets болса — signed AAB.
- CI: `test_forecast_endpoint` енді ауа райын mock арқылы алады; кілтсіз жағдай үшін бөлек тест қосылды; `tests/test_mobile_smoke.py` қосылды. Жергілікті нәтиже: 77/77.
- README-дегі build командалары түзетілді.

**Қалғаны сізден (кодпен жасалмайды):**
1. Railway: `ecopradict-mobile` сервисінде Root Directory-ді тазалау, Start Command `uvicorn main:app --host 0.0.0.0 --port $PORT`, айнымалыларды қою; `/health`-те `"api": "stub"` емес екенін тексеру. **Осыны жасамай бұл тармақты merge етсеңіз, қосымша backend таппайды** — бұрын ол басқа репоның сервисіне үнсіз ауысып жүрген.
2. GitHub-та репозиторийді private ету; кейін Railway GitHub App-қа осы репоға рұқсат беру.

---

## 1. Қысқаша қорытынды

Мобильді қосымша (Flet/Python → Flutter) жақсы бастама алған. Бірақ **қазіргі күйінде Android не iOS үшін
жаңадан жиналған нұсқа іске қосылмайды**, ал iOS build ешқашан сәтті өтпеген. Негізгі үш себеп:

| # | Мәселе | Салдары |
|---|--------|---------|
| 1 | `flet` нұсқасы бекітілмеген (`mobile/pyproject.toml:22`), ал Flet 1.0 шықты және онда `ft.ElevatedButton` жойылған | Жаңа build-те 12 экранның 6-уы құрастырылмайды → қосымша **іске қосылғанда құлайды** |
| 2 | iOS workflow (`.github/workflows/build-ios.yml:36`) Flet-те жоқ `--no-codesign --project-name` флагтарын қолданады, мобильді бума жолын көрсетпейді | GitHub Actions-та **iOS build әрдайым құлайды** (run #30804773138) |
| 3 | CI/CD соңғы 10+ іске қосуда қызыл: `test_forecast_endpoint` `WEATHERAPI_KEY` жоқта 500 қайтарады | `deploy` job ешқашан орындалмайды, қателер байқалмай қалады |

Бұдан бөлек: навигацияда 11 батырма (телефонда пайдалануға келмейді), тіл/тақырып ауыстырғанда экрандар
жаңармайды, бірнеше экран **ойдан шығарылған сандарды** көрсетеді, Optimization экраны API жауабын
дұрыс оқымайды, баптаулар сақталмайды, дүкенге (Play Store / App Store) шығаруға дайындық жоқ.

Төменде — не тексерілді, не табылды (дәлелімен), және кезеңдерге бөлінген жоспар.

---

## 2. Репозиторийлер картасы

| Репозиторий | Рөлі | Күйі |
|-------------|------|------|
| **AI-Hybrid-Energy-Source-Predictor** | Ең жаңа код: FastAPI + Streamlit + NiceGUI + **Flet mobile** + iOS workflow + API-key қорғанысы | **Негізгі (canonical) деп ұсынылады** |
| **EcoPradict-Ai** | Сол кодтың ескі көшірмесі (fork). Мобильді бөлігінде бұрынғы қателер қалған: `http://` API (Android бұғаттайды), `/chat` қате payload, `/solarman/live` POST (405) | Екі жерде қатар дамыту — қайта-қайта қате. Біріктіру керек |
| **CACER_Simulator** | RSE-CoLabs жобасының fork-ы (BSD-3). Соңғы коммит `ь` — логотип суреттерін өшіреді | Мобильді қосымшаға қатысы жоқ, тек білім беру лабораториялары үшін |

Қосымша ескерту: `AI-Hybrid` ішінде `third_party/CACER_Simulator` толық көшірме (372 файл, ~106 MB) ретінде
сақталған, ал `.gitmodules` оны әлі submodule деп жариялайды. `EcoPradict-Ai`-да ол нағыз submodule, бірақ
`d22333b` коммитіне сілтейді, ол тек сіздің fork-та бар, ал `.gitmodules` URL-і upstream-ге
(`RSE-CoLabs`) бағытталған → `git submodule update --init` сол жерде сәтсіз болады.

---

## 3. Архитектура (қазіргі)

```
 Телефон (Android APK / iOS IPA)                    Railway (бұлт)
┌──────────────────────────────┐   HTTPS/JSON   ┌──────────────────────────────┐
│ Flet app  (mobile/)          │ ─────────────▶ │ FastAPI  main.py / api/      │
│  main.py  – splash, nav      │                │  /health /predict /chat      │
│  api_client.py – urllib      │                │  /detect (YOLO11n)           │
│  state.py – жады ішіндегі    │                │  /solarman/* (live, roi, …)  │
│  views/ – 12 экран           │                │  artifacts/*.pkl модельдер   │
└──────────────────────────────┘                └──────────────────────────────┘
```

* Мобильді бума тек `flet` + `certifi` тәуелділігімен жиналады (дұрыс шешім — серверлік кітапханалар телефонға кірмейді).
* Барлық ML есептеу серверде. Сервер қолжетімсіз болса, клиент кейбір экрандарда жергілікті «fallback» сандарын шығарады.

---

## 4. Не тексерілді (әдіс)

| Тексеру | Нәтиже |
|---------|--------|
| Мобильді кодты толық оқу (`mobile/**`, ~3000 жол) | Төмендегі табыстар |
| Барлық 12 экранды **Flet 0.86.5**-те құрастыру (smoke test) | 12/12 OK, бірақ 6 экран `ElevatedButton is deprecated … will be removed in 1.0` ескертуі |
| Сол smoke test **Flet 1.0.1**-де (қазір `pip install flet` орнататын нұсқа) | **6/12 FAIL**: `AttributeError: module 'flet' has no attribute 'ElevatedButton'` (overview, predictions, faults, opt, live, settings) |
| `ElevatedButton → Button` алмастырып, 1.0.1-де қайта | 12/12 OK — конструкция деңгейінде басқа бұзылыс жоқ (құрылғыда runtime тексеру әлі керек) |
| `flet build` CLI (0.86.5 және 1.0.1) | `--no-codesign`, `--project-name`, `--target` флагтары **екеуінде де жоқ** |
| GitHub Actions логтары | iOS: `flet: error: unrecognized arguments: --no-codesign --project-name`. CI: 73/74 тест өтеді, `test_forecast_endpoint` 500 |
| Backend-ті жергілікті іске қосып, мобильді клиенттің **нақты payload**-тарымен сұрау | `/health`, `/predict`, `/chat`, `/solarman/process`, `/solarman/roi`, `/solarman/alert`, `/solarman/live?demo=true` — 200. `/solarman/live` (demo-сыз, кілтсіз) — 502. `/detect` — ultralytics жоқта 503 |
| Production Railway URL-дары | Бұл ортаның желі саясаты бұғаттады — **тексерілмеді**. Өз телефоныңыздан немесе браузерден `…/health` ашып растау керек |

---

## 5. Табылған мәселелер

Маңыздылық: 🔴 Критикалық · 🟠 Жоғары · 🟡 Орташа · ⚪ Төмен

### 5.1 Build және іске қосу

| | Мәселе | Қайда | Не істеу керек |
|---|---|---|---|
| 🔴 | `flet` бекітілмеген; Flet 1.0.1-де `ElevatedButton` жоқ → қосымша құлайды | `mobile/pyproject.toml:22`; `ElevatedButton` 6 файлда: `predictions_view.py:81`, `overview_view.py:195`, `optimization_view.py:87`, `settings_view.py:61`, `live_view.py:329`, `faults_view.py:151` | Бірден `flet==0.86.5` бекіту; кейін `ft.Button`-ға көшіп, `flet==1.0.x` бекіту |
| 🔴 | iOS workflow: жоқ флагтар, `python_app_path` берілмеген (түбірдегі `main.py` = FastAPI сервер!), түбірлік `requirements.txt` (torch, ultralytics, chromadb…) macOS-қа орнатылады | `.github/workflows/build-ios.yml:6,32,36` | `flet build ipa mobile …`; тек `flet` орнату; trigger-ді `workflow_dispatch` + `tags` + `paths: mobile/**` етіп шектеу (әр push-та macOS минуттары жұмсалады) |
| 🔴 | Android үшін CI build мүлде жоқ (APK тек қолмен жиналады) | `.github/workflows/` | `build-android.yml`: `flet build apk mobile` және `flet build aab mobile` (signing secrets арқылы) |
| 🟠 | README-дегі build командалары жұмыс істемейді (`--target` флагы жоқ) | `README.md` («Building Mobile Binaries») | `flet build apk mobile`, `flet build ipa mobile` деп түзету |
| 🟠 | CI қызыл: `test_forecast_endpoint` кілтсіз 500 | `.github/workflows/ci-cd.yml:51`, `api/routes.py:609`, `tests/test_solarman_api.py:215` | Ауа райын тестте mock жасау **немесе** `/solarman/forecast`-қа Open-Meteo fallback қосу (`src/monitoring/api_client.py`-де клиент бар, кілт керек емес) |
| 🟡 | `flutter-action` 3.24 қолмен бекітілген — Flet өзіне қажет Flutter нұсқасын басқарады, сәйкессіздік қаупі | `build-ios.yml` | Flet-тің өзі Flutter-ді орнатуына мүмкіндік беру, қадамды алып тастау |

### 5.2 Деректердің дұрыстығы (пайдаланушыға жалған сан көрсетпеу)

| | Мәселе | Қайда | Не істеу керек |
|---|---|---|---|
| 🟠 | Optimization экраны `optimal_dispatch` кілтін оқиды, ал `/predict` оны қайтармайды → «Solar Supply» орнына **қолжетімді** қуат (мыс. 1244 kW), батарея үшін ойдан `min(battery, 50)`, желі үшін әрдайым `0.0` | `optimization_view.py:72-76` | API-дің нақты өрістерін қолдану: `solar_used`, `wind_used`, `battery_used`, `shortfall_kw`, `curtailment_kw` |
| 🟠 | Training экраны: R² 98.4%, RMSE 12.4, MAE 8.7 — қатаң жазылған және **мақаладағы метрикаларға қайшы** (R² 0.9967/0.9971, MAE 227/213 kW) | `training_view.py:17,32,47` | `artifacts/model_metrics.json`-ды API арқылы беру (`GET /metrics`) немесе дұрыс сандарды қою |
| 🟠 | Sustainability: 412.8 т CO₂, 18 650 ағаш, 88.4% — ойдан шығарылған | `sustainability_view.py:18,34,70` | `src/sustainability/` функцияларын API арқылы шақыру |
| 🟠 | Labs: `tot = s*0.85 + w*0.70`, `eff = 92 + b/1000*6` — физикалық мағынасы жоқ формула | `labs_view.py:29-30` | Backend-тегі `src/simulation/` модульдерін API арқылы қолдану немесе экранды «оқу демосы» деп анық белгілеу |
| 🟠 | Басты экрандағы «Күн өндірісі / Жел өндірісі» — нақты өлшем емес, әдепкі слайдер мәндерімен (900 W/m², 6.5 m/s) жасалған ML болжам | `overview_view.py:243-255` | «Сценарий бойынша болжам» деп белгілеу немесе кірістерді нақты ауа райынан (`/solarman/weather`) алу |
| 🟡 | `get_solarman_live` әрдайым `demo=true` жібереді → серверде Solarman кілттері болмаса, **демо деректер «Real-time» ретінде** көрінеді | `api_client.py:406`, `overview_view.py:143` | `demo=false`; `source == "demo"` болса анық «ДЕМО» белгісі |
| 🟡 | `predict()` офлайн болса ойдан сан қайтарады (`is_fallback: True`), бірақ бірде-бір экран бұл белгіні көрсетпейді; Predictions экраны әдепкі «420.5 kW» көрсетеді | `api_client.py:258-275`, `predictions_view.py:22-24,59-60` | Офлайн күйде «—» және себебін көрсету, немесе «жуық бағалау» белгісі |

### 5.3 UX, навигация, тіл

| | Мәселе | Қайда | Не істеу керек |
|---|---|---|---|
| 🟠 | `NavigationBar`-да **11 батырма** (Material ұсынымы 3–5). 393 px экранда әрқайсысына ~35 px — белгілер оқылмайды | `components/nav_bar.py` | 5 негізгі қойынды + «Тағы» мәзірі (7-бөлімді қараңыз) |
| 🟠 | Тіл/тақырып ауыстырғанда тек AppBar өзгереді: барлық экран түстер мен мәтінді құрастыру сәтінде бір рет алады (`c = state.colors` — 12 экранда) | `main.py:139-142`, `views/*` | Экрандарды жалқау (lazy) factory арқылы құрастырып, тіл/тақырып өзгергенде кэшті тазалап қайта құрастыру |
| 🟠 | Локализация толық емес: 35 `state.text()` шақыруына қарсы ~121 қатаң жазылған мәтін; навигация белгілері тек қазақша; `kk` сөздігінде 5 кілт жоқ (`st_btn_test`, `st_dark`, `st_lang`, `st_light`, `st_theme`) | `config.py`, `nav_bar.py`, `views/*` | Барлық мәтінді `LOCALIZATION`-ға көшіру, екі тілді салыстыратын тест |
| 🟠 | Header «⚠️ Интернет жоқ» деп қалып қоюы мүмкін: health 2 с ішінде жауап бермесе, нәтиже келгенде AppBar ешқашан жаңармайды (`state.subscribe` еш жерде қолданылмайды) | `main.py:182-204`, `state.py` | Health аяқталғанда `refresh_ui()` шақыру |
| 🟡 | Баптаулар (тіл, тақырып, сервер URL) сақталмайды — әр іске қосқанда қалпына келеді | `state.py` | Flet `SharedPreferences` сервисі арқылы сақтау |
| 🟡 | Settings-те API URL өрісі жоқ, ал `README.md` және `RAILWAY_DEPLOYMENT.md` оны енгізуді айтады | `settings_view.py` | Өрісті қайтару (кеңейтілген баптау ретінде) немесе құжатты түзету |
| 🟡 | `learn` экраны құрастырылады, бірақ навигацияда жоқ — ешқашан ашылмайды | `main.py:144,172` | «Тағы» мәзіріне қосу |
| ⚪ | `page.title = "… iPhone 16 Simulation"`, терезе өлшемі телефонда да орнатылады | `main.py:57-68` | Тек desktop preview кезінде |

### 5.4 Өнімділік және желі

| | Мәселе | Қайда | Не істеу керек |
|---|---|---|---|
| 🟡 | Іске қосқанда 12 экранның бәрі бірден құрастырылады; Predictions және Optimization құрастыру кезінде-ақ `/predict` шақырады (Overview-да бұрын түзетілген race қайталанады) | `main.py:166-179`, `predictions_view.py:77`, `optimization_view.py:83` | Экрандарды алғаш ашылғанда құрастыру; жүктеуді `.data` hook арқылы |
| 🟡 | Solarman экранындағы слайдерлер әр жылжығанда сервер сұрауын жібереді (`on_change`) | `live_view.py:325-327` | `on_change_end` қолдану |
| 🟡 | Health тізбекті: ең нашар жағдайда 20 + 5×8 = 60 с; бір URL сәтсіз болса, қосымша басқа хостқа (соның ішінде `www.ecopredict.kz`) үнсіз ауысады | `api_client.py:162-216` | Бір канондық URL + қайталау (retry/backoff); ауысуды Settings-те көрсету |
| 🟡 | Ақау анықтау: тек галерея (камера жоқ), сурет кішірейтілмейді — телефон фотосы 10 MB шегінен асуы мүмкін (сервер 413) | `faults_view.py:117-149`, `api/routes.py:387` | Камера мүмкіндігі (`--permissions camera photo_library`), жүктеу алдында өлшемді тексеру/сығу |
| ⚪ | Inverter SN-дері кодта қатаң жазылған | `live_view.py:27` | Серверден тізім алу (`GET /solarman/devices`) |

### 5.5 Backend және қауіпсіздік (мобильдің тұрақты жұмысы үшін)

| | Мәселе | Қайда | Не істеу керек |
|---|---|---|---|
| 🟠 | Екі түрлі backend деплойы: `mobile/` ішінде `Procfile`, `requirements.txt` және `main.py`-дағы FastAPI бөлігі (221–335 жолдар) — Railway «Root Directory = mobile» кезінде `api/` көрінбейді, тек stub жұмыс істейді. Клиент бірнеше URL-ды кезекпен сынайды | `mobile/Procfile`, `mobile/requirements.txt`, `mobile/main.py:221-335`, `api_client.py:164-174` | Бір ғана Railway сервисі (репо түбірінен), бір канондық HTTPS домен; `mobile/` ішінен серверлік кодты алып тастау |
| 🟠 | `/detect`, `/chat`, `/predict` — ашық, rate limit жоқ. YOLO — қымбат операция; кез келген адам серверді жүктей алады | `api/routes.py` | IP бойынша rate limit (мыс. `slowapi`), сұрау өлшемі шегі, таймауттар |
| 🟡 | CORS: `allow_origins=["*"]` + `allow_credentials=True` | `main.py:52`, `api/main.py:21` | Мобильге CORS керек емес; веб үшін нақты домендер |
| 🟡 | `/predict` ішінде `print()` debug | `api/routes.py:205-206` | `logger.debug` |
| 🟡 | Минималды қосымша нұсқасын тексеру жоқ — API өзгерсе, ескі APK үнсіз бұзылады | — | `GET /version` → `min_app_version`; қосымшада «Жаңартыңыз» хабарламасы |
| ⚪ | Git-те `__pycache__/run_nicegui.cpython-313.pyc` бар | репо түбірі | Өшіру (`.gitignore` бар) |

### 5.6 Дүкенге шығару (Play Store / App Store) дайындығы

| | Не жетіспейді |
|---|---|
| 🟠 | **Android**: signing keystore жоқ, AAB build жоқ, `build_number` / `build_version` басқарылмайды |
| 🟠 | **iOS**: Apple Developer аккаунты, Team ID, signing сертификаты, provisioning profile, App Store Connect жазбасы; фото кітапханасына рұқсат сипаттамасы (`NSPhotoLibraryUsageDescription`, камера қосылса — `NSCameraUsageDescription`) |
| 🟠 | Қосымша иконкасы мен splash суреті жоқ (`mobile/assets/icon.png` жоқ → әдепкі Flet иконкасы) |
| 🟠 | Құпиялылық саясаты (privacy policy) URL — екі дүкен де міндетті түрде талап етеді; Play «Data safety», App Store «App Privacy» формалары |
| 🟡 | Скриншоттар, сипаттама (KK/EN), жас рейтингі |
| 🟡 | Crash/қате есебі жоқ (мыс. Sentry) — пайдаланушыда не бұзылғанын білу мүмкін емес |

---

## 6. Даму жоспары (кезеңдер)

Әр кезеңнің соңында — **қабылдау критерийі** (не болса «дайын» деп есептейміз).

### 0-кезең — Шұғыл: қосымша жиналып, іске қосылсын (1–2 күн)

1. ✅ `flet==1.0.1` бекітілді және код 1.0-ге көшірілді (шешім бойынша 0.86.5 орнына).
2. ✅ iOS workflow-ды түзету: `flet build ipa mobile`, тек `pip install "flet[cli]==1.0.1"`, trigger — `workflow_dispatch` + `v*` тегтері + `paths: mobile/**`. Signing жоқ кезде smoke үшін `flet build ios-simulator mobile`.
3. ✅ Жаңа `build-android.yml`: `flet build apk mobile` → artifact ретінде жүктеу.
4. ✅ CI-дегі `test_forecast_endpoint`-ті түзету (mock немесе Open-Meteo fallback).
5. ✅ `tests/test_mobile_smoke.py`: барлық экранды бекітілген Flet нұсқасында құрастыратын тест (осы талдаудағы smoke скрипт негізінде) — Flet жаңартуы бір нәрсені бұзса, CI бірден көрсетеді.
6. ✅ README build командаларын түзету.

**Критерий:** CI жасыл; Android APK және iOS simulator build Actions-та сәтті; APK телефонда ашылады.

### 1-кезең — Деректердің дұрыстығы (3–5 күн)

1. Optimization экранын `/predict`-тің нақты өрістеріне көшіру (`solar_used`, `wind_used`, `battery_used`, `shortfall_kw`, `curtailment_kw`).
2. Training: `GET /metrics` (API) → `artifacts/model_metrics.json`; экран сол сандарды көрсетеді.
3. Sustainability: `src/sustainability/` арқылы есептейтін endpoint; экран оны шақырады.
4. Labs: `src/simulation/` endpoint-тері немесе экранды «оқу демосы» деп белгілеу.
5. Барлық «fallback / demo» деректерге көрінетін белгі (badge); Solarman `demo=false`, серверде кілттер бапталуы тиіс.
6. Басты экрандағы KPI атауларын түзету («сценарий болжамы») немесе нақты ауа райынан кіріс алу.

**Критерий:** Қосымшада бірде-бір сан кодта қатаң жазылмаған; офлайн/демо күйі әрдайым анық көрсетіледі.

### 2-кезең — UX, тіл, навигация (1–2 апта)

1. Навигация: 5 қойынды — **Басты · Болжам** (ML + 24h ішкі tab) **· Solarman · AI Кеңесші · Тағы** (Ақау/YOLO, Оңтайландыру, Экология, Лаборатория, Оқу, ML модель, Баптаулар). Планшетте `NavigationRail`.
2. Экрандарды lazy factory арқылы құрастыру; тіл/тақырып өзгерсе қайта құрастыру.
3. Толық локализация (KK/EN): барлық мәтін `LOCALIZATION`-да; кілттер сәйкестігін тексеретін тест.
4. Баптауларды `SharedPreferences`-та сақтау (тіл, тақырып, сервер URL).
5. Health нәтижесі келгенде header-ді жаңарту; қайта қосылу батырмасы.
6. Слайдерлерге `on_change_end`; Predictions/Optimization-ды құрастыру кезінде емес, ашылғанда жүктеу.
7. Ақау анықтау: камера + галерея, сурет өлшемін тексеру.
8. Flet 1.0: ✅ көшірілді (0-кезеңде); қалғаны — нақты құрылғыда толық тексеру.

**Критерий:** Барлық экран 360–430 px енінде дұрыс көрінеді; EN режимінде қазақша мәтін қалмайды; баптаулар қайта іске қосқаннан кейін сақталады.

### 3-кезең — Backend тұрақтылығы және қауіпсіздік (1 апта, 2-кезеңмен қатар болады)

1. Бір Railway сервисі (репо түбірінен), бір канондық домен; `mobile/` ішінен `Procfile`, `requirements.txt`, FastAPI бөлігін алып тастау; клиенттегі URL тізімін қысқарту.
2. Rate limiting (`/detect`, `/chat`, `/predict`), CORS түзету, `print` → `logger`.
3. `GET /version` (min_app_version) және қосымшада мәжбүрлі жаңарту хабарламасы.
4. Production-да `WEATHERAPI_KEY`, `ECOPREDICT_API_KEY`, Solarman кілттері, YOLO салмақтары бар екенін тексеру (`/health` оларды көрсетуі тиіс).
5. Мониторинг: Railway логтары + uptime тексеру; қалауы бойынша Sentry (backend + мобиль).

**Критерий:** Бір URL; `/health` барлық тәуелділік күйін шынайы көрсетеді; жүктеме тестінде сервер құламайды.

### 4-кезең — Дүкенге шығару (1–2 апта; аккаунттар дайын болса)

**Android (Google Play)**
1. Upload keystore жасау → GitHub Secrets; `flet build aab mobile` signing-пен.
2. Иконка (`mobile/assets/icon.png`, adaptive icon), splash, `build_number` автоматты өсіру.
3. Play Console: privacy policy URL, Data safety, content rating, скриншоттар (KK/EN), **Internal testing** → Closed → Production.

**iOS (App Store)**
1. Apple Developer Program аккаунты, Bundle ID (`kz.ecopredict.…`), сертификат + provisioning profile → GitHub Secrets.
2. `flet build ipa mobile --ios-team-id … --ios-export-method app-store …`, `--permissions photo_library` (камера қосылса `camera`).
3. App Store Connect: App Privacy, скриншоттар, **TestFlight** → Review → Release.

**Критерий:** Екі платформада да ішкі тестерлер дүкен арқылы орната алады.

### 5-кезең — Сапа және қолдау (тұрақты)

1. CI-де `ruff` мобильді буманы да тексерсін (қазір тек `api src dashboard tests`), `continue-on-error` алып тастау.
2. `api_client` үшін unit тесттер (payload пішімдері — бұрынғы 422/405 қателерінің алдын алу), API контракт тесттері.
3. Нақты құрылғыларда тексеру тізімі (Android 10–15, iPhone SE / 15 / 16), офлайн, баяу желі, қараңғы/жарық тақырып.
4. Репозиторийлерді біріктіру: `AI-Hybrid` негізгі; `EcoPradict-Ai`-ды архивтеу немесе тек зеркало ету; CACER-ді біркелкі қосу (не submodule, не vendored — біреуі).

---

## 7. Сіздің шешіміңіз керек сұрақтар

1. ~~**Flet нұсқасы**~~ — **шешілді: бірден 1.0-ге көшеміз** (жасалды).
2. **Дүкен аккаунттары**: Apple Developer Program (жылына ~$99) және Google Play Console (бір рет ~$25) бар ма / кім тіркейді?
3. ~~**Канондық backend URL**~~ — **шешілді: осы репоның Railway сервисі** (`ecopradict-mobile-production`).
4. **Solarman кілттері**: production серверде нақты кілттер болады ма? Болмаса, Solarman экраны демо режимде «ДЕМО» белгісімен көрсетіледі.
5. ~~**Негізгі репозиторий**~~ — **шешілді: `AI-Hybrid-Energy-Source-Predictor`, private болады.**
6. **Экрандар жиыны**: мобильде 11 бөлімнің бәрі керек пе, әлде Labs/Learn/Training-ті «Тағы» ішіне қоямыз ба?
