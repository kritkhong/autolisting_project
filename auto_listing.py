from pathlib import Path, PosixPath
from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
import PIL
import re


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
def batch_resize_imgs(folder_path: PosixPath, img_size: int) -> PosixPath:
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


def extract_info(item: PosixPath, code_prefix: str, ocr) -> dict:
    info = {'need_verify': False}
    # caption = create_caption(item)
    res = read_code_price(item, code_prefix, ocr)
    print(res)
    # info['code'] = code
    # info['price'] = price
    # info['caption'] = caption

    # [ [code1] , [price] ]              1 code 1 price = OK
    # [ [code1,code2,code3] , [price] ]  multiple code with same price = OK
    # [ [...] , [price1, price2] ]       multiple price found = call for MANUAL
    # [ [] , [] ]                        no code or no price found = call for MANUAL
    if (False):
        info['need_verify'] = True

    return info


def read_code_price(item: PosixPath, code_prefix: str, ocr) -> list:
    text_read = ocr.ocr(f'{item}', cls=False)
    text_read = text_read[0]
    str_list = []
    for line in text_read:
        str_list.append(line[1][0])  # Now we get list of strings found
    code_list = []
    price_list = []
    code_regex = r'[' + f'{code_prefix}' + r']\d{2,4}'
    price_regex = r'(^|=|\s)(\d{0,2},?\d{2,3})'
    for str in str_list:
        code_list.extend(re.findall(code_regex, str))
        for groups in re.findall(price_regex, str):
            price_list.append(groups[1])

    # return in list of list
    # [ [code1,code2,...] , [price, ...] ]]
    return [code_list, price_list]


def create_caption(item: PosixPath) -> str:
    # using AI this always came out with something
    # just put something in front of string if not sure
    pass


# main function
ocr = PaddleOCR(lang='en')
imgs_dir = batch_resize_imgs(dir_path, img_size)
for img in imgs_dir.iterdir():
    info = extract_info(img, code_prefix, ocr)
    if (info['need_verify']):
        pass
        # raname
        # may be save file to subfolder 'manual needs' with some name then run through each item again at the end of all process using img show and prompt for human work
    else:
        pass
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

        #       extract code from image, price ->  item_info <-----------***** how to indicate RegEx?
        #       rename img to code
        #       use chatgpt vision to write a caption <-----------***** think about the prompt
        #       write item_info to xlsx file

        # ________DONE FOR NOW_________
