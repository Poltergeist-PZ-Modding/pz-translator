import os
import pathlib
from pz_languages import getLanguages
from deep_translator import GoogleTranslator

LanguagesDict = getLanguages(False)
# translations also have %Map/ files
FileList = [ "Challenge", "ContextMenu", "DynamicRadio", "EvolvedRecipeName", "Farming", "GameSound", 
            "IG_UI", "ItemName", "Items", "MakeUp", "Moodles", "Moveables", "MultiStageBuild", "Recipes", 
            "Recorded_Media", "Sandbox", "Stash", "SurvivalGuide", "Tooltip", "UI"]

class pz_translator_zx:
    
    def __init__(self,baseDir:str="",source:str="EN",config:str=None,gitAtr:bool=True):
        if not config:
            self.baseDir = baseDir
            self.sourceLang = LanguagesDict[source]
            self.translator = GoogleTranslator(self.sourceLang["tr_code"])
        else:
            self.fromConfig(config)
        if gitAtr:
            self.checkGitAtributesFile(False)

    def fromConfig(self,file):
        from configparser import ConfigParser
        config = ConfigParser()
        config.read(file)
        self.baseDir = config["Directories"][config["Translate"]["target"]]
        source = config["Translate"]["source"]
        # source = config.get("Translate","source")
        self.sourceLang = LanguagesDict[source]
        self.translator = GoogleTranslator(self.sourceLang["tr_code"])
        if "files" in config["Translate"]:
            self.files = [x for x in [x.strip() for x in config["Translate"]["files"].split(",")] if x in FileList]
        else:
            self.files = FileList
        # self.translateLanguages = self.getLanguagesFromConfig(config)
        self.translateLanguages = []
        # createDirs = config["Translate"]["createDirs"]
        createDirs = config.getboolean("Translate","createDirs")
        languages = None
        if "languages" in config["Translate"]:
            languages = [x for x in [x.strip() for x in config["Translate"]["languages"].split(",")] if x in LanguagesDict]
        else:
            languages = LanguagesDict
        languagesBlacklist = None
        if "languagesBlacklist" in config["Translate"]:
            languagesBlacklist = {x for x in [x.strip() for x in config["Translate"]["languagesBlacklist"].split(",")] if x in LanguagesDict}
        else:
            languagesBlacklist = {}
        for id in languages:
            if id == source or id in languagesBlacklist:
                continue
            if os.path.isdir(os.path.join(self.baseDir,id)):
                self.translateLanguages.append(LanguagesDict[id])
            elif createDirs:
                pathlib.Path(self.getFilePath(id)).mkdir()
                self.translateLanguages.append(LanguagesDict[id])

    def getFilePath(self,langId: str, file: str = None):
        if not file:
            return os.path.join(self.baseDir, langId)
        else:
            return os.path.join(self.baseDir, langId, file + "_" + langId + ".txt")

    def readSourceFile(self,file:str):
        try:
            with open(self.getFilePath(self.sourceLang["id"],file),'r',encoding=self.sourceLang["charset"]) as f:
                lines = []
                tDict = {}
                validLine = False
                key = ""
                text = ""
                
                lines += f.readline().replace("{","{{").replace(self.sourceLang["id"],"{language}")

                for line in f:
                    line = line.replace("{","{{")
                    line = line.replace("}","}}")
                    if "=" in line and "\"" in line:
                        index1 = line.index("=")
                        index2 = line.index("\"",index1+1)
                        index3 = line.rindex("\"")
                        key = line[:index1].strip().replace(".","-")
                        text = line[index2+1:index3]
                        lines += line[:index2+1], "{", key, "}", line[index3:]
                        tDict[key] = text
                        validLine = True
                    elif "--" in line or not line.strip() or line.strip().endswith("..") and not validLine:
                        validLine = False
                        lines += line
                    else:
                        validLine = True
                        lines += line

                    if not validLine or not line.strip().endswith(".."):
                        validLine = False
                        key = ""
                        text = ""

                return "".join(lines), tDict
        except FileNotFoundError:
            return None, None

    def fillTranslationsFromFile(self,lang:dict,file:str,trTexts:dict):
        try:
            with open(self.getFilePath(lang["id"],file),'r',encoding=lang["charset"]) as f:
                validLine = False
                key = ""
                text = ""
                
                f.readline()

                for line in f:
                    if "=" in line and "\"" in line:
                        index1 = line.index("=")
                        index2 = line.index("\"",index1+1)
                        index3 = line.rindex("\"")
                        key = line[:index1].strip().replace(".","-")
                        text = line[index2+1:index3]
                        trTexts[key] = text
                        validLine = True
                    elif "--" in line or not line.strip() or line.strip().endswith("..") and not validLine:
                        validLine = False
                    else:
                        validLine = True

                    if not validLine or not line.strip().endswith(".."):
                        validLine = False
                        key = ""
                        text = ""
        except:
            pass
    
    # def translate_single(oTexts: dict, tTexts):
    #     for key, value in oTexts.items():
    #         if key not in tTexts:
    #             try:
    #                 translation = translator.translate(value, tLang["tr_code"], oLang.lower())
    #                 tTexts[key] = translation.text
    #             except:
    #                 print("Failed to translate: " + tTexts["language"] + " | " + value)
    #                 tTexts[key] = "tr?: " + value

    def translate_batch(self,tLang,oTexts,tTexts):
        keys, values = [],[]
        for key in oTexts:
            if key not in tTexts:
                keys.append(key)
                values.append(oTexts[key].replace("<","<{").replace(">","}>").replace("%1","{%1}"))
        if keys:
            try:
                print("    Translation size: ",len(values))
                translations = self.translator.translate_batch(values)
                for i,key in enumerate(keys):
                    tTexts[key] = translations[i].replace("{%1}","%1").replace("<{","<").replace("}>",">")
                    try:
                        tTexts[key].encode(tLang["charset"])
                    except:
                        print("can not encode: ",key,tTexts[key])
            except:
                for i,k in enumerate(keys):
                    print("Failed to translate: " + tTexts["language"] + " | " + values[i])
                    tTexts[k] = "tr?: " + values[i]

    def getTranslations(self,oTexts: dict, tLang: dict, file: str):
        trTexts = {"language":tLang["id"]}
        self.fillTranslationsFromFile(tLang,file,trTexts)
        self.translate_batch(tLang,oTexts,trTexts)
        return trTexts

    def writeTranslation(self,lang: dict, file: str, text: str):
        try:
            with open(self.getFilePath(lang["id"],file),"w",encoding=lang["charset"],errors="replace") as f:
                f.write(text)
        except Exception as e:
            print("Failed to write " + lang["id"] + " " + file)
            print(e)
            print(text)

    def _translateAll(self):
        for file in self.files:
            templateText, oTexts = self.readSourceFile(file)
            if not oTexts:
                continue
            for lang in self.translateLanguages:
                print("Begin Translation Check for: {lang}, {file}".format(file=file,lang=lang["text"]))
                self.translator.target = lang["tr_code"]
                self.writeTranslation(lang,file,templateText.format_map(self.getTranslations(oTexts,lang,file)))

    def translate(self,languages:list|dict=LanguagesDict,files:list=FileList,createDirs:bool=False):
        self.translateLanguages = []
        self.files = files
        sourceId = self.sourceLang["id"]
        for id in languages:
            if id == sourceId:
                continue
            if os.path.isdir(os.path.join(self.baseDir,id)):
                self.translateLanguages.append(LanguagesDict[id])
            elif createDirs:
                pathlib.Path(self.getFilePath(id)).mkdir()
                self.translateLanguages.append(LanguagesDict[id])
        self._translateAll()

    # used to reincode files
    def convertTranslations(self,readEncodes:dict,languages:list|dict =LanguagesDict,files=FileList):
        for id in languages:
            lang = LanguagesDict[id]
            for file in files:
                oFile = self.getFilePath(id,file)
                if os.path.isfile(oFile):
                    f = open(oFile,"r", encoding=readEncodes[id])
                    text = f.read()
                    f.close()

                    # text.encode("utf-8")

                    f = open(oFile,"w", encoding=lang["charset"])
                    f.write(text)
                    f.close()

    def checkGitAtributesFile(self,force:bool=False):
        fPath = os.path.join(self.baseDir,".gitattributes")
        if force or not os.path.isfile(fPath):
            if os.path.isdir(fPath):
                return
            text = None
            with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gitatributes-template.txt"),"r",encoding="utf-8") as f:
                text = f.read()
            with open(fPath,"w",encoding="utf-8") as f:
                f.write(text)            

if __name__ == '__main__':    
    pz_translator_zx(config="config.ini")._translateAll()

### TODO: fix special cases e.g. %1, <br>...
### TODO: fix wrong encodes ?