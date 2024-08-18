import re
import os
import sys
from aqt.utils import showWarning
from aqt import mw

addon_dir = os.path.dirname(os.path.realpath(__file__))
vendor_dir = os.path.join(addon_dir, "vendor")
sys.path.append(vendor_dir)
import openai

import time;
from openai import error


from html import unescape


def create_prompt(note, prompt_config):
    prompt_template = prompt_config['prompt']
    pattern = re.compile(r'\{\{\{(\w+)\}\}\}')
    field_names = pattern.findall(prompt_template)
    for field_name in field_names:
        if field_name not in note:
            raise ValueError(f"Field '{field_name}' not found in note.")
        prompt_template = prompt_template.replace(f'{{{{{{{field_name}}}}}}}', note[field_name])
    # unescape HTML entities and replace line breaks with spaces
    prompt_template = unescape(prompt_template)
    # remove HTML tags
    prompt_template = re.sub('<.*?>', '', prompt_template)
    return prompt_template


def send_prompt_to_openai(prompt):
    config = mw.addonManager.getConfig(__name__)
    if config['emulate'] == 'yes':
        print("Fake request chatgpt: ", prompt)
        return f"This is a fake response for emulation mode for the prompt {prompt}."

    try:
        print("Request to ChatGPT: ", prompt)
        openai.api_key = config['apiKey']

        def try_call():
            # gpt-3.5-turbo
            # gpt-4o-mini
            response = openai.ChatCompletion.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}], max_tokens=2000)
            print("Response from ChatGPT", response)
            return response.choices[0].message.content.strip()

        maximum = 300
        while maximum > 0:
            maximum -= 1
            try:
                return try_call()

            except error.RateLimitError as e:
                time.sleep(1.0)  # gpt-4o is has a token limit

    except Exception as e:
        print(f"An error occurred while processing the note: {str(e)}", file=sys.stderr)
        return None


def send_prompt_to_openai_image(prompt):
    config = mw.addonManager.getConfig(__name__)
    if config['emulate'] == 'yes':
        print("Fake request chatgpt: ", prompt)
        return f"This is a fake response for emulation mode for the prompt {prompt}."

    try:
        import requests
        import json
        import base64
        import pathlib

        print("Request to ChatGPT: ", prompt)
        api_key = config['apiKey']
        media_dir = pathlib.Path(mw.col.media.dir())

        # https://platform.openai.com/docs/api-reference/images/create
        url = "https://api.openai.com/v1/images/generations"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        data = {
            "prompt": prompt,
            "n": 1,
            "model": 'dall-e-3',
            "quality": 'hd',
            "response_format": "b64_json",
            "size": "1024x1024"  # Optional: can be adjusted to different sizes like "256x256", "512x512"
        }

        response = requests.post(url, headers=headers, data=json.dumps(data))

        if response.status_code == 200:
            response_json = response.json()
            revised_prompt = response_json["data"][0]["revised_prompt"]
            file_name = f"{revised_prompt[:100]}-{response_json['created']}"

            # with open(media_dir / f"{file_name}.json", mode="w", encoding="utf-8") as file:
            #     json.dump(response_json, file)

            image_info = (f"""<img alt="generated image" src="{file_name}.png">"""
                f"""\n:::plugin:::\n{response_json['created']},\n{revised_prompt},\n{file_name}.png"""
            )
            print(image_info)

            image_data = base64.b64decode(response_json["data"][0]["b64_json"])
            with open(media_dir / f"{file_name}.png", mode="wb") as png:
                png.write(image_data)

            # dalle 3 has request limit https://platform.openai.com/docs/guides/rate-limits/usage-tiers?context=tier-free
            # check your tier on https://platform.openai.com/settings/organization/limits
            time.sleep(10.0)
            return image_info

        print(f"Failed to get response: {response.status_code}")
        print(response.text)
        print(data)
        return None

    except Exception as e:
        print(f"An error occurred while processing the note: {str(e)}", file=sys.stderr)
        return None


send_prompt_to_openai = send_prompt_to_openai_image
