import requests
import json
import time
import pickle

class WeChatPush:
    def __init__(self, token_str, token_file='access_token.data'):
        """
        初始化 WeChatPush 类的实例
        corpid: 企业微信的 corpid（公司 ID）
        corpsecret: 企业微信的 corpsecret（应用密钥）
        agentid: 企业微信的 agentid（应用 ID）
        :param token_file: 存储 access_token 的文件路径（默认 'access_token.data'）
        """
        self.token_list = token_str.split('#')
        self.corpid = self.token_list[0]  # 企业微信的 corpid
        self.corpsecret = self.token_list[1]  # 企业微信的 corpsecret
        self.agentid = self.token_list[2]  # 企业微信的 agentid
        self.token_file = token_file
        # 加载本地保存的 access_token
        self.access_token = self._load_access_token()

    def _load_access_token(self):
        """
        从二进制文件读取 access_token，如果 token 有效则返回，否则返回 None
        :return: 返回有效的 access_token 或 None
        """
        try:
            with open(self.token_file, 'rb') as f:
                data = pickle.load(f)
                access_token = data.get('access_token')
                expire_time = data.get('expire_time')
                # 如果 token 存在且没有过期，则返回该 token
                if access_token and time.time() < expire_time:
                    return access_token
        except (FileNotFoundError, EOFError):
            # 如果文件未找到或为空，则返回 None
            return None
        return None

    def _save_access_token(self, access_token, expires_in):
        """
        以二进制方式保存新的 access_token 到文件
        :param access_token: 新的 access_token
        :param expires_in: 过期时间（单位：秒）
        """
        expire_time = time.time() + expires_in  # 计算过期时间
        data = {
            "access_token": access_token,
            "expire_time": expire_time
        }
        # 将 access_token 和过期时间以二进制方式保存到文件
        with open(self.token_file, 'wb') as f:
            pickle.dump(data, f)
        self.access_token = access_token

    def _get_access_token(self):
        """
        获取有效的 access_token
        :return: 如果已有有效 token，返回该 token；否则请求新 token
        """
        if self.access_token:
            # 如果已经有有效的 token，直接返回
            return self.access_token

        # 请求企业微信获取新的 token
        url = f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corpid}&corpsecret={self.corpsecret}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('errcode') == 0:
                # 如果请求成功，保存新的 token 并返回
                access_token = data['access_token']
                expires_in = data['expires_in']
                self._save_access_token(access_token, expires_in)
                return access_token
            else:
                raise Exception(f"获取 access_token 失败: {data['errmsg']}")
        else:
            raise Exception(f"请求失败, 错误代码: {response.status_code}")

    def send_message(self, title, content):
        """
        发送企业微信消息
        :param title: 消息的标题
        :param content: 消息的内容（HTML 格式）
        :return: 返回发送请求的响应 JSON 数据
        """
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "zh-CN,zh;q=0.9",
            "content-type": "application/json;charset=UTF-8",
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
        }

        # 获取有效的 access_token
        access_token = self._get_access_token()
        # 构建发送消息的 URL
        push_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}'

        # 清理 HTML 标签，只保留纯文本
        clean_digest = content.replace("<div>", "").replace("</div>", "") \
                             .replace("<ul>", "").replace("</ul>", "") \
                             .replace("<li>", "").replace("</li>", "") \
                             .replace("<span>", "\n").replace("</span>", "")

        # 构建消息的 JSON 数据
        data = {
            "touser": "@all",  # 发送给所有用户
            "msgtype": "mpnews",  # 消息类型是图文消息
            "agentid": int(self.agentid),  # 应用 ID
            "mpnews": {
                "articles": [
                    {
                        "title": title.replace("\n", ""),  # 消息标题
                        "thumb_media_id": "2olmh7kAnR5KVR0BuHzAiOuWEFkBF8ITqi6AQxTUR3bQiFpnP2UukUn9xNtk-LvIm",  # 消息缩略图的 Media ID
                        "author": "锐大神",  # 消息作者
                        "content_source_url": "https://www.fglt.net/index.php",  # 消息的内容链接
                        "content": content,  # 消息详细内容
                        "digest": clean_digest.strip(),  # 消息摘要（去除 HTML 标签后的摘要）
                    }
                ]
            },
        }

        # 发送 POST 请求
        response = requests.post(url=push_url, json=data, headers=headers)
        if response.status_code == 200:
            print("消息发送成功")
            return response.json()
        else:
            print(f"消息发送失败, 错误代码: {response.status_code}")
            return None


# 使用示例
if __name__ == "__main__":
    # 创建 WeChatPush 实例
    Corppid_Corpsecret_Agentid = "wwe11a5be7f"
    wx = WeChatPush(Corppid_Corpsecret_Agentid)

    # 消息内容
    summary = "这是一个示例标题"
    result = "<div>这是一个示例摘要</div>"  # 需要清理的 HTML 格式摘要
    results = "这里是文章的详细内容"

    # 发送消息
    wx.send_message(summary, result)
