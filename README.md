# Loretta no Shouzou translation project

Modifies the `Loretta no Shouzou - Sherlock Holmes (Japan).rom` for the SG-1000 so it can be played in languages other than Japanese.

## Dependencies

* Python 3.8
* `loretta.sg` ROM file with md5 of `8dcdd83e58be634a3735911a1af05bb3`. This should be placed in the base folder (next to the `patch.sh` script).

### Creating the patched ROM

Run the `patch.sh` script to generate a `loretta_en.sg` file from the files in the `english` subdirectory.
```
$ ./patch.sh
```

### Individial steps

The following describes the steps taken by the `patch.sh` script:

* The `font.txt` and `password_font.txt` files are imported to update the 8x8 fonts.
* The `password_text.txt` and `title_text.txt` files are imported to update the text on the title screen and password input screen
* The `menu.txt` and `words.txt` files are imported to update the in-game menus.
* The `time.txt` file is imported to update the display of the in game Time command.
* The `text.txt` file is processed to generate the `pairs.txt` file. In order to fit all the translated text into the ROM, some form of compression is required. I've taken the simplest approach and assign the most common pairs to unused bytecodes in the tile table. `pairs.txt` will contain the mapping for the most common pairs.
* The `new_text_routine.txt` file is processed. This modifies the code to support the repurposed bytecodes.
* The `text.txt` and `text2.txt` files are imported to update the game text.
* The `title.png` file is imported to update the title screen graphic.

