import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Initialize the Telegram bot with your bot token
bot = telebot.TeleBot('Add_your_token_here')

# Define the scope for Google Sheets API
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

# Load credentials from a JSON file (credentials.json) and create a client to interact with Google Sheets
creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)

client = gspread.authorize(creds)

# Define the URL of the Google Sheets document
tablitsa = 'https://docs.google.com/spreadsheets/d/10MlGJUcY1ZwWQ_ifWwxpD3iZvdKR_RXnS1Nb4M9eoWo/edit?hl=ru#gid=0'

# Open the specified Google Sheets document and select the first sheet
sheet = client.open_by_url(tablitsa).sheet1

# Define constants for user states
WAITING_FOR_DATA = 2
WAITING_FOR_DATA_STATE = 1

# Create a dictionary to store the current state of users
user_state = {}

# Function to display the main menu options when the user starts the bot or types '/start'
def repeat(message):
    user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
    user_markup.row('/start','Скинь таблицу', '/stop')
    user_markup.row('Добавь товар', 'Добавь цену конкурентов')
    bot.send_message(message.chat.id, 'Что будем делать дальше?', reply_markup=user_markup)

# Handler for the '/start' command
@bot.message_handler(commands=['start'])
def start(message):
    user_markup = telebot.types.ReplyKeyboardMarkup(True, True)
    user_markup.row('/start','Скинь таблицу', '/stop')
    user_markup.row('Добавь товар', 'Добавь цену конкурентов')
    bot.send_message(message.chat.id, 'Рад вас приветствовать', reply_markup=user_markup)

# Handler for the 'Добавь товар' option in the main menu
@bot.message_handler(func=lambda message: message.text == 'Добавь товар')
def add_data(message):
    # Set the user state to WAITING_FOR_DATA_STATE to expect the user to input data
    user_state[message.chat.id] = WAITING_FOR_DATA_STATE
    bot.send_message(message.chat.id, 'Введите данные для добавления в таблицу в формате "название цена"')

# Handler for processing the data entered by the user when in WAITING_FOR_DATA_STATE
@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == WAITING_FOR_DATA_STATE)
def process_data(message):
    data = message.text.split('\n')
    for row in data:
        row_data = row.split()
        if len(row_data) >= 2 and row_data[-1].replace('.', '').isnumeric():
            # Extract name and price from the input message
            name = ' '.join(row_data[:-1]).strip()
            price_str = row_data[-1].strip().replace(',', '.')
            price = float(price_str)
            # Get the current time in the format "mm.dd HH:MM"
            current_time = datetime.now().strftime("%m.%d %H:%M")
            # Append the data to the Google Sheets document
            sheet.append_row([message.from_user.first_name, current_time, name, price, round(price * 1.1, 2)], value_input_option='USER_ENTERED', insert_data_option='INSERT_ROWS', table_range='A:B')
            bot.send_message(message.chat.id, f'Добавлено: {name} - {price}')
        else:
            bot.send_message(message.chat.id, 'Некорректный формат данных, введите данные в формате "Название цена"')
    user_state[message.chat.id] = None
    repeat(message)

# Handler for the 'Добавь цену конкурентов' option in the main menu
@bot.message_handler(func=lambda message: message.text == 'Добавь цену конкурентов')
def alternative_price(message):
    # Set the user state to WAITING_FOR_DATA to expect the user to input data
    user_state[message.chat.id] = WAITING_FOR_DATA
    bot.send_message(message.chat.id, 'Введите название товара и альтернативную цену в формате "название цена"')

# Handler for the 'Отправь в канал' option in the main menu
@bot.message_handler(func=lambda message: message.text == 'Отправь в канал')
def alternative_price(message):
    # Send a message to a specific Telegram channel with ID "-1001875591155"
    bot.send_message(chat_id="-1001875591155", text='Всем ку')

# Handler for processing the alternative price data entered by the user when in WAITING_FOR_DATA
@bot.message_handler(func=lambda message: user_state.get(message.chat.id) == WAITING_FOR_DATA)
def process_alt_price(message):
    data = message.text.split('\n')
    for row in data:
        row_data = row.split()
        if len(row_data) >= 2 and row_data[-1].replace('.', '').isnumeric():
            # Extract name and alternative price from the input message
            name = ' '.join(row_data[:-1]).strip()
            price_str = row_data[-1].strip().replace(',', '.')
            price = float(price_str)
            
            # Find all occurrences of the product name in the sheet
            cell_list = sheet.findall(name)
            if cell_list:
                # Update the alternative price for each occurrence of the product
                for cell in cell_list:
                    sheet.update_cell(cell.row, 6, price)
                bot.send_message(message.chat.id, f'Добавлена альтернативная цена для товара "{name}": {price}')
            else:
                bot.send_message(message.chat.id, f'Товар "{name}" не найден в таблице')
        else:
            bot.send_message(message.chat.id, 'Некорректный формат данных, введите данные в формате "название цена"')
    user_state[message.chat.id] = None
    repeat(message)

# Handler for the 'Скинь таблицу' option in the main menu
@bot.message_handler(func=lambda message: message.text == 'Скинь таблицу')
def google_sheet(message):
    # Send the URL of the Google Sheets document to the user
    bot.send_message(message.chat.id, tablitsa)

# Start the bot and keep it running indefinitely
bot.polling(none_stop=True)
