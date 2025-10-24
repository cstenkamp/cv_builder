# CV-Generator

A tool to convert allow to write a Curriculum Vitae in YAML, to then be exported to Latex and thus PDF (upcoming) as well as HTML. This repo can run as a separate container and hosts the HTML in Flask (see https://cstenkamp.de/getcv/cv), which can even be embedded into Hugo (see my [blogpost](https://cstenkamp.de/tech_posts/hugo_dynamic_content/)). It is customizable and allows currently for multiple languages with translations and content that's only supposed to be in one language - future work will extend this to also be able to customize text length or categories of content - stay tuned for that. 

## Features

### Translation-tools

* Translation-tables: a single word can be translated into multiple languages (or not, just keep the original). Every occurance of that word will be translated, no matter if it's a key or a value.
    ```
    Variants:
      Language:
        en:
          name:    English
          default: true
          datefmt: "%m/%d/%Y"
        de:
          name:    Deutsch
          datefmt: "%d.%m.%Y"
    
    Translations:
      en:
        Hiwi:       Student research assistant
        Lebenslauf: Curriculum Vitae
      de:
        Hiwi:       Studentische Hilfskraft
    ```
  
* You can add `_de` or `_en` to keys, such that they are used instead of the default-key (so if you have `title` and `title_de` with english as default language, it selects either the one or the other)
* You can have `[en]` or `[de]` in the key of a section such that it only occurs in the respective language
* You can start list-items with the language (eg. `- [en] only in english`) to have that element only in that language
* If one of the entries of a dictionary-item is eg. `show_on:    de`, it will only show in this language
* If you use `date(year-month-day)` to identify dates and set a `datefmt` for the respective languages, it will automatically be printed correctly for the respective language.

### Formatting-Tools

* Markdown is allowed in keys and values
* `img(imgname)` can be used to include an image - which will available at its domain using Flask
* `_hidden` as part of the key hides it from HTML (but not Latex)
* Automatically removes some Latex-design-commands (eg. `small`)
* Automatically removes sentences which say "enclosed" or similar
* You can add style-commands as curly brackets into the key of a section, which will change the style of its children. Currently existing:
  * `{doubleitem}` is to have two children for an entry (like the `cvlistedoubleitem` in moderncv) 
  * `{yearlist}` is for a year-list (see `Awards` in sample_cv.yaml), makes it look similar to the main sections
  * `{paragraphs}` designs a list not as bullet points, but as individual paragraphs.

## Syntax

* Special Sections: 
  * `Variants`
  * `Translations`
* Specify either `website` or `optshort` for list-items

## ADDITIONS 2025
* Can have [de,lg] in titles to only show for this combination
* How are variants used? 
  * `[de]` in section title
  * `_de` in key
  * dictionary has key `show_on` with value `de`

## TODO

* _de nutzen können für sprache, aber auch _long für lange descriptions und auch nen ding für nontech, aber das halt variabel halten und dafür nen extra-yaml-teil 
* YAML autoformatten dazu wie ich das jetzt hab
* Explain HERE how the different ´cvitem` Latex entries are generated
* yearlist Zeitstrahl design
* Postprocessing-script to make links to my websites
* Allow for dividers in sections ("Tutor Jobs")
* Allow to merge different cats (such that I can do voctional experience in non-CS under another headline)
* Tex-File contains work-contactinfo, should be able to also add that in yaml

* If I have languages [de, en] (en default) and length [short, long] (short default), and for one thing I have the entries xyz, xyz_long & xyz_de.... and no xyz_de_long, then how do I decide if that one takes xyz_long or xyz_de? -> PRIORITY 


### NOW

* _de nutzen können für sprache, aber auch _long für lange descriptions und auch nen ding für nontech, aber das halt variabel halten und dafür nen extra-yaml-teil 
* autoformatten dazu wie ich das jetzt hab
* CV mit postprocessing-script dass die links macht
* Subsections (Tutor Jobs)



## Further links

* https://tex-talk.net/2011/10/overkill-is-a-good-thing/
* https://www.texdev.net/2011/11/05/writing-a-curriculum-vitae-in-latex-part-1/