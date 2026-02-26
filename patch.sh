cp loretta.sg loretta_en.sg
echo --- Importing fonts ---
./import.py --rom loretta_en.sg --font english/font.txt
./import.py --rom loretta_en.sg --font english/password_font.txt
echo --- Importing menu text ---
./import.py --rom loretta_en.sg --charmap english/font.txt --text english/menu.txt
./import.py --rom loretta_en.sg --charmap english/font.txt --text english/words.txt
./import.py --rom loretta_en.sg --charmap english/font.txt --text english/time.txt
#echo --- Repositioning screen data to make more space for text
#./screen-pack.py --rom loretta_en.sg
echo --- Importing dialog text ---
./calculate-pairs.py --text english/text.txt --charmap english/font.txt --out english/pairs.txt
./import.py --rom loretta_en.sg --charmap english/font.txt --text english/new_text_routine.txt | grep -v " 0 strings"
./import.py --rom loretta_en.sg --charmap english/font.txt --text english/text.txt
./import.py --rom loretta_en.sg --charmap english/font.txt --text english/text2.txt
echo --- Importing title graphics ---
./import.py --rom loretta_en.sg --charmap english/password_font.txt --text english/password_text.txt
./import.py --rom loretta_en.sg --charmap english/password_font.txt --text english/title_text.txt
./import-screen.py --rom loretta_en.sg --screen english/title.png --address 0x1A128 --tileaddress 0x19F8B --tilespace 0x1D8

