import json
import time
from datetime import datetime

filename_json = '../data/json/tokens.json'
filename_txt = '../data/txt/only_read_tokens.txt'


def read_txt_tokens():
    with open(filename_txt, 'r') as f:
        data = f.readlines()
    return [token.replace('\n', '') for token in data]


def change_token(current_token):
    tokens = read_txt_tokens()
    if current_token != tokens[-1]:
        current_token = tokens[tokens.index(current_token) + 1]
        return current_token
    elif current_token == tokens[-1]:
        current_token = tokens[0]
        return current_token


def create_json_from_txt():
    tokens = read_txt_tokens()
    data = {token: True for token in tokens}
    with open(filename_json, 'w') as f:
        json.dump(data, f, indent=4)


def check_new_tokens_from_txt():
    tokens = read_txt_tokens()

    with open(filename_json, 'r') as f:
        try:
            data_json = json.load(f)
        except json.decoder.JSONDecodeError:
            create_json_from_txt()

    if len(data_json) != len(tokens):
        new_json = {token: True for token in tokens}
        with open(filename_json, 'w') as f:
            json.dump(new_json, f, indent=4)


def update_tokens_status():
    check_new_tokens_from_txt()
    with open(filename_json, 'r') as f:
        data = json.load(f)

    while True:
        print(f'Sleep for update tokens status for {60 - datetime.now().second}')
        time.sleep(60 - datetime.now().second)
        for token, status in data.items():
            data[token] = True
        with open(filename_json, 'w') as f:
            json.dump(data, f, indent=4)


def choose_first_free_token():
    with open(filename_json, 'r') as f:
        data = json.load(f)

    for token, status in data.items():
        if status is True:
            return token


def choose_next_free_token(current_token: str):
    with open(filename_json, 'r') as f:
        data = json.load(f)
    tokens = list(data.keys())
    for token in tokens:
        if token == current_token:
            i = tokens.index(token)
            if i + 1 != len(tokens):
                for t in tokens[i:]:
                    if data[t] is True:
                        return t
            else:
                for t in tokens[:i]:
                    if data[t] is True:
                        return t
    print('No free token :(')


def change_token_status_to_false(current_token: str):
    with open(filename_json, 'r') as f:
        data = json.load(f)
    for token in data.keys():
        if token == current_token:
            data[token] = False
    with open(filename_json, 'w') as f:
        json.dump(data, f, indent=4)


def main():
    token = 't.13A47sZrBoScLGaKcsy4vzrgqROnzKZa_fIPEs54JZbS4TslCANytqZcK69IfOYGSw5_r0pvnKc5HM0u_KxNVg'
    create_json_from_txt()
    # update_tokens_status()
    # print(choose_first_free_token())


if __name__ == '__main__':
    main()
