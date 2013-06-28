#coding: utf-8
__author__ = 'watsy'

import datetime
import json



from db import DBEngine , DBUser , DBRelationship, DBOfflineMsg, DBTravel, DBTraveluser, DBOfflineAddFriend

from models import UserObject, UserModel
from models import USERS_PAGES_SIZE


#接受协议
from protocol import PackageLogin, PackageRegister, PackageGetNotFriendsByCodeAndDate, \
    PackageAddFriendRequest, PackageAddFriendStatus , PackageGetFriends , PackageDeleteFriend , \
    PackageGetFriendDetail , PackageSendChatMessage

#错误编码
from protocol import PACKAGE_ERRCODE_INPUTWRONG,PACKAGE_ERRCODE_LENGTHTOSHORT,PACKAGE_ERRCODE_USERISEXIST , \
    PACKAGE_ERRCODE_LENGTHTOSHORT , PACKAGE_ERRCODE_FRIENDSHIPEXIST , PACKAGE_ERRCODE_USERFRIENDID , \
    PACKAGE_ERRCODE_NOTHISUSER , PACKAGE_ERRCODE_USERID

#发送协议
from protocol import ComplexEncoder, SendToClientPackage, \
    SendToClientPackageRegister, SendToClientPackageUser, \
    SendToClientPackageChatMessage, SendToClientPackageRecvAddFriendRequest, \
    SendToClientAddFriend, SendToClientAddFriendStatusReuest, SendToClientPackageOfflineChatMessage , \
    SendToClientUserOnOffStatus






class Logic(object):

    def __init__(self):

        self.onlineUsers = UserModel()
        self.dbEngine = DBEngine()


    def reset(self):

        self.onlineUsers.reset()


    def findBadInput(self, inputstring):
        """
        输入是否合法，防止sql注入
        """
        if '\'' in inputstring:
            return True
        elif '\"' in inputstring:
            return True
        elif '`' in inputstring:
            return True
        elif ' ' in inputstring:
            return True

    ####################################################################################
    #协议处理部分
    ####################################################################################
    def handlePackage(self, connection , package):
        """
        逻辑处理部分
        """
        if isinstance(package, PackageRegister):
            self.handleUserRegister(connection , package)

        elif isinstance(package, PackageLogin):
            self.handleUserLogin(connection , package)

        elif isinstance(package, PackageGetNotFriendsByCodeAndDate):
            self.handleGetNotFriendsWithCodeAndDate( connection , package )

        elif isinstance( package , PackageAddFriendRequest ):
            self.handleAddFriendRequest( connection, package )

        elif isinstance( package , PackageAddFriendStatus ):
            self.handleAddFriendRequestStatus( connection , package )

        elif isinstance( package , PackageGetFriends ):
            self.handleGetFriends( connection, package )

        elif isinstance( package , PackageDeleteFriend ):
            self.handleDeleteFriend( connection , package )

        elif isinstance( package , PackageGetFriendDetail ):
            self.handleGetFriendDetail( connection , package )

        elif isinstance( package , PackageSendChatMessage ):
            self.handleSendChatMessage( connection , package )



    def closeConnection(self, connection):

        user = self.onlineUsers.getUserByConnection(connection)
        self.onlineUsers.deleteUserByUser(user)

        friends = user.getAllFriends()
        if len(friends) > 0:
            self.broadcastOnlineStatusToAllFriend( user , 0 )


    ####################################################################################
    #逻辑处理
    ####################################################################################
    def handleUserRegister(self, connection , package):
        """
        用户注册处理
        """
        retPackage = SendToClientPackage('register')

        #step 1，检查参数合法性
        if self.findBadInput(package.username) or self.findBadInput(package.password):
            #帐号异常
            retPackage.errcode = PACKAGE_ERRCODE_INPUTWRONG

        #step 2，检查参数长度
        elif len(package.username) < 6 or len(package.password) < 6:
            #长度太小
            retPackage.errcode = PACKAGE_ERRCODE_LENGTHTOSHORT

        else:
            #step 3，检查用户是否存在
            db_user = self.dbEngine.isUserExist(package.username, package.password)

            #不存在用户，插入数据库
            if not db_user:
                #插入数据库
                self.dbEngine.register_new_user(package.username, package.password)
                retPackage.status = 1

            else:
                #已经存在用户，返回从新注册
                retPackage.errcode = PACKAGE_ERRCODE_USERISEXIST

        connection.send_message( json.dumps(retPackage, cls=ComplexEncoder) )



    def handleUserLogin(self, connection , package):
        """
        用户登录处理
        """
        retPackage = SendToClientPackage('login')
        #step 1，检查参数合法性
        if self.findBadInput(package.username) or self.findBadInput(package.password):

            retPackage.errcode = PACKAGE_ERRCODE_INPUTWRONG

        else:

            #step 2. 查询数据库
            db_user = self.dbEngine.isUserExist(package.username, package.password)

            if db_user:

                #step 1. 枚举在线好友，如果在线，退掉
                online_user = self.onlineUsers.getUserExistByUsername(package.username)
                if online_user:
                    #step 1.发送异地登录消息
                    another = SendToClientPackage('anotherlogin')
                    another.status = 1

                    online_user.connection.send_message( json.dumps( another , cls= ComplexEncoder ) )

                    #step 2.关闭联接
                    online_user.connection.close()

                #从新加入到在线用户
                user = UserObject(connection, db_user)
                self.onlineUsers.addNewOnlineUser(user)

                retPackage.status = 1
                retPackage.obj = SendToClientPackageUser( user.DBUser.uid,
                                                          user.DBUser.username,
                                                          user.DBUser.sex,
                                                          user.DBUser.description)


                #加载好友列表
                self.getUserFriendsWithDBAndOnLineUsers( user )

                #检查离线消息，是否有人希望添加我为好友
                self.getAllAddFriendRequestFromDBAndSendToClient( user )

                #是否有人给我发离线消息
                self.getOfflineChatMessageAndSendWithUser( user )

                #广播好友列表，通知本人上线
                self.broadcastOnlineStatusToAllFriend( user , 1 )

                #修改在线列表,本人上线
                self.setUserOnlineInOnlineUsersFriends( user )

            else:
                #用户不存在，提醒注册
                retPackage.errcode = 10010

        connection.send_message( json.dumps(retPackage, cls=ComplexEncoder) )



    def handleGetNotFriendsWithCodeAndDate(self, connection, package):
        """
        根据code和date获取好友信息
        """
        user = self.onlineUsers.getUserByConnection(connection)

        retPackage = SendToClientPackage('getfriendlistbytrainandtime')

        #step 1 检查是否为自己
        if user.DBUser.uid == int (package.uid):

            retPackage.status = 1

            ret_friends = self.getNotFriendsWithCodeAndDateAndPage(user ,
                                                                   package.traincode,
                                                                   package.date,
                                                                   package.page)


            if ret_friends and len(ret_friends) > 0:
                retPackage.obj = ret_friends

        else:
            #用户ID错误
            retPackage.errcode = PACKAGE_ERRCODE_USERID

        connection.send_message( json.dumps(retPackage, cls= ComplexEncoder) )



    def handleAddFriendRequest(self, connection , package):
        """
        有人想添加好友
        """
        user = self.onlineUsers.getUserByConnection(connection)

        retPackage = SendToClientPackage('addfriend')

        bFriendship = False
        #检查是否是自己
        #并且不是自己想要添加自己为好友
        if user.DBUser.uid == int(package.uid) and user.DBUser.uid != package.fid:

            friend = user.getFriendWithId(package.fid)
            if friend:
                bFriendship = True

            if not bFriendship:
                retPackage.status = 1
                user.connection.send_message( json.dumps(retPackage , cls= ComplexEncoder) )

                #step2 在线,发送添加
                online_user = self.onlineUsers.getUserExistByUserid(package.fid)

                if online_user:

                    addreq = SendToClientPackageRecvAddFriendRequest(package.uid,
                                                                     package.fid ,
                                                                     user.DBUser.username,
                                                                     user.DBUser.sex,
                                                                     user.DBUser.description,
                                                                     package.msg, datetime.datetime.now())
                    retPackage.obj = addreq

                    online_user.connection.send_message( json.dumps(retPackage, cls= ComplexEncoder) )
                else:
                    #插入数据库,等待上线时候通知
                    self.dbEngine.setOfflineAddFriendReuqest(package.uid, package.fid, package.msg, datetime.datetime.now())

            else:
                #已经是好友，返回错误信息
                retPackage.errcode = PACKAGE_ERRCODE_FRIENDSHIPEXIST
                user.connection.send_message( json.dumps(retPackage , cls= ComplexEncoder) )


        else:
            #用户ID错误，或者用户ID等于好友ID
            retPackage.errcode = PACKAGE_ERRCODE_USERFRIENDID
            user.connection.send_message( json.dumps(retPackage , cls= ComplexEncoder) )



    def handleAddFriendRequestStatus(self, connection ,package):
        """
        应答是否同意添加好友请求
        """
        user = self.onlineUsers.getUserByConnection(connection)

        retPackage = SendToClientPackage('addfriendstatus')
        #自己的id
        if user.DBUser.uid == int(package.uid) and user.DBUser.uid != int(package.fid):

            #如果同意
            if package.agree:
                #step 1. 检查是否是自己的好友

                if not self.dbEngine.getFriendshipWithUserFriendId(package.uid, package.fid):

                    db_friend = self.dbEngine.getUserInfoWithUserId(package.fid)

                    #存在数据库中
                    if db_friend:
                        retPackage.status = 1
                        #保存关系到数据库
                        self.dbEngine.setFriendshipWithUserIds(package.uid, package.fid)

                        user.connection.send_message( json.dumps(retPackage, cls= ComplexEncoder) )
                        #检查是否在线,在线发送上线通知
                        online_friend = self.onlineUsers.getUserExistByUserid(package.fid)

                        if online_friend:
                            #当前在线
                            online_status = SendToClientAddFriendStatusReuest(package.uid,
                                                                              package.fid,
                                                                              user.DBUser.username,
                                                                              user.DBUser.sex,
                                                                              user.DBUser.description,
                                                                              package.agree)
                            retPackage.obj = online_status
                            #发送有人添加好友申请
                            online_friend.connection.send_message( json.dumps( retPackage, cls=ComplexEncoder ) )

                            #添加到我的好友列表
                            user.addFriend(online_friend)

                    else:
                        #数据库中不存在此用户
                        retPackage.errcode = PACKAGE_ERRCODE_NOTHISUSER

                        #返回添加好友状态
                        user.connection.send_message( json.dumps(retPackage, cls= ComplexEncoder) )


                else:
                    #已经是好友提示
                    retPackage.errcode = PACKAGE_ERRCODE_FRIENDSHIPEXIST

                    user.connection.send_message( json.dumps( retPackage , cls= ComplexEncoder ) )

            else:
                #返回状态
                retPackage.status = 1
                #返回添加好友状态
                user.connection.send_message( json.dumps(retPackage, cls= ComplexEncoder) )

                #TODO:拒绝不提示
                pass

        else:
            #用户ID异常
            retPackage.errcode = PACKAGE_ERRCODE_USERFRIENDID
            user.connection.send_message( json.dumps( retPackage , cls= ComplexEncoder ) )



    def handleGetFriends(self , connection , package ):
        """
        获取好友列表
        """
        user = self.onlineUsers.getUserByConnection(connection)

        retPackage = SendToClientPackage('getfriends')
        #自己的id
        if user.DBUser.uid == int(package.uid):

            retFriend = self.getUserFriendsWithUserAndPage( user, int(package.page) )

            if len(retFriend) > 0:
                retPackage.obj = retFriend

            retPackage.status = 1

        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID

        user.connection.send_message( json.dumps( retPackage , cls= ComplexEncoder ) )


    def handleDeleteFriend(self , connection , package):
        """
        删除好友
        """
        user = self.onlineUsers.getUserByConnection(connection)

        retPackage = SendToClientPackage('delfriend')
        #自己的id
        if user.DBUser.uid == int(package.uid) and user.DBUser.uid != int(package.fid):

            retPackage.status = 1
            #从数据库中删除
            self.dbEngine.deleteFriendshipByUserAndFriendId( package.uid, package.fid )

            user.connection.send_message( json.dumps( retPackage , cls=ComplexEncoder ) )

            #给在线好友发送通知，删除
            online_friend = self.onlineUsers.getUserExistByUserid( package.fid )
            if online_friend:
                sendObj = SendToClientPackageUser(user.DBUser.uid,
                                                  user.DBUser.username,
                                                  user.DBUser.sex,
                                                  user.DBUser.description)
                retPackage.obj = sendObj
                online_friend.connection.send_message( json.dumps( retPackage , cls=ComplexEncoder ) )

                #从维护的好友列表中删除
                user.deleteFriend(online_friend)


        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID
            user.connection.send_message( json.dumps( retPackage , cls= ComplexEncoder ) )



    def handleGetFriendDetail(self, connection , package):
        """
        获得用户相信信息
        """
        user = self.onlineUsers.getUserByConnection(connection)

        retPackage = SendToClientPackage('delfriend')
        #自己的id
        if user.DBUser.uid == int(package.uid) and user.DBUser.uid != int(package.fid):

            retPackage.status = 1

            #TODO:获取用户详细资料返回

        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID
            user.connection.send_message( json.dumps( retPackage , cls= ComplexEncoder ) )


    def handleSendChatMessage(self, connection , package):
        """
        发送聊天消息
        """
        user = self.onlineUsers.getUserByConnection(connection)

        retPackage = SendToClientPackage('sendchatmsg')
        #自己的id
        if user.DBUser.uid == int(package.uid) and user.DBUser.uid != int(package.fid):

            #寻找好友ID
            for friend in user.getAllFriends():
                if friend.DBUser.uid == int(package.fid):
                    #发送消息给好友
                    retPackage.status = 1

                    user.connection.send_message( json.dumps( retPackage, cls= ComplexEncoder ) )

                    chat = SendToClientPackageChatMessage(user.DBUser.uid ,package.fid, package.chatmsg)
                    retPackage.obj = chat
                    if friend.connection:
                        friend.connection.send_message( json.dumps(retPackage, cls= ComplexEncoder) )
                    else:
                        #当前不在线，数据库插入离线消息
                        self.dbEngine.addOfflineChatMessageWithUserId(user.DBUser.uid ,
                                                                      package.fid,
                                                                      package.chatmsg,
                                                                      datetime.datetime.now())

                    return



        else:
            retPackage.errcode = PACKAGE_ERRCODE_USERID
            user.connection.send_message( json.dumps( retPackage , cls= ComplexEncoder ) )



    ####################################################################################
    #逻辑中的部分细节处理
    ####################################################################################

    def getUserFriendsWithDBAndOnLineUsers(self , user):
        """
        获取用户的所有好友信息
        """
        #step 1.从数据库加载
        (user1Friends, user2Friends) = self.dbEngine.getUserFriendshipWithUserId( user.DBUser.uid )

        for friend in user1Friends:
            db_user = self.dbEngine.getUserInfoWithUserId(friend.user2id)
            friend = UserObject(None , db_user )
            user.addFriend( friend )
            online_friend = self.onlineUsers.getUserExistByUsername(db_user.username)
            if online_friend:
                friend.connection = online_friend.connection
                friend.online = True

        for friend in user2Friends:
            db_user = self.dbEngine.getUserInfoWithUserId(friend.user1id)
            friend = UserObject(None , db_user )
            user.addFriend( friend )
            online_friend = self.onlineUsers.getUserExistByUsername(db_user.username)
            if online_friend:
                friend.connection = online_friend.connection
                friend.online = True



    def broadcastOnlineStatusToAllFriend(self, user, online):
        """
        广播用户的上线下线消息
        """
        retPackage = SendToClientPackage('useronoffline')

        for friend in user.getAllFriends():
            #通知所有好友下线
            retPackage.status = 1
            obj = SendToClientUserOnOffStatus(user.DBUser.uid ,
                                                  user.DBUser.username,
                                                  user.DBUser.sex,
                                                  user.DBUser.description,
                                                  online)
            retPackage.obj = obj

            if friend.connection:
                friend.connection.send_message( json.dumps( retPackage , cls=ComplexEncoder ) )

            if not online:
                #清空联接
                online_friend = self.onlineUsers.getUserExistByUsername(friend.DBUser.username)
                if online_friend:
                    #从好友列表里面将自己的connection 清0
                    myself = online_friend.getFriendWithUsername( user.DBUser.username )
                    myself.connection = None

    def setUserOnlineInOnlineUsersFriends(self, user):
        """
        将在线用户列表里面的所有状态修改为本人在线
        """

        for friend in user.getAllFriends():
            online_friend =  self.onlineUsers.getUserExistByUsername( friend.DBUser.username )
            if online_friend:
                myself = online_friend.getFriendWithUsername( user.DBUser.username )
                myself.connection = user.connection



    def getAllAddFriendRequestFromDBAndSendToClient(self, user):
        """
        从数据库获取所有申请添加好友的用户并发送给用户
        """
        add_requests = []
        offline_add_friend_requests = self.dbEngine.getOfflineAddFriendRequests( user.DBUser.uid )
        for off_add_req in offline_add_friend_requests:
            db_user = self.dbEngine.getUserInfoWithUserId( off_add_req.fromid )
            send_request = SendToClientPackageRecvAddFriendRequest(off_add_req.fromid ,
                                                                   db_user.username ,
                                                                   off_add_req.toid ,
                                                                   db_user.sex,
                                                                   db_user.description,
                                                                   off_add_req.msg,
                                                                   off_add_req.lastdate)
            add_requests.append(send_request)

        if len(add_requests) > 0:
            #发送
            retRequest = SendToClientPackage('addfriend')
            retRequest.status = 1
            retRequest.obj = add_requests

            user.connection.send_message( json.dumps( retRequest , cls=ComplexEncoder ) )

            #删除离线好友请求
            self.dbEngine.deleteOfflineAddFriendRequestWithUserId( user.DBUser.uid )



    def getOfflineChatMessageAndSendWithUser(self , user):
        """
        获取所有离线消息并发送
        """
        db_offline_chat_messages = self.dbEngine.getAllOfflineChatMessageWithUserId( user.DBUser.uid )


        ret_off_chat_messages = []
        if db_offline_chat_messages:
            for off_chat_msg in db_offline_chat_messages:
                off_msg = SendToClientPackageOfflineChatMessage(off_chat_msg.fromuserid,
                                                                off_chat_msg.touserid,
                                                                off_chat_msg.msg,
                                                                off_chat_msg.last_date )

                ret_off_chat_messages.append(off_msg)

        if ret_off_chat_messages:
            #发送离线消息
            retPackage = SendToClientPackage('sendchatmsg')
            retPackage.status = 1
            retPackage.obj = ret_off_chat_messages

            user.connection.send_message( json.dumps( retPackage , cls=ComplexEncoder ) )

            #从数据库中删除
            self.dbEngine.deleteAllOfflineChatMessageWithUserId( user.DBUser.uid )



    def getNotFriendsWithCodeAndDateAndPage(self , user , traincode, date , page):
        """
        根据列车或者航班+日期获取的好友
        """
        friends = self.dbEngine.getNotfriendsWithCodeAndDate(traincode, date)
        ret_friends = []
        nCount = 0
        if friends:
            for friend in friends:
                #不是自己
                if friend.userid != user.DBUser.uid:
                    #计算页码
                    if (nCount / 20 == page):
                        db_friend = self.dbEngine.getUserInfoWithUserId(friend.userid)
                        ret_friend = SendToClientPackageUser(db_friend.uid, db_friend.username, db_friend.sex, db_friend.description)
                        ret_friends.append(ret_friend)

                    nCount += 1

        return ret_friends



    def getUserFriendsWithUserAndPage(self, user , page):
        """
        获取用户好友
        """
        retFriends = []
        friends = user.getAllFriends()
        friendCount = len(friends)
        if friends and friendCount > 0:
            nStart = 0
            nEnd = 0

            #计算页码是否在范围内
            if USERS_PAGES_SIZE * page < friendCount:

                #计算结束页码
                if USERS_PAGES_SIZE * (page + 1) > friendCount:
                    nEnd = friendCount - USERS_PAGES_SIZE * page
                else:
                    nEnd = USERS_PAGES_SIZE * page

                #在页码范围内的好友
                friends = friends[nStart * USERS_PAGES_SIZE : nEnd]
                for friend in friends:
                    online = False
                    if friend.connection:
                        online = True
                    retUser = SendToClientPackageUser(friend.DBUser.uid,
                                                      friend.DBUser.username,
                                                      friend.DBUser.sex,
                                                      friend.DBUser.description,
                                                      online)
                    retFriends.append( retUser )


        return retFriends
