# Chatbot
### Author: Christopher Symonds
This is my implementation of a chatbot using a selection of APIs. You are free to use and build from this, however please credit as appropriate.

You may need an API key depending on the model you wish to use.

## Setup

1. If you don’t have Python installed, [install it from here](https://www.python.org/downloads/)

    Documentation for the [OpenAI chatGPT API is available here.](https://platform.openai.com/docs/libraries)

2. Clone this repository

   ```bash
   $ git clone git@github.com:csymonds/chatbot.git
   ```

3. Navigate into the project directory
   
   ```bash
   $ cd chatbot
   ```
## Virtual environment and dependency installation
4. Virtualize (Note: Windows users will see `venv/Scripts/activate`)
   ```
   $ python -m venv venv
   $ . venv/Scripts/activate
   ```

5. Install the library dependencies
   ```bash
   $ pip install -r requirements.txt
   ```
   

6. Add keys

   Step 1: Make a copy of the example environment variables files

   ```bash
   $ cp example_key_openai.txt key_openai.txt
   ```

   Step 2: Copy in your key to the respective file

      Add your [OpenAI API key](https://beta.openai.com/account/api-keys) to the newly created `key_openai.txt` file
    
      
7. Deactivate when finished
   ```
   $ deactivate
   ```

