var socket=null;
function connectWebSocket(){
  if(socket!==null){
    return;
  }
  console.log('Connecting websocket...');
  var url=BASE_URL+'/stomp';
  socket=new WebSocket(url.replace(/http:/i, 'ws:'));
  socket.onopen=function(){
    console.log('Websocket connected');
  };
  socket.onerror=function(e){
    console.log('Websocket error: '+e.data);
  };
  socket.onclose=function(e){
    console.log('Websocket closing: '+e.data);
  };
}
function subscribeToTopic(topic){
  connectWebSocket();
  if(socket.readyState==0){
    socket.onopen=function() {
      socket.send(JSON.stringify({
        'type':'SUBSCRIBE',
        'topic':topic
      }));
      console.log('Websocket subscribing to topic: '+topic);
    }
  }else{
    socket.send(JSON.stringify({
      'type':'SUBSCRIBE',
      'topic':topic
    }));
    console.log('Websocket subscribing to topic: '+topic);
  }
}
function unsubscribeToTopic(topic){
  console.log('Unsubscribing to topic...');
  if(socket!==null&&socket.readyState!=0){
    socket.send(JSON.stringify({
      'type':'UNSUBSCRIBE',
      'topic':topic
    }));
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