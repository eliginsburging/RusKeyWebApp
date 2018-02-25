# Generated by Django 2.0.2 on 2018-02-25 01:39

from django.db import migrations
from django.templatetags.static import static
import os


class verbclass(object):
    def __init__(self, verbFileName):
        with open('ruskeyverbs/static/ruskeyverbs/verbs/' + verbFileName) as verbFile:
            self.verbFileLinesList = verbFile.readlines()
            self.infinitive = self.verbFileLinesList[0].replace(u'\n', '')
            self.aspect = self.verbFileLinesList[1].replace(u'\n', '')
            self.frequencyRank = self.verbFileLinesList[2].replace(u'\n', '')
            self.meaning = self.verbFileLinesList[3].replace(u'\n', '')
            self.indicativeFirstSg = self.verbFileLinesList[4].replace(u'\n', '')
            self.indicativeSecondSg = self.verbFileLinesList[5].replace(u'\n', '')
            self.indicativeThirdSg = self.verbFileLinesList[6].replace(u'\n', '')
            self.indicativeFirstPl = self.verbFileLinesList[7].replace(u'\n', '')
            self.indicativeSecondPl = self.verbFileLinesList[8].replace(u'\n', '')
            self.indicativeThirdPl = self.verbFileLinesList[9].replace(u'\n', '')
            self.imperativeSg = self.verbFileLinesList[10].replace(u'\n', '')
            self.imperativePl = self.verbFileLinesList[11].replace(u'\n', '')
            self.pastMasc = self.verbFileLinesList[12].replace(u'\n', '')
            self.pastFem = self.verbFileLinesList[13].replace(u'\n', '')
            self.pastNeut = self.verbFileLinesList[14].replace(u'\n', '')
            self.pastPl = self.verbFileLinesList[15].replace(u'\n', '')
            self.examplesList = []
            self.examplesListTranslations = []
            self.verbAudioList = []
            for i in range(16,len(self.verbFileLinesList)-1,2):
                self.examplesList.append(
                    self.verbFileLinesList[i].replace(u'\n',''))
                self.examplesListTranslations.append(
                    self.verbFileLinesList[i+1].replace(u'\n',''))
            for i in range(len(self.examplesList)):
                audioFileName = ('./verbAudio/'
                                 + verbFileName[:-4]
                                 + str(i)
                                 + '.mp3')
                self.verbAudioList.append(audioFileName)
            self.verbAudioList.append('./verbAudio/'
                                      + verbFileName[:-4]+'.mp3')
            #append conjugation audio last so that indexes for examples line up

            self.transliterateDict = {'а': 'a',
                                      'б': 'b',
                                      'в': 'v',
                                      'г': 'g',
                                      'д': 'd',
                                      'е': 'je',
                                      'ё': 'jo',
                                      'ж': 'zh',
                                      'з': 'z',
                                      'и': 'i',
                                      'й': 'j',
                                      'к': 'k',
                                      'л': 'l',
                                      'м': 'm',
                                      'н': 'n',
                                      'о': 'o',
                                      'п': 'p',
                                      'р': 'r',
                                      'с': 's',
                                      'т': 't',
                                      'у': 'u',
                                      'ф': 'f',
                                      'х': 'kh',
                                      'ц': 'ts',
                                      'ч': 'ch',
                                      'ш': 'sh',
                                      'щ': 'shch',
                                      'ъ': '',
                                      'ы': 'y',
                                      'ь': '',
                                      'э': 'e',
                                      'ю': 'ju',
                                      'я': 'ja',
                                      chr(769): ''}

    def transliterate(self):
        """returns a transliterated version of the infitive form"""
        result = ""
        for letter in self.infinitive:
            result += self.transliterateDict.get(letter, letter)
        return result


def load_data(apps, schema_editor):
    file_list = os.listdir('ruskeyverbs/static/ruskeyverbs/verbs/')
    file_list.sort()
    Verb = apps.get_model("ruskeyverbs", "Verb")
    Example = apps.get_model("ruskeyverbs", "Example")
    verb_count = 1
    example_count = 1
    verb_model_dict = {}
    example_model_dict = {}
    for file in file_list:
        currentVerb = verbclass(file)
        verb_model_dict[str(verb_count)] = Verb(infinitive=currentVerb.infinitive,
                                                trans_infinitive=currentVerb.transliterate(),
                                                aspect=currentVerb.aspect,
                                                meaning=currentVerb.meaning,
                                                first_sg=currentVerb.indicativeFirstSg,
                                                second_sg=currentVerb.indicativeSecondSg,
                                                third_sg=currentVerb.indicativeThirdSg,
                                                first_pl=currentVerb.indicativeFirstPl,
                                                second_pl=currentVerb.indicativeSecondPl,
                                                third_pl=currentVerb.indicativeThirdPl,
                                                imperative_sg=currentVerb.imperativeSg,
                                                imperative_pl=currentVerb.imperativePl,
                                                past_masc=currentVerb.pastMasc,
                                                past_fem=currentVerb.pastFem,
                                                past_neut=currentVerb.pastNeut,
                                                past_pl=currentVerb.pastPl,
                                                audio_file=currentVerb.verbAudioList[-1])
        verb_model_dict[str(verb_count)].save()
        for i in range(len(currentVerb.examplesList)):
            example_model_dict[str(example_count)] = Example(verb=verb_model_dict[str(verb_count)],
                                                             russian_text=currentVerb.examplesList[i],
                                                             translation_text=currentVerb.examplesListTranslations[i],
                                                             example_audio=currentVerb.verbAudioList[i])
            example_model_dict[str(example_count)].save()
            example_count += 1
        verb_count += 1


class Migration(migrations.Migration):

    dependencies = [
        ('ruskeyverbs', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_data),
    ]