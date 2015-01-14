var ip   = "127.0.0.1",
    port = 1337,
    http = require('http');

function onRequest(request, response) {
  console.log("Request received.");
  response.writeHead(200, {"Content-Type": "text/plain"});
  response.write("Hello World");
  response.end();
}
http.createServer(onRequest).listen(port, ip);
console.log("Server has started.");
