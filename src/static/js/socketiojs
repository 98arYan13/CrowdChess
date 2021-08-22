$(document).ready(function(){
    var socket = io.connect('http://127.0.0.1:5000');
    var socket_messages = io('http://127.0.0.1:5000/messages')
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
    socket_users.on('connect', () => {
        socket_users.send('I am now connected');
        socket_users.emit('my event', {data: 'I\'m connected!'})
        socket_users.emit('test_event', {data: 'I\'m connected!'})
    });
    socket_users.on('my response', (data) => {
        socket_users.log(data) // nothing show on console
        socket_users.log('xxx')
    });
    socket_users.on('server originated', function(msg) {
        alert(msg)
    })
});