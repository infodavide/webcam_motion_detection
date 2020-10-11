/* methods prefixed by '_' can be considered as private or protected (called by the other methods of the object or by html handler defined by this class */
class SettingsController{
  /* constructor */
  constructor(){
    console.log('Initialization of SettingsController...');
    this._values=[];
    $('#content').html('<div id="settings_content"></div>');
    // name, type, read-only, required, min, max, visible without authentication
    this._definitions=[
      ['version','string',true,true,0,0,false],
      ['video_device','string',false,true,4,96,true],
      ['video_device_address','string',false,true,4,512,true],
      ['notification_delay','number',false,true,0,3600,true],
      ['http_port','number',false,true,80,65535,true],
      ['user_display_name','string',false,true,4,128,true],
      ['email','string',false,true,3,255,false],
      ['user','string',true,true,0,0,false],
      ['password','password',false,false,0,32,false]
    ];
    this._get();
  }
  getResourceKey(){
    return 'settings';
  }
  _showValues(values){
    var content='<div style="margin-top:16px;"><h1 data-i18n="settings"></h1><p data-i18n="settings_description"></p>';
    var disabled;
    if(isAdmin){
      disabled=false;
      content+='<form id="settings_form" onsubmit="controller._save();return false;">';
    }else{
      disabled=true;
    }
    content+='<div class="row row-header">';
    content+='<div class="column col-lg-2 col-header" data-i18n="name"></div>';
    content+='<div class="column col-lg-5 col-header" data-i18n="value"></div>';
    content+='<div class="column col-lg-5 col-header" data-i18n="comment"></div>';
    content+='</div>';
    content+='<div id="settings_div">';
    console.log('Listing settings...');
    if(isValid(values)){
      this._definitions.forEach(function(definition){
        // name, type, read-only, required, min, max, visible without authentication
        if(definition[6]||isAdmin){
          content+='<div class="row">';
          content+='<div class="column col-lg-2 capitalized" data-i18n="'+definition[0]+'"></div>';
          const disabled=definition[2]||!isAdmin;
          const options=buildInputOptions(definition[0]+'_input',definition[1],definition[3],disabled,definition[4],definition[5]);
          var value=values[definition[0]];
          if(definition[1]=='password'){
            value=''
          }
          content+='<div class="column col-lg-5">';
          content+=buildInput($.i18n(definition[0]), value, options);
          content+='</div><div class="column col-lg-5 capitalized" data-i18n="'+definition[0]+'_description"></div>';
          content+='</div>';
        }
      });
    }else{
      content+='<div class="row"><div class="column col-lg-12" data-i18n="no_setting"></div></div>';
    }
    content+='</div>';
    if(isAdmin){
      content+='<div style="margin-top:16px;">';
      content+='<button type="submit" id="btn_submit_settings" class="btn btn-primary mb-2" data-i18n="save"></button>';
      content+='<button id="btn_cancel_settings" class="btn btn-primary mb-2" onclick="controller._cancel();" data-i18n="cancel"></button>';
      content+='</div>';
      content+='</form>';
    }
    content+='</div>';
    $('#settings_content').html(content);
  }
  _get(){
    const obj=this;
    jQuery.ajax({
      type:'GET',
      url:REST_BASE_URL+'/'+obj.getResourceKey(),
      dataType:'json',
      async:true,
      accept:'application/json',
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
        var values={};
        if(isValid(response)){
          values=response;
        }
        obj._showValues(values);
      },
      error:function(x,status,error){
        handleAjaxError(x,status,error);
      }
    });
  }
  _save(){
    if(!isAdmin){
      return;
    }
    const obj=this;
    var data={};
    this._definitions.forEach(function(definition){
      // name, type, read-only, required, min, max, visible without authentication
      if(definition[2]){
        return;
      }
      var v=$('#'+definition[0]+'_input').val();
      if(!isValid(v)){
        console.log(definition[0] + ' is not valid: ' + v);
      }else if(v==''){
        console.log(definition[0] + ' is empty and ignored');
      }else if(definition[1]=='boolean'){
        data[definition[0]]=v.toLowerCase()=='true';
      }else if(definition[1]=='number'){
        data[definition[0]]=parseInt(v);
      }else if(definition[1]=='password'){
        data[definition[0]]=md5(v);
      }else{
        data[definition[0]]=v;
      }
    });
    const json=JSON.stringify(data);
    // console.log('JSON: '+json);
    jQuery.ajax({
      type:"POST",
      url:REST_BASE_URL+'/'+obj.getResourceKey(),
      async:true,
      contentType:'application/json',
      dataType: 'json',
      data:json,
      success:function(response){
        // console.log("Response: "+JSON.stringify(response));
      },
      error:function(x){
        handleValidationError(obj.getResourceKey(),x);
      }
    });
  }
}