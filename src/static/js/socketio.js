$(document).ready(function(){
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var socket_messages = io('http://' + document.domain + ':' + location.port + '/messages')
    var socket_users = io('http://' + document.domain + ':' + location.port + '/users') // users connected
    $('#send').on('click', function() {
        var message = $('#message').val();
        socket_messages.emit('message from user', message)
    })
    
    socket_messages.on('from flask', function(msg) {
        alert(msg);
    });
    socket_messages.on('message', function(msg) {
        alert(msg);
    });

    socket.on('connect', () => {
        socket.send('I am now connected');
        socket.emit('my event', {data: 'I\'m connected!'})
    });
    socket.on('my response', (data) => {
        socket.log(data)
        socket.log('xxx')
    });
    socket.on('server originated', function(msg) {
        alert(msg)
    })
    socket_users.on('online users', function(msg) {
        console.log(parseInt(msg.users_count))
    })
});