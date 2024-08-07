from openai import OpenAI
from typer import Typer
from rich.console import Console
from rich.markdown import Markdown

app = Typer()
client = OpenAI()

console = Console()


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
    md = Markdown(response.choices[0].message.content)
    console.print(md)


if __name__ == "__main__":
    app()
