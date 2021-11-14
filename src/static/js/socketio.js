$(document).ready(function(){

    var protocol = window.location.protocol;
    var socket = io.connect(protocol + '//' + document.domain + ':' + location.port);

    // online status, show entire webpage
    socket.on('connected users', function(msg) {
        $("#total_online_users").text(msg.users_count)
        console.log('online users: ' + parseInt(msg.users_count))
    });

});