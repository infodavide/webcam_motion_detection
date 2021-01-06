function basename(path) {
  return path.replace(/.*\//, '');
}
function dirname(path) {
  return path.match(/.*\//)[0].slice(0,-1);
}
const BASE_URL=window.location.protocol+'//'+document.domain+':'+location.port;
const REST_BASE_URL=BASE_URL+'/rest';
const DEFAULT_CONTENT='home';
const cookieOptions={
  path: '/',
  expires: 7
};
Handlebars.registerHelper('BASE_URL',function(options){
  return BASE_URL;
});
Handlebars.registerHelper('REST_BASE_URL',function(options){
  return REST_BASE_URL;
});
function capitalize(value) {
  return value.charAt(0).toUpperCase()+value.slice(1);
}
$(document).ready(function(){
  var _old_hide=$.fn.hide;
  $.fn.hide=function(){
    $(this).addClass('invisible');
    $(this).removeClass('visible');
    return _old_hide.apply(this,arguments);
  };
  var _old_show=$.fn.show;
  $.fn.show=function(){
    $(this).addClass('visible');
    $(this).removeClass('invisible');
    return _old_show.apply(this,arguments);
  };
  $.each(['show','hide'],function(i,ev){
    var el=$.fn[ev];
    $.fn[ev]=function(){
      this.trigger(ev);
      return el.apply(this,arguments);
    };
  });
  $.timeago.settings.refreshMillis=15000;
  $('time.timeago').timeago();
  $.ajaxSetup({
    timeout:60000,
    error:function(x,status,error){
      handleAjaxError(x,status,error);
    }
  });
  $("[data-hide]").on("click", function(){
    $(this).closest("." + $(this).attr("data-hide")).hide();
  });
});
function handleAjaxError(x,status,error){
  var message;
  if(isValid(x.status)&&x.status==200){
    return;
  }
  if(isValid(x.status)&&x.status==401){
    message=$.i18n('unauthorized')+': '+$.i18n('authentication_required');
  }else if(isValid(x.responseText)&&x.responseText!==''){
    message=$.i18n('error_code')+': '+x.status+'<br/>'+$.i18n('message')+': '+x.responseText;
  }else if(isValid(error)&&error!==''){
    message=$.i18n('error_code')+': '+x.status+'<br/>'+$.i18n('message')+': '+error;
  }
  if(isValid(x.status)&&x.status!=400){
    showError(message);
  }
}
function clearAlerts(){
  $('#alert_messages').children('div').each(function() {
    if($(this).attr('id')!='alert_message_template'){
      $(this).remove();
    }
  });
}
function showAlert(message,type){
  if(!isValid(message)){
    clearAlerts();
    return;
  }
  var alert_messages=$('#alert_messages');
  while(alert_messages.children('div').length > 4){
    // we keep the fist one as it is the template for alert messages
    alert_messages.children('div')[1].remove();
  }
  // we clone the template for alert messages
  var alert_message=alert_messages.find('#alert_message_template').clone();
  const timeago=alert_message.find('time');
  timeago.attr('datetime', new Date().toISOString())
  timeago.timeago();
  alert_message.removeAttr('id');
  alert_message.removeClass('alert-success alert-info alert-warning alert-danger');
  const icon=alert_message.find('.icon')
  icon.removeClass('info-icon warning-icon error-icon');
  const panel=alert_message.find('.message')
  if(type==-1){
    panel.attr('title',$.i18n('error'));
    icon.addClass('error-icon');
    alert_message.addClass('alert-danger');
  }else if(type==0){
    panel.attr('title',$.i18n('warning'));
    icon.addClass('warning-icon');
    alert_message.addClass('alert-warning');
  }else{
    panel.attr('title',$.i18n('information'));
    icon.addClass('info-icon');
    alert_message.addClass('alert-info');
  }
  panel.html(message);
  alert_messages.append(alert_message);
  alert_message.show();
  $('html, body').animate({
    scrollTop: 0
  }, 1000);
}
function showError(message){
  showAlert(message,-1);
}
function showInfo(message){
  showAlert(message,1);
}
function showWarning(message){
  showAlert(message,0);
}
var controller;
function showContent(newContent){
  if(newContent===null||typeof newContent=='undefined'||newContent==='null'){
    newContent=DEFAULT_CONTENT;
  }
  Cookies.set('currentPage',newContent,cookieOptions);
  if(newContent=='detection_zone'){
    controller=new DetectionZoneController();
  }else if(newContent=='detection_periods'){
    controller=new DetectionPeriodsController();
  }else if(newContent=='detection_filters'){
    controller=new DetectionFiltersController();
  }else if(newContent=='status'){
    controller=new StatusController();
  }else if(newContent=='settings'){
    controller=new SettingsController();
  }else if(newContent=='help'){
    showHelp();
  }else{
    controller=new HomeController();
  }
}
$(document).ready(function(){
  console.log('Initializing...');
  var path=BASE_URL+'/templates/header.html';
  $.ajax({
    url: path,
    cache:true,
    success:function(data){
      var templateInput={};
      var template=Handlebars.compile(data);
      $('#header').html(template(templateInput));
      if(menuController){
        menuController.update();
      }
    }
  });
  path=BASE_URL+'/templates/footer.html';
  $.ajax({
    url: path,
    cache:true,
    success:function(data){
      var templateInput={};
      var template=Handlebars.compile(data);
      $('#footer').html(template(templateInput));
    }
  });
});