$(document).ready(function(){
    var socket = io.connect('http://' + document.domain + ':' + location.port);

    // online status, show entire webpage
    socket.on('connected users', function(msg) {
        $("#total_online_users").text(msg.users_count)
        console.log('online users: ' + parseInt(msg.users_count))
    });

});