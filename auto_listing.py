
import PIL
import re
import base64
import json
import shutil
from collections import deque
from datetime import datetime
from pathlib import Path
from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
from dotenv import dotenv_values
from openai import OpenAI
from openpyxl import load_workbook

import csv  # temporary


# Adjustable variable
img_size = 500
stock_name = 'CN_JUN'  # stock_code = f'{stock_name}{stock_no:04}'
stock_no = 1
item_count = 10
price_check = 3000  # if price is suspiciously high call for manual check

# User's input
while (True):
    dir_path = Path(input('Specify full directory address of target folder: '))
    if dir_path.exists():
        break
    else:
        print('Path doesn\'t exist. Please check the address or path format or any typos.')
code_prefix = input(
    'Please specify the LETTER(s) code for more accuracy [if not just press \'Enter\']: ')


# resize entire folder of image and save to jpg format (acceptable format for chatGpt) return path of the result folder
def batch_resize_imgs(folder_path: Path, img_size: int) -> Path:
    result_folder = folder_path / 'result'
    result_folder.mkdir(exist_ok=True)
    for item in folder_path.iterdir():
        try:
            im = Image.open(item)
        except (PIL.UnidentifiedImageError, IsADirectoryError):
            continue
        ratio = min(im.size)/img_size if min(im.size) > img_size else 1
        size = (int(im.width / ratio), int(im.height / ratio))
        resized_img = im.resize(size)
        output_name = f'{result_folder}/{item.stem}.jpg'
        resized_img.save(output_name)
    return result_folder


# extract info from each images return return list of [code, caption, price]
def extract_info(item: Path, code_prefix: str, ocr) -> list:
    # call read code and price function
    cp_response = read_code_price(item, code_prefix, ocr)
    print(cp_response)
    code_list = cp_response[0]
    price_list = cp_response[1]

    # [ [code1] , [price] ]              1 code 1 price = OK
    # [ [code1,code2,code3] , [price] ]  multiple code with same price = OK
    # [ [...] , [price1, price2] ]       multiple price found = call for MANUAL
    # [ [] , [] ]                        no code or no price found = call for MANUAL

    # None value in any data point indicates that it needs human manual verification
    if len(price_list) > 1 or len(price_list) == 0:
        price_list = [None]
    price = price_list[0]
    if len(code_list) == 0:
        code_list = [None]

    # return list of [code, caption, price]
    if len(code_list) > 1:
        captions = multi_captions(item, code_list)
        info_list = []
        for code in code_list:
            info_list.append([code, captions[code], price])
        return info_list
    else:
        caption = single_caption(item)
        return [[code_list[0], caption, price]]


def read_code_price(item: Path, code_prefix: str, ocr) -> list:
    text_read = ocr.ocr(f'{item}', cls=False)
    text_read = text_read[0]
    str_list = []
    code_list = []
    price_list = []
    if (text_read):
        for line in text_read:
            str_list.append(line[1][0])  # Now we get list of strings found
        # if code prefix is not specified make it to A-Z
        code_prefix = 'A-Z' if code_prefix == '' else code_prefix.upper()
        # Regex explain: 1 Alphabet follow by 01-09 , 10-999
        code_regex = r'([' + f'{code_prefix}' + r'](0[1-9]|[1-9]\d{1,2}))'
        # Regex explain: (3-4 digits number) note: 2 digits make many noises e.g. size, model
        price_regex = r'([1-9]\d{2,3})'
        # often time when Thai language appear the ocr just ignore the Thai and concat text without white space example "A29 กระเป๋า 590" output = "A29590"
        # this pattern use often by this store
        concat_bug_regex = r'([' + f'{code_prefix}' + \
            r'](0[1-9]|[1-9]\d{1,2}))[a-zA-Z\s=]*([1-9]\d{2,3})'
        for str in str_list:
            match = re.findall(concat_bug_regex, str)
            # if match special case no need to match each code and price case
            if match:
                for group in match:
                    code_list.append(group[0])
                    price_list.append(group[2])
            # else match code first of match means it's not a price
            else:
                match = re.findall(code_regex, str)
                if match:
                    for group in match:
                        code_list.append(group[0])
                else:
                    for group in re.findall(price_regex, str):
                        price_list.append(group)
        # return in list of list
        # [ [code1,code2,...] , [price, ...] ]]
    return [code_list, price_list]


def single_caption(item: Path) -> str:
    ##### FOR TESTING #####
    return "--test caption--"
    #######################

    img_path = str(item)
    with open(img_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    env_vars = dotenv_values('.env')

    client = OpenAI(api_key=env_vars['OPEN_AI_KEY'])
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "Your duty is product captioning. \nMy products are mainly Disneyland and Disney's store products and some other store's product that fall in the same category such as gift ,souvenir that have cartoon or fantasy character design, sometime there are other kind of product too, you can caption this kind as you see proper.\nHow this work is\nI will send you the image of the product. You only return the caption phrase (in Thai language), not a sentence.\nThe caption phrase have a brief structure as below:\n1. Type of product\n2. Color of product (if have multiple indicates a few main ones)\n3. Design or print on product : this part can be what character, color of that character, pattern, color of pattern, special texture etc as you see proper.\n\nfor example: กระติกน้ำเก็บอุณหภูมิสีแดง รูป Mickey Mouse ใส่ชุดสีน้ำเงิน\nnotes:\n- Sometimes, there is a hint of product type in the picture as a text in Thai.\n- You can name character in English\n- We have some usual products, use these words: \n'พวง ตต ' is plush keychain (small doll with keyring), \n'ตต ' is plush doll (relatively bigger dool),\n'กระเป๋าเหรียญ' is small pocket with keyring, can be plush keyring with zip pocket\n"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            },
        ],
        temperature=1,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format={
            "type": "text"
        }
    )
    caption = response.choices[0].message.content
    print(caption)
    return caption


def multi_captions(item: Path, code_list: list) -> dict:
    ##### FOR TESTING #####
    test_dict = {}
    for code in code_list:
        test_dict[code] = "--test caption--"
    return test_dict
    #######################
    img_path = str(item)
    with open(img_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    env_vars = dotenv_values('.env')

    client = OpenAI(api_key=env_vars['OPEN_AI_KEY'])
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "Your duty is product captioning. \nMy products are mainly Disneyland and Disney's store products and some other store's product that fall in the same category such as gift ,souvenir that have cartoon or fantasy character design, sometime there are other kind of product too, you can caption this kind as you see proper.\nHow this work is\nI will send you the image of the product and list(array) contain product label code that label on the image.\nYou only return in raw JSON string of input product label code as a key and the caption phrase (in Thai language) as a value.\nIf my input is wrong, please explain the error in english uppercase in the caption.\nfor example:  input = ['A05','K034','A28'] \noutput = { \"A05\": caption#1, \"K034\": caption#2, \"A28\": \"NOT FOUND**\"}\nThe caption phrase have a brief structure as below:\n1. Type of product\n2. Color of product (if have multiple indicates a few main ones)\n3. Design or print on product : this part can be what character, color of that character, pattern, color of pattern, special texture etc as you see proper.\n\nfor example: กระติกน้ำเก็บอุณหภูมิสีแดง รูป Mickey Mouse ใส่ชุดสีน้ำเงิน\nnotes:\n- Sometimes, there is a hint of product type in the picture as a text in Thai.\n- You can name character in English\n- We have some usual products, use these words: \n'พวง ตต ' is plush keychain (small doll with keyring), \n'ตต ' is plush doll (relatively bigger dool),\n'กระเป๋าเหรียญ' is small pocket with keyring, can be plush keyring with zip pocket"
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": str(code_list)
                    }
                ]
            },
        ],
        temperature=1,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        response_format={
            "type": "text"
        }
    )
    str_response = json_trim(response.choices[0].message.content)
    print(str_response)
    return json.loads(str_response)


def json_trim(string: str) -> str:
    regex = r'[{\[].*[}\]]'
    match = re.search(regex, string, re.DOTALL)
    return match.group()


def img_rename(img: Path, info_list: list) -> str:
    list = []
    for info in info_list:
        list.append(info[0])
    if (list[0]):
        new_name = str(img.parent / ('_'.join(list) + img.suffix))
    else:
        new_name = str(img)
    img.rename(new_name)
    return new_name


# main function
ocr = PaddleOCR(lang='en', use_dilation=True)
# batch_resize_imgs return path of the result folder
imgs_dir = batch_resize_imgs(dir_path, img_size)

path_temp_xls = Path('./stock_template.xlsx')
path_result_xls = imgs_dir / \
    ('stock_' + datetime.now().strftime(r'%d%m%y_%H%M%S') + '.xlsx')
shutil.copy(path_temp_xls, path_result_xls)

# EXCEL PART
wb = load_workbook(path_result_xls)
ws = wb.active
check_needed = deque()
for img in imgs_dir.iterdir():
    print(img)
    if (img.suffix == '.xlsx'):
        continue
    info_list = extract_info(img, code_prefix, ocr)
    img_name = img_rename(img, info_list)  # rename image to sale code

    for info in info_list:
        # stock_name is hard coded for sake of testing you can make it user input
        stock_code = f'{stock_name}{stock_no:04}'
        # A:stock_code B:sale_code C:caption E:count(default=10) F:price
        row_val = {
            'A': stock_code,
            'B': info[0],
            'C': info[1],
            'E': item_count,
            'F': info[2],
        }
        ws.append(row_val)
        stock_no += 1

        # check_info = {
        #     'row': ws.max_row,
        #     'col': [],
        #     'img': img_name
        # }
        # # check to see if this row need manual work
        # if row_val['B'] == None:
        #     check_info["col"].append('B')
        # if row_val['F'] == None or int(row_val['F']) > price_check:
        #     check_info["col"].append('F')
        # # if manual needed put it queue
        # if len(check_info["col"] > 0):
        #     check_needed.append(check_info)
        #     # TODO
        #     # if GUI not running ----> run it
        #     gui_check()
        #     # let user check while automation is running


wb.save(path_result_xls)

# Now implement this csv to template xlsx
'''
    What tpe of info require manual work
    for now
    1. No price
    2. No code

    to consider
    1. Multi-caption
    2. Too expensive? >2,000
    '''
# if the img need Manual work in GUI as condition above
# Create manual work LIST might contain ---> file_path, info_list, position in xlsx
# skip renaming? if no code
# Queue the human work in LIST?
# Show img in GUI with highlight what's need attention
# back to rename
# edit xlsx

# ________DONE FOR NOW_________
