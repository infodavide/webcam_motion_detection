var socket=null;
function connectWebSocket(){
  if(socket!==null){
    return;
  }
  console.log('Connecting websocket...');
  var url=BASE_URL+'/stomp';
  socket=io(url.replace(/http:/i, 'ws:'));
  socket.on('connect', function(){console.log('Websocket connected');});
  socket.on('error',function(e){console.log('Websocket error: '+e);});
  socket.on('disconnect',function(e){console.log('Websocket closing: '+e);});
}
function subscribeToTopic(topic){
  connectWebSocket();
  socket.emit('subscribe',topic);
  console.log('Websocket subscribing to topic: '+topic);
}
function unsubscribeToTopic(topic){
  console.log('Unsubscribing to topic...');
  if(socket!==null){
    socket.emit('unsubscribe',topic);
    console.log('Websocket unsubscribing from topic: '+topic);
  }
}
function onWebSocketMessage(){
  // noop
}
function disconnectWebSocket(){
  if(socket!==null){
    unsubscribeToTopic('');
    socket.close();
  }
  socket=null;
  console.log("Websocket disconnected");
}