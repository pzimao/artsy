import sys
from re import compile, findall
from os import mkdir, path, walk, remove, system
from PIL import Image
from threading import Thread
from time import time, sleep, localtime, strftime
import subprocess
import traceback
from socket import setdefaulttimeout

setdefaulttimeout(30)
reload(sys)


class MyThread(Thread):
    def __init__(self, url, path, src_url, host):
        """Constructor"""
        Thread.__init__(self)
        self.url = url
        self.path = path
        self.src_url = src_url
        self.host = host

    def run(self):
        try_count = 5
        while try_count > 0:
            try:
                curl_str = gen_curl_str(self.url, self.path)
                system(curl_str)
                break
            except:
                try_count = try_count - 1
                continue
        if path.getsize(self.path) < 250:
            remove(self.path)


def get_img_link(content):
    pattern1 = compile(r'(https://\w+\.cloudfront\.net/[\w_\-]+)/large\.jpg')
    if len(findall(pattern1, content)) > 0:
        for s in findall(pattern1, content):
            return s


def check_img_size(img_url, img_path):
    cur_size = 12
    try_count = 2
    while cur_size > 0 and try_count > 0:
        try:
            curl_str = gen_curl_str(img_url + '/dztiles/' + str(cur_size) + '/0_0.jpg', img_path)
            system(curl_str)
            if path.getsize(img_path) > 250:
                return img_url + '/dztiles/' + str(cur_size) + '/'
            cur_size = cur_size - 1
            try_count = 3
        except:
            try_count = try_count - 1
            continue
    if try_count <= 0:
        return ''
    return img_url + '/dztiles/0/'


def download_img_part(img_url, title):
    item_path = 'D:/Artsy/%s' % title
    mkdir(item_path)
    mkdir(item_path + '/result')
    mkdir(item_path + '/part')
    url = check_img_size(img_url, item_path + "/part/0_0.jpg")
    if url == '':
        print 'image url is invalid'
        return ''
    print 'downloading...'
    thread_ls = []
    for i in range(0, 10):
        for j in range(0, 10):
            if i != 0 or j != 0:
                img_name = str(i) + '_' + str(j)
                img_part_path = 'D:/Artsy/%s/part/%s.jpg' % (title, img_name)
                t = MyThread(url + img_name + '.jpg', img_part_path, url, img_url.split('/')[2])
                t.start()
                thread_ls.append(t)
    for i in thread_ls:
        i.join()
    return item_path


def imgmerge(path, img_name):
    high_size = 512
    width_size = 512
    imagefile = []
    col_ls = []
    row_ls = []
    width_final = 0
    high_final = 0
    for root, dirs, files in walk(path + '/part/'):
        for f in files:
            if '_' in f:
                img = Image.open(path + '/part/' + f)
                col_pos = int(f.split('_')[0])
                row_pos = int(f.split('_')[-1].split('.')[0])
                imagefile.append((img, col_pos, row_pos))
                if col_pos not in col_ls:
                    col_ls.append(col_pos)
                    width_final = width_final + img.size[0]
                if row_pos not in row_ls:
                    row_ls.append(row_pos)
                    high_final = high_final + img.size[1]

    target = Image.new('RGB', (width_final, high_final))
    for img_unit in imagefile:
        col_pos = img_unit[1]
        row_pos = img_unit[2]
        target.paste(img_unit[0], (width_size * (col_pos), high_size * (row_pos)))
    target.save(path + '/result/' + img_name + '.jpg', quality=100)
    print 'image save path: ', (path + '/result/' + img_name + '.jpg')


def main(url):
    content = ''
    try_count = 10
    while try_count > 0:
        try:
            content = get_page_content(url)
            break
        except:
            try_count = try_count - 1
            continue
    if try_count <= 0:
        return '0'
    title = strftime("%Y_%m_%d_%H_%M_%S", localtime(int(time())))
    img_part_link = get_img_link(content)
    if img_part_link == '':
        return '0'
    img_dir = download_img_part(img_part_link, title)
    if img_dir == '':
        return '0'
    imgmerge(img_dir, title)
    return '1'


def get_page_content(url):
    command_str = gen_curl_str(url)
    result = subprocess.Popen(command_str, shell=True, stdout=subprocess.PIPE)
    content = result.communicate()
    return str(content)


def gen_curl_str(url, write_path=''):
    command_str = 'curl -s -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3724.8 Safari/537.36" -H "Referer: ' + url + '" '
    command_str = command_str + url + " "
    if write_path != '':
        command_str = command_str + "> " + write_path
    return command_str


if __name__ == '__main__':
    if not path.exists('D:/Artsy'):
        mkdir('D:/Artsy')
    while True:
        url = raw_input('input image url:')
        try:
            start_time = time()
            if main(url) == '1':
                print 'download success, takes ', str(int(time() - start_time)), ' seconds'
            else:
                print 'download failed'
        except:
            print 'download abort'
            sleep(1)
        finally:
            print '-------------------'
