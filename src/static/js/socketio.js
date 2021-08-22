$(document).ready(function(){
    var socket = io.connect('http://' + document.domain + ':' + location.port);
    var socket_messages = io('http://' + document.domain + ':' + location.port + '/messages')

    // online status, show entire webpage
    /*socket.on('connect', () => {
        $(".status-circle").css("background-color", "grey");
    });*/
    socket.on('connected users', function(msg) {
        $("#total_online_users").text(msg.users_count)
        console.log('online users: ' + parseInt(msg.users_count))
    });

    // currently present users on homepage (main page)
    socket_users.on('on_main_page_users', function(msg) {
        console.log('visiting main page users: ' + parseInt(msg.users_count))
    });
});