import gdown


def download_material():
    url = 'https://drive.google.com/uc?id=1svoqVt5AA-FarH9HApVhxY-Zfby-4fzL'
    output = 'cache/docs.txt'
    gdown.download(url, output, quiet=False)
    url = 'https://drive.google.com/uc?id=1MM33I5jI7XSOPXsuMWwq0QJBzfcUy_2S'
    output = 'cache/tf_idf.txt'
    gdown.download(url, output, quiet=False)
