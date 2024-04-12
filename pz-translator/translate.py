"""
Script to process and fill mod translations for Project Zomboid
"""

import os
import sys
from pathlib import Path
from shutil import copyfile
import json
from configparser import ConfigParser
from deep_translator import GoogleTranslator
from languages_info import PZ_LANGUAGES
from translation_types import TranslateType, TRANSLATION_TYPES

TAG_MODULATION = [
    ("<", "{<{"),
    (">", "}>}"),
    ("%1", "{%1}"),
    ("%2", "{%2}"),
    ("%3", "{%3}"),
]

def tags_mod(text:str):
    """
    modulate special tags from changing during translation
    """
    for k, v in TAG_MODULATION:
        text = text.replace(k,v)
    return text

def tags_demod(text:str):
    """
    demodulate special tags
    """
    for k, v in TAG_MODULATION:
        text = text.replace(v,k)
    return text

class Translator:
    """
    Translator class for the "Translate folder"
    """

    def __init__(self, translate_path: Path = None):
        config_path = Path(__file__).parent.parent / "config.ini"
        assert config_path.is_file(), f"Missing config file: {config_path}"
        self.config = ConfigParser()
        self.config.read(config_path)

        if translate_path is None:
            self.root = Path(self.config["Directories"]["Translate"])
        else:
            self.root = translate_path
        source = self.config["Translate"]["source"]
        source_path = self.get_path(source)
        assert source_path.is_dir(), f"Missing source directory: {source_path}"

        self.warnings = 0
        self.source_lang = PZ_LANGUAGES[source]
        self.languages = self.compute_languages()
        self.files = self.compute_files()
        self.import_path = None
        option = self.config.get("Directories", "Import", fallback=None)
        if option:
            _path = Path(option).resolve()
            if _path.is_dir():
                self.import_path = _path
            else:
                self.warn(f"Import directory {_path} is not valid")
        self.translator = GoogleTranslator(self.source_lang["tr_code"])
        self.check_gitattributes()

    def get_path(self, lang_id: str, file: TranslateType = None) -> Path:
        """
        if file is used then returns the path to the file for the language,
        otherwise returns the `Translate/language` path.
        """

        if file is None:
            return self.root.joinpath(lang_id)
        return self.root.joinpath(file.get_path(lang_id)).resolve()

    def get_import_path(self, lang_id: str, file: TranslateType) -> Path | None:
        """
        returns the path of the import file or None if there is no import path
        """

        if self.import_path is None:
            return None
        return self.import_path.joinpath(file.get_path(lang_id)).resolve()

    def get_translation_type(self, case: str) -> type[TranslateType] | None:
        'return translation type class'

        ttc = TRANSLATION_TYPES.get(case, None)
        if ttc is None:
            self.warn(f'Unknown translation type: {case}')
        return ttc

    def get_radio_path(self) -> Path | None:
        'return path of folder containing RadioData'

        if self.root.parts[-4:] == ("media","lua","shared","Translate"):
            _path = Path(*self.root.parts[:-3],"radio")
            if _path.exists():
                return _path
        else:
            _path = self.root / "TV_Radio"
            if _path.exists():
                return _path
        return None

    def get_valid_languages(self, translate: list | dict, create: set | list) -> list[dict]:
        """
        return final list of languages to translate, removing languages without a directory
        """

        languages = []
        for lang in translate:
            lang_path = self.get_path(lang)
            if lang_path.is_dir():
                languages.append(PZ_LANGUAGES[lang])
            elif lang in create:
                lang_path.mkdir()
                languages.append(PZ_LANGUAGES[lang])

        return languages

    def compute_languages(self):
        "compute languages for translation"

        option = self.config.get("Translate","languagesExclude",fallback=None)
        if option:
            lang_exclude = {x for x in [x.strip() for x in option.split(",")] if x in PZ_LANGUAGES}
        else:
            lang_exclude = set()
        lang_exclude.add(self.source_lang["name"])
        option = self.config.get("Translate","languagesTranslate",fallback=None)
        if option:
            lang_translate = [x for x in [x.strip() for x in option.split(",")] if x not in lang_exclude and x in PZ_LANGUAGES]
        else:
            lang_translate = [x for x in PZ_LANGUAGES if x not in lang_exclude]
        option = self.config.get("Translate","languagesCreate",fallback=None)
        if option:
            lang_create = {x for x in [x.strip() for x in option.split(",")] if x in lang_translate}
        else:
            lang_create = lang_translate

        return self.get_valid_languages(lang_translate,lang_create)

    def compute_files(self) -> list[TranslateType]:
        """
        get list of source files to translate.
        """

        files = []
        option = self.config.get("Translate","files",fallback=None)
        if option:
            for each in option.split():
                each = each.strip()
                tclass = self.get_translation_type(each)
                if tclass is None:
                    continue
                tobj = tclass(self)
                if self.get_path(self.source_lang["name"], tobj).is_file():
                    files.append(tobj)
        else:
            suffix = f'_{self.source_lang["name"]}.txt'
            source_path = self.get_path(self.source_lang["name"])
            with os.scandir(source_path) as dir_entries:
                for each in dir_entries:
                    if each.is_dir():
                        for name in ["title.txt","description.txt"]:
                            for fp in Path(each).rglob(name):
                                tclass = self.get_translation_type("MapInfo")
                                files.append(tclass(self,str(fp.relative_to(source_path))))
                    elif each.name.endswith(suffix):
                        tclass = self.get_translation_type(each.name.removesuffix(suffix))
                        if tclass is not None:
                            files.append(tclass(self))
            # source_path = self.get_radio_path()
            # if source_path:
            #     tclass = self.get_translation_type("RadioData")
            #     files.append(tclass(self))
        return files

    def translate_missing(self, tlang: dict, file: TranslateType, src_map: dict, tr_map: dict):
        'translate missing texts using translators single text function'

        #import saved auto-translations
        file_path = self.get_path(tlang["name"], file)
        temp_file_path = file_path.parent.joinpath(f'{file_path.stem}_translator_temp.txt')
        auto_translations = {}
        if temp_file_path.is_file():
            file.parse_translation(temp_file_path, tlang, auto_translations, True)
            for key, text in auto_translations.items():
                if key not in tr_map:
                    tr_map[key] = text 
        #check missing and translate
        untranslated = [key for key in src_map if not tr_map.get(key, None)]
        if untranslated:
            print(f" - Translating number of texts: {len(untranslated)}")
            self.translator.target = tlang["tr_code"]
            try:
                for key in untranslated:
                    tr_map[key] = tags_demod(self.translator.translate(tags_mod(src_map[key])))
            except KeyboardInterrupt:
                for key in untranslated:
                    if key not in tr_map:
                        break
                    auto_translations[key] = tr_map[key]
                file.export(temp_file_path, tlang, auto_translations)
                raise
            except Exception:
                self.warn("failed to translate file")
                for key in reversed(untranslated):
                    if key in tr_map:
                        break
                    tr_map[key] = ""
        #remove temp file
        temp_file_path.unlink(missing_ok=True)

    def get_translations(self, source_texts: dict, tr_lang: dict, file: TranslateType) -> dict:
        'return dictionary with translation texts'

        tr_map = {}
        tr_map["__language_name__"] = tr_lang["name"]
        # add existing tranlsations
        fp = self.get_path(tr_lang["name"], file)
        if fp.is_file():
            file.parse_translation(fp, tr_lang, tr_map)
        # import translations on top
        fp = self.get_import_path(tr_lang["name"],file)
        if fp and fp.is_file():
            file.parse_translation(fp, tr_lang, tr_map, True)
        # translate missing
        self.translate_missing(tr_lang, file, source_texts, tr_map)
        return tr_map

    def write_translation(self, lang: dict, file: TranslateType, text: str):
        'write the translation file'

        try:
            with open(self.get_path(lang["name"],file),"w",encoding=lang["charset"],errors="replace") as f:
                f.write(text)
        except Exception as e:
            self.warn(f"Failed to write {lang['name']} {file.name}\nException: {e}\nText:\n{text}")

    def translate_main(self):
        """
        translate class instance
        """

        for file in self.files:
            source_fp = self.get_path(self.source_lang["name"],file)
            template, source_map = file.parse_source(source_fp, self.source_lang)
            for lang in self.languages:
                # translate, paste template, or remove.
                if source_map:
                    print(f"Begin Translation Check for: {file.name}, {lang['name']}, {lang['text']}")
                    self.write_translation(lang,file,template.safe_substitute(self.get_translations(source_map,lang,file)))
                elif template:
                    self.write_translation(lang,file,template)
                else:
                    self.get_path(lang["name"],file).unlink(missing_ok=True)
        print(f"\nFinished with {self.warnings} warnings.")

    def translate_specific(self, languages: list | dict, files: list, languages_create: set[str]):
        """
        translate specific languages and files
        """

        self.files = [c() for c in [self.get_translation_type(x) for x in files] if c is not None]
        self.languages = self.get_valid_languages(languages,languages_create)
        self.translate_main()

    def reencode_translations(self, read: dict, languages: list = None, files: list = None,
                              errors: str | None = "replace"):
        '''
        attempt to convert to appropriate encoding
        '''

        if not languages:
            languages = self.languages
        if not files:
            files = self.files
        for lang in languages:
            for file in files:
                file_path = self.get_path(lang["name"],file)
                if file_path.is_file():
                    with open(file_path, "r", encoding=read[lang["name"]], errors=errors) as f:
                        text = f.read()
                    with open(file_path, "w", encoding=lang["charset"], errors=errors) as f:
                        f.write(text)

    def reencode_initial(self):
        '''
        Rewrites existing files, assumes files were using correct encoding. 
        Use when first adding gitattributes file without translating files.
        '''

        self.reencode_translations(
            { lang["name"]: lang["charset"] for lang in PZ_LANGUAGES.values() },
            [self.source_lang] + self.languages,
            self.files
        )

    def check_gitattributes(self):
        """
        add gitattributes file if it doesn't exist
        """

        if not self.config.getboolean("DEFAULT","create_gitattributes"):
            return
        fpath = self.root / ".gitattributes"
        if not fpath.is_file():
            copyfile(Path(__file__).parent.parent / "templates" / ".gitattributes",fpath,follow_symlinks=False)
            if self.config.getboolean("DEFAULT","pause_on_gitattributes"):
                self.reencode_initial()
                input("Added .gitattributes file. Press Enter to continue.\n")

    def warn(self, message: str):
        """print warning message"""
        self.warnings += 1
        print(f" - Warning: {message}")

def try_translate_project(root: Path) -> bool:
    'translate project'

    if root.joinpath("project.json").is_file():
        print(f"< Translating project: {root.name} >")
        r = False
        with open(root.joinpath("project.json"),"r",encoding="utf-8") as f:
            project = json.load(f)
        exclude = project.get("workshop",{}).get("excludes",[])
        for mod_id in project.get("mods",[]):
            if mod_id in exclude:
                continue
            r = try_translate_mod(root / mod_id) or r
        return r
    return False

def try_translate_mod(root: Path) -> bool:
    'translate mod'

    if root.joinpath("mod.info").is_file():
        print(f"< Translating mod: {root.name} >")
        translate_path = root.joinpath("media","lua","shared","Translate")
        if translate_path.is_dir():
            Translator(translate_path).translate_main()
            return True
        print("Invalid mod translation dir: ",translate_path)
    return False

def main():
    'main'

    if len(sys.argv) == 1:
        print("< Translating from config file >")
        Translator().translate_main()
    else:
        root = Path(sys.argv[1]).resolve()
        if not root.is_dir():
            print(f"Directory {root} does not exist:")
        elif try_translate_project(root):
            return
        elif try_translate_mod(root):
            return
        else:
            print("< Translating directory >")
            Translator(root).translate_main()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user")
