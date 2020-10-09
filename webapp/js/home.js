/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class HomeController{
  /* initialize the main view */
  init(){
    console.log('Initialization of HomeController...');
    subscribeToTopic('video');
    content = '<div id="video"><img id="video_img" src="' + BASE_URL + '/video" style="-webkit-user-select: none;" width="1037" height="583"/></div>';
    $('#content').html(content);
    if(socket!=null){
      socket.onmessage=function(e){obj._onMessage(e);};
    }
  }
  /* process the incoming websocket message */
  _onMessage(e){
    if(isValid(e.data)){
      var message=JSON.parse(e.data);
      // console.log(message);
      if(isValid(message)&&message.topic==='video'){
        var d = new Date();
        $('#video_img').attr('src', BASE_URL + '/video?'+d.getTime());
      }else{
        onWebSocketMessage(e);
      }
    }
  }
}
const homeController=new HomeController();