# bilive-kplayer

哔哩哔哩直播弹幕点播。python脚本，通过[bilibili-api](https://nemo2011.github.io/bilibili-api/#/)获取直播间弹幕，根据弹幕指令控制[kplayer](https://docs.kplayer.net/v0.5.7/api/)RPC API接口播放，点播视频。

> 受限于[kplayer环境要求](https://docs.kplayer.net/v0.5.7/quick/install.html)，仅支持Linux环境并需要满足x86_64(amd64)与aarch64(arm64)CPU架构的硬件环境上运行.

## 使用方法

1. 克隆本项目

```shell
git clone https://github.com/Airmole/bilive-kplayer.git
```

> 项目目录下的kplayer文件可更新替换适合您机器的[kplayer发行版本](https://github.com/bytelang/kplayer-go/releases)
> 
> yt-dlp 用于下载用户点播视频，也可根据情况更新替换最新[yt-dlp发行版本](https://github.com/yt-dlp/yt-dlp/releases)

2. 配置kplayer config

```shell
# 复制kplayer配置文件，并编辑配置参数
cp ./config.json.example ./config.json
```

3. 修改配置python脚本

打开编辑 `main.py` 修改python配置参数

```python
# 仅管理员可弹幕指令控制
adminer_control = False
# 管理员权限哔哩哔哩账号昵称
adminer_nickname = 'Airmole'
# 直播间号
room_id = 22783053
# kplayer token参数见kplayer config配置
kplayer_token = 'bilive-kplayer'
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
save_order_log = True
# 弹幕回复所需cookie Credential（获取方式：https://nemo2011.github.io/bilibili-api/#/get-credential）
credential = Credential(sessdata="你的 SESSDATA", bili_jct="你的 bili_jct", buvid3="你的 buvid3", dedeuserid="你的 DedeUserID")
```

> 务必修改直播间号，否则监听的弹幕指令是我直播间的弹幕

4. 安装依赖

```shell
pip3 install -r requirements.txt
```

5. 启动kplayer

```shell
./kplayer play start -d
```

6. 启动python监听控制脚本

```shell
python3 ./main.py
```

finished！完成启动，去你直播间发送弹幕【查看正在播放】试试看？

## 弹幕指令有哪些

弹幕指令配置在 `main.py` 第36行，可以根据自己需要添加，修改配置。 

```python
# 弹幕命令关键字设置
command_show_unplay_text = '查看未播放'
command_show_playing = '查看正在播放'
command_show_next_text = '查看下一条播放信息'
command_jump_time_text = '跳转时间到'  # 例如：跳转时间到30s
command_play_next_text = '播放下一条'
command_order_video_text = '点播视频'  # 例如：点播视频BV1Xt411F7tn
command_order_music_text = '点歌'  # 例如： 点歌 芒种 音阙诗听
command_show_duration_text = '查看播了多久了'
```

## 如何获取cookie

1. 哔哩哔哩网页版在自己直播间，按下键盘F12，打开开发工具，发送一条弹幕

<img width="1070" alt="image" src="https://user-images.githubusercontent.com/20333663/204129388-1d31e59c-b715-4597-baf3-0c5aee94b45d.png">


2. 右键send,复制->复制为curl


3. 粘贴到[https://curlconverter.com/python/](https://curlconverter.com/python/)的curl command输入框，下方会自动识别出现cookies


<img width="1394" alt="image" src="https://user-images.githubusercontent.com/20333663/204129666-9ad3ba46-023a-4527-849f-b8dce535a0e9.png">


4. 将cookies复制，并粘贴到 `main.py` 中cookie的位置，改为cookie


> 注意，复制的是cookies = { ，复制到 `main.py` 中之后记得要改成 cookie = { 

## 相关参考文档

- [bilibili-api](https://nemo2011.github.io/bilibili-api/#/)
- [kplayer](https://docs.kplayer.net/)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [yt-dlp 用法选项](https://blog.csdn.net/z_y_z_l/article/details/121015231)
