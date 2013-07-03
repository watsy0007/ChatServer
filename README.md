version 0.1 版本还存在一些BUG，采用sqlite数据库做为测试  
关于推送部分大家可以在pypi搜索anps 下载安装apnsclient 测试  

###通用部分

提交  
length = json整体包长  
action = 协议关键字  

部分提交部分提交 uid ，为了使协议通用语web环境  

返回  
status = 状态  
1. 成功  
2. 失败    

errcode = 错误代码,需要具体定义 
common  
10000  
10001  	用户ID错误  
10002		好友ID错误(此用户不是你好友)  
10003		用户或者好友ID错误。（ID非自己ID，或者好友ID与自己ID相同）  

注册  
10011		帐号存在  
10012		输入异常  
10013		帐号或密码长度不足  
登录  
10021		帐号不存在  
10022		密码错误  
10023		异地登录，退出当前帐号  

好友  
10031		已经是好友  
10032		不存在此用户  


action = 提交协议  


####注册  

提交  
username 用户名  
password 密码  
{  
    "length":12,  
    "datas":{  
        "type":"register",  
        "username":"watsy",  
        "password":"123456"  
    }  
}  


返回  
{  
"status":1,  
"errcode":0,  
“action”:”register”  
"datas":{}  
}

####登录  
提交  
datas[token]  	如果允许推送，ios的devicetoken信息  
{  
    "length":12,  
    "datas":{  
        "type":"login",  
        "username":"watsy",  
        "password":"123456",  
        "devicetoken":""  
    }  
}  

返回  
datas[uid]		用户ID  
datas[name]		用户名  
datas[head]		用户头像  
datas[description]	用户描述  
datas[token] 		登录key，(可以用在web直接提交数据)  
{  
    "status":1,  
    "errcode":0,  
    "action":"login",  
    "datas":{  
        "uid":1,  
        "name":"watsy",  
        "head":"xxxx.jpg",  
        "description":"hello world",  
        "token":"abcdefghikklmnopqrstuvwxyz"  
    }  
}  


#####异地登录  
返回  
{
    "status":1,  
    "errcode":0,  
    "action":"anotherlogin",  
    "datas":{  
    }  
}  


####获取好友  

提交  
page 	为获取好友页码。1页为20个好友  
{  
    "length":12,  
    "datas":{  
        "type":"getfriends",  
        "uid":1,  
        "page":1  
    }  
}  


返回  
id 		用户id  
name		用户名称  
sex		性别  
head		用户头像  
online		当前在线  

{  
    "status":1,  
    "errcode":0,  
    "action":"getfriends",  
    "datas":[  
        {  
            "id":1,  
            "name":"watsy1",  
            "sex":1,  
            "head":"xxxx.jpg",  
            "online":1  
        }  
    ]  
}  


其他协议类似。。。   

