from Logger import Log


class LanguageManager:
    text = {
        "en": {
            "welcome_label": "Welcome to\nAutomatic Beer Tap Machine",
            "info_label": "System is initializing, please ensure\na wired internet connection.",
            "prompt_label": "Please select a beer and\nbring your glass under the tap.",
            "error_label": "Oops, an error occurred.\n\n%s",
            "pouring_label": "Your beer is being poured,\nplease wait.",
            "pouring_finished_label": "Glass successfully poured,\nplease remove it from the tap.\n\nCheers!",
            "remaining_balance_label": "Remaining balance: %s€",
            "beer.title": "%s",
            "beer.style": "%s",
            "beer.abv": "%s%% ABV",
            "beer.ebc": "%s EBC",
            "beer.ibu": "Bitterness: %s",
            "beer.kcal": "%s kcal / 100ml",
            "beer.price": "%s€ / liter",
            "error.GENERAL_ERROR": "Unexpected error happened. Please reach out to system administrator.",
            "error.GLASS_REMOVED_PREMATURELY": "Your glass was removed prematurely. You have been charged only for poured beer.",
            "error.INSUFFICIENT_BALANCE": "Your glass does not have sufficient funds to pour the whole glass of beer.",
            "error.GLASS_NOT_RECOGNIZED": "Your glass is not yet registered in our system, please turn to cashier for help.",
            "error.KEG_EMPTY": "Beer keg you are trying to pour is empty. We apologise for any inconvenience.",
            "error.TAP_NOT_CONNECTED": "Beer keg you are trying to pour is not connected to the system.",
            "error.LOCAL_NETWORK_PROBLEM": "There seems to be a problem with network. Please ensure a wired internet connection."
        },
        "sl": {
            "welcome_label": "Dobrodošli v avtomatskem\ntočilnem stroju za pivo",
            "info_label": "Sistem se zaganja, počakajte...\n\nPrenos podatkov zahteva\nstabilno internetno povezavo.",
            "prompt_label": "Prosimo izberite pivo in\npristavite svoj kozarec pod točilno mesto.",
            "error_label": "Ups, pojavila se je napaka.\n\n%s",
            "pouring_label": "Vaše pivo se toči,\nprosimo počakajte trenutek.",
            "pouring_finished_label": "Pivo je natočeno.\nKozarec lahko odstranite izpod točilnega mesta.\n\nNa zdravje!",
            "remaining_balance_label": "Preostalo dobroimetje: %s€",
            "beer.title": "%s",
            "beer.style": "%s",
            "beer.abv": "%s%% ABV",
            "beer.ebc": "%s EBC",
            "beer.ibu": "Grenkoba: %s",
            "beer.kcal": "%s kcal / 100ml",
            "beer.price": "%s€ / liter",
            "error.GENERAL_ERROR": "Zgodila se je nepričakovana napaka. Prosimo obrnite se na administratorja sistema",
            "error.GLASS_REMOVED_PREMATURELY": "Vaš kozarec je bil odstavljen prehitro. Zaračunali smo vam samo natočeno količino.",
            "error.INSUFFICIENT_BALANCE": "Vaš kozarec nima zadostnega dobroimetja za točenje polnega kozarca izbranega piva.",
            "error.GLASS_NOT_RECOGNIZED": "Vaš kozarec še ni zabeležen v našem sistemu, prosimo obrnite se na blagajničarja.",
            "error.KEG_EMPTY": "Sod piva, iz katerega poskušate točiti, je prazen. Prosimo izberite drugo vrsto piva.",
            "error.TAP_NOT_CONNECTED": "Sod piva, iz katerega poskušate točiti, ni priključen na sistem.",
            "error.LOCAL_NETWORK_PROBLEM": "Zdi se, da je prišlo do težave z omrežjem. Prosimo, zagotovite žično internetno povezavo."
        }
    }
    default_language = "en"  # Default language is English
    current_language = default_language

    @staticmethod
    def set_language(language):
        if language is None:
            return
        # Set the current language (according to two-letter ISO 639-1 code)
        if language in LanguageManager.text:
            LanguageManager.current_language = language
        else:
            Log.error(f"Language '{language}' is not supported, using en as default.")
            LanguageManager.current_language = LanguageManager.default_language

    @staticmethod
    def get_text_for_language(key, language):
        # Get text in the current language for the given key
        if key in LanguageManager.text[language]:
            return LanguageManager.text[language][key]
        else:
            if language != LanguageManager.default_language:
                Log.warn(f"Text with key '{key}' not configured for language '{language}'. "
                         f"Trying default language '{LanguageManager.default_language}'.")
                return LanguageManager.get_text_for_language(key, LanguageManager.default_language)
            else:
                Log.error(f"Text with key '{key}' not configured for language '{language}'. Check implementation.")
                return None

    @staticmethod
    def get_text(key):
        return LanguageManager.get_text_for_language(key, LanguageManager.current_language)

    @staticmethod
    def get_text_with_parameter(key, parameter: str):
        text = LanguageManager.get_text(key)
        if text is not None and "%s" in text:
            return text % parameter
        return text
