from requests import get
from json import loads


def get_anime_data(search):
    title_data_list = []
    url = 'https://api.ohli.moe/search?query=' + search
    response = get(url)

    if response.status_code == 200:

        txt = response.text
        json_data = loads(txt)

        for j in json_data:
            tmp_start = str(j["sd"])
            start_date = tmp_start[2:4] + '.' + tmp_start[4:6]
            if j["ed"] == 99999999:
                end_date = 'XX.XX'
            else:
                tmp_end = str(j["ed"])
                end_date = tmp_end[2:4] + '.' + tmp_end[4:6]
            item_num = j["i"]
            title = j["s"]

            title_data_list.append([start_date, end_date, item_num, title])

    else :
        print(response.status_code)

    return title_data_list


def get_sub_data(title_data):
    sub_url_and_name = []
    url = 'https://api.OHLI.moe/timetable/cap?i=' + str(title_data[2])
    response = get(url).text
    json_data = loads(response)
    print('json data : ', json_data)
    for one in json_data:
        if str(one['s']) == '0.0':
            continue
        sub_url_and_name += [one['a'], one['n'], one['s']],
    return sub_url_and_name


if __name__ == '__main__':
    title_data_list = get_anime_data("리제로")
    print('title : ', title_data_list)
    for data in title_data_list:
        sub_url_and_name = get_sub_data(data)
        print(data)
        print(sub_url_and_name)