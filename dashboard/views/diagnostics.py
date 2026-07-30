from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dotenv import load_dotenv
import streamlit as st

from dashboard.components.icons import icon_text
from dashboard.utils.i18n import get_texts
from dashboard.utils.models_loader import load_clean_dirty_model, load_yolo_model

load_dotenv()


def render(lang: str, texts: dict | None = None, models_status: dict | None = None) -> None:
    models_status = models_status or {"solar": False, "wind": False, "lstm": False}
    texts = {**get_texts(lang), **(texts or {})}

    st.markdown(icon_text("diagnostics", "System Diagnostics & Faults" if lang == "en" else "Күн станциясының ақаулықтарын диагностикалау", size=22, as_heading=True, level=3), unsafe_allow_html=True)
    st.markdown(f'<p style="color:#8b949e;">{"Diagnose physical, environmental, inverter, and telemetry faults in your solar panels and system." if lang == "en" else "Күн панельдері мен жүйедегі физикалық, экологиялық, инверторлық және телеметриялық ақауларды диагностикалау және шешу."}</p>', unsafe_allow_html=True)

    # ------------------ INTERACTIVE DIAGNOSTIC WIZARD ------------------
    st.markdown("---")
    st.markdown(f'<h4>{" Interactive Diagnostics Wizard" if lang == "en" else " Интерактивті диагностика шебері"}</h4>', unsafe_allow_html=True)

    symptoms = [
        "Таңдау..." if lang == "kk" else "Select...",
        "Ластану және шаң (Өнімділіктің 10-30%-ға төмендеуі)" if lang == "kk" else "Soiling & Dust (10-30% drop in generation)",
        "Көлеңкенің түсуі (Бір панельге көлеңке түсіп, тізбек жұмысының нашарлауы)" if lang == "kk" else "Shading Obstruction (Partial shade on panel dropping string output)",
        "Микрожарықтар мен Деградация (Жел, бұршақ немесе соққыдан кейін өнімділіктің біртіндеп кемуі)" if lang == "kk" else "Microcracks & Degradation (Gradual drop after high winds, hail or impact)",
        "Ыстық нүктелер (Күн астында жеке ұяшықтың қатты қызып кетуі)" if lang == "kk" else "Hot Spots (Extreme local heating of cells under sun)",
        "PID деградациясы (Жоғары кернеуден өнімділіктің күрт кемуі)" if lang == "kk" else "Potential Induced Degradation (PID - Sudden high-voltage drop)",
        "Grid Over/Under Voltage (Электр желісіндегі кернеудің тұрақсыздығы)" if lang == "kk" else "Grid Over/Under Voltage (External grid instability/safety shutoff)",
        "Insulation Resistance Fault (Оқшаулау кедергісінің төмендеуі / Қысқа тұйықталу қаупі)" if lang == "kk" else "Insulation Resistance Fault / Isolation Error (Damaged cable or moisture)",
        "Overheating (Инвертордың қатты қызып, өнімділікті автоматты шектеуі - Derating)" if lang == "kk" else "Inverter Overheating (Automatic power derating due to heat/airflow)",
        "Data Logger Offline (Мониторинг жүйесінің істен шығуы немесе өшуі)" if lang == "kk" else "Data Logger Connection Offline (Wi-Fi/4G/Logger stick connection error)",
        "Smart Meter CT Clamp Error (Өндіріс пен тұтыну статистикасының араласып кетуі)" if lang == "kk" else "Smart Meter / CT Clamp incorrect installation (Reversed statistics)"
    ]

    selected_symptom = st.selectbox(
        "Ақаулық белгісін немесе кодыңызды таңдаңыз / Select symptom or error code:" if lang == "kk" else "Select symptom or error code:",
        symptoms,
        index=0
    )

    if selected_symptom != symptoms[0]:
        diag_data = {}
    
        if "Soiling" in selected_symptom or "Ластану" in selected_symptom:
            diag_data = {
                "severity": " Medium / Орташа",
                "color": "#ffc107",
                "meaning": "Панель бетіне шаң, құм, құс саңғырығы немесе ағаш жапырақтарының жиналуы. Тіпті жұқа шаң қабатының өзі өнімділікті 10-15%-ға, ал қатты ластану 30%-дан астамға төмендетеді." if lang == "kk" else "Accumulation of dust, sand, bird droppings, or leaves. Even a thin dust layer can decrease efficiency by 10-15%, while heavy dirt drops it by over 30%.",
                "causes": ["Шаңды аймақтар немесе ұзақ уақыт жаңбырдың жаумауы.", "Құстардың ұя салу белсенділігі.", "Панель бұрышының өте төмен болуы (су мен кірдің өздігінен ақпауы)."] if lang == "kk" else ["Dusty environments or long dry periods without rain.", "Bird activity.", "Low installation tilt angle preventing self-cleaning."],
                "actions": ["Панельдерді салқын кезде (таңертең немесе кешкісін) таза сумен жуу. Ыстық кезде жусаңыз, суық судан әйнек сынуы мүмкін.", "Жуу кезінде қатты химиялық құралдарды немесе темір щеткаларды қолданбау (әйнекті зақымдауы мүмкін).", "Орнату бұрышын кем дегенде 10-15 градусқа жеткізу."] if lang == "kk" else ["Wash panels with clean water when they are cool (morning/evening) to avoid thermal shock/cracking.", "Do not use abrasive tools or harsh chemicals.", "Ensure tilt angle is at least 10-15 degrees for self-cleaning."]
            }
        elif "Shading" in selected_symptom or "Көлеңкенің" in selected_symptom:
            diag_data = {
                "severity": " Medium / Орташа",
                "color": "#ffc107",
                "meaning": "Маңайдағы ағаштар, ғимараттар, мұржалар немесе көрші панельдердің көлеңкесі. Тіпті бір ғана панельдің кішкентай бұрышына көлеңке түссе, бүкіл тізбектің (string) өнімділігі айтарлықтай төмендеп кетеді." if lang == "kk" else "Shadows from nearby trees, buildings, chimneys, or adjacent panels. Shading on even a small corner of one panel can severely drop the yield of the entire string.",
                "causes": ["Жыл мезгілі мен күн қозғалысына байланысты көлеңке бұрышының өзгеруі.", "Маңайдағы ағаштардың өсіп кетуі.", "Жобалау кезінде панельдер арақашықтығының дұрыс есептелмеуі."] if lang == "kk" else ["Changing sun angles across seasons.", "Overgrown nearby trees.", "Incorrect row spacing during design/installation."],
                "actions": ["Панельдерге көлеңке түсіріп тұрған ағаш бұтақтарын кесу.", "Жүйеге Bypass диодтарының дұрыс жұмыс істеп тұрғанын тексеру.", "Аса күрделі көлеңкелер жағдайында микроинверторларды немесе оптимизаторларды (Tigo, SolarEdge) орнату."] if lang == "kk" else ["Trim tree branches obstructing the sun.", "Ensure bypass diodes are functioning correctly.", "Install power optimizers (e.g., Tigo, SolarEdge) or microinverters for complex shading issues."]
            }
        elif "Microcracks" in selected_symptom or "Микрожарықтар" in selected_symptom:
            diag_data = {
                "severity": " High / Жоғары",
                "color": "#dc3545",
                "meaning": "Тасымалдау, орнату немесе қатты бұршақ соғу кезінде панельдің ішкі кремний элементтерінде көзге көрінбейтін микрожарықтар пайда болады. Бұл уақыт өте келе ток өткізгіштікті нашарлатады." if lang == "kk" else "Invisible cracks in the silicon cells caused by transport, rough installation, or heavy hail. These degrade electrical pathways and performance over time.",
                "causes": ["Орнату кезінде панельдің үстіне басу немесе құлатып алу.", "Қатты бұршақ немесе экстремалды қар жүктемесі.", "Температураның күрт өзгеруі (термиялық кернеу)."] if lang == "kk" else ["Stepping on panels or rough handling during installation.", "Heavy hail or heavy snow load.", "Extreme thermal cycling/stress."],
                "actions": ["Электролюминесценттік (EL) тестілеу арқылы ақаулы панельді анықтау.", "Зақымдану деңгейі жоғары болса, ақаулы панельді жаңасымен ауыстыру.", "Келесі жобаларда бұршаққа төзімді шынысы бар сапалы Tier-1 панельдерін таңдау."] if lang == "kk" else ["Identify damaged panels using electroluminescence (EL) imaging.", "Replace severely damaged modules to avoid string-wide losses.", "Specify high-quality, hail-resistant Tier-1 panels for replacements."]
            }
        elif "Hot Spots" in selected_symptom or "Ыстық" in selected_symptom:
            diag_data = {
                "severity": " Critical / Қауіпті",
                "color": "#dc3545",
                "meaning": "Көлеңке немесе ішкі ақау салдарынан панельдің белгілі бір ұяшығы (cell) энергия өндірудің орнына, оны тұтына бастайды да, қатты қызып кетеді. Бұл панельдің күйіп кетуіне және өрт қаупіне әкелуі мүмкін." if lang == "kk" else "Local overheating where a cell consumes power instead of producing it, often due to shading or cell defects. This can melt components and poses a serious fire hazard.",
                "causes": ["Ұзақ уақыт бойы бір ұяшыққа көлеңке түсуі немесе қатты кір басуы.", "Байпас диодының (Bypass diode) бұзылуы.", "Өндірістік дефектілер."] if lang == "kk" else ["Long-term localized shading or thick dirt/bird droppings.", "Bypass diode failure.", "Manufacturing defects in cell solder joints."],
                "actions": ["Тепловизор (Thermal camera) арқылы панельдерді тексеріп, ыстық нүктелерді анықтау.", "Егер диод бұзылса, инвертордың қосқыш қорабындағы (junction box) диодты ауыстыру.", "Күйіп кеткен панельді шұғыл түрде тізбектен алып тастап, жаңасына ауыстыру."] if lang == "kk" else ["Scan panels with a thermal camera to locate hot spots.", "Check and replace faulty bypass diodes in the junction box.", "Immediately disconnect and replace severely burned modules."]
            }
        elif "PID" in selected_symptom or "PID" in selected_symptom:
            diag_data = {
                "severity": " High / Жоғары",
                "color": "#dc3545",
                "meaning": "Панельдің ішкі элементтері мен жерге тұйықтау (ground) арасындағы жоғары кернеу айырмашылығынан болатын деградация. Бұл өнімділікті күрт төмендетеді." if lang == "kk" else "Potential Induced Degradation (PID) is caused by leakage currents between the PV cells and the frame/ground under high voltage. This drops output dramatically.",
                "causes": ["Жүйедегі жоғары кернеу (мысалы, ұзын тізбектер).", "Ылғалдылық пен жоғары температура.", "Нашар жерге тұйықтау (grounding)."] if lang == "kk" else ["High system voltage (e.g., long series strings).", "High humidity and temperature.", "Improper grounding of module frames."],
                "actions": ["Жерге тұйықтау тізбегінің тұтастығы мен сапасын тексеру.", "Инверторға PID қалпына келтіргішін (PID box / Anti-PID module) орнату. Ол түнде панельдерге кері кернеу беріп, поляризацияны жояды.", "PID-ке төзімді (PID-free) күн панельдерін сатып алу."] if lang == "kk" else ["Verify grounding circuit resistance and frame connections.", "Install an anti-PID box that applies a reverse bias at night to recover performance.", "Specify PID-resistant (PID-free) panels for new installations."]
            }
        elif "Grid" in selected_symptom or "Grid" in selected_symptom:
            diag_data = {
                "severity": " Warning / Ескерту",
                "color": "#ffc107",
                "meaning": "Сыртқы электр желісіндегі (grid) кернеудің тым жоғары немесе төмен болуы. Мұндай кезде инвертор қауіпсіздік үшін өшіп қалады немесе қуатты автоматты түрде шектейді." if lang == "kk" else "External grid voltage is outside safety parameters. The inverter goes offline or curtails power to protect itself and the grid.",
                "causes": ["Сыртқы желіде жүктеменің кенеттен азаюы немесе көбеюі.", "Маңайдағы басқа күн станцияларының көптеп желіге қуат беруі (кернеуді көтереді).", "Инвертордың желіге қосылатын кабельдерінің тым жұқа болуы (кабельде кернеу өседі)."] if lang == "kk" else ["Sudden load shifts on the local utility grid.", "High density of solar systems exporting power on the same line.", "AC cable impedance is too high (thin cables raise local AC voltage)."],
                "actions": ["Инвертордың AC шығысындағы кабель қимасын тексеру және қажет болса қалыңдату.", "Инвертор баптауларында кернеудің рұқсат етілген шектерін (Grid Protection Settings) жергілікті желі операторымен келісе отырып сәл кеңейту.", "Желі операторына хабарласып, трансформатор кернеуін реттеуді сұрау."] if lang == "kk" else ["Verify AC cable sizing; upgrade to thicker cable to lower voltage drop.", "Adjust inverter grid protection thresholds slightly (coordinate with grid operator).", "Request local grid operator to adjust utility transformer taps."]
            }
        elif "Insulation" in selected_symptom or "Insulation" in selected_symptom:
            diag_data = {
                "severity": " Critical / Қауіпті",
                "color": "#dc3545",
                "meaning": "Кабельдердің оқшаулау қабатының зақымдалуынан немесе қосқыш қораптарға ылғал кіруінен жүйеде қысқа тұйықталу және өрт қаупінің туындауы. Қауіпсіздік үшін инвертор жұмысын толық тоқтатады." if lang == "kk" else "Leakage current detected due to damaged cable insulation or moisture ingress in connectors. The inverter immediately shuts down to prevent shocks and fires.",
                "causes": ["Кабельді кеміргіштердің зақымдауы немесе күн астында тозуы.", "MC4 коннекторына судың кіріп кетуі.", "Жерге тұйықтаудың нашарлауы."] if lang == "kk" else ["Cables damaged by rodents or UV wear.", "Water ingress in poorly sealed MC4 connectors.", "Breakdown of insulation between DC conductors and ground."],
                "actions": ["Инвертор өшірулі кезде мультиметр арқылы тұрақты ток (DC) тізбектерінің жерге қатысті кедергісін тексеру.", "Ақаулы кабельді немесе ылғал кірген MC4 коннекторын тауып, ауыстыру.", "Панель астындағы кабельдердің жерге тимей, арнайы науада (tray) немесе гофрада тұрғанына көз жеткізу."] if lang == "kk" else ["Disconnect DC side and measure insulation resistance of strings to ground.", "Find and replace the damaged cable run or waterlogged MC4 connector.", "Ensure DC cables are routed off the roof surface, using conduit or cable trays."]
            }
        elif "Overheating" in selected_symptom or "Overheating" in selected_symptom:
            diag_data = {
                "severity": " Warning / Ескерту",
                "color": "#ffc107",
                "meaning": "Инвертордың ішкі температурасының рұқсат етілген шектен асып кетуі. Ол өзін қорғау және күйіп кетпеу үшін өнімділік қуатын автоматты түрде азайтады (derating)." if lang == "kk" else "Internal temperature of the inverter exceeds thermal limits. The inverter automatically scales down power output (derating) to avoid damage.",
                "causes": ["Инвертордың тікелей күн астында немесе тар, желдетілмейтін бөлмеде орнатылуы.", "Суыту желдеткішінің (cooling fan) немесе радиатор қанаттарының шаң басуы.", "Инвертор астында немесе маңында жылу бөлетін өзге құрылғылардың орналасуы."] if lang == "kk" else ["Inverter installed in direct sunlight or unventilated spaces.", "Dust/debris clogging cooling fans or heatsink fins.", "Ambient temperature around inverter exceeds rated operating limits."],
                "actions": ["Инвертор үстіне күннен қорғайтын арнайы қалқа (canopy) орнату немесе оны көлеңкелі/салқын бөлмеге көшіру.", "Желдеткіштерді тексеру, шаңынан тазарту, бұзылған болса ауыстыру.", "Инвертордың айналасында ауа айналымы үшін кем дегенде 30-50 см бос орын қалдыру."] if lang == "kk" else ["Install a sunshade canopy over outdoor inverters or relocate to a cool, shaded area.", "Clean heatsink fins and ensure cooling fans rotate freely.", "Maintain required clearances (30-50 cm) around the chassis for heat dissipation."]
            }
        elif "Offline" in selected_symptom or "Offline" in selected_symptom:
            diag_data = {
                "severity": " Info / Ақпараттық",
                "color": "#0dcaf0",
                "meaning": "Күн станциясы жұмыс істеп тұрса да, оның телеметрия деректері Solarman серверіне жетпейді. Дашбордта өнімділік нөл немесе құрылғы 'Offline' болып көрінеді." if lang == "kk" else "Data logger (Wi-Fi/4G stick) cannot upload telemetry data. The dashboard shows zero generation or an offline warning, though the system may still run.",
                "causes": ["Жергілікті Wi-Fi роутердің өшіп қалуы немесе интернеттің жоғалуы.", "Data Logger стигі мен инвертор портының (COM) арасындағы контактінің нашарлауы.", "Logger стигінің бұзылуы немесе прошивкасының ескіруі."] if lang == "kk" else ["Local Wi-Fi router outage or cellular internet signal loss.", "Loose connection between data logger stick and inverter COM port.", "Data logger hardware failure or outdated firmware."],
                "actions": ["Жергілікті Wi-Fi желісінің жұмысын және интернет жылдамдығын тексеру.", "Data Logger стигін инвертордан суырып, контактілерін тазалап қайта тығыз қосу.", "Стиктегі индикаторлық жарықтардың (LED) күйін тексеру (мысалы, Link немесе NET шамдары жасыл түспен жыпылықтап тұруы керек)."] if lang == "kk" else ["Verify local Wi-Fi router power status and internet connectivity.", "Unplug and firmly re-seat the data logger stick into the inverter's COM/RS-485 port.", "Inspect status LEDs (NET/Link status) on the logger stick to verify cloud sync status."]
            }
        elif "Smart Meter" in selected_symptom or "Smart" in selected_symptom:
            diag_data = {
                "severity": " Warning / Ескерту",
                "color": "#ffc107",
                "meaning": "Интеллектуалды есептегіштің (Smart Meter) немесе оған қосылған ток өлшегіш қысқыштардың (CT Clamp) қате орнатылуы. Нәтижесінде дашбордта өндірілген энергия тұтыну ретінде, ал тұтыну өндіріс ретінде қате статистикамен көрсетіледі." if lang == "kk" else "Smart meter or Current Transformer (CT) clamps are installed incorrectly, causing production and consumption statistics to swap, showing reversed metrics.",
                "causes": ["CT Clamp қысқышын сымға өткізгенде бағыт нұсқағышын (K->L немесе Source->Load) теріс қаратып орнату.", "Инвертор немесе есептегіш баптауларында CT қатынасының (Ratio) қате таңдалуы.", "Метр кабельдерінің фазаларының (L1, L2, L3) араласып кетуі."] if lang == "kk" else ["CT clamps oriented backwards on phase conductors (K->L arrow pointing to grid instead of load).", "Incorrect CT turns ratio programmed in the meter or inverter.", "Phase rotation mismatch between meter voltage taps and CT clamp phases."],
                "actions": ["CT Clamp қысқыштарының үстіндегі бағыт көрсеткішін тексеріп, оны желіден тұтынушыға қарай (немесе нұсқаулық бойынша) бағыттау.", "Ток өлшегіш сымдардың тиісті фазалық терминалдарға (L1, L2, L3) дұрыс қосылғанын тексеру.", "Метр мен инвертор арасындағы RS485 байланыс кабельдерінің оң/теріс (A/B) полярлығын тексеру."] if lang == "kk" else ["Verify CT clamp orientation arrows and flip them if they are reversed.", "Match CT clamp phases exactly with voltage reference phase connections.", "Ensure RS-485 polarities (A+ and B-) match between the meter and the inverter."]
            }
        
        st.markdown(f"""
        <div style="border: 2px solid {diag_data['color']}; border-radius: 10px; padding: 20px; margin-top: 15px; background-color: rgba(22, 27, 34, 0.6);">
            <h4 style="margin-top:0; color:{diag_data['color']};"> {selected_symptom.split('(')[0].strip()}</h4>
            <p><strong> {"Severity / Қауіптілік деңгейі" if lang == "kk" else "Severity Level"}:</strong> {diag_data['severity']}</p>
            <p><strong> {"Meaning / Мағынасы" if lang == "kk" else "Meaning"}:</strong><br>{diag_data['meaning']}</p>
        </div>
        """, unsafe_allow_html=True)
    
        col_c, col_a = st.columns(2)
        with col_c:
            with st.container(border=True):
                st.markdown(f"** {'Ықтимал себептері' if lang == 'kk' else 'Potential Causes'}**")
                for cause in diag_data["causes"]:
                    st.markdown(f"- {cause}")
        with col_a:
            with st.container(border=True):
                st.markdown(f"** {'Шешу жолдары мен кеңестер' if lang == 'kk' else 'Troubleshooting Actions'}**")
                for action in diag_data["actions"]:
                    st.markdown(f"- {action}")

    # ------------------ TELEMETRY-BASED DIAGNOSTICS & LOSS ANALYSIS ------------------
    st.markdown("---")
    st.markdown(icon_text("analysis", "Telemetry-Based Diagnostics" if lang == "en" else "Телеметрия негізіндегі диагностика", size=18, as_heading=True, level=4), unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:#8b949e;">{"Analyze power loss, temperature degradation, and soiling using current Solarman inverter data." if lang == "en" else "Ағымдағы Solarman инвертор деректерін қолдана отырып, қуат шығынын, температуралық деградацияны және ластануды талдаңыз."}</p>',
        unsafe_allow_html=True
    )

    # Get telemetry data
    sm_dc_cap = st.session_state.get("sm_dc_cap_val", 50.0)
    sm_irrad = st.session_state.get("sm_irrad_val", 900)
    sm_amb_temp = st.session_state.get("sm_amb_temp_val", 30)
    sm_module_temp = st.session_state.get("sm_module_temp_val", 38)
    sm_active_power = st.session_state.get("sm_active_power_val", 42.5)

    # Calculate expected power
    # Standard temp coefficient is -0.4% per deg C above 25C module temp
    temp_coef = -0.004
    temp_diff = max(0.0, sm_module_temp - 25.0)
    temp_loss_pct = temp_diff * 0.4 * 100.0
    temp_multiplier = 1.0 + (temp_coef * temp_diff)

    # Theoretical DC output under current irradiation (no temperature loss)
    theoretical_dc_no_temp = sm_dc_cap * (sm_irrad / 1000.0)
    # Expected output after temperature losses
    expected_dc_output = theoretical_dc_no_temp * temp_multiplier

    # Real-time system efficiency (Performance Ratio relative to current expected)
    if expected_dc_output > 0:
        actual_pr = (sm_active_power / expected_dc_output) * 100.0
    else:
        actual_pr = 0.0
    
    # Render UI layout
    col_t1, col_t2 = st.columns([1, 1])

    with col_t1:
        st.markdown(f"** {'Ағымдағы Solarman телеметриясы' if lang == 'kk' else 'Current Solarman Telemetry'}**")
        st.write(f"- **{'Номиналды қуат' if lang == 'kk' else 'DC Capacity'}:** {sm_dc_cap:.1f} kWp")
        st.write(f"- **{'Күн сәулесі' if lang == 'kk' else 'Irradiation'}:** {sm_irrad:.0f} W/m²")
        st.write(f"- **{'Панель температурасы' if lang == 'kk' else 'Module Temp'}:** {sm_module_temp:.1f} °C")
        st.write(f"- **{'Нақты өндіріс' if lang == 'kk' else 'Actual Output'}:** {sm_active_power:.1f} kW")
    
        # Expected outputs
        st.write(f"- **{'Температурасыз теориялық' if lang == 'kk' else 'Theoretical DC (STC)'}:** {theoretical_dc_no_temp:.2f} kW")
        st.write(f"- **{'Температуралық шығынмен күтілетін' if lang == 'kk' else 'Expected DC Output'}:** {expected_dc_output:.2f} kW")
    
    with col_t2:
        st.markdown(f"** {'Тиімділік және Жүйелік талдау' if lang == 'kk' else 'System Efficiency Analysis'}**")
    
        # Display gauge / text color based on efficiency
        if actual_pr >= 80.0:
            status_text = " Жақсы жұмыс істеп тұр / Optimal Performance" if lang == "kk" else " Optimal Performance"
            status_color = "#2ea44f"
            loss_desc = "Жүйе қалыпты және таза күйде жұмыс істеуде. Жалпы шығындар қалыпты деңгейде." if lang == "kk" else "System runs optimally under current conditions. Normal losses only."
        elif 70.0 <= actual_pr < 80.0:
            status_text = " Жеңіл ластану / Light Soiling & Dust" if lang == "kk" else " Light Soiling & Dust"
            status_color = "#ffc107"
            loss_desc = "Өнімділік сәл төмендеген. Панельдерде жеңіл шаң қабаты немесе ішінара көлеңке болуы мүмкін (5-15% қуат жоғалту)." if lang == "kk" else "Slight drop in efficiency. Likely due to thin dust layer or minor shading (5-15% loss)."
        elif 50.0 <= actual_pr < 70.0:
            status_text = " Орташа және жоғары ластану / Moderate to Heavy Soiling" if lang == "kk" else " Moderate to Heavy Soiling"
            status_color = "#fd7e14"
            loss_desc = "Қуат өндірісі айтарлықтай төмен! Панельдерді шаң мен кірден жуу ұсынылады (15-30% қуат жоғалту)." if lang == "kk" else "Washing panels is recommended to recover 15-30% loss."
        else:
            status_text = " Ақаулық немесе Жоғары кедергі / Critical Outage or Obstruction" if lang == "kk" else " Critical Outage or Obstruction"
            status_color = "#dc3545"
            loss_desc = "Экстремалды қуат жоғалту! Жүйедегі ақауды (тізбектің өшуі, инвертордың қызып кетуі немесе қалың көлеңке/кір) шұғыл тексеріңіз." if lang == "kk" else "Critical drop in power! Check for string disconnects, shading, inverter faults, or thick dirt/snow."
        
        st.markdown(f"""
        <div style="background-color:rgba(22, 27, 34, 0.5); padding: 15px; border-radius:10px; border-left: 5px solid {status_color};">
            <h5 style="margin-top:0; color:{status_color};">{status_text}</h5>
            <p style="font-size:1.6rem; font-weight:800; margin: 10px 0;">Efficiency: {actual_pr:.1f}%</p>
            <p style="font-size:0.9rem; color:#8b949e; margin-bottom:0;">{loss_desc}</p>
        </div>
        """, unsafe_allow_html=True)
    
        # Breakdown of losses
        st.write("")
        st.markdown(f"** {'Шығындар құрамы' if lang == 'kk' else 'Estimated Loss Breakdown'}**")
        st.write(f"-  **{'Температуралық шығын' if lang == 'kk' else 'Temperature degradation loss'}:** {temp_loss_pct:.1f}%")
        system_loss = max(0.0, 100.0 - actual_pr - temp_loss_pct)
        st.write(f"-  **{'Ластану және өзге шығындар' if lang == 'kk' else 'Soiling, shading & inverter losses'}:** {system_loss:.1f}%")

    # ------------------ AI IMAGE-BASED DUST/SOILING DETECTION ------------------
    st.markdown("---")
    st.markdown(f'<h4>{" AI Image-Based Soiling & Fault Detection" if lang == "en" else " Интеллектуалды сурет талдау жүйесі (Шаң/Ақаулықтар)"}</h4>', unsafe_allow_html=True)
    st.markdown(
        f'<p style="color:#8b949e;">{"Upload a photo of a solar panel to analyze faults using our ResNet50 and YOLOv11 AI models." if lang == "en" else "Күн панелінің фотосуретін жүктеп, оны ResNet50 немесе YOLOv11 модельдері арқылы шаң немесе ақаулықтарға талдаңыз."}</p>',
        unsafe_allow_html=True
    )

    # Model selection
    model_choice = st.radio(
        "Диагностикалық модельді таңдаңыз / Select Diagnostic Model:" if lang == "kk" else "Select Diagnostic Model:",
        [
            "ResNet50 Classifier (Clean/Dirty)" if lang == "en" else "ResNet50 Классификаторы (Таза/Лас)",
            "YOLOv11 Object Detector (6-class Faults)" if lang == "en" else "YOLOv11 Объект детекторы (6-ақау түрі)"
        ],
        horizontal=True
    )

    uploaded_file = st.file_uploader(
        "Күн панелінің суретін жүктеңіз / Upload Solar Panel Image:" if lang == "kk" else "Upload Solar Panel Image:",
        type=["jpg", "jpeg", "png"],
        key="soiling_image_uploader"
    )

    if uploaded_file is not None:
        col_img, col_pred = st.columns([1, 1])
        with col_img:
            st.image(uploaded_file, caption="Жүктелген сурет / Uploaded Image" if lang == "kk" else "Uploaded Image", width='stretch')
    
        with col_pred:
            if st.button("Диагностиканы бастау / Start AI Diagnosis" if lang == "kk" else "Start AI Diagnosis", width='stretch'):
                with st.spinner("Модель жүктелуде және сурет талдануда... / Analyzing image..."):
                    try:
                        import cv2
                        import numpy as np
                        from PIL import Image
                    
                        if "ResNet50" in model_choice:
                            import tensorflow as tf
                            # Load model from cache
                            model = load_clean_dirty_model()
                        
                            # Open and preprocess image
                            img = Image.open(uploaded_file).convert("RGB")
                            img_resized = img.resize((224, 224))
                            img_array = tf.keras.preprocessing.image.img_to_array(img_resized)
                            img_array = tf.expand_dims(img_array, 0)
                        
                            # Preprocess input using ResNet50 preprocess_input
                            preprocessed_img = tf.keras.applications.resnet50.preprocess_input(img_array)
                        
                            # Run prediction
                            predictions = model.predict(preprocessed_img)
                            probs = predictions[0]
                        
                            clean_prob = float(probs[0]) * 100
                            dirty_prob = float(probs[1]) * 100
                        
                            st.markdown(f"##### ** {'Талдау нәтижесі' if lang == 'kk' else 'Analysis Result'}:**")
                        
                            # Clean vs Dirty progress bars
                            st.write(f"{'Таза панель' if lang == 'kk' else 'Clean panel'}: {clean_prob:.2f}%")
                            st.progress(clean_prob / 100.0)
                        
                            st.write(f"{'Шаң/Лас панель' if lang == 'kk' else 'Dusty/Dirty panel'}: {dirty_prob:.2f}%")
                            st.progress(dirty_prob / 100.0)
                        
                            if clean_prob > dirty_prob:
                                st.success(
                                    f" **Панель таза! / Panel is Clean!** (Сенімділік / Confidence: {clean_prob:.2f}%)"
                                    if lang == "kk" else
                                    f" **Panel is Clean!** (Confidence: {clean_prob:.2f}%)"
                                )
                            else:
                                st.warning(
                                    f" **Панель шаң басқан немесе ластанған! / Panel is Dusty or Dirty!** (Сенімділік / Confidence: {dirty_prob:.2f}%)\n\n"
                                    " **Ұсыныс / Recommendation:** Панель бетінде шаң немесе кір жиналған. Өнімділікті 10-30%-ға арттыру үшін панель бетін жуу ұсынылады."
                                    if lang == "kk" else
                                    f" **Panel is Dusty or Dirty!** (Confidence: {dirty_prob:.2f}%)\n\n"
                                    " **Recommendation:** Dust or dirt has accumulated. Cleaning the panels is recommended to restore 10-30% of lost generation."
                                )
                        else:
                            # Load YOLO model
                            yolo_model = load_yolo_model()
                        
                            # Open PIL image
                            img = Image.open(uploaded_file).convert("RGB")
                        
                            # Predict using YOLOv11-nano
                            results = yolo_model.predict(img, conf=0.25)
                        
                            # Plot bounding boxes
                            plotted_img = results[0].plot() # numpy array BGR
                            plotted_img_rgb = cv2.cvtColor(plotted_img, cv2.COLOR_BGR2RGB)
                        
                            # Display annotated image
                            st.image(plotted_img_rgb, caption="YOLOv11 Диагностика нәтижесі / YOLOv11 Diagnosis Result" if lang == "kk" else "YOLOv11 Diagnosis Result", width='stretch')
                        
                            boxes = results[0].boxes
                            if boxes is None or len(boxes) == 0:
                                st.success(
                                    " **Ешқандай ақаулық анықталған жоқ! / No faults detected!**"
                                    if lang == "kk" else
                                    " **No faults detected!**"
                                )
                            else:
                                st.markdown(f"##### ** {'Анықталған ақаулықтар' if lang == 'kk' else 'Detected Faults'}:**")
                                detected_names = []
                                for box in boxes:
                                    cls_id = int(box.cls[0])
                                    conf = float(box.conf[0]) * 100
                                    name = yolo_model.names[cls_id]
                                    detected_names.append(name)
                                    st.write(f"-  **{name}** (Сенімділік / Confidence: {conf:.1f}%)")
                                
                                # Recommendations
                                st.markdown(f"##### ** {'AI Ұсыныстар' if lang == 'kk' else 'AI Recommendations'}:**")
                                unique_detections = set(detected_names)
                                for det in unique_detections:
                                    if det == "Dust" or det == "Bird":
                                        st.info(" **Dust / Bird:** Панель беті кірлеген. Оны таза сумен жуу арқылы өнімділікті қалпына келтіріңіз." if lang == "kk" else " **Dust / Bird:** Panel surface is soiled. Wash with clean water to restore yield.")
                                    elif det == "Physical":
                                        st.warning(" **Physical:** Панельде механикалық зақым немесе сызаттар байқалды. Физикалық бүлінулер өрт қаупін тудыруы мүмкін." if lang == "kk" else " **Physical:** Physical damage or cracks detected on modules. High risk of hot spots/fire.")
                                    elif det == "Electrical":
                                        st.error(" **Electrical:** Электрлік қосылыстарда немесе тізбектерде ақау анықталды. Кабельдер мен коннекторларды тексеріңіз." if lang == "kk" else " **Electrical:** Electrical anomaly detected. Inspect junction boxes, cabling, and connections.")
                                    elif det == "Snow":
                                        st.info(" **Snow:** Панель бетіне қар жиналған. Сақтық шараларын сақтай отырып, қарды тазалаңыз." if lang == "kk" else " **Snow:** Panel surface is covered in snow. Carefully sweep it off.")
                                    elif det == "Clean":
                                        st.success(" **Clean:** Панельдің таза бөлігі немесе таза панельдер анықталды." if lang == "kk" else " **Clean:** Clean panel surfaces detected.")
                                    
                    except Exception as ex:
                        st.error(f"Қате орын алды / Error: {str(ex)}")

    # ------------------ KNOWLEDGE BASE ACCORDIONS ------------------
    st.markdown("---")
    st.markdown(f'<h4>{" Solar Diagnostics Knowledge Base" if lang == "en" else " Күн станциялары ақауларының білім қоры"}</h4>', unsafe_allow_html=True)

    with st.expander(" 1. Физикалық және сыртқы кедергілер (Physical & External Obstacles)", expanded=False):
        st.markdown("""
        *   **Ластану және шаң (Soiling):** Панель бетіне шаң, құм немесе құс саңғырығының жиналуы. Жұқа шаң қабаты өнімділікті 10-15%-ға, ал қатты ластану 30%-дан астамға төмендетеді. 
            *   *Шешімі:* Салқын кезде (таңертең/кешке) таза сумен жуу.
        *   **Көлеңке түсуі (Shading):** Ағаштар, ғимараттар немесе мұржалардың көлеңкесі. Тіпті кішкене көлеңке бүкіл тізбектің (string) өнімділігін күрт төмендетеді.
            *   *Шешімі:* Бұтақтарды кесу, Bypass диодтарын тексеру немесе Тіго оптимизаторларын орнату.
        *   **Микрожарықтар (Microcracks):** Кремний элементтеріндегі көзге көрінбейтін жарықтар. Тасымалдау немесе бұршақ соққысынан болады.
            *   *Шешімі:* Ақаулы панельдерді тестілеп, қажет болса ауыстыру.
        *   **Ыстық нүктелер (Hot Spots):** Ұяшықтың өндіру орнына энергия тұтынып, қатты қызып кетуі (өрт қаупі бар).
            *   *Шешімі:* Тепловизормен тексеру, диодтарды ауыстыру.
        *   **PID деградациясы (Potential Induced Degradation):** Жерге тұйықтау мен элементтер арасындағы жоғары кернеуден болатын деградация.
            *   *Шешімі:* Жерге тұйықтау сапасын арттыру, Anti-PID блоктарын орнату.
        """)
    
    with st.expander(" 2. Инвертор және Жүйелік ақаулар (Inverter & System Faults)", expanded=False):
        st.markdown("""
        *   **MPPT қатесі (Maximum Power Point Tracking):** Инвертордың күн сәулесіне сай ең тиімді кернеуді таңдау алгоритмінің бұзылуы.
        *   **Grid Over/Under Voltage (Желі кернеуінің қатесі):** Сыртқы желідегі кернеудің тұрақсыздығы. Инвертор қауіпсіздік үшін өшіп қалады.
            *   *Шешімі:* Шығыс AC кабелін қалыңдату немесе инвертордың қорғаныс шектерін кеңейту.
        *   **Insulation Resistance Fault (Оқшаулау кедергісі):** Кабель зақымдалып немесе ылғал кіріп, қысқа тұйықталу қаупінің туындауы.
            *   *Шешімі:* DC сымдарын мультиметрмен өлшеп, ақаулы коннекторды ауыстыру.
        *   **Қатты қызып кету (Overheating):** Инвертор температурасының көтерілуінен қуаттың шектелуі (derating).
            *   *Шешімі:* Инвертор үстіне көлеңке қалқа орнату, желдеткішін тазалау.
        """)
    
    with st.expander(" 3. Электрлік қосылыстар мен Кабель ақаулары (Electrical & Connections)", expanded=False):
        st.markdown("""
        *   **MC4 коннекторларының нашарлауы:** Байланыстың нашар болуы немесе ылғалдану қарсылықты арттырып, қызып кетуге және энергия жоғалтуға әкеледі.
            *   *Шешімі:* Коннекторларды дұрыс қысу және су өткізбейтін етіп оқшаулау.
        *   **Кабель қимасының дұрыс таңдалмауы:** Кабель тым жұқа немесе тым ұзын болса, кернеудің жоғалуы (Voltage drop) артады.
            *   *Шешімі:* Жобалық кабель қимасын есептеп, сәйкес кабельді таңдау.
        *   **Тізбектегі сәйкессіздік (String Mismatch):** Бір тізбекке қуаттары әртүрлі панельдер қосылса, бүкіл тізбек ең әлсіз панельдин жылдамдығымен жұмыс істейді.
            *   *Шешімі:* Бір тізбекке тек бірдей маркалы және бірдей қуатты панельдерді біріктіру.
        """)
    
    with st.expander(" 4. Мониторинг және Байланыс ақаулары (Monitoring & Data Logs)", expanded=False):
        st.markdown("""
        *   **Data Logger стигінің байланыс үзілуі (Offline):** Wi-Fi/4G сигналының нашарлығынан мәліметтердің Solarman серверіне жетпей қалуы.
            *   *Шешімі:* Роутерді тексеру, стикті суырып қайта салу, индикатор шамдарын тексеру.
        *   **Smart Meter / CT Clamp теріс орнатылуы:** Өндіріс пен тұтыну статистикасының араласып кетуі.
            *   *Шешімі:* Ток өлшегіш қысқыштардың бағытын (K->L нұсқағышын) тексеріп, дұрыстап бұрау.
        """)

    with st.expander(" 5. Ақауды қалай анықтауға болады? (How to Detect Faults)", expanded=False):
        st.markdown("""
        *   **Solarman-дегі Alerts немесе Faults бөлімін бақылау:** Онда нақты қате коды (мысалы, Grid Fault, Isolation Fault) жазылады.
        *   **Күнделікті өнімділік қисық сызығын (Yield Curve) бақылау:** Кенет төмендеу болса — көлеңке немесе желі сөнуі. Күн ашық кезде де өндіріс өте төмен болса — қатты ластану немесе инвертордың қызып кетуі (derating).
        """)

