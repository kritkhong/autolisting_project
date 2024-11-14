from paddleocr import PaddleOCR, draw_ocr
from PIL import Image
import PIL
from pathlib import Path


# ask user for folder location
while (True):
    dir_path = Path(input('Specify full directory address of target folder: '))
    if dir_path.exists():
        break
    else:
        print('Path doesn\'t exist. Please check the address or path format or any typos.')


# create result folder in side folder user provided
result_folder = dir_path / 'post_imgs'
result_folder.mkdir(exist_ok=True)

# makes image's width/height limited to {size_max} px, remain original ratio
img_size = 500

ocr = PaddleOCR(lang='en')  # need to run only once to load model into memory

# iterate trough 'image' files in folder
for item in sorted(dir_path.iterdir()):
    if not item.is_dir():
        try:
            im = Image.open(item)
        except (PIL.UnidentifiedImageError):
            continue

#       resize image 500px?
        ratio = min(im.size)/img_size if min(im.size) > 500 else 1
        size = (int(im.width / ratio), int(im.height / ratio))
        resized_img = im.resize(size)
#       if not jpg -> change format to jpg
        output_name = f'{result_folder}/{item.stem}.jpg'
        resized_img.save(output_name)

#       item_info = [ {code} , {caption}, {price}]

        result = ocr.ocr(output_name, cls=False)
        result = result[0]
        print(f'------------------{item.stem}---------------------')
        for line in result:
            print(line)

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
