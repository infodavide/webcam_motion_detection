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
    var serviceUrl=REST_BASE_URL+'/app/health';
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
        $('#system_status').html(response.sys.cpuLoad+'%');
        if(response.health===0){
          $('.menu').css('background','green');
          if(typeof subscribeToTopic==='function'&&!isValid(socket)&&isValid(controller)){
            controller.init();
          }
        }else if(response.health===-1){
          $('.menu').css('background','yellow');
        }else{
          if (typeof disconnectWebSocket==='function') {
            disconnectWebSocket();
          }
          $('.menu').css('background','red');
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
  var content='<h1>Disk</h1>';
  content+=addTableHeader();
  content+=addTableRow('Usage','The greater percentage of used space on disks',health.storage.status+'%');
  // disks
  for(var i=0;i<health.storage.disks.length;i++){
    var item=health.storage.disks[i];
    var text='Status: '+item.status+'%<br/>';
    text+='Free space: '+item.usable+'<br/>';
    text+='Total space: '+item.total+'<br/>';
    text+='Used space: '+item.used;
    content+=addTableRow(item.name,'The path or name of the disk or partition',text);
  }
  $('#content').html(content);
}

function showMemory(){
  if(!isValid(health)){
    console.log('health is not valid');
    return;
  }
  // header
  var content='<h1>Memory</h1>';
  content+=addTableHeader();
  // system
  content+=addTableRow('Usage','The percentage of used memory space',health.memory.sys.status+'%');
  content+=addTableRow('Free memory','The amount of free memory on the system',health.memory.sys.free);
  content+=addTableRow('Total memory','The total amount of memory on the system',health.memory.sys.total);
  content+=addTableRow('Used memory','The amount of used memory',health.memory.sys.used);
  // swap
  content+=addTableRow('Total Swap memory','The total amount of swap memory',health.memory.swap.total);
  content+=addTableRow('Used Swap memory','The amount of used swap memory',health.memory.swap.used);
  $('#content').html(content);
}

function showSystem(){
  if(!isValid(health)){
    console.log('health is not valid');
    return;
  }
  // header
  var content='<h1>System</h1>';
  content+=addTableHeader();
  content+=addTableRow('Logical processors','The number of logical processors',health.sys.processors);
  content+=addTableRow('Uptime','The uptime',health.sys.uptime);
  content+=addTableRow('CPU load','The greater percentage of used CPU',health.sys.cpuLoad+'%');
  content+=addTableRow('CPU temperature','The CPU temperature',health.sys.cpuTemperature+'°');
  $('#content').html(content);
}