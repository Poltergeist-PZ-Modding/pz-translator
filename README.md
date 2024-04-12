# pz-translator

Project Zomboid translations automation scripts, initialise translations with automatic translations.

## Requirements

- Python 3.11
- [deep_translator](https://pypi.org/project/deep-translator/) 1.11

## How to use

1. Copy `config.ini` from `templates` to the top level folder.
2. run `repository/pz-translator/translate.py` directly or using the command line.

You can pass the directory path of either of these to the script and it will work.
- **Translate** folder
- **Mod** folder (requires: mod.info)
- **Project** folder (requires: project.json like from pzstudio)

You can pass the script the path to either of these and it will work.
- **Translate** folder
- **Mod** folder (r: mod.info)
- **Project** folder (r: project.json like from pzstudio)
> Notes
- You can run the script directly, without any arguments and it will translate the folder set in the `config.ini` file; [Directories] Target.
- Online translations can take a long time if you have a lot of texts, you can use KeyboardInterrupt (CTRL + C) to quit and the translated texts progress will be saved.

### command line

example for windows, you can also write this into a cmd file for shortcut.
```
py "repository/pz-translator/translate.py" "path to translate"
```

### VSCode task

You can add a task like this to run the script. This will target the workspaceFolder for translation.
```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Translate Project",
      "type": "shell",
      "command": "py",
      "args": [ "repository/pz-translator/translate.py", "${workspaceFolder}" ],
      "group": "none",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
  ]
}

```
> See https://go.microsoft.com/fwlink/?LinkId=733558 for the documentation about the tasks.json format

## Languages

Select a handful of languages that either translate effectively or can be improved, as not all languages translate well or have variations, such as Brazilian Portuguese (pt-BR).

## Text Translator

Deep translator supports different translators, you can find more information at: [https://pypi.org/project/deep-translator/](https://pypi.org/project/deep-translator/)

## Warning!

The script rewrites the translation files, if you are not using version control then keep backups.
