"""
File Specific Classes
"""

from pathlib import Path
from string import Template
from io import StringIO
from typing import Tuple

class TranslationTemplate(Template):
    'Custom Template'
    idpattern = Template.delimiter
    braceidpattern = r'([^}]*)'

class TranslateType():
    "Base class"

    name: str

    def __init__(self, parent, name: str = None):
        self.parent = parent
        if name:
            self.name = name

    def get_path(self, lang: str) -> str:
        """return file path string for language"""
        raise NotImplementedError()

    def parse_source(self, fp: Path, lang: dict) -> Tuple[TranslationTemplate, dict]:
        "read source file"
        raise NotImplementedError()

    def parse_translation(self, fp: Path, lang: dict, mapping: dict, is_import: bool = False):
        "read translation file"
        raise NotImplementedError()

    def add_to_template(self, template: StringIO, text: str = None, is_key: bool = False, replace: list = None):
        "add to template"

        if template is None:
            return
        if is_key:
            template.write("${"+text+"}")
        else:
            text = text.replace("$","$$")
            if replace:
                for k,v in replace:
                    text = text.replace(k,v)
            template.write(text)

    def export(self, fp: Path, language: dict, texts: dict):
        'write the translations from dictionary'
        raise NotImplementedError()

class File(TranslateType):
    "File class"

    PREFIXES: list[str] = []

    def get_path(self, lang: str) -> str:
        return f'{lang}/{self.name}_{lang}.txt'

    def parse_source(self, fp: Path, lang: dict) -> Tuple[TranslationTemplate, dict]:
        mapping = {}
        return (self.parse_file(fp, lang, mapping, True, True), mapping)

    def parse_translation(self, fp: Path, lang: dict, mapping: dict, is_import: bool = False):
        self.parse_file(fp, lang, mapping, False, not is_import)

    def parse_file(self, fp: str, lang: dict, mapping: dict, create_template: bool, check_duplicate: bool) -> TranslationTemplate:
        """
        parse the translation file
        concatenation: join and format lines.
        """

        template = StringIO() if create_template else None

        with open(fp,'r',encoding=lang["charset"]) as f:
            key = ""
            text = ""
            concat = False
            lines = None

            line = f.readline()
            self.add_to_template(template, line, False, [("_" + lang["name"], "_${__language_name__}")])

            for line in f:
                stripped = line.strip()
                if "=" in stripped and "\"" in stripped:
                    if concat:
                        self.parent.warn(f'Concat interrupted for {key}')
                        mapping[key] = mapping.get(key,"")
                    index1 = line.index("=")
                    index2 = line.index("\"",index1+1)
                    index3 = line.rindex("\"")
                    key = line[:index1].strip()
                    text = line[index2+1:index3]
                    if ".." in stripped:
                        concat = True
                    if self.PREFIXES and not any(key.startswith(pre) for pre in self.PREFIXES):
                        self.parent.warn(f'Possibly misspelled key: {key}')
                    #TODO apply replace for improved support
                    # for prefix in ["Recipe_", "DisplayName_", "DisplayName", "EvolvedRecipeName_", "ItemName_"]:
                    #     if key.startswith(prefix):
                    #         key.replace(prefix,"")
                    #         break
                    # key = next((key.replace(prefix, "") for prefix in ["recipe", "DisplayName_"] if key.startswith(prefix)), key)

                    # fix for format
                    key = key.replace("{","}")
                    if check_duplicate and key in mapping:
                        self.parent.warn(f'Duplicate key: {key}')
                    if not key:
                        self.parent.warn("No key in:\n" + line)
                    else:
                        self.add_to_template(template, line[:index2+1])
                        self.add_to_template(template, key, True)
                        self.add_to_template(template, line[index3:])
                elif stripped and "--" not in stripped and (stripped.endswith("..") or concat):
                    if concat and '"' in stripped:
                        text = stripped[stripped.index("\"")+1:stripped.rindex("\"")]
                    else:
                        text = ""
                    concat = True
                else:
                    concat = False

                if concat and stripped.endswith(".."):
                    if not lines:
                        lines = ['']
                        join_str = f'"..\n{line[:line.find(stripped[0])]}    "'
                    if text:
                        lines.append(text)
                    continue
                if lines:
                    if text:
                        lines.append(text)
                    text = join_str.join(lines)
                    lines = None
                if key:
                    if not text:
                        self.parent.warn(f'{key} is missing translation')
                    # set text to mapping
                    mapping[key] = text
                else:
                    self.add_to_template(template,line)

                key = ""
                text = ""
                concat = False

        if template:
            text = template.getvalue()
            template.close()
            return TranslationTemplate(text)
        return None
    
    def export(self, fp: Path, language: dict, texts: dict):
        texts.pop("__language_name__", None)
        lines = "\n".join([f'    {key} = "{text}",' for key, text in texts.items()])
        with open(fp, "w", encoding=language["charset"], errors="replace") as file:
            file.write(f'{self.name}_{language["name"]} = {{\n{lines}\n}}\n')

class Challenge(File):
    """ Challenge """

    name = "Challenge"
    PREFIXES = ["Challenge_"]

class ContextMenu(File):
    """ ContextMenu """

    name = "ContextMenu"
    PREFIXES = ["ContextMenu_"]

class DynamicRadio(File):
    """ DynamicRadio """

    name = "DynamicRadio"
    # PREFIXES = ["AEBS_"]

class EvolvedRecipeName(File):
    """ EvolvedRecipeName """

    name = "EvolvedRecipeName"
    # PREFIXES = ["EvolvedRecipeName_"]

class Farming(File):
    """ Farming """

    name = "Farming"
    PREFIXES = ["Farming_"]

class GameSound(File):
    """ GameSound """

    name = "GameSound"
    PREFIXES = ["GameSound_"]

class IGUI(File):
    """ IG_UI """

    name = "IG_UI"
    PREFIXES = ["IGUI"]

class ItemName(File):
    """ ItemName """

    name = "ItemName"
    # PREFIXES = ["ItemName_"]

class MakeUp(File):
    """ MakeUp """

    name = "MakeUp"
    PREFIXES = ["MakeUp"]

class Moodles(File):
    """ Moodles """

    name = "Moodles"
    PREFIXES = ["Moodles_"]

class Moveables(File):
    """ Moveables """

    name = "Moveables"
    # PREFIXES = None

class MultiStageBuild(File):
    """ MultiStageBuild """

    name = "MultiStageBuild"
    PREFIXES = ["MultiStageBuild_"]

class Recipes(File):
    """ Recipes """

    name = "Recipes"
    # PREFIXES = ["Recipes_"]

class RecordedMedia(File):
    """ Recorded_Media """

    name = "Recorded_Media"
    PREFIXES = ["RM_"]

class Sandbox(File):
    """ Sandbox """

    name = "Sandbox"
    PREFIXES = ["Sandbox_"]

class Stash(File):
    """ Stash """

    name = "Stash"
    PREFIXES = ["Stash_"]

class SurvivalGuide(File):
    """ SurvivalGuide """

    name = "SurvivalGuide"
    PREFIXES = ["SurvivalGuide_"]

class Tooltip(File):
    """ Tooltip """

    name = "Tooltip"
    PREFIXES = ["Tooltip_"]

class UI(File):
    """ UI """

    name = "UI"
    PREFIXES = ["UI_"]

class MapInfo(TranslateType): #TODO test
    "map.info"
    # titles only read first line

    def get_path(self, lang: str) -> str:
        return f'{lang}/{self.name}'

    def parse_source(self, fp: Path, lang: dict) -> Tuple[TranslationTemplate, dict]:
        with open(fp,"r",encoding=lang["charset"]) as f:
            return "{text}", {"text": f.read()}

    def parse_translation(self, fp: Path, lang: dict, mapping: dict, is_import: bool = False):
        with open(fp,"r",encoding=lang["charset"]) as f:
            mapping["text"] = f.read()

    def export(self, fp: Path, language: dict, texts: dict):
        with open(fp, "w", encoding=language["charset"], errors="replace") as file:
            file.write(texts["text"])

TRANSLATION_TYPES = {
    "Challenge": Challenge,
    "ContextMenu": ContextMenu,
    "DynamicRadio": DynamicRadio,
    "EvolvedRecipeName": EvolvedRecipeName,
    "Farming": Farming,
    "GameSound": GameSound,
    "IG_UI": IGUI,
    "ItemName": ItemName,
    # "Items": Items, # outdated
    "MakeUp": MakeUp,
    "Moodles": Moodles,
    "Moveables": Moveables,
    "MultiStageBuild": MultiStageBuild,
    # "News": News,
    "Recipes": Recipes,
    "Recorded_Media": RecordedMedia,
    "Sandbox": Sandbox,
    "Stash": Stash,
    "SurvivalGuide": SurvivalGuide,
    "Tooltip": Tooltip,
    "UI": UI,
    "MapInfo": MapInfo,
    # "RadioData": , #skip for now
}
