import gdown


def download_material():
    url = 'https://drive.google.com/uc?id=1LrAu8jYKUNbWnhhALXJpSOO5nBk2yKGP'
    output = 'cache/docs.bin'
    gdown.download(url, output, quiet=False)
    url = 'https://drive.google.com/uc?id=1uuIa9TMVgvAopaPwD3xGjpLZfeH73Doc'
    output = 'cache/tf_idf.bin'
    gdown.download(url, output, quiet=False)
