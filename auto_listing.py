from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
import PIL
from pathlib import Path, PosixPath

# Adjustable variable
img_size = 500

# User's input
while (True):
    dir_path = Path(input('Specify full directory address of target folder: '))
    if dir_path.exists():
        break
    else:
        print('Path doesn\'t exist. Please check the address or path format or any typos.')


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


def extract_info(item: PosixPath) -> dict:
    info = {'need_verify': False}
    caption = create_caption(item)
    (code, price) = read_code_price(item)
    info['code'] = code
    info['price'] = price
    info['caption'] = caption

    # how to indicate file that need human manual read  *******
    if ():
        info['need_verify'] = True

    return info


def read_code_price(item: PosixPath) -> tuple:
    # something using Regex
    # Multiple codes
    # code not found
    # price not found
    pass


def create_caption(item: PosixPath) -> str:
    # using AI this always came out with something
    # just put something in front of string if not sure
    pass


# main function
ocr = PaddleOCR(lang='en')  # need to run only once to load model into memory
imgs_dir = batch_resize_imgs(dir_path, img_size)
for img in imgs_dir.iterdir():
    res = extract_info(img)
    if (res['need_verify']):
        pass
        # raname
        # may be save file to subfolder 'manual needs' with some name then run through each item again at the end of all process using img show and prompt for human work
    else:
        # rename to code .jpg

        # result = ocr.ocr(output_name, cls=False)
        # result = result[0]
        # print(f'------------------{item.stem}---------------------')
        # for line in result:
        #     print(line)

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
