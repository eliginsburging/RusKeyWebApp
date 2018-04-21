from django import forms

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext as _


def count_vowels(word):
    """takes a string and returns the number of Russian vowels"""
    # For use in checking whether a word has a stress
    vowels = "аеёиоуыэюяАЕЁИОУЫЭЮЯ"
    count = 0
    for vowel in vowels:
        count += word.count(vowel)
    return count


class MultipleChoiceForm(forms.Form):

    def __init__(self, choices, *args, **kwargs):
        super(MultipleChoiceForm, self).__init__(*args, **kwargs)
        self.fields['answer'] = forms.ChoiceField(choices=choices, label='')


class FillInTheBlankForm(forms.Form):
    verb_part_of_speech = forms.CharField(label="Fill in the blank:")

    def clean_verb_part_of_speech(self):
        data = self.cleaned_data['verb_part_of_speech']
        return data


class ArrangeWordsForm(forms.Form):

    def __init__(self, example_sentence_list, sentence_len, *args, **kwargs):
        super(ArrangeWordsForm, self).__init__(*args, **kwargs)
        # since we are adding three other random forms of the verb,
        for i in range(sentence_len):
            self.fields[f'custom_{i}'] = forms.ChoiceField(choices=example_sentence_list, label='')


class ReproduceSentenceForm(forms.Form):
    sentence_field = forms.CharField(label="Type the sentence in Russian:")

    def clean_sentence_field(self):
        data = self.cleaned_data['sentence_field']
        return data
