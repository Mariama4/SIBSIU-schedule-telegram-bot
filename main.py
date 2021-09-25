from bs4 import BeautifulSoup
from aiogram.types import ReplyKeyboardMarkup
import requests as request
from pdf2image import convert_from_path
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
import os

TOKEN = "2015437517:AAGoA9bop5hHJp-7g6OjY86KLY-wtusHyyo"
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)


class CurrentSchedule(object):
    """docstring"""

    groupName = ''
    fileName = ''
    fileLink = ''

    def __init__(self, groupName = '', fileName = '', fileLink = ''):
        """Constructor"""
        self.groupName = groupName
        self.fileName = fileName
        self.fileLink = fileLink

def getSchedule():
    local = 'https://www.sibsiu.ru/raspisanie/'

    response = request.get(local)

    responceText = BeautifulSoup(response.text, 'lxml')

    links = responceText.find_all('li', class_='ul_file')

    local = local[0:-12]

    dictOfSchedule = dict()
    listOfGroupName = []
    listOfFileName = []
    localDir = os.getcwd()
    i = 0

    for link in links:
        pdfLink = str(link).split('"')[3].replace('\\', '/')
        groupName = pdfLink.split('/')[3]
        if groupName not in listOfGroupName:
            listOfGroupName.append(groupName)
            try:
                os.makedirs(localDir + pdfLink[0:18] + groupName + '/Расписание%20занятий')
            except:
                pass
        scheduleName = link.string
        resultLink = local + pdfLink
        resultLink = resultLink.replace(' ', '%20')
        listOfFileName.append(scheduleName)

        dictOfSchedule[f'{i}'] = (
        {'Group': {'Name': {f'{groupName}'}, 'Schedule Name': {f'{scheduleName}'}, 'Link': {f'{resultLink}'}}})
        i += 1

    return listOfGroupName, listOfFileName, dictOfSchedule

def CheckLastModified(link):
    CurrentSchedule.fileLink = link[21:]
    res = request.get(link)
    res.encoding = 'utf-8'
    lastModified = res.headers['Last-Modified'] # дата последнего обновления файла

    return lastModified , res

def ConvertPDFtoPNG(res):
    path = (os.getcwd() + CurrentSchedule.fileLink).replace('/','\\')
    with open(path, 'wb') as f:
        f.write(res.content)

    popplerPath = "poppler-21.09.0\\Library\\bin"
    images = convert_from_path(path, 300, poppler_path=popplerPath)

    outputList = path[41:].replace('\\','/').split('/')
    outputList.pop(0)
    outputList.pop(4)
    outputPath = ''
    for i, val in enumerate(outputList):
        outputPath = outputPath + '/' + val

    outputPath = outputPath + '/raspisanie.png'
    outputPath = os.getcwd() + outputPath.replace('/','\\')
    images[0].save(outputPath )

    return outputPath

listOfGroupName, listOfFileName, dictOfSchedule = getSchedule()

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    for i in listOfGroupName:
        button = types.KeyboardButton(text=i)
        keyboard.add(button)
    await message.reply(f'Привет,  {message.from_user.first_name} \nВыбери институт*:', reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in listOfGroupName)
async def without_puree(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    CurrentSchedule.groupName = message.text
    for i in dictOfSchedule:
        if str(dictOfSchedule[i]['Group']['Name'])[2:-2] == message.text:
            button = types.KeyboardButton(text=str(dictOfSchedule[i]['Group']['Schedule Name'])[2:-2])
            keyboard.add(button)

    caption = 'Выберите файл и дождитесь ответа:'
    await bot.send_message(message.chat.id,caption, reply_markup=keyboard)

@dp.message_handler(lambda message: message.text in listOfFileName)
async def without_puree(message: types.Message):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    button = types.KeyboardButton(text='В начало')
    keyboard.add(button)
    f = False
    caption = ''
    photo = ''


    for i in dictOfSchedule:
        if str(dictOfSchedule[i]['Group']['Name'])[2:-2] == CurrentSchedule.groupName:
            if str(dictOfSchedule[i]['Group']['Schedule Name'])[2:-2] == message.text:
                date, res = CheckLastModified(str(dictOfSchedule[i]['Group']['Link'])[2:-2])
                photo = open(ConvertPDFtoPNG(res), "rb")
                caption = f'Дата обновления на сайте: {date}\nРасписание:'
                f = True
                continue

    if f:
        await bot.send_photo( message.chat.id,
                            photo,
                            caption,
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
    for i in listOfGroupName:
        button = types.KeyboardButton(text=i)
        keyboard.add(button)
    await message.reply(f'Привет,  {message.from_user.first_name} \nВыбери институт*:', reply_markup=keyboard)

@dp.message_handler(lambda message: message.text == "Дата обновления")
async def without_puree(message: types.Message):
    date =  CheckLastModified()[0] # [0] - дата обновления, [1] - .pdf файл
    caption = f'Дата последнего обновления расписания на сайте сибгиу - {date}'
    await bot.send_message( message.chat.id,
                          caption)

@dp.message_handler(content_types=['text'])
async def get_text_messages(message: types.Message):
    print(message)
    await bot.send_message( message.chat.id,"🤩")

if __name__ == '__main__':
   executor.start_polling(dp)




