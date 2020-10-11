var refreshTimeoutId=null;
var health=null;
var refreshTime=300;
var healthCheckEnabled=false;
$(document).ready(function(){
  setRefreshTime(Cookies.get('refreshTime'));
  loadHealth(true);
});
function setRefreshTime(seconds){
  if(!isValid(seconds)){
    seconds=300;
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
        $('#storage_status').html(response.storage.status+'%');
        $('#memory_status').html(response.memory.sys.status+'%');
        $('#system_status').html(response.sys.cpuLoad);
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
        $('#storage_status').html('N/A');
        $('#memory_status').html('N/A');
        $('#system_status').html('N/A');
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
function showDisk(){
  if(!isValid(health)){
    console.log('health is not valid');
    return;
  }
  // header
  var content='<h1>'+$.i18n('storage')+'</h1>';
  content+=addTableHeader();
  content+=addTableRow($.i18n('usage'), $.i18n('the_greater_percentage_of_used_space'),health.storage.status+'%');
  // disks
  for(var i=0;i<health.storage.disks.length;i++){
    const item=health.storage.disks[i];
    var text=$.i18n('status')+': '+item.status+'%<br/>';
    text+=$.i18n('free_space')+': '+item.usable+'<br/>';
    text+=$.i18n('total_space')+': '+item.total+'<br/>';
    text+=$.i18n('used_space')+': '+item.used;
    content+=addTableRow(item.name,$.i18n('the_path_or_name_of_the_partition'),text);
  }
  $('#content').html(content);
}
function showMemory(){
  if(!isValid(health)){
    console.log('health is not valid');
    return;
  }
  // header
  var content='<h1>'+$.i18n('memory')+'</h1>';
  content+=addTableHeader();
  // system
  content+=addTableRow($.i18n('usage'),$.i18n('the_percentage_of_used_space'),health.memory.sys.status+'%');
  content+=addTableRow($.i18n('free_space'),$.i18n('the_amount_of_free_space'),health.memory.sys.free);
  content+=addTableRow($.i18n('total_space'),$.i18n('the_total_amount_of_space'),health.memory.sys.total);
  content+=addTableRow($.i18n('used_space'),$.i18n('the_amount_of_used_space'),health.memory.sys.used);
  // swap
  content+=addTableRow($.i18n('total_swap_space'),$.i18n('the_total_amount_of_swap_space'),health.memory.swap.total);
  content+=addTableRow($.i18n('used_swap_space'),$.i18n('the_amount_of_used_swap_space'),health.memory.swap.used);
  $('#content').html(content);
}
function showSystem(){
  if(!isValid(health)){
    console.log('health is not valid');
    return;
  }
  // header
  var content='<h1>'+$.i18n('system')+'</h1>';
  content+=addTableHeader();
  content+=addTableRow($.i18n('processors'),$.i18n('the_number_of_processors'),health.sys.processors);
  content+=addTableRow($.i18n('uptime'),$.i18n('the_duration_since_start'),health.sys.uptime);
  content+=addTableRow($.i18n('cpu_load'),$.i18n('the_cpu_load'),health.sys.cpuLoad+'%');
  content+=addTableRow($.i18n('cpu_temperature'),$.i18n('the_cpu_temperature'),health.sys.cpuTemperature+'°');
  content+=addTableRow($.i18n('mac_address'),$.i18n('the_mac_address'),health.sys.macAddress);
  content+=addTableRow($.i18n('ipv4_address'),$.i18n('the_ipv4_address'),health.sys.ipv4Address);
  content+=addTableRow($.i18n('ssid'),$.i18n('the_ssid'),health.sys.ssid);
  $('#content').html(content);
}