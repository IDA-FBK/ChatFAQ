# ChatFAQ

A conversational agent built for the italian language that is able to give responses that belong to a specific domain of interest, related to health care area, using a LLM. In this case, the field considered is pregnancy and the first thousand days of the infant and GPT-4o is considered. 

## Try ChatFAQ 
You can try a version of ChatFAQ with the complete set of documents at this link
## Running the Code for a Demo
### 1. Prerequisites

- OpenAI Token
- Telegram Bot Token 

### 2. Set up the Project Environment

- Ensure to have Conda installed. If not, follow the instructions [here](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html).

- Create and Activate the virtual environment:
    ```bash
    python3 -m venv venv  # Create
    source venv/bin/activate    # Activate
    ```
- Install the dependencies:
    ```bash
    cd ChatFAQ
    pip install -r requirements.txt
    ```

- Dowload the linguistic model ```it_core_news_sm``` of spaCy
    ```bash
    python -m spacy download it_core_news_sm
    ```

- Modify the `.env` file with your OpenAI and Telegram Bot tokens:
    ```
    TELEGRAM_BOT_TOKEN = your_telegram_bot_token
    API_KEY_OPENAI = your_api_key_openai
    ```


### 3. Run the program
- Run the main script:
  ```bash
  python main.py
  ```