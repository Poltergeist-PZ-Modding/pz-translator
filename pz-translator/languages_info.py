"""
Generate language information for translations
"""

import os
import pathlib
import json
from configparser import ConfigParser
from deep_translator import GoogleTranslator

Aliases = {
    'AR': ['spanish'], #ar
    'CA': ['catalan'],
    'CH': ['chinese (traditional)'],
    'CN': ['chinese (simplified)'],
    'CS': ['czech'],
    'DA': ['danish'],
    'DE': ['german'],
    'EN': ['english'],
    'ES': ['spanish'],
    'FI': ['finnish'],
    'FR': ['french'],
    'HU': ['hungarian'],
    'ID': ['indonesian'],
    'IT': ['italian'],
    'JP': ['japanese'],
    'KO': ['korean'],
    'NL': ['dutch'],
    'NO': ['norwegian'],
    'PH': ['tagalog','filipino'],
    'PL': ['polish'],
    'PT': ['portuguese'],
    'PTBR': ['portuguese'], #br
    'RO': ['romanian'],
    'RU': ['russian'],
    'TH': ['thai'],
    'TR': ['turkish'],
    'UA': ['ukrainian'],
}

def get_translate_path():
    """
    return the path of the Project Zomboid Translate folder
    """
    config = ConfigParser()
    config.read(pathlib.Path(__file__).parent.parent / "config.ini")
    return pathlib.Path(config["Directories"]["PZTranslateDir"])

def get_translate_codes(name):
    """
    return the codes for translations
    """
    if name == "google":
        return GoogleTranslator().get_supported_languages(True)
    return None

def parse_language_file(fpath: pathlib.Path):
    """
    LanguageFile instance uses ScriptParser to read the file and sets the values to LanguageFileData object
    """
    with open(fpath,"r",encoding="UTF-8") as f:
        d = {}
        for line in f:
            for it in line.split(","):
                if "=" in it:
                    key, value = it.split("=",1)
                    key = key.strip()
                    value = value.strip()
                    d[key] = value
    return d

def generate_info():
    """
    loop from all directories and gather information about the languages
    """
    translate_path = get_translate_path()
    translate_codes = get_translate_codes("google")
    info = {}
    with os.scandir(translate_path) as dir_entries:
        for each in dir_entries:
            if each.is_dir():
                lpath = translate_path.joinpath(each.name,"language.txt")
                if not lpath.is_file:
                    continue
                d = parse_language_file(lpath)
                if not (all(x in d for x in ["text", "charset", "VERSION"]) and d["VERSION"] == "1"):
                    continue
                data = {}
                data["text"] = d["text"]
                data["charset"] = d["charset"]
                data["name"] = each.name
                for k in ["base","azerty"]:
                    if k in d:
                        data[k] = d[k]
                data["tr_code"] = next((translate_codes[x] for x in Aliases[each.name] if x in translate_codes) , None)
                if data["tr_code"] is None:
                    print("no tr_code found for",each.name,data["text"])
                    data["tr_code"] = "en"
                info[each.name] = data

    return info

def get_languages_info(generate: bool = False) -> dict[str, dict]:
    """
    returns the languages information
    """
    ipath = pathlib.Path(__file__).parent.parent / "LanguagesInfo.json"
    if generate or not ipath.is_file():
        d = generate_info()
        with open(ipath,"w",encoding="utf-8") as f:
            json.dump(d,f,indent=2)
        write_gitattributes_template()
        return d
    with open(ipath,"r",encoding="utf-8") as f:
        return json.load(f)

def write_gitattributes_template():
    'write gitattributes based on languages info'

    fp = pathlib.Path(__file__).parent.parent.joinpath("templates",".gitattributes")
    with open(fp,"w",encoding="utf-8") as f:
        f.write("""# Translation files are encoded differently per-language
# see https://github.com/TheIndieStone/ProjectZomboidTranslations/blob/master/.gitattributes
# see https://github.com/TheIndieStone/ProjectZomboidTranslations/issues/155
""")
        for name, lang in PZ_LANGUAGES.items():
            f.write(f'{name}/*.txt text working-tree-encoding={lang["charset"].lower()} encoding=utf-8,\n')
        f.write("""
# exception: keep the language definition/credits utf-8
*/credits.txt text working-tree-encoding=utf-8 encoding=utf-8
*/language.txt text working-tree-encoding=utf-8 encoding=utf-8
*/Translated by.txt text working-tree-encoding=utf-8 encoding=utf-8
""")

PZ_LANGUAGES = get_languages_info()
