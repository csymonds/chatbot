import os
import openai
import re
from time import time
from uuid import uuid4
import utils

# Global constants:
OPENAI_KEY_FILE = 'key_openai.txt'
GPT3_MODEL = 'text-davinci-003'
GPT35_MODEL = 'gpt-3.5-turbo'
GPT4_MODEL = 'gpt-4'
MODEL_TEMP = 0.75
TOP_P = 1
TOKENS = 600
BOT_NAME = 'Cortex'
SYSTEM_MESSAGE_CHAT = utils.open_file('ltm/system_message_chat.txt')
# read in all json files in ltm to append to chat messages
EXAMPLE_MESSAGES = []
for file in os.listdir('ltm'):
    if file.endswith('.json'):
        EXAMPLE_MESSAGES += utils.load_json(f'ltm/{file}')

USE_GPT4 = True

# Define the directories to save logs and conversation data.
DIRECTORIES = ['gpt4_logs', 'gpt3_logs', 'cortex']


def create_directory_if_not_exists(directory_name):
    """
    Create the specified directory if it does not already exist.
    """
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)


def get_openai_api_key():
    """
    Load the OpenAI API key from the specified file.
    """
    return utils.open_file(OPENAI_KEY_FILE).strip()


def cleanup_text(text):
    """
    Clean up the text by removing unnecessary spaces and line breaks.
    """
    text = re.sub('[\r\n]+', '\n', text)
    text = re.sub('[\t ]+', ' ', text)
    return text

def format_response(response):
    formatted_response = response.replace('```', '\n')
    return formatted_response

def check_save_file(text):
    """
    Check for the presence of the keywords 
    for code and save to the appropriate file(s). e.g. code_type, file_name, and file_content
    """

    # check for the number of instances of 'code_type' in text
    num_code_types = text.count('code_type')
    # loop through the number of instances of 'code_type' in text
    for i in range(num_code_types):
        print('found code in text:\n', text)
        # get the first instances of code_type, file_name, and file_content (there could be more than one)
        match  = re.search('code_type:(.+?)\n', text)
        if match:
            code_type = match.group(i+1)
        file_name = re.search('file_name:(.+?)\n', text).group(i+1)
        # here we want to search for code after 'file_content:' but only until the next instance of 'code_type' or the end of the text
        file_content = re.search('file_content:(.+?)\ncode_type', text).group(i+1)
        # save the file content to the specified file name to code_files directory
        utils.save_file(f'code_files/{file_name}', file_content)

def save_log_and_return_text(filename, response, text, prompt):
    """
    Save the log to a file and return the cleaned text.
    """
    utils.save_file(filename, prompt + '\n\n==========\n\n' + text)
    return text.strip()


def gpt3_embedding(content, engine='text-embedding-ada-002'):
    """
    Create an embedding of the specified content using the specified engine.
    """
    content = content.encode(encoding='ASCII', errors='ignore').decode()
    response = openai.Embedding.create(input=content, engine=engine)
    return response['data'][0]['embedding']


def chat_completion(prompt, unique_id):
    """
    Generate a chat completion using either GPT-3.5 or GPT-4, depending on the global setting.
    """
    prompt = prompt.encode(encoding='ASCII', errors='ignore').decode()
    model = GPT4_MODEL if USE_GPT4 else GPT35_MODEL
    system_message = SYSTEM_MESSAGE_CHAT
    messages = [
        {"role": "system", "content": system_message},
    ]
    messages += EXAMPLE_MESSAGES
    messages += [
        {"role": "user", "content": prompt}
        ]
    utils.append_json(f'cortex/{unique_id}.json', messages)
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=MODEL_TEMP,
        top_p=TOP_P
    )
    text = response['choices'][0]['message']['content']
    text = cleanup_text(text)
    text = format_response(text)
    check_save_file(text)
    filename = f'{time()}_{model}.txt'
    return save_log_and_return_text(f'gpt4_logs/{filename}', response, text, prompt), response


def gpt3_completion(prompt):
    """
    Generate a GPT-3 completion for the specified prompt.
    """
    prompt = prompt.encode(encoding='ASCII', errors='ignore').decode()
    response = openai.Completion.create(
        model=GPT3_MODEL,
        prompt=prompt,
        max_tokens=TOKENS,
        temperature=MODEL_TEMP
    )
    text = response['choices'][0]['text']
    text = cleanup_text(text)
    filename = f'{time()}_gpt3.txt'
    return save_log_and_return_text(f'gpt3_logs/{filename}', response, text, prompt)


def chat(message):
    """
    Conduct a chat with the user, saving the conversation data.
    """
    timestamp = time()
    unique_id = str(uuid4())
    metadata = {
        'speaker': 'user',
        'time': timestamp,
        'message': message,
        'timestring': utils.timestamp_to_datetime(timestamp),
        'uuid': unique_id
    }
    utils.save_json(f'cortex/{unique_id}.json', metadata)
    text, response = chat_completion(message, unique_id)
    utils.append_json(f'cortex/{unique_id}.json', response)
    print(f'\n\n{BOT_NAME}: \n', text)


def init():
    """
    Initialize the application, setting the OpenAI API key and creating necessary directories.
    """
    openai.api_key = get_openai_api_key()

    for directory in DIRECTORIES:
        create_directory_if_not_exists(directory)


def main():
    """
    The main application loop.
    """
    init()

    while True:
        user_input = input('\n\nUSER: ')
        if user_input.lower() == 'quit':
            break
        chat(user_input)


if __name__ == '__main__':
    main()

