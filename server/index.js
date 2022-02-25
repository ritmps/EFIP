// ------------------------------------------------- websocket server -------------------------------------------------


// Importing the required modules
const WebSocketServer = require('ws');
 
// Creating a new websocket server
const wss = new WebSocketServer.Server({ port: 9000 })

// store client socket in global variable so that we can send coordinates to it later
let client = null;
 
// Creating connection using websocket
wss.on("connection", ws => {
    console.log("new client connected");
    client = ws;
});
console.log("The WebSocket server is running on port 9000");

// ------------------------------------ server code -------------------------------------------

// HTTP

const http = require('http');

const requestListener = function (req, res) {
    res.writeHead(200);
    // console.log('request');
    // console.log(req.url);

    if (req.url.indexOf('?c=') != -1) {

        // parse x and y coordinates
        const arguments = req.url.split('=')[1];
        const x = arguments.split('&')[0];
        const y = arguments.split('&')[1];
        // console.log('Coordinates received: x = ' + x + ', y = ' + y);
        if (client != null) {
            client.send(JSON.stringify([Date.now(), x, y]));
        }
    }

    res.end('');
}

const server = http.createServer(requestListener);
server.listen(5000);

// ------------------------------------------------- static web server -------------------------------------------------

const express = require('express')
const app = express()
const port = 80

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`)
})

app.use(express.static('public'))