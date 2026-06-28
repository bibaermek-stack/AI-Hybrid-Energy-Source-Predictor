knowledge = {
    "en": {
        "solar": """Solar power generation is influenced by three key factors:
1. **Solar Irradiation (W/m²)**: Direct correlation with output. Higher irradiation means more energy.
2. **Ambient & Module Temperature (°C)**: Solar panels perform less efficiently at high temperatures. The output drops by approximately 0.4% per °C above 25°C module temperature.
3. **Time of Day and Season**: Peak generation occurs between 11 AM and 2 PM, and is higher during summer months.

Optimization tip: Keep panels clean and install them at an angle matching your latitude for maximum year-round energy capture.""",

        "wind": """Wind power generation depends heavily on:
1. **Wind Speed (m/s)**: The relationship is cubic (Power ∝ Speed³). A small increase in wind speed yields a massive increase in power output. Most turbines cut-in at 3 m/s, reach rated capacity at 12-15 m/s, and cut-out at 25 m/s.
2. **Wind Direction (°)**: Modern turbines rotate (yaw) to face the wind. Rapid changes in direction can temporarily reduce output.
3. **Theoretical Power Curve**: Defines the manufacturer's expected power for any given wind speed.

Optimization tip: Turbines should be placed in areas with unobstructed wind flow, avoiding wake effects from other turbines.""",

        "hybrid": """Hybrid solar-wind systems are highly efficient because solar and wind energy are complementary:
1. **Day vs. Night**: Solar energy is generated during the day, while wind speeds are often stronger at night.
2. **Seasonal Complementarity**: Solar output is highest in summer, whereas wind speeds are generally stronger during winter.
3. **Smart Optimization**: Our AI optimizer evaluates both outputs and suggests the best primary source or combination to stabilize the grid and reduce battery storage dependency.

Optimization tip: A hybrid ratio of 60% wind and 40% solar works best in moderate climates to ensure 24/7 continuous base power.""",

        "battery": """Battery storage is critical for hybrid energy systems to manage intermittency:
1. **Peak Shaving**: Store excess energy generated during peak solar/wind hours and release it during high demand.
2. **Depth of Discharge (DoD)**: Maintain battery state of charge between 20% and 80% to double the battery lifespan.
3. **Optimal Capacity**: A typical residential hybrid system requires a 10-15 kWh battery to cover overnight loads.""",

        "faq": """Frequently Asked Questions:
- **Q: Why does high temperature reduce solar output?**
  A: Photovoltaic cells are semiconductors. High heat increases the conductivity, reducing the voltage difference and dropping the overall efficiency.
- **Q: What is cut-in and cut-out speed?**
  A: Cut-in (typically 3 m/s) is when the turbine starts generating electricity. Cut-out (typically 25 m/s) is when it shuts down to prevent structural damage from high winds.
- **Q: How does the AI model predict output?**
  A: It uses historical weather sensor data and energy logs. Solar is predicted via Random Forest, and wind is predicted using XGBoost."""
    },
    
    "kk": {
        "solar": """Күн энергиясын өндіруге үш негізгі фактор әсер етеді:
1. **Күн сәулесінің түсуі (Вт/м²)**: Шығыс қуатпен тікелей байланысты. Күн сәулесі неғұрлым көп болса, соғұрлым энергия көп болады.
2. **Температура (°C)**: Күн панельдері жоғары температурада аз тиімділікпен жұмыс істейді. Панель температурасы 25°C-тан асқанда, тиімділік әр градусқа шамамен 0.4%-ға төмендейді.
3. **Күн уақыты мен маусым**: Ең көп энергия сағат 11:00 мен 14:00 аралығында өндіріледі және жаз айларында жоғары болады.

Оңтайландыру кеңесі: Панельдерді таза ұстаңыз және ең көп энергия алу үшін оларды ендік бұрышына сәйкес орнатыңыз.""",

        "wind": """Жел энергиясын өндіру келесі факторларға байланысты:
1. **Жел жылдамдығы (м/с)**: Тәуелділік кубтық сипатқа ие (Қуат ∝ Жылдамдық³). Жел жылдамдығының сәл артуы қуатты айтарлықтай арттырады. Турбиналар 3 м/с-те іске қосылады, 12-15 м/с-те толық қуатқа жетеді және 25 м/с-те тоқтайды.
2. **Жел бағыты (°)**: Заманауи турбиналар желге қарай бұрылады. Бағыттың жылдам өзгеруі қуатты уақытша азайтуы мүмкін.
3. **Теориялық қуат қисығы**: Жел жылдамдығына сәйкес өндірілуі тиіс өндірушінің есептік қуаты.

Оңтайландыру кеңесі: Турбиналарды жел кедергісіз соғатын, басқа турбиналардың көлеңкесінен тыс ашық жерлерде орналастыру керек.""",

        "hybrid": """Гибридті күн-жел жүйелері өте тиімді, өйткені олар бірін-бірі толықтырады:
1. **Күн мен Түн**: Күн энергиясы күндіз өндіріледі, ал жел жылдамдығы көбінесе түнде күшейеді.
2. **Маусымдық үйлесімділік**: Күн қуаты жазда, ал жел қуаты қыста жоғары болады.
3. **Ақылды оңтайландыру**: Біздің AI оңтайландырушымыз екі көздің де қуатын бағалап, желіні тұрақтандыру үшін ең тиімді негізгі көзді ұсынады.

Оңтайландыру кеңесі: Қалыпты климатта 24/7 үздіксіз қуатпен қамта обеспечение ету үшін 60% жел және 40% күн энергиясының арақатынасы тиімді.""",

        "battery": """Батареялық сақтау жүйесі энергияның тұрақсыздығын басқару үшін маңызды:
1. **Пиктік реттеу**: Өндіріс көп болған кезде артық энергияны жинап, тұтыну жоғары болған кезде желіге береді.
2. **Разрядтау тереңдігі (DoD)**: Батареяның қызмет ету мерзімін ұзарту үшін заряд деңгейін 20%-дан 80%-ға дейін сақтаңыз.
3. **Оңтайлы сыйымдылық**: Стандартты гибридті жүйе үшін түнгі жүктемені жабуға 10-15 кВт/сағ батарея жеткілікті.""",

        "faq": """Жиі қойылатын сұрақтар (FAQ):
- **С: Неліктен жоғары температура күн панелінің қуатын азайтады?**
  А: Фотоэлектрлік элементтер жартылай өткізгіштер болып табылады. Жоғары температура кедергіні өзгертіп, кернеуді төмендетеді, бұл тиімділікті азайтады.
- **С: Іске қосылу және тоқтау жылдамдығы деген не?**
  А: Іске қосылу (3 м/с) - турбина жұмыс істей бастайтын жылдамдық. Тоқтау (25 м/с) - дауыл кезінде турбинаны зақымданудан қорғау үшін автоматты түрде тоқтайтын шек.
- **С: AI моделі қуатты қалай болжайды?**
  А: Ол тарихи ауа райы деректері мен қуат журналдарын қолданады. Күн қуаты Random Forest арқылы, ал жел қуаты XGBoost арқылы болжанады."""
    }
}

def load_documents():
    return knowledge