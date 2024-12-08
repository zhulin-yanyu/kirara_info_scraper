punctuation_half_to_full = {' ': '　','!': '！','"': '＂','#': '＃','$': '＄','%': '％','&': '＆','\'': '＇','(': '（',')': '）','*': '＊','+': '＋',',': '，','.': '．','/': '／',':': '：',';': '；','<': '＜','=': '＝','>': '＞','?': '？','@': '＠','[': '［','\\': '＼',']': '］','^': '＾','_': '＿','`': '｀','{': '｛','|': '｜','}': '｝','~': '～','-': '−',}

houbun_url = 'https://houbunsha.co.jp/'

tag_cn_dict = {'表紙': '封面','巻頭カラー': '卷头彩页','ゲスト': '客串','読み切り': '读切','センターカラー': '卷中彩页'}

class Comic:
    def __init__(self, title:str='', author:str='', volume=None, date=None):
        self.title = title # 作品名称
        self.author = author # 作者
        self.volume = volume # 卷数
        self.date = date # 发行日期
        self.cover = None
        self.tags = list() # 标签

    def dispose_date(self, year, month, day):
        return f'{year}-{month}-{day}'
    
    def get_title(self):
        return self.title

class Magazine:
    def __init__(self, title:str='', cover:str='', volume:str=''):
        self.title = title # 杂志名称
        self.cover = cover # 封面
        self.mag_volume = volume # 杂志期数
        self.comics = list()
    def put_comic(self, comic:Comic):
        self.comics.append(comic)

    def get_comic(self, comic:Comic):
        self.comics.remove(comic)

    def dispose_volume(self, year, month):
        return f'20{year}年{month}月号'
    
    def put_tags_by_magazine(self, tags, comic_title:str):
        for comic in self.comics:
            for tag, value in tag_cn_dict.items():
                if tag in tags and comic.title == comic_title:
                    comic.tags.append(value)