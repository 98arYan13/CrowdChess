// source: https://stackoverflow.com/questions/25527902/drawing-arrows-on-a-chess-board-in-javascript
function drawArrow(arrow) {
    //create a canvas over the chessboard
    var canvas = '<canvas id="canvas" class="canvas" width="396" height="396"><\/canvas>';
    $("#chess_board").append(canvas);
    //variables to be used when creating the arrow
    var ctx = document.getElementById("canvas").getContext('2d')
    var headlen = 5;

    //arrow = "h1a8"
    
    // coordinations of tip and tale of arrow by file letter to ascii, and rank number
    // oriantation = 'white'
    if(board.orientation() == 'white') {
        var fromx = ((arrow.charCodeAt(0) - 97) * 50 + 25);
        var tox = ((arrow.charCodeAt(2) - 97) * 50 + 25);
        var fromy = 396 - (parseInt(arrow[1]) * 49 - 25);
        var toy = 396 - (parseInt(arrow[3]) * 49 - 25);
    }

    var angle = Math.atan2(toy-fromy,tox-fromx);

    //starting path of the arrow from the start square to the end square and drawing the stroke
    ctx.beginPath();
    ctx.moveTo(fromx, fromy);
    ctx.lineTo(tox, toy);
    ctx.strokeStyle = "#0000FF";
    ctx.lineWidth = 15;
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
    ctx.strokeStyle = "#0000FF";
    ctx.lineWidth = 15;
    ctx.stroke();
    ctx.fillStyle = "#0000FF";
    ctx.fill();

    // remove canvas on click over boardchess if existed
    $('#canvas').on('click', function() {
        $('#canvas').remove();
    });
}