var authenticated={};
var isAdmin;
var isGuest;
const guest={};
guest.displayName='Guest';
guest.name='guest';
guest.role='GUEST';
guest.password=null;
$(document).ready(function(){
  $(window).on("hashchange",function(e){
    // url changes on login,need to be fixed
    // logout();
  });
  $(window).on("unload",function(e){
    // logout();
  });
  $.ajaxSetup({
    timeout:80000,
    beforeSend:function(xhr,settings){
      var authenticationToken=Cookies.get('token');
      if(authenticationToken != null){
        xhr.setRequestHeader('Authorization',authenticationToken);
      }
      if(!settings.url.includes('health') && typeof resetSessionInactivityTimer==='function'){
        resetSessionInactivityTimer();
      }
    },
    complete:function(request){
      var value=request.getResponseHeader('X-Expired-Authorization');
      var authenticationToken=Cookies.get('token');
      if(authenticationToken != null && isValid(value)){
        Cookies.remove('token');
        setAuthenticatedUser(guest);
      }
    },
    error:function(x,status,error){
      handleAjaxError(x,status,error);
    }
  });
  var currentPage=Cookies.get('currentPage');
  if(isValid(currentPage)){
    console.log('Restoring page: '+currentPage);
    Cookies.set('currentPage',currentPage,{
      path : '/',
      expires : 7
    });
  }
  setAuthenticatedUser(null);
});
function setAuthenticatedUser(response,token){
  var authenticationToken=Cookies.get('token');
  // console.log('Cookie token is: '+authenticationToken);
  if((response==null||response.name==='guest')&&authenticationToken==null){
    console.log('Invalid response and not already connected');
    authenticated=guest;
    isAdmin=false;
    isGuest=true;
    Cookies.remove('token');
    Cookies.remove('displayName');
    Cookies.remove('id');
    Cookies.remove('name');
    Cookies.remove('role');
  }else{
    // console.log("Response: "+JSON.stringify(response));
    if(response==null){
      console.log('Invalid response');
      authenticated={};
      authenticated.displayName=Cookies.get('displayName');
      authenticated.id=Cookies.get('id');
      authenticated.name=Cookies.get('name');
      authenticated.role=Cookies.get('role');
      authenticated.email=Cookies.get('email');
      authenticated.password='';
    }else{
      // console.log('Processing response');
      authenticated=response;
      authenticationToken=token;
    }
    isAdmin=authenticated.role==='ADMINISTRATOR';
    isGuest=authenticated.role==='GUEST';
    // console.log('Token is: '+authenticationToken);
    Cookies.set('token',authenticationToken,cookieOptions);
    Cookies.set('displayName',authenticated.displayName,cookieOptions);
    Cookies.set('id',authenticated.id,cookieOptions);
    Cookies.set('name',authenticated.name,cookieOptions);
    Cookies.set('role',authenticated.role,cookieOptions);
    Cookies.set('email',authenticated.email,cookieOptions);
    $('#in_usracc_id').val(authenticated.id);
    $('#in_usracc_display_name').val(authenticated.displayName);
    $('#in_usracc_email').val(authenticated.email);
    $('#in_usracc_password').val('');
    $('#in_usracc_current_password').val(authenticated.password);
  }
  console.log('Authenticated: '+authenticated.name+'('+isAdmin+','+isGuest+')');
  if(typeof disconnectWebSocket==='function'){
    disconnectWebSocket();
  }
  if(authenticated==null||isGuest){
    $('#user_display_name').html(authenticated.displayName);
    $('#div_account').hide();
    $('#mni_login').show();
  }else{
    $('#user_display_name').html(authenticated.displayName);
    $('#mni_login').hide();
    $('#div_account').show();
  }
  var currentContent=Cookies.get('currentPage');
  if (!isAdmin) {
    if(currentContent==='users'||currentContent==='acls'){
      currentContent=DEFAULT_CONTENT;
    }
  }
  showContent(currentContent);
  $('.admin-feature').each(function(){
    if (isAdmin){
      $(this).show();
    }else{
      $(this).hide();
    }
  });
}
