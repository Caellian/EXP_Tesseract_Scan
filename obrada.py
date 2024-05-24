#!/usr/bin/env python3

from pdf2image import convert_from_path
from tesserocr import PyTessBaseAPI, PSM, RIL
from tkinter import Tk, Label, Entry, Button, Canvas, Toplevel, StringVar
from PIL import Image, ImageTk, ImageDraw
import yaml
import string
import os
from subber import *

TEXT = "text.yml"
BAD_INPUT = "bad.yml"
FINAL = "final.yml"
DICT = "dict.txt"
PAGE_COUNT = 147

def yaml_str_normalize(string):
    return string.replace('\\', "\\\\").replace('\"', "\\\"").replace('“', "\\\"").replace('—', "-")

def get_text():
    # if text exists, return path
    if os.path.exists(TEXT):
        return TEXT
    
    with open(TEXT, "w+") as dump:
        with PyTessBaseAPI(path="/usr/share/tessdata/", psm=PSM.AUTO, lang="hrv") as api:
            for i in range(2, PAGE_COUNT + 1):
                api.SetImageFile(f"./pages/p{i:03d}.png")
                boxes = api.GetComponentImages(RIL.TEXTLINE, True);
                dump.write(f"page-{i}:\n")
                dump.write(f"  page: {i}\n")
                dump.write(f"  image: \"./pages/p{i:03d}.png\"\n")
                dump.write(f"  boxes:\n")
                print(f"PAGE {i}; {len(boxes)} components")
                for i, (im, box, _, _) in enumerate(boxes):
                    api.SetRectangle(box['x'], box['y'], box['w'], box['h'])
                    ocrResult = api.GetUTF8Text()
                    conf = api.MeanTextConf()
                    text = ocrResult.replace("\n", "").strip()
                    if len(text) == 0:
                        continue
                    
                    dump.write(f"    - text: \"{yaml_str_normalize(text)}\"\n")
                    dump.write(f"      box: [{box['x']}, {box['y']}, {box['w']}, {box['h']}]\n")
                    dump.write(f"      confidence: {conf}\n")
                    print(u"Box[{0}]: x={x}, y={y}, w={w}, h={h}, "
                        "confidence: {1}, text: {2}".format(i, conf, ocrResult, **box))
    return TEXT

def get_dict(path = DICT):
    # if dict exists, return path
    if os.path.exists(path):
        return path
    
    all_words = []
    last = None

    with open(get_text(), "r") as f:
        content = yaml.safe_load(f)
        # iterate over objects
        for page in content:
            print(f"Processing: {page}")
            boxes = content[page]["boxes"]
            if boxes is None:
                continue
            for box in boxes:
                text = box["text"]
                words = list(filter(lambda x: len(x.strip()) > 0, map(lambda x: x.strip(), text.split(" "))))

                if last is not None:
                    words[0] = last + words[0]

                if words[-1].endswith("-"):
                    last = words[-1][:-1]
                    words = words[:-1]
                else:
                    last = None

                all_words.extend(words)
        
    with open(path, "w+") as dfile:
        for word in all_words:
            dfile.write(word + "\n")

    return path

dictionary_global = {}
def load_dict(name = DICT):
    if name in dictionary_global:
        return dictionary_global[name]

    print("Loading dictionary...")
    path = get_dict(name)
    lines = open(path).read().split()

    dictionary_global[name] = {
        "words": lines,
        "fuzzy": list(map(lambda it: it.lower(), lines))
    }
    return dictionary_global[name]

PUNCTUATION = set([".", ",", "!", "?", ";", ":", "(", ")", "...", "?!"])
UPPER = set([c for c in string.ascii_uppercase])
UPPER.update(["Š", "Ž", "Č", "Ć", "Đ"])
LOWER = set([c for c in string.ascii_lowercase])
LOWER.update(["š", "ž", "č", "ć", "đ"])
SYMBOLS = set(["="])

def intersperse(lst, item):
    result = [item] * (len(lst) * 2 - 1)
    result[0::2] = lst
    return result

def depunct(word):
    before = None
    after = None
        
    if word == " ":
        return before, word, after
    elif len(word) == 0:
        return before, word, after
    
    first = word[0]
    if first in PUNCTUATION:
        before = [first]
        word = word[1:]
    while first is not None:
        if len(word) == 0:
            break
        first = word[0]
        if first in PUNCTUATION:
            before.append(first)
            word = word[1:]
        else:
            first = None
        
    if word == " ":
        return before, word, after
    elif len(word) == 0:
        return before, word, after

    last = word[-1]
    if last in PUNCTUATION:
        word = word[:-1]
        after = [last]
    while last is not None:
        if len(word) == 0:
            break
        last = word[-1]
        if last in PUNCTUATION:
            after.insert(0, last)
            word = word[:-1]
        else:
            last = None
        
    return before, word, after

def is_number(word):
    if len(word) == 0:
        return False
    if word[-1] == "%":
        word = word[:-1]
    try:
        float(word)
        return True
    except ValueError:
        return False

def keep_caps(word):
    if word[0] in UPPER:
        other_upper = True # all caps
        other_lower = True # first word in sentence?
        for c in word[1:]:
            if c in UPPER:
                other_lower = False
            else:
                other_upper = False
        return other_upper or other_lower

def check_word_in_dict(word, dictionary):
    result = []
    try:
        di = dictionary["fuzzy"].index(word.lower())
        if keep_caps(word):
            result.append(word)
        else:
            result.append(dictionary["words"][di])
        return result
    except ValueError:
        before, word, after = depunct(word)
        if word is None:
            return None
        try:
            di = dictionary["fuzzy"].index(word.lower())
            value = None
            if keep_caps(word):
                value = word
            else:
                value = dictionary["words"][di]
            if before is not None:
                result.extend(before)
            result.append(value)
            if after is not None:
                result.extend(after)
        except ValueError:
            return None
    return result

def line_word_iter(line):
    return filter(lambda it: len(it) > 0, map(lambda x: x.strip(), line.split(" ")))

def preprocess():
    print("Preprocessing...")
    print("Loading content...")
    content = {}
    with open(get_text(), "r") as f:
        content = yaml.safe_load(f)

    dictionary = load_dict()

    unhandled = {}
    # word ended with "-" and isn't in dictionary; look for continuation
    next_first_handled = False
    
    for page in content:
        print(f"Processing: {page}...")
        boxes = content[page]["boxes"]
        unhandled[page] = []
        
        if boxes is None:
            continue
        for box_i, box in enumerate(boxes):
            text = box["text"]
            words = list(line_word_iter(text))
            words = intersperse(words, " ")
            box_unhandled = []

            fixed_words = []

            if next_first_handled:
                fixed_words.append(words[0])
                words = words[1:]
                next_first_handled = False
            
            for word in words:
                if word == " ":
                    if len(fixed_words) > 0 and fixed_words[-1] != " ":
                        fixed_words.append(word)
                    continue
                if word in PUNCTUATION:
                    fixed_words.append(word)
                    continue
                if is_number(word):
                    fixed_words.append(word)
                    continue
                if word in SYMBOLS:
                    fixed_words.append(word)
                    continue
                
                dict_word = check_word_in_dict(word, dictionary)
                if dict_word is not None:
                    fixed_words.extend(dict_word)
                    continue
                
                before, stripped, after = depunct(word)
                if is_number(stripped):
                    if before is not None:
                        fixed_words.extend(before)
                    fixed_words.append(stripped)
                    if after is not None:
                        fixed_words.extend(after)
                    continue

                if word.endswith("-"):
                    next_first = None
                    box_i = box_i + 1
                    if len(boxes) > box_i:
                        next_box = boxes[box_i]
                        next_first = next(line_word_iter(next_box["text"]))
                        while next_first is None and len(boxes) > box_i + 1:
                            box_i += 1
                            next_box = inner_boxes[box_i]
                            next_first = next(line_word_iter(next_box["text"]))
                    else:
                        next_box = None
                        next_page_key = "page-" + str(content[page]["page"] + 1)
                        while next_first is None and content[next_page_key] is not None:
                            page_inner = content[next_page_key]
                            inner_boxes = page_inner["boxes"]
                            if inner_boxes is None:
                                next_page_key = "page-" + str(page_inner["page"] + 1)
                                continue
                            box_i = 0
                            while next_first is None and len(inner_boxes) > box_i:
                                next_box = inner_boxes[box_i]
                                next_first = next(line_word_iter(next_box["text"]))
                            next_page_key = "page-" + str(page_inner["page"] + 1)
                            
                    if next_first is not None:
                        dict_word = check_word_in_dict(word[:-1] + next_first, dictionary)
                        if dict_word is not None:
                            fixed_words.append(word)
                            next_first_handled = True
                            continue

                box_unhandled.append({
                    "page": page,
                    "image": content[page]["image"],
                    "box": box["box"],
                    "text": box["text"],
                    "word": word
                })

            text = "".join(fixed_words).strip()

            for u in box_unhandled:
                u["used"] = text
                unhandled[page].append(u)

        if len(unhandled[page]) == 0:
            del unhandled[page]

    print(f"Done.")
    
    return {
        "content": content,
        "unhandled": unhandled
    }

PREPROC_RESULT = "state.yml"

def main():
    if os.path.exists(PREPROC_RESULT):
        data = yaml.safe_load(open(PREPROC_RESULT, "r"))
    else:
        data = preprocess()
        yaml.dump(data, open(PREPROC_RESULT, "w+"))

    first = next(iter(data["unhandled"]))
    if first is None:
        print(f"You're in luck! '{TEXT}' has no errors.")
        exit(0)
    first = data["unhandled"][first][0]

    window = Tk()
    
    def close_window():
        window.destroy()
    
    # Open an image file
    img = Image.open(first["image"])

    # Draw a red rectangle on the image
    draw = ImageDraw.Draw(img)
    x, y = first["box"][0], first["box"][1]
    ex, ey = x+ first["box"][2], y+ first["box"][3]
    draw.rectangle([x, y, ex, ey], outline="red")

    # Convert the image to a Tkinter-compatible photo image
    tk_img = ImageTk.PhotoImage(img)

    # Create a canvas and add the image to it
    canvas = Canvas(window, width=img.width, height=img.height)
    canvas.create_image(0, 0, anchor="nw", image=tk_img)
    canvas.grid(column=0, row=0, rowspan=6)

    # Create labels
    found_label = Label(window, text=f"In: \"{first['text']}\"")
    found_label.grid(column=1, row=0)

    unknown_label = Label(window, text=f"Unknown: \"{first['word']}\"")
    unknown_label.grid(column=1, row=1)

    # Create a row with a label and a text box
    subvar = StringVar()
    subvar.set(first['word'])
    substitution_label = Label(window, text="Substitution:")
    substitution_label.grid(column=1, row=2, sticky="e")
    substitution_value = Entry(window, textvariable=subvar)
    substitution_value.grid(column=2, row=2, sticky="w")

    replace_button = Button(window, text="Replace", command=close_window)
    replace_button.grid(column=1, row=3)
    keep_button = Button(window, text="Keep", command=close_window)
    keep_button.grid(column=2, row=3)

    window.mainloop()

    
if __name__ == "__main__":
    main()
