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
  $.i18n().load({
    'en': 'js/i18n/en.json',
    'it': 'js/i18n/it.json',
    'fr': 'js/i18n/fr.json'
   }).done(function() {
    var userLanguage=Cookies.get('language');
    if (!isValid(userLanguage)){
      userLanguage=navigator.language||navigator.userLanguage;
      if (isValid(userLanguage)){
        userLanguage=userLanguage.split('-')[0];
        $.i18n().locale=userLanguage;
      }
    }
    applyTranslations();
    $('body').bind('DOMSubtreeModified', function(e){
      applyTranslation(e);
    });
  });
});