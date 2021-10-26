// source: https://stackoverflow.com/questions/25527902/drawing-arrows-on-a-chess-board-in-javascript
function drawArrow(arrow, color) {

    // get size of canvas according to chess_board size
    canvasWidth = $('#chess_board').width();

    //create a canvas over the chessboard
    if ($("#canvas").length === 0) {
        var canvas = '<canvas id="canvas" class="canvas" width=' + canvasWidth + ' height=' + canvasWidth + '><\/canvas>';
        $("#chess_board").append(canvas);
    }
    
    //variables to be used when creating the arrow
    var ctx = document.getElementById("canvas").getContext('2d')
    var headlen = Math.round(0.0125 * canvasWidth);

    //arrow = "h1a8"
    
    // coordinations of tip and tale of arrow by file letter to ascii, and rank number
    // oriantation = 'white'
    if(board.orientation() == 'white') {
        var fromx = Math.round((arrow.charCodeAt(0) - 97) * (canvasWidth / 8) + (canvasWidth / 16));
        var tox = Math.round((arrow.charCodeAt(2) - 97) * (canvasWidth / 8) + (canvasWidth / 16));
        var fromy = Math.round(canvasWidth - (parseInt(arrow[1]) * (canvasWidth / 8) - (canvasWidth / 16)));
        var toy = Math.round(canvasWidth - (parseInt(arrow[3]) * (canvasWidth / 8) - (canvasWidth / 16)));
    }
    // oriantation = 'black'
    if(board.orientation() == 'black') {
        var fromx = Math.round(canvasWidth - ((arrow.charCodeAt(0) - 97) * (canvasWidth / 8) + (canvasWidth / 16)));
        var tox = Math.round(canvasWidth - ((arrow.charCodeAt(2) - 97) * (canvasWidth / 8) + (canvasWidth / 16)));
        var fromy = Math.round(parseInt(arrow[1]) * (canvasWidth / 8) - (canvasWidth / 16));
        var toy = Math.round(parseInt(arrow[3]) * (canvasWidth / 8) - (canvasWidth / 16));
    }

    var angle = Math.atan2(toy-fromy,tox-fromx);

    //starting path of the arrow from the start square to the end square and drawing the stroke
    ctx.beginPath();
    ctx.moveTo(fromx, fromy);
    ctx.lineTo(tox, toy);
    ctx.strokeStyle = color;
    ctx.lineWidth = Math.round(0.04 * canvasWidth);
    ctx.stroke();

    //starting a new path from the head of the arrow to one of the sides of the point
    ctx.beginPath();
    ctx.moveTo(tox, toy);
    ctx.lineTo(tox-headlen*Math.cos(angle-Math.PI/7),toy-headlen*Math.sin(angle-Math.PI/7));

    //path from the side point of the arrow, to the other side point
    ctx.lineTo(tox-headlen*Math.cos(angle+Math.PI/7),toy-headlen*Math.sin(angle+Math.PI/7));

    //path from the side point back to the tip of the arrow, and then again to the opposite side point
    ctx.lineTo(tox, toy);
    ctx.lineTo(tox-headlen*Math.cos(angle-Math.PI/7),toy-headlen*Math.sin(angle-Math.PI/7));

    //draws the paths created above
    ctx.strokeStyle = color;
    ctx.lineWidth = Math.round(0.04 * canvasWidth);
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.fill();

    // remove canvas on click over boardchess if existed
    /*$('#canvas').on('click', function() {
        $('#canvas').remove();
    });*/
    
}