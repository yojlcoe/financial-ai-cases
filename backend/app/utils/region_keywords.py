"""Region-based keyword mapping utility."""
from typing import List, Optional


def get_keywords_by_region(region: Optional[str]) -> List[str]:
    """
    Get search keywords based on region/language code.

    Args:
        region: Region code in format "country-language" (e.g., "jp-jp", "us-en")
                If None or empty, returns default English keywords.

    Returns:
        List of keywords appropriate for the region/language
    """
    if not region:
        return ["AI", "generative AI", "agentic AI", "digital transformation", "automation", "case study"]

    # Extract language code from region (format: country-language)
    lang_code = region.split("-")[1] if "-" in region else "en"

    # Language-specific keyword mappings
    keywords_map = {
        "jp": ["AI", "生成AI", "AIエージェント", "DX", "デジタル", "自動化", "事例"],
        "zh": ["AI", "生成式AI", "智能代理", "人工智能", "数字化转型", "自动化", "案例"],
        "tzh": ["AI", "生成式AI", "智能代理", "人工智慧", "數位轉型", "自動化", "案例"],
        "ko": ["AI", "생성형 AI", "에이전틱 AI", "인공지능", "디지털 전환", "자동화", "사례"],
        "es": ["AI", "IA generativa", "IA agéntica", "inteligencia artificial", "transformación digital", "automatización", "caso de estudio"],
        "pt": ["AI", "IA generativa", "IA agêntica", "inteligência artificial", "transformação digital", "automação", "estudo de caso"],
        "fr": ["AI", "IA générative", "IA agentique", "intelligence artificielle", "transformation numérique", "automatisation", "étude de cas"],
        "de": ["AI", "generative KI", "agentische KI", "künstliche Intelligenz", "digitale Transformation", "Automatisierung", "Fallstudie"],
        "it": ["AI", "IA generativa", "IA agentica", "intelligenza artificiale", "trasformazione digitale", "automazione", "caso di studio"],
        "nl": ["AI", "generatieve AI", "agentische AI", "kunstmatige intelligentie", "digitale transformatie", "automatisering", "casestudy"],
        "sv": ["AI", "generativ AI", "agentisk AI", "artificiell intelligens", "digital transformation", "automatisering", "fallstudie"],
        "da": ["AI", "generativ AI", "agentisk AI", "kunstig intelligens", "digital transformation", "automatisering", "casestudie"],
        "no": ["AI", "generativ AI", "agentisk AI", "kunstig intelligens", "digital transformasjon", "automatisering", "case study"],
        "fi": ["AI", "generatiivinen tekoäly", "agenttitekoäly", "tekoäly", "digitaalinen muutos", "automaatio", "tapaustutkimus"],
        "pl": ["AI", "generatywna AI", "agentowa AI", "sztuczna inteligencja", "transformacja cyfrowa", "automatyzacja", "studium przypadku"],
        "ru": ["AI", "генеративный ИИ", "агентный ИИ", "искусственный интеллект", "цифровая трансформация", "автоматизация", "кейс"],
        "ar": ["AI", "الذكاء الاصطناعي التوليدي", "الذكاء الاصطناعي الوكيل", "الذكاء الاصطناعي", "التحول الرقمي", "الأتمتة", "دراسة حالة"],
        "th": ["AI", "AI สร้างสรรค์", "AI แบบเอเจนต์", "ปัญญาประดิษฐ์", "การเปลี่ยนแปลงดิจิทัล", "ระบบอัตโนมัติ", "กรณีศึกษา"],
        "vi": ["AI", "AI sinh tạo", "AI tác nhân", "trí tuệ nhân tạo", "chuyển đổi số", "tự động hóa", "nghiên cứu điển hình"],
        "id": ["AI", "AI generatif", "AI agentik", "kecerdasan buatan", "transformasi digital", "otomasi", "studi kasus"],
        "ms": ["AI", "AI generatif", "AI agentik", "kecerdasan buatan", "transformasi digital", "automasi", "kajian kes"],
        "tl": ["AI", "generative AI", "agentic AI", "artipisyal na katalinuhan", "digital transformation", "automation", "case study"],
        "he": ["AI", "בינה מלאכותית יוצרת", "בינה מלאכותית סוכנית", "בינה מלאכותית", "טרנספורמציה דיגיטלית", "אוטומציה", "מקרה בוחן"],
        "tr": ["AI", "üretken yapay zeka", "ajantik yapay zeka", "yapay zeka", "dijital dönüşüm", "otomasyon", "vaka çalışması"],
        "cs": ["AI", "generativní AI", "agentní AI", "umělá inteligence", "digitální transformace", "automatizace", "případová studie"],
        "sk": ["AI", "generatívna AI", "agentná AI", "umelá inteligencia", "digitálna transformácia", "automatizácia", "prípadová štúdia"],
        "hu": ["AI", "generatív AI", "ágensalapú AI", "mesterséges intelligencia", "digitális átalakulás", "automatizálás", "esettanulmány"],
        "ro": ["AI", "AI generativă", "AI agentică", "inteligență artificială", "transformare digitală", "automatizare", "studiu de caz"],
        "bg": ["AI", "генеративен изкуствен интелект", "агентен изкуствен интелект", "изкуствен интелект", "дигитална трансформация", "автоматизация", "казус"],
        "hr": ["AI", "generativna AI", "agentna AI", "umjetna inteligencija", "digitalna transformacija", "automatizacija", "studija slučaja"],
        "sl": ["AI", "generativna umetna inteligenca", "agentna umetna inteligenca", "umetna inteligenca", "digitalna transformacija", "avtomatizacija", "študija primera"],
        "et": ["AI", "generatiivne tehisintellekt", "agentpõhine tehisintellekt", "tehisintellekt", "digitaalne transformatsioon", "automatiseerimine", "juhtumiuuring"],
        "lv": ["AI", "ģeneratīvais mākslīgais intelekts", "aģentu mākslīgais intelekts", "mākslīgais intelekts", "digitālā transformācija", "automatizācija", "gadījuma izpēte"],
        "lt": ["AI", "generatyvinis dirbtinis intelektas", "agentinis dirbtinis intelektas", "dirbtinis intelektas", "skaitmeninė transformacija", "automatizavimas", "atvejo tyrimas"],
        "el": ["AI", "γεννητική τεχνητή νοημοσύνη", "πρακτορική τεχνητή νοημοσύνη", "τεχνητή νοημοσύνη", "ψηφιακός μετασχηματισμός", "αυτοματοποίηση", "μελέτη περίπτωσης"],
        "uk": ["AI", "генеративний штучний інтелект", "агентний штучний інтелект", "штучний інтелект", "цифрова трансформація", "автоматизація", "кейс"],
        "ca": ["AI", "IA generativa", "IA agèntica", "intel·ligència artificial", "transformació digital", "automatització", "estudi de cas"],
    }

    # Return keywords for the language, defaulting to English if not found
    return keywords_map.get(lang_code, ["AI", "generative AI", "agentic AI", "digital transformation", "automation", "case study"])
