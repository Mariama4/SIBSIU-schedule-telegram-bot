# -*- coding: utf-8 -*-
from time import sleep, time
from functools import wraps
import shutil
from bs4 import BeautifulSoup
from aiogram.types import ReplyKeyboardMarkup
import requests as request
from pdf2image import convert_from_path, convert_from_bytes
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import os
from aiogram.types import ReplyKeyboardRemove, \
    ReplyKeyboardMarkup, KeyboardButton, \
    InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "***"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

class CurrentData(object):
    """docstring"""

    listOfGroupName = ''
    listOfFileName = ''
    dictOfSchedule = ''
    listOfGroupNameRus = ''
    countOfPics = 0

    def __init__(self, listOfGroupName = '', listOfFileName = '', dictOfSchedule = '',listOfGroupNameRus = '', countOfPics = 0):
        """Constructor"""
        self.listOfGroupName = listOfGroupName
        self.listOfFileName = listOfFileName
        self.dictOfSchedule = dictOfSchedule
        self.listOfGroupNameRus = listOfGroupNameRus
        self.countOfPics = countOfPics


class CurrentSchedule(object):
    """docstring"""

    groupName = ''
    fileName = ''
    fileLink = ''

    def __init__(self, groupName = '', fileName = '', fileLink = '', countOfPics = 0):
        """Constructor"""
        self.groupName = groupName
        self.fileName = fileName
        self.fileLink = fileLink
        self.countOfPics = countOfPics


def mult_threading(func):
    """Декоратор для запуска функции в отдельном потоке"""

    @wraps(func)
    def wrapper(*args_, **kwargs_):
        import threading
        func_thread = threading.Thread(target=func,
                                       args=tuple(args_),
                                       kwargs=kwargs_)
        func_thread.start()
        return func_thread

    return wrapper

def getSchedule():
    local = 'https://www.sibsiu.ru/raspisanie/'

    response = request.get(local)

    responceText = BeautifulSoup(response.text, 'lxml')

    links = responceText.find_all('li', class_='ul_file')
    _listOfGroupNameRus = responceText.find_all('p', class_='p_title')

    local = local[0:-12]

    dictOfSchedule = dict()
    listOfGroupName = []
    listOfFileName = []
    listOfGroupNameRus = []
    localDir = os.getcwd()
    shutil.rmtree(localDir + "\\files")
    os.mkdir(localDir + "\\files")
    i = 0
    _i = 0

    for link in links:
        pdfLink = str(link).split('"')[3].replace('\\', '/')
        groupName = pdfLink.split('/')[3]

        if _listOfGroupNameRus[_i].text == 'Институт физической культуры, здоровья и спорта':
            _i += 1
        groupNameRus = _listOfGroupNameRus[_i].text
        if groupName not in listOfGroupName:
            listOfGroupName.append(groupName)
            listOfGroupNameRus.append(groupNameRus)
            _i += 1
        scheduleName = link.string
        resultLink = local + pdfLink
        resultLink = resultLink.replace(' ', '%20')
        listOfFileName.append(scheduleName)

        dictOfSchedule[f'{i}'] = (
        {'Group': {'Name': {f'{groupName}'}, 'Schedule Name': {f'{scheduleName}'}, 'Link': {f'{resultLink}'}}})
        i += 1


    return listOfGroupName, listOfFileName, dictOfSchedule, listOfGroupNameRus


def UpdateData():
    CurrentData.listOfGroupName, \
    CurrentData.listOfFileName, \
    CurrentData.dictOfSchedule, \
    CurrentData.listOfGroupNameRus = getSchedule()


def CheckLastModified(link):
    CurrentSchedule.fileLink = link[21:]
    res = request.get(link)
    res.encoding = 'utf-8'
    lastModified = res.headers['Last-Modified'] # дата последнего обновления файла

    return lastModified , res


def ConvertPDFtoPNG(res):

    path = (os.getcwd() + CurrentSchedule.fileLink)

    path = path.split('/')
    path.pop(len(path) - 1)

    _path = ''

    for i, val in enumerate(path):
        _path = _path + '/' + val
    path = _path[1:].replace('/', '\\')

    try:
        os.makedirs(path)
    except:
        pass

    path = (os.getcwd() + CurrentSchedule.fileLink).replace('\\', '/').replace('/', '\\')
    with open(f'{path}', 'wb') as f:
        f.write(res.content)

    popplerPath = "poppler-21.09.0\\Library\\bin"
    images = convert_from_bytes(open(fr'{path}', 'rb').read(), dpi=300, poppler_path=popplerPath)
    countOfPics = len(images)

    outputList = path[41:].split('\\')
    outputList.pop(0)
    outputList.pop(len(outputList)-1)
    outputPath = ''
    for i, val in enumerate(outputList):
        outputPath = outputPath + '/' + val

    outputPath = outputPath + f'/raspisanie{i}.png'
    outputPath = os.getcwd() + outputPath
    for i in range(1, countOfPics+1):
        outputPath = outputPath[:-5] + str(i) + outputPath[-4:]
        images[i-1].save(fr'{outputPath}')

    return outputPath, countOfPics

###

UpdateData()

###

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for i, val in enumerate(CurrentData.listOfGroupName):
        button = InlineKeyboardButton(text=CurrentData.listOfGroupNameRus[i], callback_data=val)
        keyboard.add(button)
    await message.reply(f'Привет,  {message.from_user.first_name} \nВыбери институт*:', reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in CurrentData.listOfGroupNameRus)
async def without_puree(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    numOfPos = CurrentData.listOfGroupNameRus.index(message.text)
    result = CurrentData.listOfGroupName[numOfPos]
    CurrentSchedule.groupName = result
    for i in CurrentData.dictOfSchedule:
        if str(CurrentData.dictOfSchedule[i]['Group']['Name'])[2:-2] == CurrentSchedule.groupName:
            button = types.KeyboardButton(text=str(CurrentData.dictOfSchedule[i]['Group']['Schedule Name'])[2:-2])
            keyboard.add(button)

    caption = 'Выберите файл и дождитесь ответа:'
    await bot.send_message(message.chat.id,caption, reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in CurrentData.listOfFileName)
async def without_puree(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton(text='В начало')
    keyboard.add(button)
    f = False
    f_ = False
    caption = ''
    photo = ''

    media = types.MediaGroup()
    for i in CurrentData.dictOfSchedule:
        if str(CurrentData.dictOfSchedule[i]['Group']['Name'])[2:-2] == CurrentSchedule.groupName:
            if str(CurrentData.dictOfSchedule[i]['Group']['Schedule Name'])[2:-2] == message.text:
                date, res = CheckLastModified(str(CurrentData.dictOfSchedule[i]['Group']['Link'])[2:-2])
                path, countOfPics = ConvertPDFtoPNG(res)
                if countOfPics != 1:
                    for i in range(1, countOfPics+1):
                        path = path[:-5] + str(i) + path[-4:]
                        media.attach_photo(open(path, "rb"), f'Страница документа: {i}')
                else:
                    path = path[:-5] + str(1) + path[-4:]
                    photo = open(path, "rb")
                    caption =  f'Дата обновления на сайте: {date}\nСтраница документа: {1}'
                    f_ = True
                f = True
                continue

    if f and f_ == False:
        await bot.send_media_group(message.from_user.id, media)
        await bot.send_message(message.chat.id,text=f'Дата обновления на сайте: {date}',
                               reply_markup=keyboard)
    elif f_:
        await bot.send_photo(message.chat.id,caption=caption, photo=photo,
        reply_markup=keyboard)
    else:
        await bot.send_message(message.chat.id,'Ошибка!',
        reply_markup=keyboard)

@dp.message_handler(commands="dice")
async def cmd_dice(message: types.Message):
    await message.answer_dice(emoji="🎲")

@dp.message_handler(lambda message: message.text == "В начало")
async def without_puree(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for i, val in enumerate(CurrentData.listOfGroupName):
        button = InlineKeyboardButton(text=CurrentData.listOfGroupNameRus[i], callback_data=val)
        keyboard.add(button)
    await bot.send_message(message.chat.id,f'Привет,  {message.from_user.first_name} \nВыбери институт*:', reply_markup=keyboard)

@dp.message_handler(content_types=['text'])
async def get_text_messages(message: types.Message):
    print(message)
    await bot.send_message( message.chat.id,"🤩")

if __name__ == '__main__':
   executor.start_polling(dp)



