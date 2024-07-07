import telebot
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto, InputMediaDocument
import os
import logging

# Configurações de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Token do bot do Telegram
API_TOKEN = '7490063304:AAHU9346-1HWbd0G7InbmlQXecdTmdPpKFU'

bot = telebot.TeleBot(API_TOKEN)

# Dicionário para armazenar as imagens e seus filtros
image_filters = {}

# Verifica se as pastas de imagens e documentos existem, caso contrário, cria
def check_and_create_directory(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

check_and_create_directory('images')
check_and_create_directory('documents')

# Função para adicionar uma nova imagem com filtros
def add_image(image_path, filters):
    image_filters[image_path] = filters

# Função para criar um teclado inline
def create_inline_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Upload", callback_data='upload'))
    keyboard.add(InlineKeyboardButton("Listar", callback_data='list'))
    keyboard.add(InlineKeyboardButton("Filtrar", callback_data='filter'))
    keyboard.add(InlineKeyboardButton("Ajuda", callback_data='help'))
    return keyboard

# Função para remover o teclado inline
def remove_inline_keyboard(message: Message, text: str):
    markup = telebot.types.ReplyKeyboardRemove(selective=False)
    bot.send_message(message.chat.id, text, reply_markup=markup)

# Função para salvar arquivos
def save_file(file_info, save_path):
    downloaded_file = bot.download_file(file_info.file_path)
    with open(save_path, 'wb') as new_file:
        new_file.write(downloaded_file)

# Comando de ajuda
@bot.message_handler(commands=['help'])
def send_help(message: Message):
    help_text = (
        "/help - Mostra esta mensagem de ajuda\n"
        "/upload - Envia uma imagem ou documento PDF para adicionar filtros\n"
        "/list - Lista todas as imagens e documentos com seus filtros\n"
        "/filter - Filtra imagens e documentos com base nos filtros especificados\n"
    )
    bot.reply_to(message, help_text)
    bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=create_inline_keyboard())

# Manipulador para o callback dos botões inline
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    remove_inline_keyboard(call.message, "Processando sua solicitação...")
    if call.data == 'upload':
        handle_upload(call.message)
    elif call.data == 'list':
        list_images(call.message)
    elif call.data == 'filter':
        filter_images(call.message)
    elif call.data == 'help':
        send_help(call.message)

# Comando para enviar uma imagem ou documento
def handle_upload(message: Message):
    bot.reply_to(message, "Envie a imagem ou documento PDF que deseja adicionar.")

# Manipulador de fotos
@bot.message_handler(content_types=['photo'])
def handle_photo(message: Message):
    try:
        logger.info(f"Photo received from user: {message.from_user.username}")
        photo_id = message.photo[-1].file_id
        file_info = bot.get_file(photo_id)
        
        # Nome da imagem com base no usuário e photo_id
        image_name = f"{message.from_user.username}_{photo_id}.jpg"
        image_path = os.path.join('images', image_name)
        
        # Salva a imagem
        save_file(file_info, image_path)
        
        bot.reply_to(message, "Imagem recebida! Envie agora os filtros (separados por vírgula) para essa imagem.")
        
        # Armazena temporariamente o caminho da imagem
        bot.register_next_step_handler(message, lambda msg: save_filters(msg, image_path))
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar a imagem. Tente novamente.")

# Manipulador de documentos
@bot.message_handler(content_types=['document'])
def handle_document(message: Message):
    try:
        logger.info(f"Document received from user: {message.from_user.username}")
        document_id = message.document.file_id
        file_info = bot.get_file(document_id)
        
        # Nome do documento original
        document_name = message.document.file_name
        document_path = None
        
        if message.document.mime_type.startswith('image/'):
            # Salva a imagem
            document_path = os.path.join('images', document_name)
            save_file(file_info, document_path)
            bot.reply_to(message, "Imagem recebida como documento! Envie agora os filtros (separados por vírgula) para essa imagem.")
        elif message.document.mime_type == 'application/pdf':
            # Salva o PDF
            document_path = os.path.join('documents', document_name)
            save_file(file_info, document_path)
            bot.reply_to(message, "Documento PDF recebido! Envie agora os filtros (separados por vírgula) para esse documento.")
        else:
            bot.reply_to(message, "Documento recebido, mas não é uma imagem nem um PDF.")
            return
        
        # Armazena temporariamente o caminho do documento
        bot.register_next_step_handler(message, lambda msg: save_filters(msg, document_path))
    except Exception as e:
        logger.error(f"Error handling document: {e}")
        bot.reply_to(message, "Ocorreu um erro ao processar o documento. Tente novamente.")

def save_filters(message: Message, document_path: str):
    try:
        filters = [f.strip() for f in message.text.split(',')]
        add_image(document_path, filters)
        bot.reply_to(message, f"Documento salvo com filtros: {', '.join(filters)}")
        bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=create_inline_keyboard())
    except Exception as e:
        logger.error(f"Error saving filters: {e}")
        bot.reply_to(message, "Ocorreu um erro ao salvar os filtros. Tente novamente.")

# Comando para listar imagens e documentos com filtros
def list_images(message: Message):
    try:
        if not image_filters:
            bot.reply_to(message, "Nenhuma imagem ou documento foi adicionado ainda.")
            bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=create_inline_keyboard())
            return

        for document_path, filters in image_filters.items():
            if document_path.endswith('.jpg'):
                with open(document_path, 'rb') as image_file:
                    bot.send_photo(message.chat.id, image_file, caption=f"Filtros aplicados: {', '.join(filters)}")
            elif document_path.endswith('.pdf'):
                with open(document_path, 'rb') as pdf_file:
                    bot.send_document(message.chat.id, pdf_file, caption=f"Filtros aplicados: {', '.join(filters)}")
        bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=create_inline_keyboard())
    except Exception as e:
        logger.error(f"Error listing images/documents: {e}")
        bot.reply_to(message, "Ocorreu um erro ao listar as imagens/documentos. Tente novamente.")

# Comando para filtrar imagens e documentos
def filter_images(message: Message):
    try:
        bot.reply_to(message, "Envie os filtros que deseja utilizar para buscar imagens e documentos (separados por vírgula).")
        bot.register_next_step_handler(message, perform_filter)
    except Exception as e:
        logger.error(f"Error initiating filter process: {e}")
        bot.reply_to(message, "Ocorreu um erro ao iniciar o processo de filtragem. Tente novamente.")

def perform_filter(message: Message):
    try:
        requested_filters = [f.strip() for f in message.text.split(',')]
        response_sent = False
        
        for document_path, filters in image_filters.items():
            if all(req_filter in filters for req_filter in requested_filters):
                if document_path.endswith('.jpg'):
                    with open(document_path, 'rb') as image_file:
                        bot.send_photo(message.chat.id, image_file, caption=f"Filtros aplicados: {', '.join(filters)}")
                elif document_path.endswith('.pdf'):
                    with open(document_path, 'rb') as pdf_file:
                        bot.send_document(message.chat.id, pdf_file, caption=f"Filtros aplicados: {', '.join(filters)}")
                response_sent = True
        
        if not response_sent:
            bot.reply_to(message, "Nenhuma imagem ou documento encontrado com os filtros especificados.")
        
        bot.send_message(message.chat.id, "Escolha uma opção:", reply_markup=create_inline_keyboard())
    except Exception as e:
        logger.error(f"Error performing filter: {e}")
        bot.reply_to(message, "Ocorreu um erro ao filtrar as imagens/documentos. Tente novamente.")

# Manipulador padrão para exibir o teclado inline sempre que uma mensagem for recebida
@bot.message_handler(func=lambda message: True)
def default_response(message: Message):
    bot.reply_to(message, "Bem-vindo! Use o teclado abaixo para selecionar uma opção.", reply_markup=create_inline_keyboard())

# Função principal para iniciar o bot
if __name__ == '__main__':
    logger.info("Bot is running...")
    bot.polling(none_stop=True)
