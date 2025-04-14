
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext, filters
from aiogram.dispatcher.filters.state import State, StatesGroup


import json

# db.py module for working with local database
import db

# api.py module for working with blockchain throughtoncenter api
import api
from config import settings

# take BOT_TOKEN and wallet adresses from config.json
TELEGRAM_BOT_TOKEN = settings.telegram_bot_token
MAINNET_WALLET = settings.mainnet_wallet
TESTNET_WALLET = settings.testnet_wallet
WORK_MODE = settings.work_mode

if WORK_MODE == "mainnet":
    WALLET = MAINNET_WALLET
else:
    WALLET = TESTNET_WALLET


# Configure logging
logging.basicConfig(level=logging.INFO)


bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.HTML)

# storage=MemoryStorage() needed for FSM
dp = Dispatcher(bot, storage=MemoryStorage())


class DataInput (StatesGroup):
    firstState = State()
    secondState = State()
    WalletState = State()
    PayState = State()


# /start command handler
@dp.message_handler(commands=['start'], state='*')
async def cmd_start(message: types.Message):
    await bot.delete_webhook()
    await message.answer(f"WORKMODE: {WORK_MODE}")
    # check if user is in database. if not, add him
    isOld = db.check_user(
        message.from_user.id, message.from_user.username, message.from_user.first_name)
    # if user already in database, we can address him differently
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    await message.answer("Как подавать котлеты?", reply_markup=keyboard)
    if isOld == False:
        await message.answer(f"You are new here, {message.from_user.first_name}!")
        await message.answer(f"to buy air send /buy")
    else:
        await message.answer(f"Welcome once again, {message.from_user.first_name}!")
        await message.answer(f"to buy more air send /buy")

    await DataInput.firstState.set()


@dp.message_handler(commands=['cancel'], state="*")
async def cmd_cancel(message: types.Message):
    await message.answer("Canceled")
    await message.answer("/start to restart")
    await DataInput.firstState.set()


@dp.message_handler(commands=['buy'], state=DataInput.firstState)
async def cmd_buy(message: types.Message):
    # reply keyboard with air types
    keyboard = types.InlineKeyboardMarkup(row_width=2, resize_keyboard=True)
    #buttons = ['Just pure 🌫', 'Spring forest 🌲','Sea breeze 🌊','Fresh asphalt 🛣']
    keyboard.add(
        types.InlineKeyboardButton(text='Just pure 🌫',callback_data='Just pure 🌫'), 
        types.InlineKeyboardButton(text='Spring forest 🌲',callback_data='Spring forest 🌲'),
        types.InlineKeyboardButton(text='Sea breeze 🌊',callback_data='Sea breeze 🌊'),
        types.InlineKeyboardButton(text='Fresh asphalt 🛣',callback_data='Fresh asphalt 🛣'),
    )
    await message.answer(f"Choose your air: (or /cancel)", reply_markup=keyboard)
    await DataInput.secondState.set()


@dp.message_handler(commands=['me'], state="*")
async def cmd_me(message: types.Message):
    await message.answer(f"Your transactions")
    # db.get_user_payments returns list of transactions for user
    transactions = db.get_user_payments(message.from_user.id)
    print('trns = ', transactions)
    if transactions is None:
        await message.answer(f"You have no transactions")
    else:
        for transaction in transactions:
            # we need to remember that blockchain stores value in nanotons. 1 toncoin = 1000000000 in blockchain
            await message.answer(f"{int(transaction['value'])/1000000000} - {transaction['comment']}")


# handle air type


# @dp.message_handler(state=DataInput.secondState)
@dp.callback_query_handler(
    lambda call: call.data in [
        'Just pure 🌫',
        'Spring forest 🌲',
        'Sea breeze 🌊',
        'Fresh asphalt 🛣'
    ], 
    state=DataInput.secondState,
)
async def air_type(call: types.CallbackQuery, state: FSMContext):
    if call.data == "Just pure 🌫":
        await state.update_data(air_type="Just pure 🌫")
        await DataInput.WalletState.set()
    elif call.data == "Fresh asphalt 🛣":
        await state.update_data(air_type="Fresh asphalt 🛣")
        await DataInput.WalletState.set()
    elif call.data == "Spring forest 🌲":
        await state.update_data(air_type="Spring forest 🌲")
        await DataInput.WalletState.set()
    elif call.data == "Sea breeze 🌊":
        await state.update_data(air_type="Sea breeze 🌊")
        await DataInput.WalletState.set()
    else:
        await call.message.answer("Wrong air type")
        await DataInput.secondState.set()
        return
    await call.message.answer(f"Send your wallet address")

# handle wallet address

@dp.message_handler(state=DataInput.WalletState)
async def user_wallet(message: types.Message, state: FSMContext):
    if len(message.text) == 48:
        res = api.detect_address(message.text)
        if res == False:
            await message.answer("Wrong wallet address")
            await DataInput.WalletState.set()
            return
        else:
            user_data = await state.get_data()
            air_type = user_data['air_type']
            # inline button "check transaction"
            keyboard2 = types.InlineKeyboardMarkup(row_width=1)
            keyboard2.add(types.InlineKeyboardButton(
                text="Check transaction", callback_data="check"))
            keyboard1 = types.InlineKeyboardMarkup(row_width=1)
            keyboard1.add(types.InlineKeyboardButton(
                text="Ton Wallet", url=f"ton://transfer/{WALLET}?amount=1000000000&text={air_type}"))
            keyboard1.add(types.InlineKeyboardButton(
                text="Tonkeeper", url=f"https://app.tonkeeper.com/transfer/{WALLET}?amount=1000000000&text={air_type}"))
            keyboard1.add(types.InlineKeyboardButton(
                text="Tonhub", url=f"https://tonhub.com/transfer/{WALLET}?amount=1000000000&text={air_type}"))
            await message.answer(f"You choose {air_type}")
            await message.answer(f"Send <code>1</code> toncoin to address \n<code>{WALLET}</code> \nwith comment \n<code>{air_type}</code> \nfrom your wallet ({message.text})", reply_markup=keyboard1)
            await message.answer(f"Click the button after payment", reply_markup=keyboard2)
            await DataInput.PayState.set()
            await state.update_data(wallet=res)
            await state.update_data(value_nano="1000000000")

    else:
        await message.answer("Wrong wallet address")
        await DataInput.WalletState.set()


@dp.callback_query_handler(lambda call: call.data == "check", state=DataInput.PayState)
async def check_transaction(call: types.CallbackQuery, state: FSMContext):
    # send notification
    user_data = await state.get_data()
    source = user_data['wallet']
    value = user_data['value_nano']
    comment = user_data['air_type']
    print('source, value, comment = ',source, value, comment)
    result = api.find_transaction(source, value, comment)
    if result == False:
        await call.answer("Wait a bit, try again in 10 seconds. You can also check the status of the transaction through the explorer (ton.sh/)", show_alert=True)
    else:
        db.v_wallet(call.from_user.id, source)
        await call.message.edit_text("Transaction is confirmed \n/start to restart")
        await state.finish()
        await DataInput.firstState.set()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
