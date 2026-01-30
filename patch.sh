cp loretta.sg loretta_en.sg
echo --- Importing font ---
./import.py --rom loretta_en.sg --font english/font.txt
./import.py --rom loretta_en.sg --font english/password_font.txt
echo --- Importing menu text ---
./import.py --rom loretta_en.sg --text english/title_text.txt --charmap english/password_font.txt
./import.py --rom loretta_en.sg --text english/menu.txt --charmap english/font.txt
./import.py --rom loretta_en.sg --text english/words.txt --charmap english/font.txt
./import.py --rom loretta_en.sg --text english/time.txt --charmap english/font.txt
echo --- Importing dialog text ---
./import.py --rom loretta_en.sg --text english/text.txt --charmap english/font.txt

