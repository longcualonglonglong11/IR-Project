from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from model import search

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

search("fetching", 1)


@app.get("/")
async def read_root(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})


@app.get("/search/{query}", response_class=HTMLResponse)
async def read_item(request: Request, query: str):
    data, time, quantity = search(query, 20)
    if len(data) == 0:
        data = [
            "Not found result with '{}'\n".format(query),
        ]

    results = []
    for cont in data:
        header = cont.split('\n')[0]
        results.append({
            "header": cont.split('\n')[0],
            "content": cont[len(header):]
        })
    return templates.TemplateResponse("index.html",
                                      {"request": request, "results": results, "quantity": quantity,
                                       "time": time})
