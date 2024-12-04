from urllib.parse import quote
from bs4 import BeautifulSoup, Tag
from datetime import datetime
import requests
import time
import json
import re


re_kan = re.compile(r'(\d)巻') # 卷数
re_date = re.compile(r'(\d{4})年(\d{1,2})月(\d{1,2})日')

def get_jp(url:str, encoding:str = 'Shift_JIS'):
    resp = requests.get(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'},
        )
    resp.encoding = encoding
    return resp
def search_old_comics(range_min:int, range_max:int):
    # 爬取“既刊ラインナップ”
    base_url = 'http://www.dokidokivisual.com/comics/past/?tp=release&pn='
    url_list = [f'{base_url}{i}' for i in range(range_min, range_max+1)]
    result_dict = dict()

    for url in url_list[::-1]:
        resp = get_jp(url)
        if resp:
            resp_text = resp.text

            bs = BeautifulSoup(resp_text, 'html.parser')
            h2 = bs.find_all('h2', class_='date-title')
            for i in range(len(h2)):
                next_sibling = h2[i].find_next_sibling()
                month = h2[i].text.replace('発行', '')
                comics = list()

                while next_sibling and next_sibling.name != 'h2':
                    for j in next_sibling.find_all('div', class_='extra'):
                        title = j.find('p', class_='r-photo').find('img').attrs['title']
                        title = title.replace('\u3000', '　')
                        num_match = re_kan.search(j.find('strong').text)
                        if num_match:
                            kan_num = num_match.group(1)
                        author = j.find_all('p')[1].text
                        date = search_issuance_date(title, kan_num)
                        comics.append({
                            '标题': title,
                            '卷数': kan_num,
                            '作者': author,
                            '发行日期': date,
                        })
                        time.sleep(2) # 设置延时
                    next_sibling = next_sibling.find_next_sibling()
                result_dict[i+1] = {
                    '发行月份': month,
                    '发行作品': comics
                }
    return result_dict

def search_new_comics():
    # 爬取“新刊情報”
    base_url = 'http://www.dokidokivisual.com/comics/'
    result_dict = dict()

    resp = get_jp(base_url)
    if resp:
        resp_text = resp.text
        bs = BeautifulSoup(resp_text, 'html.parser')
        monthly = bs.find_all('div', class_='monthly')
        for i in range(len(monthly)):
            month = monthly[i].find('h2').text.replace('新刊', '')
            comics = list()

            for j in monthly[i].find_all('div', class_='item clearfix'):
                title = j.find('p', class_='photo').find('img').attrs['title']
                title = title.replace('\u3000', '　')
                num_match = re_kan.search(j.find('strong').text)
                if num_match:
                    kan_num = num_match.group(1)
                author = j.find('div', class_='item-right').find_all('p')[0].text
                the_date = j.find('div', class_='item-right').find_all('p')[1]
                date_match = re_date.search(the_date.text)
                if date_match:
                    y, m, d = date_match.groups()
                comics.append({
                    '标题': title,
                    '卷数': kan_num,
                    '作者': author,
                    '发行日期': f'{y}-{m}-{d}', # 日期格式：yyyy-mm-dd
                })
            result_dict[i+1] = {
                '发行月份': month,
                '发行作品': comics
            }
    return result_dict

def search_issuance_date(title, kan_num):
    # 搜索最新卷的发行日期
    base_url = 'https://houbunsha.co.jp/comics/detail.php?p='
    date = None

    # 添加数字
    full_width_dict = {chr(i): chr(i + 0xFEE0) for i in range(0x30, 0x3A)}  # 数字
    full_width_dict.update({chr(i): chr(i + 0xFEE0) for i in range(0x41, 0x5B)})  # 大写字母
    full_width_dict.update({chr(i): chr(i + 0xFEE0) for i in range(0x61, 0x7B)})  # 小写字母

    # 添加其他常用标点符号
    punctuation_half_to_full = {
        ' ': '　',
        '!': '！',
        '"': '＂',
        '#': '＃',
        '$': '＄',
        '%': '％',
        '&': '＆',
        '\'': '＇',
        '(': '（',
        ')': '）',
        '*': '＊',
        '+': '＋',
        ',': '，',
        '.': '．',
        '/': '／',
        ':': '：',
        ';': '；',
        '<': '＜',
        '=': '＝',
        '>': '＞',
        '?': '？',
        '@': '＠',
        '[': '［',
        '\\': '＼',
        ']': '］',
        '^': '＾',
        '_': '＿',
        '`': '｀',
        '{': '｛',
        '|': '｜',
        '}': '｝',
        '~': '～',
        '-': '−',
    }

    full_width_dict.update(punctuation_half_to_full)

    # 替换半角字符为全角字符
    if re.match(r'!\w', title):
        title = title.replace('!', '! ')
    title = title.replace('!', '！　')
    title = ''.join(full_width_dict.get(char, char) for char in title)
    encoded_title = quote(title, encoding='EUC-JP')
    resp = get_jp(f'{base_url}{encoded_title}', 'EUC-JP')

    if resp:
        resp_text = resp.text
        bs = BeautifulSoup(resp_text, 'html.parser')
        dd = bs.find_all('dd', class_='comicsno')

        for i in dd:
            num = re_kan.search(i.find('span').text)
            if num and kan_num and num.group(1) == kan_num:
                date_match = re.search(r'(\d{4})/(\d{1,2})/(\d{1,2})', i.text)
                if date_match:
                    y, m, d = date_match.groups()
                    date = f'{y}-{m}-{d}' # 日期格式：yyyy-mm-dd
                    return date
            else:
                continue
    return None

def get_comics_in_magazine(magazines:list|str, year:str = ''):
    # 抓取杂志连载的漫画
    base_url = 'http://www.dokidokivisual.com'
    old_magazines_of_year = 'backnumber/index.php?y='
    result_dict = dict()
    urls = list()
    magazines = magazines if isinstance(magazines, list) else [magazines] # 转换成列表

    if year:
        year = year if '20' in year else f'20{year}'
        for m in magazines:
            year_url = f'{base_url}/magazine/{m}/{old_magazines_of_year}{year}'

            resp = get_jp(year_url)
            if resp:
                resp_text = resp.text
                bs = BeautifulSoup(resp_text, 'html.parser')
                section = bs.find_all('div', class_='section')
                for j in section:
                    photo = j.find_all('p', class_='r-photo')
                    a_href = [f'{base_url}/magazine/{m}/{k.find('a').attrs['href'].replace('..', '')}' for k in photo]
                    urls.extend(a_href)


    else:
        urls = [f'{base_url}/magazine/{m}/' for m in magazines]

    for i in range(len(urls)):
        resp = get_jp(urls[i])
        if resp:
            resp_text = resp.text
            bs = BeautifulSoup(resp_text, 'html.parser')

            photo = bs.find('div', class_='photo')
            img = photo.find('img') # 杂志封面 # type: ignore
            magazine_name = img.attrs['alt'] # 杂志名称 # type: ignore
            img_src = img.attrs['src'] # type: ignore

            month_match = re.search(r'.*?(\d{2})(\d{2}).*?', img_src)
            if month_match:
                y, m = month_match.groups()
            monthly = f'20{y}年{m}月号' # 杂志月号

            comics_msg = photo.find('ul', class_='lineup') # type: ignore
            comics = comics_msg.find_all('li') # type: ignore

            # 获取右侧的细致信息
            info = photo.find_next_sibling('div', class_='info') # type: ignore
            info_comics = list()
            if isinstance(info, Tag):
                if info and '◆◆' in info.text:
                    sections = info.find_all(string=re.compile(r"◆◆.*?◆◆"))
                    for section in sections:
                        strong = section.find_next()
                        section_match = re.search(r'◆◆(.+)◆◆', section.text)
                        tags = section_match.group(1) # type: ignore
                        while strong:
                            if strong.name == 'strong' and '◆' not in strong.text:
                                title_match = re.search(r'[「|『](.+)[」|』]', strong.text)
                                title = title_match.group(1) # type: ignore
                                info_comics.append((tags, title))
                            try:
                                next_sibling_str = strong.next_sibling.get_text(strip=True)
                            except:
                                next_sibling_str = ''
                            strong = strong.find_next()
                            if re.search(r"◆◆.*?◆◆", next_sibling_str):
                                break
                            if not strong or strong.find_parent('div', class_='info') != info:
                                break
                elif info and info.find_all('u'):
                    sections = info.find_all('u')

                    for s in range(len(sections)):
                        previous_br = sections[s].find_previous()
                        next_br = sections[s].find_next()
                        next_u = next_br.find_next() if next_br and next_br.name == 'br' else None
                        previous_u = previous_br.find_previous() if previous_br and previous_br.name == 'br' else None
                        if next_u and next_u.name == 'u':
                            continue
                        elif previous_u and previous_u.name == 'u':
                            tags = f'{sections[s-1].get_text(strip=True)}\n{sections[s].get_text(strip=True)}'
                        else:
                            tags = sections[s].get_text(strip=True)
                        strong = sections[s].find_next()
                        while strong:
                            if strong.name == 'strong':
                                title_match = re.search(r'[「|『](.+)[」|』]', strong.text)
                                title = title_match.group(1) # type: ignore
                                info_comics.append((tags, title))
                            strong = strong.find_next()
                            if strong.name == 'u':
                                break
                            if not strong or strong.find_parent('div', class_='info') != info:
                                break

            comic_list = list()
            if comics:
                for item in comics:
                    text = item.get_text()
                    title_match = re.search(r'(.+)[「|『](.+)[」|』]', text)
                    if title_match:
                        author = title_match.group(1)
                        title = title_match.group(2)
                        comic_list.append({
                            '标题': title,
                            '作者': author
                        })
            else:
                comics = comics_msg.find_all('font', color='#8000FF') # type: ignore
                if comics:
                    for item in comics:
                        author = item.parent.previous_sibling.text.strip() if item.parent.previous_sibling.text.strip() != '' else item.previous_sibling.text.strip()
                        title_match = re.search(r'[「|『](.+)[」|』]', item.text)
                        if title_match:
                            title = title_match.group(1)
                            comic_list.append({
                                '标题': title,
                                '作者': author
                            })

            comic_list = put_tags_by_magazine(comic_list, info_comics)
            result_dict[i+1] = {
                '杂志名称': magazine_name,
                '杂志封面': f'{base_url}{img_src}',
                '连载月号': monthly,
                '连载作品': comic_list
                }
    return result_dict

def put_tags_by_magazine(comic_list, tag_list):
    # 处理杂志的刊载信息，为作品打上标签
    tag_cn_dict = {
        '表紙': '封面',
        '巻頭カラー': '卷头彩页',
        'ゲスト': '客串',
        '読み切り': '读切',
        'センターカラー': '卷中彩页'
        }

    for comic in comic_list:
        for tag, title in tag_list:
            if title in comic['标题']:
                translated_tags = []
                for key, value in tag_cn_dict.items():
                    if key in tag:
                        translated_tags.append(value)
                if translated_tags:
                    comic['标签'] = translated_tags
                break
        else:
            comic['标签'] = []
    return comic_list

def sort_comics_by_release_month(comic_dict, comics = True):
    # 将字典转换为列表，并提取发行月份和作品列表
    comic_list = []
    for key, value in comic_dict.items():
        if comics:
            release_month_str = value["发行月份"]
            release_month = datetime.strptime(release_month_str.replace('年', '-').replace('月', ''), '%Y-%m')
        else:
            release_month_str = value["连载月号"]
            release_month = datetime.strptime(release_month_str.replace('年', '-').replace('月号', ''), '%Y-%m')
        comic_list.append({
            "key": key,
            "release_month": release_month,
            "data": value
        })

    # 按发行月份排序
    comic_list.sort(key=lambda x: x["release_month"])

    # 将排序后的列表转换回字典格式
    sorted_comic_dict = {item["key"]: item["data"] for item in comic_list}
    return sorted_comic_dict


if __name__ == '__main__':
    magazines = ['kirara', 'max', 'carat', 'forward']
    comics_json = 'comic_list.json'
    magazines_json = 'magazine_list.json'

    # result = search_old_comics(1, 1)
    result = get_comics_in_magazine('carat')
    with open(magazines_json, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)

