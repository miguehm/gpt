from openai import OpenAI
from typer import Typer

app = Typer()
client = OpenAI()

@app.command()
def main(prompt: str):
    response = client.chat.completions.create(
      model="gpt-4o",
      messages=[
        {
          "role": "user",
          "content": [
            {
              "type": "text",
              "text": f"{prompt}"
            }
          ]
        }
      ],
      temperature=1,
      max_tokens=1024,
      top_p=1,
      frequency_penalty=0,
      presence_penalty=0
    )
    print(response.choices[0].message.content)
    # print(response)

if __name__ == "__main__":
    app()
