/**
 * Socket.io & Redis for Chat.
 */
var port = 8899;
var socketio = require('socket.io');

var redis = require("redis"),
    PORT = 6379,
    HOST = '127.0.0.1',
    PASSWD = 'yourpasswd',
    DB = 0,
    OPTS = {auth_pass: PASSWD, selected_db: DB},
    client = redis.createClient(PORT, HOST, OPTS);

client.auth(PASSWD, function(){
    console.log('Redis Auth Successful! > redis_db:'+ DB);
});

// 消息队列
var ques = {
    "sync:msg":"chat_msg_l:u:"                  // 聊天消息
    //可扩展其他
};

// 消息类型
var queTypes = {
    "sync:msg": 0                      // 聊天消息
    //可扩展其他
};


var clientsTable = {};          //客户端版本
var socketsTable = {};          //Socket标识，(user_id)

var io = socketio.listen(port);
io.set('log level', 1);

io.on('connection', function(socket) {
    console.log('+已连接客户端 : ' + socket.id);
    //监听新用户加入
    socket.on('reg', function(data) {
        //将新加入用户的唯一标识当作socket的名称
        var argj = (typeof(data) == 'string') ? JSON.parse(data) : data;
        userName = argj.un;
        socket.username = userName;

        clientsTable[userName] = socket.id;
        socketsTable[socket.id] = userName;

        //注册在线用户 online
        client.sadd('online', userName);
        console.log("已注册在线用户"+userName);
        //接收聊天消息
        msgSyncList(userName, 'sync:msg');

    });

    //客户端应答消息走请求消息的API（Chat API）
    socket.on('ack', function(data) {
        var userName = socketsTable[socket.id];
        if (!(userName in clientsTable)) {
            return;
        }
        var argj = (typeof(data) == 'string')? JSON.parse(data): data;
        console.log('@ [' + userName + '] 获取: ' + (argj.length -1)+ '消息');

        if (argj.length == 0) {
            return;
        }
        //处理应答消息
        ackMsgList(userName, argj);

    });

    socket.on('disconnect', function() {
        //断开连接
        var socketId = socket.id;
        if (socketId in socketsTable)
        {
            var userName = socketsTable[socketId];
            if (userName in clientsTable) {
                delete clientsTable[userName];
                console.log('- 已断开连接[user] : ' + userName);
            }
            delete socketsTable[socketId];
            console.log('- 断开客户端[client] : ' + socketId);
            client.SREM('online', userName);
        }
    });
});


// 处理消息
function msgSyncList (userName, channel) {
    var key = ques[channel];
    var no = queTypes[channel];
    client.lrange(key + userName, 0, -1, function (err, res) {
        if (err || res.length == 0) {
            return;
        }
        var msgList = [{type:no}];
        for (var i in res) {
            msgList.push({mid: res[i]});
        }

        var socket = io.sockets.socket(clientsTable[userName]);
        if (socket) {
            //给客户端同步消息,客户端接受到该事件后调用ack事件来响应socket.io
            socket.emit('sync', msgList);
            console.log('>接收消息[' + userName + '] : ' + JSON.stringify(msgList));
        }
    });
}

// 处理ack消息
function ackMsgList(userName, argj) {
    var channel = getChannelByNo(argj[0].type);
    var key = ques[channel];
    var msgKey = key + userName;                //消息队列
    var msg_cmds = [];
    //删除用户事件消息队列
    argj.splice(0, 1);
    for (var a in argj) {
        var args = ['lrem', msgKey];
        args.push(1);
        args.push(argj[a].mid);
        msg_cmds.push(args);
    }
    client.multi(msg_cmds).exec();
}

// 获取数字标示对应的channel
function getChannelByNo(no){
    for(var k in queTypes) {
        if (no == queTypes[k]) {
            return k;
        }
    }
}

var sub = redis.createClient(PORT, HOST, OPTS);

//订阅消息频道sync:msg
sub.psubscribe("sync:*");

sub.on("pmessage", function(pattern, channel, message) {
    /*
     channel:消息频道
     message:user_id
     */
    console.log('~ 频道' + channel + '向用户' + message + '发送消息...' );
    var userName = message;
    if (!(userName in clientsTable)) {
        //如果用户不在线
        //发送推送
        console.log('用户: ' + userName + '不在线,消息将会在其上线后接收.');
        return;
    }
    msgSyncList(userName, channel);
});
