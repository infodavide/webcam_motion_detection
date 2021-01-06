var refreshTimeoutId=null;
var health=null;
var refreshTime=60;
var healthCheckEnabled=false;
$(document).ready(function(){
  setRefreshTime(Cookies.get('refreshTime'));
  loadHealth(true);
});
function setRefreshTime(seconds){
  if(!isValid(seconds)){
    seconds=60;
  }
  healthCheckEnabled=seconds>0;
  console.log('Setting health refresh time to '+seconds+'s');
  Cookies.set('refreshTime', seconds, cookieOptions);
  if(healthCheckEnabled){
    refreshTime=seconds;
    if(refreshTime % 60==0){
      $('#refresh_time').html((refreshTime/60)+'min');
    }else{
      $('#refresh_time').html(refreshTime+'s');
    }
  }else{
    $('#refresh_time').html('Disabled');
  }
}
function loadHealth(force, callback){
  if(healthCheckEnabled||health==null||force){
    const serviceUrl=REST_BASE_URL+'/app/health';
    jQuery.ajax({
      timeout:2000,
      type:'GET',
      url:serviceUrl,
      dataType:'json',
      async:true,
      accept:'application/json',
      contentType:'application/json',
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
        health=response;
        if(response.health==0){ // running
          $('.menu').css('background','green');
          $('#status').html($.i18n('running'));
          if(typeof subscribeToTopic==='function'&&!isValid(socket)&&isValid(controller)){
            controller.init();
          }
        }else if(response.health==1){ // not activated
          $('.menu').css('background','lightgreen');
          $('#status').html($.i18n('disabled'));
          if(typeof subscribeToTopic==='function'&&!isValid(socket)&&isValid(controller)){
            controller.init();
          }
        }else if(response.health==2){ // suspended
          $('.menu').css('background','grey');
          $('#status').html($.i18n('suspended'));
          if(typeof subscribeToTopic==='function'&&!isValid(socket)&&isValid(controller)){
            controller.init();
          }
        }else if(response.health==-1){ // off
          $('.menu').css('background','yellow');
          $('#status').html($.i18n('off'));
        }else{ // error or hardware heavy load
          if(typeof disconnectWebSocket==='function') {
            disconnectWebSocket();
          }
          $('.menu').css('background','red');
          $('#status').html($.i18n('error'));
        }
      },
      complete:function(){
        if(callback!=null){
          callback();
        }
      },
      error:function(){
        if(typeof disconnectWebSocket==='function'){
          disconnectWebSocket();
        }
        $('.menu').css('background','red');
      }
    });
  }
  console.log('Resetting health timer to '+refreshTime+'s');
  if(refreshTimeoutId!=null){
    clearTimeout(refreshTimeoutId);
  }
  refreshTimeoutId=setTimeout(loadHealth,refreshTime*1000);
}