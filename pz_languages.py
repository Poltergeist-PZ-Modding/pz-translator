import os
import json

TranslationCodes = {
    'AR': "es",
    'CA': "ca",
    'CH': "zh-tw",
    'CN': "zh-cn",
    'CS': "cs",
    'DA': "da",
    'DE': "de",
    'EN': "en",
    'ES': "es",
    'FI': "fi",
    'FR': "fr",
    'HU': "hu",
    'ID': "id",
    'IT': "it",
    'JP': "ja",
    'KO': "ko",
    'NL': "nl",
    'NO': "no",
    'PH': "tl",
    'PL': "pl",
    'PT': "pt",
    'PTBR': "pt",
    'RO': "ro",
    'RU': "ru",
    'TH': "th",
    'TR': "tr",
    'UA': "uk",
}

Aliases = {
    'AR': ['Espanol (AR)'],
    'CA': ['Catalan'],
    'CH': ['Traditional Chinese'],
    'CN': ['Simplified Chinese'],
    'CS': ['Czech'],
    'DA': ['Danish'],
    'DE': ['Deutsch'],
    'EN': ['English'],
    'ES': ['Espanol (ES)'],
    'FI': ['Finnish'],
    'FR': ['Francais'],
    'HU': ['Hungarian'],
    'ID': ['Indonesia'],
    'IT': ['Italiano'],
    'JP': ['Japanese'],
    'KO': ['Korean'],
    'NL': ['Nederlands'],
    'NO': ['Norsk'],
    'PH': ['Tagalog'],
    'PL': ['Polish'],
    'PT': ['Portuguese'],
    'PTBR': ['Brazilian Portuguese'],
    'RO': ['Romanian'],
    'RU': ['Russian'],
    'TH': ['Thai'],
    'TR': ['Turkish'],
    'UA': ['Ukrainian'],
}

def getTranslateDir():
    from configparser import ConfigParser
    config = ConfigParser()
    config.read("config.ini")
    return config["directories"]["PZTranslateDir"]

# uses scriptblock - need improvement
def readLanguageFile(filePath: str):
    try:
        with open(filePath,"r") as f:
            d = {}
            for line in f:
                for it in line.split(","):
                    if "=" in it:
                        key, value = it.split("=",1)
                        key = key.strip()
                        value = value.strip()
                        d[key] = value
            # print(d)
            if all(x in d for x in ["text", "charset"]) and d["VERSION"] == "1":
                return d
            else:
                return None
    except:
        return None

# FIXME: Catalan has encoding issues - switch to Cp1252?
def generateLanguagesInfo():
    all = {}
    translateDir = getTranslateDir()
    with os.scandir(translateDir) as tDir:
        for each in tDir:
            if each.is_dir():
                d = readLanguageFile(os.path.join(translateDir,each.name,"language.txt"))
                if not d:
                    continue
                d["id"] = each.name
                d["translate"] = TranslationCodes[each.name]
                all[each.name] = sorted(d.items())
                # print("'"+ each.name + "': ['" + d["text"].lower() + "'],")
                # print("| " + each.name + " | " + d["text"] + " | " + d["charset"] + " |")
    return all

def getLanguages(generate: bool):
    LanguagesPath = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LanguagesInfo.json")
    if generate or not os.path.isfile(LanguagesPath):
        d = generateLanguagesInfo()
        with open(LanguagesPath,"w",encoding="utf-8") as f:
            json.dump(d,f,indent=2)
        return d
    else:
        with open(LanguagesPath,"r",encoding="utf-8") as f:
            return json.load(f)
