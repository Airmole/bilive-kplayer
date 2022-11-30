#!/usr/bin/python3
import asyncio
import os
import random
import time
import uuid
import requests
from bilibili_api import live, sync, search, Credential, Danmaku

# 仅管理员可弹幕指令控制
adminer_control = False
# 管理员权限哔哩哔哩账号昵称
adminer_nickname = 'Airmole'
# 直播间号
room_id = 22783053
# kplayer RPC HTTP API服务主机及端口号
kplayer_host = '127.0.0.1:4156'
# 点播视频存放目录
video_save_path = './video'
# playlist视频存放路径
playlist_save_path = './video'
# 超时视频删除时间（单位秒）
timeout_delete = 60 * 60 * 2
# 默认播放列表文件
playlist_file = './playlist.txt'
# 点播视频大小限制
bilivideo_sizelimit = '30m'
# 弹幕发送输出提示信息
danmaku_print = True
# 记录点播日志
save_order_log = False
# 弹幕回复所需cookie
cookie = {}

# 弹幕命令关键字设置
command_show_unplay_text = '查看未播放'
command_show_playing = '查看正在播放'
command_show_next_text = '查看下一条播放信息'
command_jump_time_text = '跳转时间到'  # 例如：跳转时间到30s
command_play_next_text = '播放下一条'
command_order_video_text = '点播视频'  # 例如：点播视频BV1Xt411F7tn
command_order_music_text = '点歌'  # 例如： 点歌 芒种 音阙诗听
command_show_duration_text = '查看播了多久了'

room = live.LiveDanmaku(room_id)


# 弹幕指令处理
@room.on('DANMU_MSG')
async def on_danmaku(event):
    sender_nickname = event['data']['info'][2][1]
    # 开启了仅管理员可弹幕控制
    if adminer_control is True and adminer_nickname != sender_nickname:
        return
    # 收到弹幕
    danmu_text = event['data']['info'][1]
    print(danmu_text)
    # 查看未播放
    if danmu_text == command_show_unplay_text:
        unplayed = unplayed_list()
        tips = '还有【' + str(len(unplayed['resources'])) + '】个视频未播放'
        print(tips)
        send_danmu(tips)
    # 查看正在播放
    if danmu_text == command_show_playing:
        playing = now_playing()
        playingpath = playing['resource']['path']
        names = playingpath.split('/')
        name = names[-1].replace(' ', '')
        tips = '正在为您播放的是【' + name[0:9] + '】'
        print(tips)
        send_danmu(tips)
    # 播放时间跳转
    if danmu_text.find(command_jump_time_text) == 0:
        result = jump_playtime(danmu_text)
        tips = '即将为您跳转到【' + result['resource']['seek'] + '】秒'
        print(tips)
        send_danmu(tips)
    # 播放下一条
    if danmu_text == command_play_next_text:
        play_next()
        tips = '即将为您播放下一条'
        print(tips)
        send_danmu(tips)
    # 点播视频
    if danmu_text.find(command_order_video_text) == 0:
        tips = '收到，正在为您安排点播~'
        send_danmu(tips)
        bvid = danmu_text.replace(' ', '').replace(command_order_video_text, '')
        save_log(sender_nickname, bvid, '')
        order_bilivideo(bvid)
    # 点歌MV
    if danmu_text.find(command_order_music_text) == 0:
        tips = '收到，正在为您安排点播~'
        send_danmu(tips)
        music_name = danmu_text.replace(command_order_music_text, '')
        result = await (search_video_by_order(music_name))
        if len(result['result']) <= 0:
            return
        save_log(sender_nickname, result['result'][0]['bvid'], music_name)
        order_bilivideo(result['result'][0]['bvid'])
    # 查看下一条播放信息
    if danmu_text == command_show_next_text:
        unplayed = unplayed_list()
        if len(unplayed['resources']) == 0:
            next_filename = random_palylist_next()
            play_path = playlist_save_path + '/' + next_filename
            playlist_add(play_path)
            names = play_path.split('/')
            name = names[-1].replace(' ', '')
            tips = '稍后为您播放的是【' + name[0:9] + '】'
            print(tips)
            send_danmu(tips)
        if len(unplayed['resources']) > 0:
            names = unplayed['resources'][0]['path'].split('/')
            name = names[-1].replace(' ', '')
            tips = '稍后为您播放的是【' + name[0:9] + '】'
            print(tips)
            send_danmu(tips)
    # 查看程序运行时长
    if danmu_text == command_show_duration_text:
        info = show_duration()
        tips = '已连续直播' + str(info['duration_timestamp']) + '秒'
        print(tips)
        send_danmu(tips)


async def search_video_by_order(keyword):
    return await search.search_by_type(keyword, search_type=search.SearchObjectType.VIDEO,
                                       order_type=search.OrderVideo.TOTALRANK, page=1)


# 点播视频（BV号）
def order_bilivideo(bvid):
    delete_old_video()
    result = order_play_bilivideo(bvid)
    wait = unplayed_list()
    tips = '点播成功，您前面还有【' + str(len(wait['resources'])) + '】条视频'
    send_danmu(tips)
    print(result)


# 点播日志记录
def save_log(nickname, bvid, keyword):
    if save_order_log is not True:
        return
    now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    fo = open("./log/order.log", "a+")
    fo.write("【%s】%s 点播 %s %s\n" % (now_time, nickname, bvid, keyword))
    fo.close()


# 弹幕输出
def send_danmu(text):
    if danmaku_print is not True:
        return
    text = str(text).encode("utf-8").decode("latin1")

    headers = {
        'authority': 'api.live.bilibili.com',
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9,zh-TW;q=0.8,en-US;q=0.7,en;q=0.6',
        'content-type': 'multipart/form-data; boundary=----WebKitFormBoundaryxAwxLfgAMpU2TaLW',
        'origin': 'https://live.bilibili.com',
        'referer': ('https://live.bilibili.com/%s' % (str(room_id))),
        'sec-ch-ua': '"Google Chrome";v="107", "Chromium";v="107", "Not=A?Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    }

    data = '------WebKitFormBoundaryxAwxLfgAMpU2TaLW\r\nContent-Disposition: form-data; ' \
           'name="bubble"\r\n\r\n0\r\n------WebKitFormBoundaryxAwxLfgAMpU2TaLW\r\nContent-Disposition: form-data; ' \
           'name="msg"\r\n\r\n'+text+'\r\n------WebKitFormBoundaryxAwxLfgAMpU2TaLW\r\nContent-Disposition: form-data; ' \
           'name="color"\r\n\r\n16777215\r\n------WebKitFormBoundaryxAwxLfgAMpU2TaLW\r\nContent-Disposition: ' \
           'form-data; name="mode"\r\n\r\n1\r\n------WebKitFormBoundaryxAwxLfgAMpU2TaLW\r\nContent-Disposition: ' \
           'form-data; name="fontsize"\r\n\r\n25\r\n------WebKitFormBoundaryxAwxLfgAMpU2TaLW\r\nContent-Disposition: ' \
           'form-data; name="rnd"\r\n\r\n1669772490\r\n------WebKitFormBoundaryxAwxLfgAMpU2TaLW\r\nContent' \
           '-Disposition: form-data; name="roomid"\r\n\r\n'+str(room_id)+'\r\n------WebKitFormBoundaryxAwxLfgAMpU2TaLW\r' \
           '\nContent-Disposition: form-data; ' \
           'name="csrf"\r\n\r\na51ec36dbfa2fc7b8c47506c914b7208\r\n------WebKitFormBoundaryxAwxLfgAMpU2TaLW\r' \
           '\nContent-Disposition: form-data; ' \
           'name="csrf_token"\r\n\r\na51ec36dbfa2fc7b8c47506c914b7208\r\n------WebKitFormBoundaryxAwxLfgAMpU2TaLW--\r' \
           '\n '

    response = requests.post('https://api.live.bilibili.com/msg/send', cookies=cookie, headers=headers, data=data)
    return response


# 删除已经超时的视频
def delete_old_video():
    for root, dirs, files in os.walk(video_save_path):
        for file in files:
            if file.find('.mp4') == -1:
                continue
            now_timestamp = int(time.mktime(time.localtime(time.time())))
            filename = file.replace('.mp4', '').replace(' ', '')
            if filename.isdigit() is False:
                return
            filename_timestamp = int(file.replace('.mp4', '').replace(' ', ''))
            # 过期视频文件删除
            if now_timestamp - timeout_delete > filename_timestamp:
                full_path = root + os.sep + file
                cache_path = './cache/' + str(file) + '.kpc'
                os.remove(full_path)
                if os.path.exists(cache_path):
                    os.remove(cache_path)
                print('已清除过期视频文件' + full_path)


# 查看获取运行时长
def show_duration():
    info = get('/play/duration')
    return info.json()


# 下载B站视频并加入播放队列
def order_play_bilivideo(video_code):
    if video_code.find('BV') != 0:
        return
    filename = str(int(time.mktime(time.localtime(time.time()))))  # 使用10位时间戳作为文件名
    video_url = 'https://www.bilibili.com/video/' + video_code
    path_option = ' --paths ' + video_save_path
    filename_option = ' --output ' + filename
    num_option = ' --max-downloads 1 '
    sizelimit_option = ' --max-filesize ' + bilivideo_sizelimit
    recode_option = ' --recode-video ' + 'flv '
    os.system('./yt-dlp' + path_option + filename_option + num_option + sizelimit_option + recode_option + video_url)
    video_path = video_save_path + '/' + filename + '.flv'
    result = playlist_add(video_path)
    return result


# 增加播放资源
def playlist_add(path):
    json = {'path': path, 'unique': str(uuid.uuid1())}

    result = post('/resource/add', json)
    return result.json()


# 跳过当前播放资源
def play_next():
    result = post('/play/skip')
    return result.json()


# 当前播放资源跳转到x秒
def jump_playtime(text):
    second = text.replace(' ', '').replace(command_jump_time_text, '').replace('s', '').replace('S', '')
    playing = now_playing()
    playing_unique = playing['resource']['unique']
    if int(second) < 0 or int(second) >= int(playing['duration']):
        return
    json = {
        'unique': playing_unique,
        'seek': second
    }
    result = post('/resource/seek', json)
    return result.json()


# 查看正在播放资源信息
def now_playing():
    playing = get('/resource/current')
    return playing.json()


# kplayer未播放放资源列表
def unplayed_list():
    unplayed = get('/resource/list')
    return unplayed.json()


# POST请求Kplayer API接口
def post(uri, json=None):
    if json is None:
        json = {}
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    response = requests.post('http://' + kplayer_host + uri, headers=headers, json=json)
    return response


# GET请求Kplayer API接口
def get(uri):
    headers = {'Content-Type': 'application/json; charset=utf-8'}
    response = requests.get('http://' + kplayer_host + uri, headers=headers)
    return response


# 获取默认播放列表
def get_playlist():
    playlist_names = []
    fo = open(playlist_file, "r")
    for line in fo.readlines():  # 依次读取每行
        line = line.strip()  # 去掉每行头尾空白
        playlist_names.append(line)
    # 关闭文件
    fo.close()
    return playlist_names


# 查找播放列表下一个文件名
def get_playlist_next(now):
    playlist = get_playlist()
    try:
        index = playlist.index(now)
    except Exception:
        index = len(playlist)
    if index + 1 >= len(playlist):
        return playlist[0]
    return playlist[index + 1]


# 随机播放播放列表一个视频
def random_palylist_next():
    playlist = get_playlist()
    index = random.randint(0, len(playlist) - 1)
    return playlist[index]


@room.on('VIEW')
async def loop(event):
    unplayed = unplayed_list()
    if len(unplayed['resources']) == 0:
        print('这是最后一个视频了')
        # 播放队列要空了，加一条视频
        next_filename = random_palylist_next()
        play_path = playlist_save_path + '/' + next_filename
        playlist_add(play_path)
        print('补充播放视频：' + play_path)
    if len(unplayed['resources']) > 0:
        print('下一条播放：' + unplayed['resources'][0]['path'])


# 连接直播间弹幕
sync(room.connect())
