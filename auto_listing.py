
import PIL
import re
import base64
from pathlib import Path
from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
from dotenv import dotenv_values
from openai import OpenAI

import csv  # temporary


# Adjustable variable
img_size = 500

# User's input
while (True):
    dir_path = Path(input('Specify full directory address of target folder: '))
    if dir_path.exists():
        break
    else:
        print('Path doesn\'t exist. Please check the address or path format or any typos.')
code_prefix = input(
    'Please specify the LETTER(s) code for more accuracy [if not just press \'Enter\']: ')
code_prefix = 'A-Z' if code_prefix == '' else code_prefix.upper()
print(code_prefix)


# resize entire folder of image and save to jpg format (acceptable format for chatGpt) return path of the result folder
def batch_resize_imgs(folder_path: Path, img_size: int) -> Path:
    result_folder = folder_path / 'resized_imgs'
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

# extract info from each images return dictionary


def extract_info(item: Path, code_prefix: str, ocr) -> dict:
    # call read code and price function
    cp_response = read_code_price(item, code_prefix, ocr)
    print(cp_response)
    code_list = cp_response[0]
    price_list = cp_response[1]
    caption = create_caption(item)

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
    info_list = []
    for code in code_list:
        info_list.append([code, caption, price])
    return info_list


def read_code_price(item: Path, code_prefix: str, ocr) -> list:
    text_read = ocr.ocr(f'{item}', cls=False)
    text_read = text_read[0]
    str_list = []
    for line in text_read:
        str_list.append(line[1][0])  # Now we get list of strings found
    code_list = []
    price_list = []
    # Regex explain: 1 Alphabet follow by 01-09 , 10-9999
    code_regex = r'([' + f'{code_prefix}' + r'](0[1-9]|[1-9]\d{1,3}))'
    # Regex explain: (start of str / = / space)(2-5 digits number can have ',' separator) <-- use this one
    price_regex = r'(^|=|\s)(\d{0,2},?\d{2,3})'
    for str in str_list:
        for res_group in re.findall(code_regex, str):
            code_list.append(res_group[0])
        for res_group in re.findall(price_regex, str):
            price_list.append(res_group[1])
    # return in list of list
    # [ [code1,code2,...] , [price, ...] ]]
    return [code_list, price_list]


def create_caption(item: Path) -> str:
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
                        "text": "Your duty is product captioning. \nMy products are mainly Disneyland and Disney's store products and some other store's product that fall in the same category such as gift ,souvenir that have cartoon or fantasy character design, sometime there are other kind of product too, you can caption this kind as you see proper.\nHow this work is\nI will send you the image of the product. You only return the caption phrase (in Thai language), not a sentence.\nThe caption phrase have a brief structure as below:\n1. Type of product\n2. Color of product (if have multiple indicates a few main ones)\n3. Design or print on product : this part can be what character, color of that character, pattern, color of pattern, special texture etc as you see proper.\n\nfor example: กระติกน้ำเก็บอุณหภูมิสีแดง รูป Mickey Mouse ใส่ชุดสีน้ำเงิน\nnotes:\n- Sometimes, there is a hint of product type in the picture as a text in Thai.\n- You can name character in English\n- If picture have same product with several design,explain the product first and list all the different designs\n- We have some usual products, use these words: \n'พวง ตต ' is plush keychain (small doll with keyring), \n'ตต ' is plush doll (relatively bigger dool),\n'กระเป๋าเหรียญ' is small pocket with keyring, can be plush keyring with zip pocket\n"
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
    return response.choices[0].message.content


# main function
ocr = PaddleOCR(lang='en')
imgs_dir = batch_resize_imgs(dir_path, img_size)
with open(f'{dir_path}/csv_test_output.csv', 'w') as file:
    csv_writer = csv.writer(file)
    csv_writer.writerow(['Code', 'Product Caption', 'Price'])
    for img in imgs_dir.iterdir():
        info = extract_info(img, code_prefix, ocr)
        csv_writer.writerows(info)

        # raname
        # may be save file to subfolder 'manual needs' with some name then run through each item again at the end of all process using img show and prompt for human work

        # rename to code .jpg

        ############ THIS TO SAVE NEW FILE WITH OCR DETECTION #############
        # image = Image.open(output_name).convert('RGB')
        # boxes = [line[0] for line in result]
        # txts = [line[1][0] for line in result]
        # scores = [line[1][1] for line in result]
        # im_show = draw_ocr(image, boxes, txts, scores,
        #                    font_path='/Users/krit/Desktop/cs/project/autolisting/font/simfang.ttf')
        # im_show = Image.fromarray(im_show)
        # im_show.save(f'{result_folder}/{item.stem}_ocr.jpg')
        # ##############################################################

        # ________DONE FOR NOW_________
