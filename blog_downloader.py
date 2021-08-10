import time
#import zipfile
from functools import partial
from os import mkdir, path
from concurrent.futures import ThreadPoolExecutor
from json import loads
from requests import get
from urllib.parse import unquote
from bs4 import BeautifulSoup
from google_drive_downloader import GoogleDriveDownloader as gdd


def download(url):
    start_time = time.time()
    if '.naver.' in url:
        print('download from naver blog')
        category_num, parent_category_num, name = get_naver_category_num(url)
        blog_id = get_naver_blog_id(url)
        page_list = get_naver_page_num(category_num, parent_category_num, blog_id)
        print(page_list)
        print(len(page_list))
        make_folder(name)

        # https://www.toptal.com/python/beginners-guide-to-concurrency-and-parallelism-in-python
        with ThreadPoolExecutor(max_workers=32) as executor:
            fn = partial(naver_down, './' + name + '/')
            executor.map(fn, page_list)

        print("실행 시간 : %s초" % (time.time() - start_time))

        '''
        print("실행 시간 : %s초" % (time.time() - start_time))
        with Pool(4) as p:
            p.starmap(naver_down, zip(cycle(['./' + name + '/']), page_list), 3)
        print("실행 시간 : %s초" % (time.time() - start_time))
        '''

    elif '.tistory.' in url:
        print('download from tistory blog')
        tistory_down(url)
    elif '.blogspot.' in url:
        print('download from blogspot blog')
        blogspot_down(url)
    else:
        print('Cannot find type of this url')
        print(url)

    return

def make_folder(name):
    dir = './' + name
    if (path.isdir(dir) == False):
        mkdir(dir)
    return

def get_naver_category_num(url):
    name = 'X'
    category_num = 0
    parent_category_num = 0
    # 입력받은 주소의 페이지를 가져온다
    response = get(url)
    bs = BeautifulSoup(response.text, "html.parser")

    # 입력받은 주소에서 첨부파일이 위치하는 iframe의 주소를 찾아서
    # ifrmae의 페이지를 다시 가져온다
    new_url = "https://blog.naver.com/" + bs.iframe["src"]
    response = get(new_url).text

    # iframe의 데이터를 한 줄씩 검색하며 카테고리 넘버를 확인한다
    for line in response.splitlines():
        if 'var nickName' in line:
            name = line.split("'")[1]
        if 'var categoryNo' in line:
            category_num = line.split("'")[1]
        if 'var parentCategoryNo' in line:
            parent_category_num = line.split("'")[1]
            break

    return category_num, parent_category_num, name

def get_naver_blog_id(url):
    blog_id = url.split('/')[3]

    return blog_id

def get_naver_page_num(category_num, parent_category_num, blog_id):
    start_time = time.time()
    naver_page_list = []
    cur_page = 0

    while True:
        print('cur_page :', cur_page)
        cur_page += 1
        req_all_page_in_category = 'https://blog.naver.com/PostTitleListAsync.naver?blogId='+ blog_id \
                                   +'&viewdate=&currentPage=' + str(cur_page) \
                                   + '&categoryNo=' + str(category_num) \
                                   + '&parentCategoryNo=' + str(parent_category_num) \
                                   + '&countPerPage=30'

        response = get(req_all_page_in_category).text
        post_list, total_cnt_data = response.split('[')[1].split(']')

        for data in total_cnt_data.split(','):
            if 'totalCount' in data:
                total_cnt = data.split(':')[1][1:-1]

        if int(total_cnt) <= (cur_page-1) * 30:
            break

        json_data = loads('[' + post_list + ']')
        for data in json_data:
            naver_page_list += 'https://blog.naver.com/' + blog_id + '/' + data['logNo'],

    print("실행 시간 : %s초" % (time.time() - start_time))

    return naver_page_list

def naver_down(dir, url):

    # 입력받은 주소의 페이지를 가져온다
    response = get(url)
    bs = BeautifulSoup(response.text, "html.parser")
    
    # 입력받은 주소에서 첨부파일이 위치하는 iframe의 주소를 찾아서
    # ifrmae의 페이지를 다시 가져온다
    new_url = "https://blog.naver.com/" + bs.iframe["src"]
    response = get(new_url).text
    
    # iframe의 데이터를 한 줄씩 검색하며 첨부파일이 존재하는지 확인하여 저장한다
    for line in response.splitlines():
        if 'encodedAttachFileUrl' in line:
            json_data = line.split("'")[1]
            file_data_list = loads(json_data)
            for file_data in file_data_list:
                #print(file_data["encodedAttachFileName"])
                #print(file_data["encodedAttachFileUrl"])
                file_url = file_data["encodedAttachFileUrl"]
                file_name = file_data["encodedAttachFileName"]
                data = get(file_url)
                with open(dir + file_name, 'wb')as file:
                    file.write(data.content)
            return


def tistory_down(url):
    response = get(url).text
    for line in response.splitlines():
        if '<a href="https://blog.kakaocdn' in line:
            for tag in line.split('<'):
                if 'a href="https://blog.kakaocdn' in tag:
                    file_url = tag.split('"')[1]
                    data = get(file_url)
                    file_name = file_url.split('?')[0].split('/')[-1]
                    file_name = unquote(file_name)
                    with open(file_name, 'wb')as file:
                        file.write(data.content)
        if '/attachment/' in line:
            bs = BeautifulSoup(line, "html.parser")
            file_url = bs.select_one('a')['href']
            data = get(file_url)
            file_type = file_url.split('.')[-1]
            file_name = bs.a.get_text() + '.' + file_type
            with open(file_name, 'wb')as file:
                file.write(data.content)


def blogspot_down(url):
    response = get(url).text
    bs = BeautifulSoup(response, "html.parser")
    for link in bs.select('p > a'):
        link = link.get('href')
        response = get(link).text
        bs = BeautifulSoup(response, "html.parser")
        file_name = bs.select_one('head > meta:nth-child(6)').get('content')
        file_id = link.split('/')[5]
        gdd.download_file_from_google_drive(file_id=file_id,
                                            dest_path='./' + file_name)


if __name__ == '__main__':
    print("Down start")
    url = 'https://blog.naver.com/qtr01122/222409647579'
    #url = 'https://blog.naver.com/jejungame/222294168944'
    #url = 'https://blog.naver.com/PostView.naver?blogId=rkp324&logNo=222302471998&categoryNo=72&parentCategoryNo=0&viewDate=&currentPage=2&postListTopCurrentPage=&from=postList&userTopListOpen=true&userTopListCount=5&userTopListManageOpen=false&userTopListCurrentPage=2'
    #url = 'https://blog.naver.com/siranami/222283230370'
    #url = 'http://dariking.tistory.com/803'
    #url = 'https://fuko.tistory.com/3523?category=873476'
    #url = 'https://sungwook0208.blogspot.com/2021/03/11.html?m=1'
    download(url)