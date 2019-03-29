import requests
from celery import Celery

app = Celery('taksks',
             broker='redis://localhost',
             backend='redis://localhost')


@app.task()
def save_image(image_url, images_path, file_name, headers):
    """
    :param image_url: 图片url
    :param images_path: 图片存储路径
    :param file_name: 图片名
    :param headers: 头
    :return:
    """
    with open((images_path + '{}').format(file_name), 'wb+') as f:
        try:
            data = requests.get(image_url, headers=headers, timeout=20).content
            f.write(data)
        except Exception as e:
            print(e)
            print("下载过程出错！文件名：{}；URL：{}".format(file_name, image_url))
