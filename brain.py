import os
import openai
import re
from time import time,sleep
from uuid import uuid4
import utils

# Key files:
openAIKeyFile = 'key_openai.txt'

# GPT Params
useGPT4 = True
gpt3Model = 'text-davinci-003'
gpt35Model = 'gpt-3.5-turbo'
gpt4Model = 'gpt-4'
modelTemp = 0.6
top_p = 1
tokens = 600

# Bot Params
bot_name = 'RANDO'
system_message_rando = utils.open_file('ltm/system_message_rando.txt')
dice_roll_ex_user = utils.load_json('ltm/dice_roll_example_user.json')
dice_roll_ex_assist = utils.load_json('ltm/dice_roll_example_assist.json')
conversation_depth = 3





def gpt3_embedding(content, engine='text-embedding-ada-002'):
    content = content.encode(encoding='ASCII',errors='ignore').decode()  # fix any UNICODE errors
    response = openai.Embedding.create(input=content,engine=engine)
    vector = response['data'][0]['embedding']  # this is a normal list
    return vector


def chat_completeion(prompt):
    global gpt4Model, gpt35Model, modelTemp, top_p, assist_dice_roll
    #{
    #    "model": "gpt-3.5-turbo",
    #    messages = [
    #            {"role": "system", "content": "You are a helpful assistant."},
    #            {"role": "user", "content": prompt},
    #            {"role": "assistant", "content": "The Los Angeles Dodgers won the World Series in 2020."},
    #            {"role": "user", "content": "Where was it played?"}
    #            ]
    #}
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
    while True:
        try:
            if useGPT4:
                model=gpt4Model
            else:
                model=gpt35Model
            system_message = system_message_rando
            messages = [
                {"role": "system", "content": system_message},
            ]
            messages.append(dice_roll_ex_user)
            messages.append(dice_roll_ex_assist)
            messages += [
                {"role": "user", "content": prompt}
                ]
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                temperature=modelTemp,
                top_p=top_p)
            text = response['choices'][0]['message']['content'].strip()
            text = re.sub('[\r\n]+', '\n', text)
            text = re.sub('[\t ]+', ' ', text)
            filename = '%s_gpt4.txt' % time()
            utils.save_file('gpt4_logs/%s' % filename, prompt + '\n\n==========\n\n' + text)
            return text, response
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT4 error: %s" % oops
            print('Error communicating with OpenAI:', oops)
            sleep(1)


def gpt3_completion(prompt):
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
    while True:
        try:
            response = openai.Completion.create(
                model=gpt3Model,
                prompt=prompt,
                max_tokens=tokens,
                temperature=modelTemp)
            text = response['choices'][0]['text'].strip()
            text = re.sub('[\r\n]+', '\n', text)
            text = re.sub('[\t ]+', ' ', text)
            filename = '%s_gpt3.txt' % time()
            utils.save_file('gpt3_logs/%s' % filename, prompt + '\n\n==========\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT3 error: %s" % oops
            print('Error communicating with OpenAI:', oops)
            sleep(1)


def init():
    openai.api_key = utils.open_file(openAIKeyFile).strip()
    
    if not os.path.exists('gpt4_logs'):
        os.makedirs('gpt4_logs')

    if not os.path.exists('gpt3_logs'):
        os.makedirs('gpt3_logs')

    if not os.path.exists('cortex'):
        os.makedirs('cortex')

def chat(a):
    global bot_name
    payload = list()
    timestamp = time()
    timestring = utils.timestamp_to_datetime(timestamp)
    message = a
    #vector = gpt3_embedding(message)
    unique_id = str(uuid4())
    metadata = {'speaker': 'user', 'time': timestamp, 'message': message, 'timestring': timestring, 'uuid': unique_id}
    utils.save_json('cortex/%s.json' % unique_id, metadata)
    text, response = chat_completeion(message)
    #timestamp = time()
    #timestring = utils.timestamp_to_datetime(timestamp)
    #message = '%s: %s - %s' % (bot_name, timestring, output)
    #unique_id = str(uuid4())
    #metadata = {'speaker': bot_name, 'time': timestamp, 'message': message, 'timestring': timestring, 'uuid': unique_id}
    utils.save_json('cortex/%s.json' % unique_id, response)
    print('\n\n%s: ' % bot_name, text)
    

if __name__ == '__main__':
    
    init()

    while True:
        #### get user input, save it, vectorize it, save to pinecone
        a = input('\n\nUSER: ')
        if a == 'quit':
            break
        chat(a)
        