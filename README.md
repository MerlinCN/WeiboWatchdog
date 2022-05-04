<div align="center">

# WeiboWatchdog

_基于[WeiboBot](https://github.com/MerlinCN/WeiboBot) 开发的机器人_

<a href="https://pypi.org/project/WeiboBot/"><img alt="Python Version" src="https://img.shields.io/pypi/pyversions/WeiboBot" /></a>
<a href="https://pypi.org/project/WeiboBot/"><img alt="Python Implementation" src="https://img.shields.io/pypi/implementation/WeiboBot" /></a>
<a href="https://github.com/MerlinCN/WeiboBot/blob/master/LICENSE"><img alt="License" src="https://img.shields.io/github/license/MerlinCN/WeiboBot"></a>

</div>



`WeiboWatchdog`是`WeiboBot`的示例，用于演示如何使用`WeiboBot`，主要功能是转发微博上好看的小姐姐。

## 配置项

> 配置生成在`config.json`文件中

`cookies`:(必填)用浏览器登录m.weibo.cn,按F12获取cookies

`bark_key`:一个告警App [项目链接](https://github.com/Finb/Bark)

`special_users`:特殊用户的uid的列表（只转发别人微博的博主）

`ai_key`:百度云人体识别APIKey

`ai_secret`:百度云人体识别SecretKey

`is_repost`:是否转发微博

`is_upload`:是否上传图片