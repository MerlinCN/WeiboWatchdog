# 微博自动转发Bot

## 项目介绍

自动转发关注的人的带图微博且保存

欢迎star

## 功能介绍

- [x] 点赞
- [x] 热门推荐
- [x] 定时启动
- [x] 保存图片视频
- [x] 保存livephoto
- [x] 人体识别再转发（百度API)
- [x] 解决验证码 see->[ddddOCR](https://github.com/sml2h3/ddddocr)
- [x] 评论互动
- [ ] 私信互动
- [ ] 自动回复
- [ ] livephoto截取最后一帧

## 主循环介绍

1. 刷新主页拿到微博列表

2. 遍历微博列表

3. 如果转发过的就不转发了

4. 如果有视频则点赞

5. 如果识别到人体且图片大小满足条件则转发

6. 如果不是原创微博，但是是特殊用户（只转发别人微博的博主），则转发

7. 休眠50~60秒（间隔随意，微博对刷新主页的限制并不高）有较小概率会返回 暂无数据

8. 心跳日志

## 文件说明

[Config.py](https://github.com/MerlinCN/WeiboWatchdog/blob/master/Src/Config.py): 存放配置文件，具体可看配置项

[Main.py](https://github.com/MerlinCN/WeiboWatchdog/blob/master/Src/Main.py): 主入口

[Engine.py](https://github.com/MerlinCN/WeiboWatchdog/blob/master/Src/Engine.py): 存放主逻辑

[Funcs.py](https://github.com/MerlinCN/WeiboWatchdog/blob/master/Src/Funcs.py): 用于远程指令调用（副入口）

[MyLogger.py](https://github.com/MerlinCN/WeiboWatchdog/blob/master/Src/MyLogger.py): 日志

[AITool.py](https://github.com/MerlinCN/WeiboWatchdog/blob/master/Src/AITool.py): 百度云AI接口

[Post.py](https://github.com/MerlinCN/WeiboWatchdog/blob/master/Src/Post.py): 微博类

[PCS.py](https://github.com/MerlinCN/WeiboWatchdog/blob/master/Src/PCS.py): 文件上传到百度云盘

[Util.py](https://github.com/MerlinCN/WeiboWatchdog/blob/master/Src/Util.py): 一些小工具

## 配置项

> 配置放在Config.py里

`Cookies`：（byte）在浏览器登录后复制过来就好

`BarkKey`：（字符串）一个告警App [项目链接](https://github.com/Finb/Bark)

`SpUser`：（列表）特殊用户的uid的列表（只转发别人微博的博主）

`API_key`：（字符串）百度云APIKey

`SecretKey`：（字符串）百度云SecretKey

