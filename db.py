#! /usr/bin/env python
#coding=utf-8
__author__ = 'watsy'

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey


Base = declarative_base()


class DBUser(Base):
    """
    用户信息
    """
    __tablename__ = 'user'

    uid         = Column(Integer , primary_key=True)
    username    = Column(String)
    password    = Column(String)
    sex         = Column(Integer, default=0)
    description = Column(String)

    def __init__(self , username , password, sex = 0):

        self.username = username
        self.password = password
        self.sex = sex


    def __repr__(self):
        return "<user ('%s')>" % (self.username)


class DBOfflineAddFriend(Base):
    """
    离线添加好友消息
    """

    __tablename__ = 'offlineaddfriend'

    aid         = Column(Integer, primary_key=True)
    fromid      = Column(Integer, ForeignKey('user.uid'))
    toid        = Column(Integer, ForeignKey('user.uid'))
    msg         = Column(String)
    lastdate    = Column(DateTime)

    def __init__(self, fid, tid, msg, dateTime):
        """
        赋值
        """
        self.fromid = fid
        self.toid = tid
        self.msg = msg
        self.lastdate = dateTime




class DBTravel(Base):
    """
    列车类型
    """
    __tablename__ = 'travel'

    tid         = Column(Integer, primary_key=True)
    travelCode  = Column(String)
    date        = Column(Date)

    def __init__(self, tc, date):

        self.tid = tc
        self.date = date


class DBTraveluser(Base):
    """
    乘坐列车用户
    """

    __tablename__ = 'traveluser'

    tid         = Column(Integer, primary_key=True)
    travelid    = Column(Integer , ForeignKey('travel.tid'))
    userid      = Column(Integer , ForeignKey('user.uid'))

    def __init__(self , tid, uid):

        self.travelid = tid
        self.userid = uid


class DBRelationship(Base):
    """
    好友关系表
    """

    __tablename__ = 'relationship'

    rid         = Column(Integer, primary_key=True)
    user1id     = Column(Integer, ForeignKey('user.uid'))
    user2id     = Column(Integer, ForeignKey('user.uid'))


    def __init__(self , u1id, u2id):

        self.user1id = u1id
        self.user2id = u2id


class DBOfflineMsg(Base):
    """
    缓存离线消息
    """

    __tablename__ = 'offlinemsg'

    oid         = Column(Integer, primary_key=True)
    fromuserid  = Column(Integer, ForeignKey('user.uid'))
    touserid    = Column(Integer, ForeignKey('user.uid'))
    msg         = Column(String)
    last_date   = Column(DateTime)

    def __init__(self , fuid, touid, msg, last_date):

        self.fromuserid = fuid
        self.touserid = touid
        self.msg = msg
        self.last_date = last_date


class DBEngine(object):
    """
    数据库操作业务部分
    当前数据库操作没有异常处理和错误校验，正式发行时候应该添加上
    """

    def __init__(self):
        self.engine = create_engine('sqlite:///DB/chatdb.sqlite', echo = False)

        db_session = sessionmaker(autocommit=False,autoflush=False,bind=self.engine)
        self.session = db_session()

    def closeDB(self):

        self.session.close()

    ####################################################################################
    #user部分
    ####################################################################################
    def isUserExist(self, username, password):

        return self.session.query(DBUser).filter(DBUser.username == username, DBUser.password == password).first()


    def register_new_user(self, username , password , sex = 0):

        user = DBUser(username = username, password = password , sex = sex)
        self.session.add(user)
        self.session.commit()



    ####################################################################################
    #friends
    ####################################################################################
    def getNotfriendsWithCodeAndDate(self, code, date):
        """
        获取同行好友
        """
        try:

            travel = self.session.query(DBTravel).filter(DBTravel.travelCode == code, DBTravel.date == date).first()
            if travel:
                return self.session.query(DBTraveluser).filter(DBTraveluser.travelid == travel.tid)
        except ValueError as err:
            print err

        return None



    def getFriendshipWithUserFriendId(self, userid, friendid):
        """
        是否已经存在好友关系
        """
        friendship = self.session.query(DBRelationship).filter(DBRelationship.user1id == userid, DBRelationship.user2id == friendid).first()
        if friendship:
            return friendship
        friendship = self.session.query(DBRelationship).filter(DBRelationship.user1id == friendid, DBRelationship.user2id == userid).first()

        return friendship



    def setFriendshipWithUserIds(self, userid, friendid):
        """
        保存好友关系
        """
        relationship = DBRelationship(userid , friendid)
        self.session.add(relationship)
        self.session.commit()


    def getUserInfoWithUserId(self, userid):
        """
        根据用户id，获取用户资料
        """
        return self.session.query(DBUser).filter(DBUser.uid == userid).first()


    def getUserFriendshipWithUserId(self , userId):
        """
        根据用户ID，获取用户好友
        """
        user1Friend = self.session.query(DBRelationship).filter(DBRelationship.user1id == userId)
        user2Friend = self.session.query(DBRelationship).filter(DBRelationship.user2id == userId)

        return user1Friend, user2Friend



    def getOfflineAddFriendRequests(self , userid):
        """
        根据用户ID，获取所有离线申请添加好友的信息
        """
        return self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == userid)


    def deleteOfflineAddFriendRequestWithUserId(self , userId):
        """
        根据用户ID，删除离线好友请求
        """
        offlineAddRequests = self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == userId)
        for offlineAddReq in offlineAddRequests:
            self.session.delete(offlineAddReq)

        self.session.commit()


    def setOfflineAddFriendReuqest(self , fid, uid, msg, dateTime):
        """
        保存添加请求，当前好友为离线状态
        """
        offline_add_request = self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == fid, DBOfflineAddFriend.fromid == uid).first()
        if offline_add_request:
            self.session.query(DBOfflineAddFriend).filter(DBOfflineAddFriend.toid == fid, DBOfflineAddFriend.fromid == uid).update({'msg':msg, 'lastdate':dateTime})
        else:
            offline_add_request = DBOfflineAddFriend(uid , fid, msg, dateTime )
        self.session.add(offline_add_request)

        self.session.commit()


    def deleteFriendshipByUserAndFriendId(self , userId, friendId):
        """
        根据用户ID和好友ID删除好友关系
        """
        user1Friend = self.session.query(DBRelationship).filter(DBRelationship.user1id == userId ,DBRelationship.user2id == friendId).first()
        if not user1Friend:
            user1Friend = self.session.query(DBRelationship).filter(DBRelationship.user1id == friendId ,DBRelationship.user2id == userId).first()

        self.session.delete(user1Friend)
        self.session.commit()


    ####################################################################################
    #chat
    ####################################################################################

    def getAllOfflineChatMessageWithUserId(self, userId):
        """
        根据用户ID，获取所有离线消息
        """
        return self.session.query(DBOfflineMsg).filter(DBOfflineMsg.touserid  == userId)


    def deleteAllOfflineChatMessageWithUserId(self , userId):
        """
        根据用户ID，删除所有离线消息
        """
        offlineChatMessage = self.session.query(DBOfflineMsg).filter(DBOfflineMsg.touserid == userId)
        for offlineChatMsg in offlineChatMessage:
            self.session.delete(offlineChatMsg)

        self.session.commit()


    def addOfflineChatMessageWithUserId(self, userId, friendId, message, lastdate):
        """
        保存离线聊天消息
        """
        offChatMsg = DBOfflineMsg(userId, friendId, message, lastdate)
        self.session.add(offChatMsg)
        self.session.commit()









