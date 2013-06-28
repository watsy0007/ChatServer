#! /usr/bin/env python
#coding=utf-8

__author__ = 'watsy'

import json
import types


#通用错误
PACKAGE_ERRCODE_USERID              =   10001
PACKAGE_ERRCODE_FRIENDID            =   10002
PACKAGE_ERRCODE_USERFRIENDID        =   10003

#注册
PACKAGE_ERRCODE_USERISEXIST         =   10011
PACKAGE_ERRCODE_INPUTWRONG          =   10012
PACKAGE_ERRCODE_LENGTHTOSHORT       =   10013


#登录
PACKAGE_ERRCODE_USERNOTEXIST        =   10021
PACKAGE_ERRCODE_WRONGPASSWORD       =   10022

#好友
PACKAGE_ERRCODE_FRIENDSHIPEXIST     =   10031
PACKAGE_ERRCODE_NOTHISUSER          =   10032

####################################################################################
#接收包协议
####################################################################################
class Package(object):

    def __init__(self):
        pass

    def parser(self, datas):

        for (k , v) in datas.items():

            try:
                if  type(self.__getattribute__(k)) is not types.NoneType:
                    self.__setattr__(k, v)
            except AttributeError:
                pass


class PackageRegister(Package):
    """
    注册
    # "username":"watsy",
    # "password":"123456"
    """
    def __init__(self):
        super(PackageRegister, self).__init__()

        self.username = ''
        self.password = ''

#登录
class PackageLogin(Package):
    #{"username":"watsy", "password":"123456"}
    def __init__(self):
        super(PackageLogin, self).__init__()

        self.username = ''
        self.password = ''

#根据同车次或航班+日期获取好友列表
class PackageGetNotFriendsByCodeAndDate(Package):
    """
    "action":"getfriendlistbytrainandtime",
    "uid":1,
    "traincode":"T72",
    "date":"2013-08-05",
    "page":1
    """
    def __init__(self):

        super(PackageGetNotFriendsByCodeAndDate, self).__init__()

        self.uid = 0
        self.traincode = ''
        self.date = ''
        self.page = 0


#申请添加好友
class PackageAddFriendRequest(Package):
    """
     "uid":1,
    "fid":2,
    "msg":"hello, i'am watsy"
    """
    def __init__(self):

        super(PackageAddFriendRequest, self).__init__()

        self.uid = 0
        self.fid = 0
        self.msg = ''


#同意或者拒绝添加好友申请
class PackageAddFriendStatus(Package):
    """
    "uid":2,
    "fid":1,
    "agree":1
    """

    def __init__(self):

        super(PackageAddFriendStatus , self).__init__()

        self.uid = 0
        self.fid = 1
        self.agree = 0


#获取我的好友
class PackageGetFriends(Package):
    """
    "uid":1,
    "page":1
    """

    def __init__(self):

        super( PackageGetFriends, self ).__init__()

        self.uid = 0
        self.page = 0


#删除好友
class PackageDeleteFriend(Package):
    """
    "uid":1,
    "fid":2
    """

    def __init__(self):

        super(PackageDeleteFriend , self).__init__()

        self.uid = 0
        self.fid = 0



class PackageGetFriendDetail(Package):
    """
    查询用户资料
    参数
    "uid":1,
    "fid":2
    """

    def __init__(self):

        super(PackageGetFriendDetail , self).__init__()

        self.uid = 0
        self.fid = 0



class PackageSendChatMessage(Package):
    """
    发送聊天消息
    "uid":1,
    "fid":2,
    "chatmsg":"hello, i'am watsy"
    """

    def __init__(self):

        super (PackageSendChatMessage , self).__init__()

        self.uid = 0
        self.fid = 0
        self.chatmsg = ''



####################################################################################
#发送协议
####################################################################################



class ComplexEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj,'reprJSON'):
            return obj.reprJSON()
        else:
            return json.JSONEncoder.default(self, obj)



class SendToClientPackageRegister(object):

    def __init__(self):
        pass


class SendToClientPackageUser(object):

    def __init__(self , uid, username , sex , description , online = False):

        self.uid = uid
        self.username = username
        self.sex = sex
        self.description = description
        self.online = online


    def reprJSON(self):

        return dict(
            uid = self.uid,
            username = self.username,
            sex = self.sex,
            description = self.description,
            online = self.online,
        )



class SendToClientAddFriend(object):
    """
    添加好友，状态返回
    """
    def __init__(self):
        super(SendToClientAddFriend , self).__init__()
        pass



class SendToClientAddFriendStatusReuest(object):
    """
    添加好友状态返回
    """

    def __init__(self , fromid, toid, username , sex, description, agree):

        self.fromid = fromid
        self.toid = toid
        self.username = username
        self.sex = sex
        self.description = description
        self.agree = agree

    def reprJSON(self):

        return dict(

            fromid = self.fromid,
            toid = self.toid,

            username = self.username,
            sex = self.sex,
            description = self.description,

            agree = self.agree,

        )



class SendToClientPackageRecvAddFriendRequest(object):
    """
    发送有人申请添加消息
    """

    def __init__(self, fromid, username, toid, sex , description, msg, date):

        self.fromid = fromid
        self.toid = toid

        self.username = username
        self.sex = sex
        self.description = description

        self.msg = msg
        self.senddate = date

    def reprJSON(self):

        return dict(
            fromid = self.fromid,
            toid = self.toid,

            username = self.username,
            sex = self.sex,
            description = self.description,

            msg = self.msg,
            senddate = self.senddate.strftime("%Y-%m-%d %H:%M:%S"),
        )



class SendToClientPackageChatMessage(object):

    def __init__(self , fromid = 0, toid = 0, chatmsg = ''):

        self.fromid = fromid
        self.toid = toid
        self.chatmsg = chatmsg

    def reprJSON(self):

        return dict(fromid = self.fromid , toid = self.toid, chatmsg = self.chatmsg)



class SendToClientPackageOfflineChatMessage(object):

    def __init__(self , fromid , toid, msg , senddate):

        self.fromid = fromid
        self.toid = toid
        self.chatmsg = msg
        self.senddate = senddate

    def reprJSON(self):

        return dict(
            fromid = self.fromid,
            toid = self.toid,
            chatmsg = self.chatmsg,
            senddate = self.senddate.strftime("%Y-%m-%d %H:%M:%S"),
        )


class SendToClientUserOnOffStatus(object):
    """
    用户上线下线消息
    """

    def __init__(self , uid, username , sex , description , online):

        self.uid = uid
        self.username = username
        self.sex = sex
        self.description = description
        self.online = online


    def reprJSON(self):

        return dict(
            uid = self.uid,
            username = self.username,
            sex = self.sex,
            description = self.description,
            online = self.online,
        )


class SendToClientPackage(object):

    def __init__(self , action):

        super(SendToClientPackage , self).__init__()

        self.status = 0
        self.errcode = 0

        self.obj = None
        self.action = action

    def reprJSON(self):
        return dict(datas = self.obj, action = self.action , status = self.status, errcode = self.errcode)



####################################################################################
#协议解析
####################################################################################
class Protocol(object):

    def __init__(self):
        pass

    @staticmethod
    def checkPackage(package):

        json_msg = json.loads(package)

        protocol = {
                    'login' :                       PackageLogin ,
                    'getfriendlistbytrainandtime' : PackageGetNotFriendsByCodeAndDate,
                    'addfriend' :                   PackageAddFriendRequest,
                    'addfriendstatus' :             PackageAddFriendStatus,
                    'getfriends'    :               PackageGetFriends,
                    'delfriend' :                   PackageDeleteFriend,
                    'getfrienddetail' :             PackageGetFriendDetail,
                    'sendchatmsg' :                 PackageSendChatMessage,
                    'register' :                    PackageRegister,
        }

        if json_msg.has_key("datas") :
            datas = json_msg['datas']

            if datas.has_key('type') :
                stype = datas['type']

                #存在协议内
                if stype in protocol.keys():
                    #解析协议
                    pack = protocol[stype]()
                    pack.parser(datas)
                    return pack



        return None

