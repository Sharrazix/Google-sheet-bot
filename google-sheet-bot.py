import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

bot = telebot.TeleBot('Add_your_token_here')


scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']


creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope) #You need to use service account to run this script

    
client = gspread.authorize(creds)

tablitsa = 'https://docs.google.com/spreadsheets/d/10MlGJUcY1ZwWQ_ifWwxpD3iZvdKR_RXnS1Nb4M9eoWo/edit?hl=ru#gid=0'

sheet = client.open_by_url(tablitsa).sheet1

WAITING_FOR_DATA = 2
WAITING_FOR_DATA_STATE = 1

user_state = {}

def repeat(message):
    user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
    user_markup.row('/start','Скинь таблицу', '/stop')
    user_markup.row('Добавь товар', 'Добавь цену конкурентов')
    bot.send_message(message.chat.id,'Что будем делать дальше?', reply_markup=user_markup)

@bot.message_handler(commands=['start'])
def start(message):
    user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
    user_markup.row('/start','Скинь таблицу', '/stop')
    user_markup.row('Добавь товар', 'Добавь цену конкурентов')
    bot.send_message(message.chat.id,'Рад вас приветсвовать', reply_markup=user_markup)

@bot.message_handler(func=lambda message: message.text == 'Добавь товар')
def add_data(message):
    user_state[message.chat.id] = WAITING_FOR_DATA_STATE
    bot.send_message(message.chat.id, 'Введите данные для добавления в таблицу в формате "название цена"')

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == WAITING_FOR_DATA_STATE)
def process_data(message):
    data = message.text.split('\n')
    for row in data:
        row_data = row.split()
        if len(row_data) >= 2 and row_data[-1].replace('.', '').isnumeric():
            name = ' '.join(row_data[:-1]).strip()
            price_str = row_data[-1].strip().replace(',', '.')
            price = float(price_str)
            current_time = datetime.now().strftime("%m.%d %H:%M")
            sheet.append_row([message.from_user.first_name, current_time, name, price, round(price * 1.1, 2)], value_input_option='USER_ENTERED', insert_data_option='INSERT_ROWS', table_range='A:B')
            bot.send_message(message.chat.id, f'Добавлено: {name} - {price}')
        else:
            bot.send_message(message.chat.id, 'Некорректный формат данных, введите данные в формате "Название цена"')
    user_state[message.chat.id] = None
    repeat(message)

@bot.message_handler(func=lambda message: message.text == 'Добавь цену конкурентов')
def alternative_price(message):
    user_state[message.chat.id] = WAITING_FOR_DATA
    bot.send_message(message.chat.id, 'Введите название товара и альтернативную цену в формате "название цена"')

@bot.message_handler(func=lambda message: message.text == 'Отправь в канал')
def alternative_price(message):
    bot.send_message(chat_id="-1001875591155", text='Всем ку')

@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == WAITING_FOR_DATA)
def process_alt_price(message):
    data = message.text.split('\n')
    for row in data:
	    row_data = row.split()
	    if len(row_data) >= 2 and row_data[-1].replace('.', '').isnumeric():
	        name = ' '.join(row_data[:-1]).strip()
	        price_str = row_data[-1].strip().replace(',', '.')
	        price = float(price_str)
	        # ищем все строки таблицы, которые содержат введенное название товара
	        cell_list = sheet.findall(name)
	        if cell_list:
	            for cell in cell_list:
	                # добавляем альтернативную цену в столбец "Альтернативная цена"
	                sheet.update_cell(cell.row, 6, price)
	            bot.send_message(message.chat.id, f'Добавлена альтернативная цена для товара "{name}": {price}')
	        else:
	            bot.send_message(message.chat.id, f'Товар "{name}" не найден в таблице')
	    else:
	        bot.send_message(message.chat.id, 'Некорректный формат данных, введите данные в формате "название цена"')
    user_state[message.chat.id] = None
    repeat(message)

@bot.message_handler(func=lambda message: message.text == 'Скинь таблицу')
def google_sheet(message):
    bot.send_message(message.chat.id, tablitsa)

bot.polling(none_stop=True)
