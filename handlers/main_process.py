import logging
import config
import os

from aiogram.dispatcher import FSMContext
from aiogram.types import input_file

from states.access_code import AccessCode
from states.parse import ParseFile, HistoInfo
from parsers.main_parser import start_parse
from loader import dp, bot, db_manager
from texts.parse_text import get_cmd_parse_text
from keyboards.parse_keyboards import *
from keyboards.access_keyboard import *
from handlers.load_hist import start_hist_load
from pandas.io.excel import ExcelWriter


@dp.message_handler(commands=['parse'])
async def cmd_parse(message: types.Message, state: FSMContext):
    """ Обработчик команды /parse.

    Устанавливает состояние ожидания файла для обработки.

    :param message: Сообщение от пользователя.
    :param state: Состояние, в котором находится пользователь.
    :return:
    """

    logging.info(f"User {message.chat.id} requested {message.text}")
    if not db_manager.get_instance().check_if_user_has_access(message.chat.username, message.chat.id):
        await message.answer(f"К сожалению у Вас нет доступа к функциям бота. Желаете ввести ключ доступа?",
                             reply_markup=get_access_keyboard())
        await state.set_state(AccessCode.waiting_for_answer)
        return

    text = get_cmd_parse_text()

    await message.answer("".join(text), reply_markup=get_file_waiting_keyboard())
    await ParseFile.waiting_for_file.set()


@dp.message_handler(state=ParseFile.waiting_for_file, content_types=['document', 'text'])
async def process_parse_state(message: types.Message, state: FSMContext):
    """ Функция приема документа для обработки.

    Также контролирует выход из состояния ожидания файла.

    :param message: Сообщение от пользователя.
    :param state: Состояние, в котором находится пользователь.
    :return:
    """
    global file_name, document
    if message.content_type == 'document':
        logging.info(f"User {message.chat.id} sending some data in waiting_for_file state.")
        await message.answer(f"Загружаю Ваш файл...",
                             reply_markup=get_file_waiting_keyboard())
        try:
            document = await bot.get_file(message.document.file_id)
        except:
            logging.error(f"Ошибка в 54 handlers/main_process.py строке, не удалось загрузить файл")
            await message.answer("Ошибка загрузки файла (свыше 20 Мб)")
            await message.answer(f"Ошибка все еще не исправлена? - тогда вы можете обратиться к @NickByvaltsev",
                                 reply_markup=types.ReplyKeyboardRemove())
            await state.finish()
            return
        file_name = message.document.file_name
        await state.set_data({str(message.chat.id): document.file_path})
        await message.answer(f"Файл успешно загружен!")
    elif message.content_type == 'text' and message.text.lower() == 'обработать':
        logging.info(f"User {message.chat.id} start parse file.")
        try:
            await message.answer(f"Начинаю обработку...",
                                 reply_markup=types.ReplyKeyboardRemove())
            await start_parse((await state.get_data(str(message.chat.id)))[str(message.chat.id)], message, state,
                              file_name)
        except TypeError:
            await message.answer(f"Повторите отправку файла.", reply_markup=get_file_waiting_keyboard())
            await message.answer(f"Ошибка все еще не исправлена? - тогда вы можете обратиться к @NickByvaltsev",
                                 reply_markup=types.ReplyKeyboardRemove())
            return
        except UnicodeDecodeError:
            await message.answer(f"Необходимо отправить файл формата TXT.", reply_markup=get_file_waiting_keyboard())
            await message.answer(f"Ошибка все еще не исправлена? - тогда вы можете обратиться к @NickByvaltsev",
                                 reply_markup=types.ReplyKeyboardRemove())
            return
        await state.finish()
    elif message.content_type == 'text' and message.text.lower() == 'отмена':
        logging.info(f"User {message.chat.id} exiting from waiting_for_file state.")
        await message.answer(f"Отменяю обработку.", reply_markup=types.ReplyKeyboardRemove())
        await state.finish()
    else:
        await message.answer(f"Отправьте мне файл для обработки или напишите «отмена», чтобы выйти в меню.",
                             reply_markup=get_file_waiting_keyboard())


@dp.message_handler(commands=['load_info'], state=None)
async def hist_start(message: types.Message):
    await HistoInfo.waiting_timeframe.set()
    await message.answer(f"Введите таймфрейм: ")


@dp.message_handler(state=HistoInfo.waiting_timeframe)
async def wait_timeframe(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['timeframe'] = message.text
    await HistoInfo.next()
    await message.answer(f"Введите промежуток для анализа монет в минутах: ")


@dp.message_handler(state=HistoInfo.waiting_delta)
async def wait_delta(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['delta'] = message.text
    await HistoInfo.next()
    await message.answer(f"Введите разницу во времени сервера и gmt, например +5: ")


@dp.message_handler(state=HistoInfo.waiting_unx)
async def wait_unx(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['unx'] = message.text
    await HistoInfo.next()
    await message.answer(f"Если хотите выбрать 'Фьчерсы' введите - FUTURE, если хотите выбать 'Cпот' выберите - SPOT")


@dp.message_handler(state=HistoInfo.waiting_market)
async def wait_market(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['market'] = message.text
    info = await state.get_data()
    await message.answer(f"Начинаю обработку со следующими данными {info}")
    await state.finish()
    try:
        df = start_hist_load(info['timeframe'], info['delta'], info['unx'], info['market'],
                             xlsx_path=os.path.join(config.PATH_TO_RESULT_REPORT, f'{message.chat.id}.xlsx'))
        with ExcelWriter(os.path.join(config.PATH_TO_RESULT_REPORT, f'result.xlsx'), mode="w") as writer:
            df.to_excel(writer, sheet_name="Отчет", index=False)

        file = input_file.InputFile(os.path.join(config.PATH_TO_RESULT_REPORT, f'result.xlsx'),
                                    filename=f'{".".join(file_name.split(".")[:-1])}_result.xlsx')
        await message.answer_document(file)
    except:
        logging.info("Ошибка в файле main_proccess в 129 строке")
        await message.answer("Ошибка выгрузки исторических данных.")
