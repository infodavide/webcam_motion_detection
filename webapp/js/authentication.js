var authenticated={};
var isAdmin;
var isGuest;
const guest={};
guest.displayName=$.i18n('guest');
guest.name='guest';
guest.role='GUEST';
guest.password=null;
guest.email=null;
guest.id=0;
$(document).ready(function(){
  $(window).on("hashchange",function(e){
    // url changes on login,need to be fixed
    // logout();
  });
  $(window).on("unload",function(e){
    // logout();
  });
  $('.admin-feature').each(function(){
    if(isAdmin){
      $(this).show();
    }else{
      $(this).hide();
    }
  });
  $.ajaxSetup({
    timeout:80000,
    beforeSend:function(xhr,settings){
      var authenticationToken=Cookies.get('token');
      if(authenticationToken != null){
        xhr.setRequestHeader('Authorization',authenticationToken);
      }
    },
    complete:function(request){
      var value=request.getResponseHeader('X-Session-Inactivity-Timeout');
      if(isValid(value)&&typeof setSessionInactivityTime==='function'){
        setSessionInactivityTime(value * 60);
      }
      if(!this.url.includes('/health')&&typeof resetSessionInactivityTimer==='function'){
        resetSessionInactivityTimer();
      }
      value=request.getResponseHeader('X-Expired-Authorization');
      var authenticationToken=Cookies.get('token');
      if(authenticationToken!= null&&isValid(value)){
        Cookies.remove('token');
        setAuthenticatedUser(guest);
      }
    },
    error:function(x,status,error){
      handleAjaxError(x,status,error);
    }
  });
  const currentPage=Cookies.get('currentPage');
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
  var authenticationToken=token;
  if(!isValid(authenticationToken)){
    authenticationToken=Cookies.get('token');
  }
  console.log("Response: "+JSON.stringify(response));
  console.log('Token is: '+authenticationToken);
  if(authenticationToken==null&&(response==null||response.name==='guest')){
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
    if(response==null){
      authenticated={};
      authenticated.displayName=Cookies.get('displayName');
      authenticated.id=Cookies.get('id');
      authenticated.name=Cookies.get('name');
      authenticated.role=Cookies.get('role');
      authenticated.email=Cookies.get('email');
    }else{
      // console.log('Processing response');
      authenticated=response;
    }
    isAdmin=authenticated.role==='ADMINISTRATOR';
    isGuest=authenticated.role==='GUEST';
    Cookies.set('displayName',authenticated.displayName,cookieOptions);
    Cookies.set('id',authenticated.id,cookieOptions);
    Cookies.set('name',authenticated.name,cookieOptions);
    Cookies.set('role',authenticated.role,cookieOptions);
    Cookies.set('email',authenticated.email,cookieOptions);
    Cookies.set('token',authenticationToken,cookieOptions);
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
  var currentContent=DEFAULT_CONTENT;
  if(authenticated==null||isGuest){
    $('#user_display_name').html('');
    $('#div_account').hide();
    $('#mni_login').show();
  }else{
    $('#user_display_name').html(authenticated.displayName);
    $('#mni_login').hide();
    $('#div_account').show();
    currentContent=Cookies.get('currentPage');
  }
  showContent(currentContent);
  $('.admin-feature').each(function(){
    if(isAdmin){
      $(this).show();
    }else{
      $(this).hide();
    }
  });
}
var sessionInactivityTimeoutId=null;
var sessionInactivityTimeout=600;
function setSessionInactivityTime(seconds){
  if(!isValid(seconds)){
    seconds=600;
  }
  console.log('Setting session inactivity time to '+seconds+'s');
  sessionInactivityTimeout=seconds;
  Cookies.set('sessionInactivityTime',seconds,cookieOptions);
}
function resetSessionInactivityTimer(){
  if(sessionInactivityTimeoutId!=null){
    clearTimeout(sessionInactivityTimeoutId);
  }
  if(sessionInactivityTimeout<=0){
    console.log('Resetting session inactivity timer to none');
    sessionInactivityTimeoutId=null;
  }else if(!isGuest){
    console.log('Resetting session inactivity timer to '+sessionInactivityTimeout+'s');
    sessionInactivityTimeoutId=setTimeout(logout,sessionInactivityTimeout*1000);
  }
}
function login(id){
  console.log('Login...');
  var json={};
  json.name=$('#signin_username').val();
  json.password=$('#signin_password').val();
  // password of users are never transferred or stored in clear,always in MD5
  json.password=md5(json.password);
  // console.log("Login with data: "+JSON.stringify(json));
  jQuery.ajax({
    type:"POST",
    url:REST_BASE_URL+'/login',
    async:true,
    accept:'application/json',
    contentType:'application/json; charset=UTF-8',
    data:JSON.stringify(json),
    dataType:'json',
    success:function(response,textStatus,request){
      // console.log("Login response: "+JSON.stringify(response));
      const token=request.getResponseHeader('X-Authorization');
      if(isValid(token)){
        setAuthenticatedUser(response,token);
      }else{
        setAuthenticatedUser(response,response.password);
      }
      $('#'+id).find('.close').click();
    },
    error:function(x,status,error){
      // console.log('x: '+JSON.stringify(x));
      // console.log('status: '+JSON.stringify(status));
      // console.log('error: '+JSON.stringify(error));
      var message;
      if(isValid(x.status)&&x.status==401){
        message='Unauthorized: Authentication is required';
        const input=$('#signin_username')[0];
        if(isValid(input)){
          input.setCustomValidity("Wrong user or password");
        }
        const form=$('#signin_form')[0];
        if(isValid(form)){
          form.reportValidity();
        }
      }else if(isValid(x.responseText)&&x.responseText!==''){
        message='Error code: '+x.status+'<br/>Message: '+x.responseText;
      }else if(isValid(error)&&error!==''){
        message='Error code: '+x.status+'<br/>Message: '+error;
      }
      if(isValid(x.status)&&x.status!=400){
        showError(message);
      }
    }
  });
}
function logout() {
  console.log('Logout...');
  jQuery.ajax({
    type:"POST",
    url:REST_BASE_URL+'/logout',
    async:true,
    dataType:'text',
    complete:function(response){
      // console.log("Response: "+JSON.stringify(response));
      Cookies.remove('token');
      setAuthenticatedUser(null);
    }
  });
}
