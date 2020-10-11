const BASE_URL=window.location.protocol.startsWith('file') ? 'http://localhost:8080' : window.location.protocol+'//'+document.domain+':'+location.port;
const REST_BASE_URL=BASE_URL+'/rest';
const DEFAULT_CONTENT='home';
const cookieOptions={
  path: '/',
  expires: 7
};
var controller=null;
function capitalize(value) {
  return value.charAt(0).toUpperCase()+value.slice(1);
}
var applyingTranslation=false;
function setLanguage(value){
  if (!isValid(value)){
    return;
  }
  $.i18n().locale=value;
  Cookies.set('language',value,cookieOptions);
}
function applyTranslations(){
  if(applyingTranslation){
    return;
  }
  applyingTranslation=true;
  $('html').i18n();
  applyingTranslation=false;
}
function applyTranslation(e){
  if(applyingTranslation){
    return;
  }
  if(e.target&&e.target.id){
    applyingTranslation=true;
    $('#'+e.target.id).i18n();
    applyingTranslation=false;
  }
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
  $.i18n().load({
    'en': 'js/i18n/en.json',
    'it': 'js/i18n/it.json',
    'fr': 'js/i18n/fr.json'
   }).done(function() {
    console.log('i18n loaded');
    var userLanguage=Cookies.get('language');
    if (!isValid(userLanguage)){
      userLanguage=navigator.language||navigator.userLanguage;
      if (isValid(userLanguage)){
        userLanguage=userLanguage.split('-')[0];
        $.i18n().locale=userLanguage;
      }
    }
    console.log('Language: '+$.i18n().locale);
    applyTranslations();
    $('body').bind('DOMSubtreeModified', function(e){
      applyTranslation(e);
    });
  });
  $.ajaxSetup({
    timeout:60000,
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
    const menubar_wrapper=$('#menubar_wrapper');
    if(menubar_wrapper.hasClass('toggled')){
      menubar_wrapper.toggleClass('toggled');
    }
    const wrapper=$('#wrapper');
    if(wrapper.hasClass('toggled')){
      wrapper.toggleClass('toggled');
      hamburger_cross();
    }
    const btn_hamburger=$('#btn_hamburger');
    if(btn_hamburger.hasClass('toggled')){
      btn_hamburger.toggleClass('toggled');
    }
  });
});
function handleAjaxError(x,status,error){
  //console.log('x: '+JSON.stringify(x));
  //console.log('status: '+JSON.stringify(status));
  //console.log('error: '+JSON.stringify(error));
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
  console.log(message);
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
  if(newContent=='detection_zone'){
    controller=new DetectionZoneController();
  }else if(newContent=='detection_periods'){
    controller=new DetectionPeriodsController();
  }else if(newContent=='detection_filters'){
    controller=new DetectionFiltersController();
  }else if(newContent=='system'){
    loadHealth(true,showSystem);
  }else if(newContent=='disk'){
    loadHealth(true,showDisk);
  }else if(newContent=='memory'){
    loadHealth(true,showMemory);
  }else if(newContent=='network'){
    loadHealth(true,showNetwork);
  }else if(newContent=='settings'){
    controller=new SettingsController();
  }else if(newContent=='help'){
    showHelp();
  }else{
    controller=new HomeController();
  }
  $('#content').i18n();
}
