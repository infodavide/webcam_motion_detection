const BASE_URL=window.location.protocol.startsWith('file') ? 'http://localhost:8080' : window.location.protocol+'//'+document.domain+':'+location.port;
const REST_BASE_URL=BASE_URL+'/rest';
const DEFAULT_CONTENT='projects';
const cookieOptions={
  path: '/',
  expires: 7
};
var controller=null;
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
    timeout:10000,
    error:function(x,status,error){
      handleAjaxError(x,status,error);
    }
  });
  var trigger=$('.hamburger');
  trigger.click(function(){
    hamburger_cross();
  });
  $("[data-hide]").on("click", function(){
    $(this).closest("." + $(this).attr("data-hide")).hide();
  });
  $('[data-toggle="offcanvas"]').click(function(){
    $('#wrapper').toggleClass('toggled');
    $('#menubar_wrapper').toggleClass('toggled');
    $('#btn_hamburger').toggleClass('toggled');
  });
  $('#content').click(function(){
    var menubar_wrapper=$('#menubar_wrapper');
    if(menubar_wrapper.hasClass('toggled')){
      menubar_wrapper.toggleClass('toggled');
    }
    var wrapper=$('#wrapper');
    if(wrapper.hasClass('toggled')){
      wrapper.toggleClass('toggled');
      hamburger_cross();
    }
    var btn_hamburger=$('#btn_hamburger');
    if(btn_hamburger.hasClass('toggled')){
      btn_hamburger.toggleClass('toggled');
    }
  });
});
function handleAjaxError(x,status,error){
  // console.log('x: '+JSON.stringify(x));
  // console.log('status: '+JSON.stringify(status));
  // console.log('error: '+JSON.stringify(error));
  var message;
  if(isValid(x.status)&&x.status==200){
    return;
  }
  if(isValid(x.status)&&x.status==401){
    message='Unauthorized: Authentication is required';
  }else if(isValid(x.responseText)&&x.responseText!==''){
    message='Error code: '+x.status+'<br/>Message: '+x.responseText;
  }else if(isValid(error)&&error!==''){
    message='Error code: '+x.status+'<br/>Message: '+error;
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
  console.log(message);
  var alert_messages=$('#alert_messages');
  while(alert_messages.children('div').length > 4){
    // we keep the fist one as it is the template for alert messages
    alert_messages.children('div')[1].remove();
  }
  // we clone the template for alert messages
  var alert_message=alert_messages.find('#alert_message_template').clone();
  var timeago=alert_message.find('time');
  timeago.attr('datetime', new Date().toISOString())
  timeago.timeago();
  alert_message.removeAttr('id');
  alert_message.removeClass('alert-success alert-info alert-warning alert-danger');
  var icon=alert_message.find('.icon')
  icon.removeClass('info-icon warning-icon error-icon');
  var panel=alert_message.find('.message')
  if(type==-1){
    panel.attr('title','Error message');
    icon.addClass('error-icon');
    alert_message.addClass('alert-danger');
  }else if(type==0){
    panel.attr('title','Warning message');
    icon.addClass('warning-icon');
    alert_message.addClass('alert-warning');
  }else{
    panel.attr('title','Information message');
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
function hamburger_cross(){
  var trigger=$('.hamburger'),overlay=$('.overlay');
  if(trigger.hasClass('is-open')){
    overlay.hide();
    trigger.removeClass('is-open');
    trigger.addClass('is-closed');
  }else{
    overlay.show();
    trigger.removeClass('is-closed');
    trigger.addClass('is-open');
  }
}
function showContent(newContent){
  if(typeof unsubscribeToTopic==='function'){
    unsubscribeToTopic('');
  }
  if(newContent===null||typeof newContent=='undefined'||newContent==='null'){
    newContent=DEFAULT_CONTENT;
  }
  Cookies.set('currentPage',newContent,cookieOptions);
  // console.log(newContent);
  controller=null;
  if(newContent=='home'){
    controller=homeController;
  }else if(newContent=='system'){
    loadHealth(true,showSystem);
  }else if(newContent=='disk'){
    loadHealth(true,showDisk);
  }else if(newContent=='memory'){
    loadHealth(true,showMemory);
  }else if(newContent=='settings'){
    controller=settingController;
  }else if(newContent=='help'){
    showHelp();
  }
  if(controller!=null){
    controller.init();
  }
}
