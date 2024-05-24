# Vježba za FJJP

Cilj vježbe je obraditi skenirani udžbenik za kolegij Vjerojatnost i Statistika
koristeći tesseract ocr, kako bi se anotirale slike skeniranog udžbenika sa
tekstom.

Prvotno skeniran udžbenik je u [`original.pdf`](./original.pdf), iz njega su
stranice izrezane, očišćene, popravljene i transformirane pomoću GIMPa, kako bi
rezultati OCRa bili točniji. Obrađena verzija je [`dio1.pdf`](./dio1.pdf), no
stranice su sačuvane u [`pages`](./pages) direktoriju kako bi se olašao rad u
Pythonu. Rezultati inicijalnog OCR skeniranja su u [`text.yml`](./text.yml).

Kako bi se poboljšali rezultati, od dobivenog teksta je izgrađen i očišćen
riječnik [`dict.txt`](./dict.txt). Riječnik sadrži nekolicinu dodatnih riječi
koje nisu sadržane u knjizi, i vjerojatno mu nedostaju neke riječi koje nisu
ispravno prepoznate iz slika.



## Licenca

Kod u repozitoriju je licenciran GPLv3 licencom.

Knjiga i slike su u vlasništvu Nikole Sarapa i Školske Knjige, te su samo
popratni materijali. Njihova daljnja distribucija je zabranjena (iako više nije
u tisku i prodaji).
